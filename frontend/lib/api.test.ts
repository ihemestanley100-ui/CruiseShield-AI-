import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  getAccountIntel,
  getAiRun,
  getAuthMe,
  getAuthMode,
  getCase,
  getCaseAudit,
  getDevice,
  getGeoObservations,
  getGraph,
  getGraphOverlay,
  getHealth,
  getIntelEvidence,
  getInvestigation,
  getInvestigationIntel,
  getIpObservations,
  getReplay,
  getRisk,
  getRiskIntel,
  getTransaction,
  getTransactionIntel,
  listAlerts,
  listScenarios,
  postAiAnalysis,
  postAiFollowup,
  postDecision,
  postLogin,
  postLogout,
  postSimulation,
  REQUEST_TIMEOUT_MS,
  resetWorkspace,
  userErrorMessage,
} from "./api";

function mockFetchOnce(payload: unknown, ok = true, status = 200) {
  const fn = vi.fn().mockResolvedValue({
    ok,
    status,
    json: async () => payload,
  } as Response);
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("api client", () => {
  it("maps failures to user-worded messages without raw codes", () => {
    const t = (key: string) => `<${key}>`;
    expect(
      userErrorMessage(
        new ApiError("ADMIN_REQUIRED", "admin role required", 403, ""),
        t
      )
    ).toBe("<notPermitted>");
    expect(
      userErrorMessage(
        new ApiError("LOGIN_REQUIRED", "login required", 401, ""),
        t
      )
    ).toBe("<notPermitted>");
    expect(
      userErrorMessage(
        new ApiError("BACKEND_UNREACHABLE", "down", 0, ""),
        t
      )
    ).toBe("<unreachable>");
    expect(
      userErrorMessage(
        new ApiError("SIM_FAILED", "diverged", 500, ""),
        t
      )
    ).toBe("<loadFailed>");
    expect(
      userErrorMessage(
        new ApiError("REQUEST_TIMEOUT", "aborted", 0, ""),
        t
      )
    ).toBe("<timedOut>");
    expect(
      userErrorMessage(new ApiError("HTTP_503", "down", 503, ""), t)
    ).toBe("<unavailable>");
    expect(userErrorMessage(new Error("boom"), t)).toBe("<loadFailed>");
    expect(userErrorMessage(null, t)).toBe("<requestFailed>");
    // No code or English server text may leak into user-facing output.
    for (const code of ["ADMIN_REQUIRED", "LOGIN_REQUIRED", "SIM_FAILED"]) {
      const out = userErrorMessage(
        new ApiError(code, "server detail here", 500, ""),
        t
      );
      expect(out).not.toContain(code);
      expect(out).not.toContain("server detail here");
    }
  });

  it("calls the investigation endpoint with an encoded id", async () => {
    const fetchMock = mockFetchOnce({ investigation: {} });
    await getInvestigation("inv_84721");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/investigations/inv_84721",
      expect.objectContaining({ cache: "no-store" })
    );
  });

  it("times out a hung backend with REQUEST_TIMEOUT, not a hang", async () => {
    vi.useFakeTimers();
    try {
      // Behaves like real fetch: pends until its signal aborts.
      vi.stubGlobal(
        "fetch",
        vi.fn().mockImplementation(
          (_url: string, init?: { signal?: AbortSignal }) =>
            new Promise((_resolve, reject) => {
              init?.signal?.addEventListener("abort", () => {
                reject(
                  init.signal?.reason ??
                    new DOMException("Aborted", "AbortError")
                );
              });
            })
        )
      );
      const pending = getHealth();
      const assertion = expect(pending).rejects.toMatchObject({
        code: "REQUEST_TIMEOUT",
      });
      await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS + 100);
      await assertion;
    } finally {
      vi.useRealTimers();
    }
  });

  it("keeps caller cancellation as REQUEST_TIMEOUT and clears its timer", async () => {
    vi.useFakeTimers();
    try {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockImplementation(
          (_url: string, init?: { signal?: AbortSignal }) =>
            new Promise((_resolve, reject) => {
              init?.signal?.addEventListener("abort", () => {
                reject(
                  init.signal?.reason ??
                    new DOMException("Aborted", "AbortError")
                );
              });
            })
        )
      );
      const controller = new AbortController();
      const pending = getHealth(controller.signal);
      const assertion = expect(pending).rejects.toMatchObject({
        code: "REQUEST_TIMEOUT",
      });
      controller.abort();
      await assertion;
      expect(vi.getTimerCount()).toBe(0);
    } finally {
      vi.useRealTimers();
    }
  });

  it("lists alerts from the alerts endpoint", async () => {
    const fetchMock = mockFetchOnce({ alerts: [] });
    await listAlerts();
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/alerts",
      expect.objectContaining({ cache: "no-store" })
    );
  });

  it("maps the error envelope to ApiError", async () => {
    mockFetchOnce(
      {
        error: {
          code: "UNKNOWN_INVESTIGATION",
          message: "nope",
          trace_id: "t1",
        },
      },
      false,
      404
    );
    const err = (await getInvestigation("nope").catch(
      (e: unknown) => e
    )) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("UNKNOWN_INVESTIGATION");
    expect(err.status).toBe(404);
    expect(err.traceId).toBe("t1");
  });

  it("signals session expiry on 401/403 data responses (J3-P6)", async () => {
    const seen: string[] = [];
    const listener = (ev: Event) => seen.push(ev.type);
    window.addEventListener("csai:unauthorized", listener);
    try {
      mockFetchOnce({ error: { code: "LOGIN_REQUIRED" } }, false, 401);
      await getInvestigation("inv_84721").catch(() => null);
      mockFetchOnce({ error: { code: "ADMIN_REQUIRED" } }, false, 403);
      await postAiAnalysis("inv_84721").catch(() => null);
      mockFetchOnce({ error: { code: "X" } }, false, 500);
      await getInvestigation("inv_84721").catch(() => null);
      // Bad-password 401 on the login endpoint itself is not an expiry.
      mockFetchOnce({ error: { code: "INVALID_CREDENTIALS" } }, false, 401);
      await postLogin("judge", "wrong").catch(() => null);
      // Gate probes (/me) and logout outcomes are consumed by the gate
      // directly: signalling them re-triggers recheck() forever (/me
      // storm: 586 calls in one page load, observed in armed Edge QA).
      mockFetchOnce({ error: { code: "LOGIN_REQUIRED" } }, false, 401);
      await getAuthMe().catch(() => null);
      mockFetchOnce({ error: { code: "LOGIN_REQUIRED" } }, false, 401);
      await postLogout().catch(() => null);
    } finally {
      window.removeEventListener("csai:unauthorized", listener);
    }
    expect(seen).toEqual(["csai:unauthorized", "csai:unauthorized"]);
  });

  it("maps network failure to BACKEND_UNREACHABLE", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch"))
    );
    const err = (await getInvestigation("inv_1").catch(
      (e: unknown) => e
    )) as ApiError;
    expect(err.code).toBe("BACKEND_UNREACHABLE");
    expect(err.message).toBe("Failed to fetch");
  });

  it("posts AI analysis without inventing fields", async () => {
    const fetchMock = mockFetchOnce({ agent_run_id: "agentrun_9" });
    await postAiAnalysis("inv_84721");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/investigations/inv_84721/ai-analysis",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("calls the graph endpoint with an encoded id", async () => {
    const fetchMock = mockFetchOnce({ nodes: [], edges: [] });
    await getGraph("txn_84721");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/graph/txn_84721",
      expect.objectContaining({ cache: "no-store" })
    );
  });

  it("calls the graph overlay endpoint with an encoded id", async () => {
    const fetchMock = mockFetchOnce({ nodes: [], edges: [] });
    await getGraphOverlay("txn_84721");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/graph/txn_84721/overlay",
      expect.objectContaining({ cache: "no-store" })
    );
  });

  it("calls the DI-10 intel endpoints with encoded ids", async () => {
    const cases: [() => Promise<unknown>, string][] = [
      [() => getDevice("dev_04"), "/api/v1/devices/dev_04"],
      [() => getIpObservations("ip_02"), "/api/v1/ip-observations/ip_02"],
      [() => getGeoObservations("loc_01"), "/api/v1/geo-observations/loc_01"],
      [
        () => getTransactionIntel("txn_84721"),
        "/api/v1/transactions/txn_84721/intel",
      ],
      [
        () => getInvestigationIntel("inv_84721"),
        "/api/v1/investigations/inv_84721/intel",
      ],
      [
        () => getAccountIntel("acct_11"),
        "/api/v1/accounts/acct_11/intel",
      ],
      [
        () => getIntelEvidence("inv_84721"),
        "/api/v1/investigations/inv_84721/intel-evidence",
      ],
      [
        () => getRiskIntel("txn_84721"),
        "/api/v1/risk-intelligence/txn_84721",
      ],
    ];
    for (const [call, path] of cases) {
      const fetchMock = mockFetchOnce({});
      await call();
      expect(fetchMock).toHaveBeenCalledWith(
        `http://127.0.0.1:8000${path}`,
        expect.objectContaining({ cache: "no-store" })
      );
    }
  });

  it("calls the replay endpoint with scenario and cursor", async () => {
    const fetchMock = mockFetchOnce({ cursor: 3, total: 11 });
    await getReplay("scn_primary", 3);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/replay/scn_primary?cursor=3",
      expect.objectContaining({ cache: "no-store" })
    );
  });

  it("calls the transaction endpoint with an encoded id", async () => {
    const fetchMock = mockFetchOnce({ transaction: {} });
    await getTransaction("txn_84721");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/transactions/txn_84721",
      expect.objectContaining({ cache: "no-store" })
    );
  });

  it("calls the ai-run endpoint with an encoded id", async () => {
    const fetchMock = mockFetchOnce({ agent_run_id: "agentrun_1" });
    await getAiRun("agentrun_1");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/ai-runs/agentrun_1",
      expect.objectContaining({ cache: "no-store" })
    );
  });

  it("calls the risk endpoint with transaction and scope", async () => {
    const fetchMock = mockFetchOnce({ assessment: {} });
    await getRisk("txn_84721", "network");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/risk/txn_84721?scope=network",
      expect.objectContaining({ cache: "no-store" })
    );
  });

  it("posts simulations with target, ignored edges and assumption", async () => {
    const fetchMock = mockFetchOnce({ simulation_id: "sim_0001" });
    await postSimulation("txn_84721", ["edge_0002"], "Test assumption.");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/simulations",
      expect.objectContaining({ method: "POST" })
    );
    const body = JSON.parse(
      (fetchMock.mock.calls[0][1]?.body ?? "{}") as string
    );
    expect(body).toEqual({
      target_transaction_id: "txn_84721",
      ignored_edge_ids: ["edge_0002"],
      assumption: "Test assumption.",
      actor_id: "investigator",
    });
  });

  it("calls the case, decision and audit endpoints", async () => {
    const fetchMock = mockFetchOnce({ case: {} });
    await getCase("case_84721");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/cases/case_84721",
      expect.objectContaining({ cache: "no-store" })
    );
    await getCaseAudit("case_84721");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/cases/case_84721/audit",
      expect.objectContaining({ cache: "no-store" })
    );
  });

  it("posts decisions with the full validated payload", async () => {
    const fetchMock = mockFetchOnce({ decision: {} });
    await postDecision("case_84721", {
      decision: "Escalate",
      target_status: "INVESTIGATING",
      reason: "Network review.",
      actor_id: "investigator",
      evidence_viewed: [],
      recommendation: "",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/cases/case_84721/decisions",
      expect.objectContaining({ method: "POST" })
    );
    const body = JSON.parse(
      (fetchMock.mock.calls[0][1]?.body ?? "{}") as string
    );
    expect(body.decision).toBe("Escalate");
    expect(body.target_status).toBe("INVESTIGATING");
    expect(body.reason).toBe("Network review.");
  });

  it("lists scenarios and posts platform reset", async () => {
    const fetchMock = mockFetchOnce({ scenarios: [] });
    await listScenarios();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/platform/scenarios",
      expect.objectContaining({ cache: "no-store" })
    );
    await resetWorkspace("scn_primary");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/platform/reset",
      expect.objectContaining({ method: "POST" })
    );
    const body = JSON.parse(
      (fetchMock.mock.calls[1][1]?.body ?? "{}") as string
    );
    expect(body).toEqual({ scenario_id: "scn_primary" });
  });

  it("posts follow-ups with the question payload", async () => {
    const fetchMock = mockFetchOnce({ agent_run_id: "agentrun_10" });
    await postAiFollowup("inv_84721", "Why is dev_04 shared?");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/investigations/inv_84721/ai-followup",
      expect.objectContaining({ method: "POST" })
    );
    const body = JSON.parse(
      (fetchMock.mock.calls[0][1]?.body ?? "{}") as string
    );
    expect(body).toEqual({ question: "Why is dev_04 shared?" });
  });

  it("sends the write token on POSTs only when configured (D-002)", async () => {
    vi.stubEnv("NEXT_PUBLIC_DEMO_WRITE_TOKEN", "platform-token-1");
    const fetchMock = mockFetchOnce({ decision: {} });
    await postDecision("case_84721", {
      decision: "Monitor",
      target_status: "TRIAGED",
      reason: "x",
      actor_id: "tester",
      evidence_viewed: [],
      recommendation: "",
    });
    const headers = fetchMock.mock.calls[0][1]?.headers as Record<
      string,
      string
    >;
    expect(headers["Authorization"]).toBe("Bearer demo-token-1");
    // Only the documented public platform credential plus the Phase 5 CSRF
    // header — never anything else.
    expect(Object.keys(headers).sort()).toEqual([
      "Authorization",
      "Content-Type",
      "X-Requested-With",
    ]);
  });

  it("omits the Authorization header when no token is configured", async () => {
    vi.stubEnv("NEXT_PUBLIC_DEMO_WRITE_TOKEN", "");
    const fetchMock = mockFetchOnce({ decision: {} });
    await postDecision("case_84721", {
      decision: "Monitor",
      target_status: "TRIAGED",
      reason: "x",
      actor_id: "tester",
      evidence_viewed: [],
      recommendation: "",
    });
    const headers = fetchMock.mock.calls[0][1]?.headers as Record<
      string,
      string
    >;
    expect(headers["Authorization"]).toBeUndefined();
  });

  it("sends X-Requested-With on every POST (Phase 5 CSRF)", async () => {
    const fetchMock = mockFetchOnce({ agent_run_id: "agentrun_9" });
    await postAiAnalysis("inv_84721");
    await postAiFollowup("inv_84721", "q?");
    await postSimulation("txn_84721", [], "a");
    for (const call of fetchMock.mock.calls) {
      const headers = (call[1]?.headers ?? {}) as Record<string, string>;
      expect(headers["X-Requested-With"]).toBe("XMLHttpRequest");
    }
  });

  it("sends cookies on GET and POST (Phase 5 session)", async () => {
    const fetchMock = mockFetchOnce({});
    await getHealth();
    await postAiAnalysis("inv_84721");
    for (const call of fetchMock.mock.calls) {
      expect(call[1]?.credentials).toBe("include");
    }
  });

  it("calls the auth endpoints with the login payload", async () => {
    const fetchMock = mockFetchOnce({ auth_enabled: true });
    await getAuthMode();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/auth/mode",
      expect.objectContaining({ cache: "no-store" })
    );
    await getAuthMe();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/auth/me",
      expect.objectContaining({ cache: "no-store" })
    );
    await postLogin("judge", "s3cret");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/auth/login",
      expect.objectContaining({ method: "POST" })
    );
    const body = JSON.parse(
      (fetchMock.mock.calls[2][1]?.body ?? "{}") as string
    );
    expect(body).toEqual({ username: "judge", password: "s3cret" });
    await postLogout();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/auth/logout",
      expect.objectContaining({ method: "POST" })
    );
  });

  it("sends no credentials, tokens, or secrets by default", async () => {
    const fetchMock = mockFetchOnce({});
    await getHealth();
    await postAiAnalysis("inv_84721");
    for (const call of fetchMock.mock.calls) {
      const [url, init] = call as [string, RequestInit?];
      expect(url).not.toMatch(/key|token|secret|bearer/i);
      const headers = (init?.headers ?? {}) as Record<string, string>;
      for (const name of Object.keys(headers)) {
        expect(name.toLowerCase()).not.toMatch(
          /authorization|api[-_]?key|token|secret/
        );
      }
    }
  });
});
