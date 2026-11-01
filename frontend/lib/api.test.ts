import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
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
  getTransactionIntel,
  listAlerts,
  listScenarios,
  postAiAnalysis,
  postAiFollowup,
  postDecision,
  postLogin,
  postLogout,
  postSimulation,
  resetDemo,
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
  it("calls the investigation endpoint with an encoded id", async () => {
    const fetchMock = mockFetchOnce({ investigation: {} });
    await getInvestigation("inv_84721");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/investigations/inv_84721",
      expect.objectContaining({ cache: "no-store" })
    );
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

  it("lists scenarios and posts demo reset", async () => {
    const fetchMock = mockFetchOnce({ scenarios: [] });
    await listScenarios();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/demo/scenarios",
      expect.objectContaining({ cache: "no-store" })
    );
    await resetDemo("scn_primary");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "http://127.0.0.1:8000/api/v1/demo/reset",
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
    vi.stubEnv("NEXT_PUBLIC_DEMO_WRITE_TOKEN", "demo-token-1");
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
    // Only the documented public demo credential plus the Phase 5 CSRF
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
