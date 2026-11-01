import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import CasePage from "./page";

const { getCaseMock, getCaseAuditMock, postDecisionMock, getInvestigationMock } =
  vi.hoisted(() => ({
    getCaseMock: vi.fn(),
    getCaseAuditMock: vi.fn(),
    postDecisionMock: vi.fn(),
    getInvestigationMock: vi.fn(),
  }));

vi.mock("next/navigation", () => ({
  useParams: () => ({ caseId: "case_84721" }),
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("../../../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getCase: getCaseMock,
  getCaseAudit: getCaseAuditMock,
  postDecision: postDecisionMock,
  getInvestigation: getInvestigationMock,
}));

function caseFixture() {
  return {
    case: {
      case_id: "case_84721",
      investigation_id: "inv_84721",
      status: "TRIAGED",
      created_at: "2026-10-28T00:00:00Z",
      updated_at: "2026-10-28T01:00:00Z",
      trace_id: "t",
    },
    decisions: [
      {
        decision_id: "decision_0001",
        case_id: "case_84721",
        actor_id: "investigator",
        actor_role: "INVESTIGATOR",
        decision: "Monitor",
        reason: "Triage note.",
        evidence_viewed: [],
        recommendation_at_decision: "",
        created_at: "2026-10-28T01:00:00Z",
        authorization_scope: "demo",
        trace_id: "t",
      },
    ],
    allowed_transitions: ["INVESTIGATING", "FALSE_POSITIVE"],
    latest_ai_run: null,
  };
}

function assessmentFixture() {
  return {
    agent_run_id: "agentrun_4",
    model_id: "muse-spark-1.3",
    status: "SUCCEEDED",
    prompt_version: "cs-prompt-v2",
    conclusion: "requires_review",
    missing_information: ["Device ownership records."],
    key_findings: [
      {
        finding: "dev_04 shared.",
        confidence_label: "high",
        evidence_ids: ["evidence_edge_0002"],
      },
    ],
    schema_validation_status: "VALIDATED",
    evidence_reference_validation_status: "VALIDATED",
    latency_ms: 16733,
    completed_at: "2026-10-29T00:00:00Z",
  };
}

function auditFixture() {
  return {
    audits: [
      {
        audit_event_id: "audit_0006",
        actor_type: "human",
        actor_id: "investigator",
        action: "case.decision",
        target_type: "case",
        target_id: "case_84721",
        previous_state_reference: "NEW",
        new_state_reference: "TRIAGED",
        reason: "Monitor: Triage note.",
        timestamp: "2026-10-28T01:00:00Z",
        trace_id: "t",
        request_id: "t",
      },
    ],
  };
}

beforeEach(() => {
  getCaseMock.mockReset();
  getCaseAuditMock.mockReset();
  postDecisionMock.mockReset();
  getInvestigationMock.mockReset();
  getCaseMock.mockResolvedValue(caseFixture());
  getCaseAuditMock.mockResolvedValue(auditFixture());
  // Risk strip is best-effort: default to unavailable so existing tests
  // assert the page without it; strip tests override per case.
  getInvestigationMock.mockRejectedValue(new Error("risk down"));
  // Same reduced-motion stub as the investigation page tests: badges
  // render their authoritative final value immediately and deterministically.
  vi.stubGlobal(
    "matchMedia",
    vi.fn().mockImplementation((query: string) => ({
      matches: query === "(prefers-reduced-motion: reduce)",
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }))
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("CasePage", () => {
  it("renders section navigation matching real section anchors", async () => {
    const { container } = render(<CasePage />);
    const nav = await screen.findByRole("navigation", { name: "On this page" });
    const hrefs = [...nav.querySelectorAll("a")].map((a) =>
      a.getAttribute("href")
    );
    expect(hrefs).toEqual([
      "#overview-h",
      "#ai-assessment-h",
      "#decision-history-h",
      "#human-decision-h",
      "#audit-h",
    ]);
    for (const href of hrefs) {
      expect(container.querySelector(href as string)).not.toBeNull();
    }
  });

  it("shows the linked investigation risk when available", async () => {
    getInvestigationMock.mockResolvedValue({
      risk_transaction: { score: 35, band: "MODERATE" },
      risk_network: {
        score: 84,
        band: "HIGH",
        score_version: "risk-score-v1",
      },
    });
    render(<CasePage />);
    const strip = await screen.findByTestId("case-risk");
    // The badge counts up on the wall clock; the band and scopes render
    // immediately, the exact figure needs its settle wait.
    expect(strip.textContent).toContain("HIGH");
    expect(strip.textContent).toContain("transaction-only 35/100 MODERATE");
    expect(strip.textContent).toContain("risk-score-v1");
    await waitFor(() =>
      expect(screen.getByTestId("case-risk").textContent).toContain("84/100")
    );
    expect(
      getInvestigationMock
    ).toHaveBeenCalledWith("inv_84721", expect.any(AbortSignal));
  });

  it("hides the risk strip when the investigation fetch fails", async () => {
    render(<CasePage />);
    await waitFor(() =>
      expect(screen.getByTestId("case-status")).toHaveTextContent("TRIAGED")
    );
    await waitFor(() =>
      expect(screen.queryByTestId("case-risk")).toBeNull()
    );
  });

  it("renders status, transitions, history and audit", async () => {
    const { container } = render(<CasePage />);
    await waitFor(() =>
      expect(screen.getByTestId("case-status")).toHaveTextContent("TRIAGED")
    );
    expect(screen.getByTestId("case-transitions")).toHaveTextContent(
      "INVESTIGATING, FALSE_POSITIVE"
    );
    expect(screen.getByTestId("decision-history")).toHaveTextContent(
      "Monitor"
    );
    expect(screen.getByTestId("decision-history")).toHaveTextContent(
      "Triage note."
    );
    expect(container.querySelectorAll("[data-audit-row]")).toHaveLength(1);
  });

  it("shows a loading state while the case detail is unavailable", async () => {
    let resolveCase!: (value: unknown) => void;
    getCaseMock.mockReturnValue(
      new Promise((resolve) => {
        resolveCase = resolve;
      })
    );
    render(<CasePage />);
    expect(screen.getByText("Loading case…")).toBeTruthy();
    expect(screen.queryByTestId("ai-assessment")).toBeNull();
    expect(screen.queryByTestId("ai-assessment-empty")).toBeNull();
    resolveCase(caseFixture());
    await waitFor(() =>
      expect(screen.getByTestId("case-status")).toHaveTextContent("TRIAGED")
    );
  });

  it("appends a recorded decision and its audit entry", async () => {
    postDecisionMock.mockResolvedValue({
      decision: {
        decision_id: "decision_0002",
        case_id: "case_84721",
        actor_id: "investigator",
        actor_role: "INVESTIGATOR",
        decision: "Escalate",
        reason: "Network review.",
        evidence_viewed: [],
        recommendation_at_decision: "",
        created_at: "2026-10-29T00:00:00Z",
        authorization_scope: "demo",
        trace_id: "t",
      },
      audit: {
        audit_event_id: "audit_0007",
        actor_type: "human",
        actor_id: "investigator",
        action: "case.decision",
        target_type: "case",
        target_id: "case_84721",
        previous_state_reference: "TRIAGED",
        new_state_reference: "INVESTIGATING",
        reason: "Escalate: Network review.",
        timestamp: "2026-10-29T00:00:00Z",
        trace_id: "t",
        request_id: "t",
      },
      case: {
        case_id: "case_84721",
        investigation_id: "inv_84721",
        status: "INVESTIGATING",
        created_at: "c",
        updated_at: "u",
        trace_id: "t",
      },
    });
    const { container } = render(<CasePage />);
    await waitFor(() =>
      expect(screen.getByTestId("case-status")).toHaveTextContent("TRIAGED")
    );
    fireEvent.change(screen.getByLabelText("Decision"), {
      target: { value: "Escalate" },
    });
    fireEvent.change(screen.getByLabelText(/Reason/), {
      target: { value: "Network review." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Record decision" }));
    await waitFor(() =>
      expect(screen.getByTestId("case-status")).toHaveTextContent(
        "INVESTIGATING"
      )
    );
    expect(postDecisionMock).toHaveBeenCalledTimes(1);
    expect(
      container.querySelector('[data-audit-row="audit_0007"]')
    ).not.toBeNull();
  });

  it("shows the advisory AI assessment without touching case state", async () => {
    getCaseMock.mockResolvedValue({
      ...caseFixture(),
      latest_ai_run: assessmentFixture(),
    });
    render(<CasePage />);
    await waitFor(() =>
      expect(screen.getByTestId("ai-assessment")).toHaveTextContent(
        "Conclusion: requires_review"
      )
    );
    const panel = screen.getByTestId("ai-assessment");
    expect(panel).toHaveTextContent("evidence_edge_0002");
    expect(panel).toHaveTextContent("Confidence: high");
    expect(
      screen.getByText(/Advisory only: Muse Spark analysis/)
    ).toBeTruthy();
    expect(
      screen.getByText(/Missing information:/)
    ).toHaveTextContent("Device ownership records.");
    // Advisory display changes nothing about the case itself.
    expect(screen.getByTestId("case-status")).toHaveTextContent("TRIAGED");
    expect(getCaseMock).toHaveBeenCalledTimes(1);
  });

  it("handles a missing AI assessment safely", async () => {
    getCaseMock.mockResolvedValue(caseFixture());
    render(<CasePage />);
    await waitFor(() =>
      expect(screen.getByTestId("ai-assessment-empty")).toHaveTextContent(
        "No AI investigation assessment is available yet."
      )
    );
    expect(screen.queryByTestId("ai-assessment")).toBeNull();
    expect(screen.getByTestId("case-status")).toHaveTextContent("TRIAGED");
  });

  it("handles an undefined assessment from a pre-F2 backend", async () => {
    const fixture = caseFixture() as unknown as Record<string, unknown>;
    delete fixture.latest_ai_run;
    getCaseMock.mockResolvedValue(fixture);
    render(<CasePage />);
    await waitFor(() =>
      expect(screen.getByTestId("ai-assessment-empty")).toHaveTextContent(
        "No AI investigation assessment is available yet."
      )
    );
    expect(screen.queryByTestId("ai-assessment")).toBeNull();
    // The rest of the page still works: history, form, audit.
    expect(screen.getByTestId("decision-history")).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Record decision" })
    ).toBeTruthy();
  });

  it("handles partial assessment fields without crashing", async () => {
    getCaseMock.mockResolvedValue({
      ...caseFixture(),
      // Partial payload by design: proves the UI tolerates it.
      latest_ai_run: {
        agent_run_id: "agentrun_9",
        conclusion: "requires_review",
      } as unknown as NonNullable<
        ReturnType<typeof caseFixture>["latest_ai_run"]
      >,
    });
    render(<CasePage />);
    await waitFor(() =>
      expect(screen.getByTestId("ai-assessment")).toHaveTextContent(
        "Conclusion: requires_review"
      )
    );
    expect(screen.getByTestId("ai-assessment")).toHaveTextContent(
      "unknown model"
    );
    expect(screen.getByTestId("case-status")).toHaveTextContent("TRIAGED");
  });

  it("shows a not-found state for an unknown case", async () => {
    getCaseMock.mockRejectedValue(
      new ApiError("CASE_NOT_FOUND", "no case", 404, "t")
    );
    render(<CasePage />);
    await waitFor(() =>
      expect(screen.getByText("Case not found")).toBeTruthy()
    );
  });

  it("shows an error with retry when the backend is unreachable", async () => {
    getCaseMock.mockRejectedValue(
      new ApiError("BACKEND_UNREACHABLE", "Failed to fetch", 0, "")
    );
    render(<CasePage />);
    await waitFor(() =>
      expect(
        screen.getByText("BACKEND_UNREACHABLE: Failed to fetch")
      ).toBeTruthy()
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeTruthy();
  });

  it("shows breadcrumbs with route params on every state", async () => {
    getCaseMock.mockRejectedValue(new ApiError("E", "m", 0, ""));
    getCaseAuditMock.mockRejectedValue(new ApiError("E", "m", 0, ""));
    render(<CasePage />);
    const nav = await screen.findByRole("navigation", { name: "Breadcrumb" });
    expect(nav.querySelector("a")?.getAttribute("href")).toBe("/demo");
    expect(
      within(nav).getByText("Case case_84721").getAttribute("aria-current")
    ).toBe("page");
  });
});
