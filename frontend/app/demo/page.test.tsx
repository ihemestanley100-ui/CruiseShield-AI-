import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  type AuditEntry,
  type CaseDetail,
  type GraphResponse,
  type HealthCheck,
  type InvestigationDetail,
} from "../../lib/api";
import CommandPage from "./page";

const {
  getHealthMock,
  getInvestigationMock,
  getGraphMock,
  getCaseMock,
  getCaseAuditMock,
  getReplayMock,
} = vi.hoisted(() => ({
  getHealthMock: vi.fn(),
  getInvestigationMock: vi.fn(),
  getGraphMock: vi.fn(),
  getCaseMock: vi.fn(),
  getCaseAuditMock: vi.fn(),
  getReplayMock: vi.fn(),
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: React.ReactNode;
    [key: string]: unknown;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

vi.mock("../../lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getHealth: getHealthMock,
  getInvestigation: getInvestigationMock,
  getGraph: getGraphMock,
  getCase: getCaseMock,
  getCaseAudit: getCaseAuditMock,
  getReplay: getReplayMock,
}));

function healthFixture(): HealthCheck {
  return {
    status: "healthy",
    version: "1.0.0-p0",
    scenario_id: "scn_primary",
    run_id: "run_test",
    checks: { store: "PASS", seed_integrity: "PASS" },
  };
}

function investigationFixture(): InvestigationDetail {
  const rules = [
    "R-001",
    "R-002",
    "R-003",
    "R-004",
    "R-005",
    "R-006",
    "R-007",
    "R-008",
  ].map((rule_id) => ({
    rule_result_id: `rr_${rule_id}_84721`,
    rule_id,
    rule_version: "1.0",
    triggered: true,
    threshold: "seeded",
    explanation: `${rule_id} seeded explanation.`,
    source_record_ids: ["txn_84721"],
    evidence_ids: [`evidence_rr_${rule_id}_84721`],
    trace_id: "trace_demo_84721",
  }));
  return {
    investigation: {
      investigation_id: "inv_84721",
      alert_id: "alert_84721",
      transaction_id: "txn_84721",
      status: "OPEN",
    },
    alert: { alert_id: "alert_84721", title: "Seeded alert", status: "OPEN" },
    transaction: {
      transaction_id: "txn_84721",
      amount_minor: 48000000,
      currency: "NGN",
      channel: "MOBILE_APP",
      sender_account_id: "acct_A",
      receiver_account_id: "acct_B",
      occurred_at: "2026-10-27T10:00:00Z",
    },
    risk_transaction: {
      risk_assessment_id: "risk_transaction_84721",
      target_id: "txn_84721",
      target_type: "transaction",
      score: 35,
      band: "MODERATE",
      score_version: "risk-score-v1",
      computed_at: "2026-10-27T10:00:00Z",
      limitations: "Deterministic demo risk score.",
    },
    risk_network: {
      risk_assessment_id: "risk_network_84721",
      target_id: "txn_84721",
      target_type: "network",
      score: 84,
      band: "HIGH",
      score_version: "risk-score-v1",
      computed_at: "2026-10-27T10:00:00Z",
      limitations: "Deterministic demo risk score.",
    },
    rule_results: rules,
    case: { case_id: "case_84721", status: "OPEN" },
    evidence_package_id: "evidence_pkg_scn_primary_1.0.0",
    evidence_count: 39,
  };
}

function graphFixture(): GraphResponse {
  return {
    transaction_id: "txn_84721",
    nodes: [
      {
        node_id: "acct_A",
        node_type: "account",
        display_label: "Account A",
        synthetic_flag: true,
        source_record_ids: ["seed:scn_primary:acct_A"],
      },
      {
        node_id: "acct_B",
        node_type: "account",
        display_label: "Account B",
        synthetic_flag: true,
        source_record_ids: ["seed:scn_primary:acct_B"],
      },
      {
        node_id: "dev_04",
        node_type: "device",
        display_label: "Device 04",
        synthetic_flag: true,
        source_record_ids: ["seed:scn_primary:dev_04"],
      },
    ],
    edges: [
      {
        edge_id: "edge_0001",
        source_node_id: "acct_A",
        target_node_id: "acct_B",
        relationship_type: "SENT_TO",
        source_event_ids: ["evt_demo_84721"],
        evidence_ids: ["evidence_edge_0001"],
        valid_from: "2026-10-27T10:00:00Z",
        valid_to: null,
        synthetic_flag: true,
        trace_id: "trace_demo_84721",
      },
      {
        edge_id: "edge_0002",
        source_node_id: "acct_B",
        target_node_id: "dev_04",
        relationship_type: "USES_DEVICE",
        source_event_ids: ["evt_demo_84721"],
        evidence_ids: ["evidence_edge_0002"],
        valid_from: "2026-10-27T10:00:00Z",
        valid_to: null,
        synthetic_flag: true,
        trace_id: "trace_demo_84721",
      },
    ],
    provenance_errors: [],
    counts: { nodes: 22, edges: 30 },
  };
}

function caseFixture(): CaseDetail {
  return {
    case: {
      case_id: "case_84721",
      investigation_id: "inv_84721",
      status: "OPEN",
      created_at: "2026-10-27T10:00:00Z",
      updated_at: "2026-10-27T10:00:00Z",
      trace_id: "trace_demo_84721",
    },
    decisions: [],
    allowed_transitions: ["INVESTIGATING"],
    latest_ai_run: {
      agent_run_id: "agentrun_0001",
      model_id: "muse-spark-1.3",
      status: "SUCCEEDED",
      prompt_version: "v1",
      conclusion: "Network shows coordinated device sharing.",
      missing_information: [],
      key_findings: [
        {
          finding: "Device dev_04 shared by three accounts.",
          confidence_label: "high",
          evidence_ids: ["evidence_edge_0002"],
        },
      ],
      schema_validation_status: "PASS",
      evidence_reference_validation_status: "PASS",
      latency_ms: 1200,
      completed_at: "2026-10-27T10:05:00Z",
    },
  };
}

function auditFixture(): { audits: AuditEntry[] } {
  return {
    audits: [
      {
        audit_event_id: "audit_0001",
        actor_type: "service",
        actor_id: "seed",
        action: "demo.reset",
        target_type: "scenario",
        target_id: "case_84721",
        previous_state_reference: "",
        new_state_reference: "scn_primary",
        reason: "seeded scenario",
        timestamp: "2026-10-27T10:00:00Z",
        trace_id: "trace_demo_84721",
        request_id: "req_1",
      },
    ],
  };
}

function replayFirst() {
  return {
    scenario_id: "scn_primary",
    cursor: 0,
    total: 11,
    current_event: null,
    cumulative_event_ids: [],
    cumulative_transaction_ids: [],
    cumulative_edge_ids: [],
    counts: { events: 0, transactions: 0, edges: 0 },
  };
}

function replayFull() {
  return {
    ...replayFirst(),
    cursor: 11,
    counts: { events: 11, transactions: 11, edges: 30 },
  };
}

function mockAllReady() {
  getHealthMock.mockResolvedValue(healthFixture());
  getInvestigationMock.mockResolvedValue(investigationFixture());
  getGraphMock.mockResolvedValue(graphFixture());
  getCaseMock.mockResolvedValue(caseFixture());
  getCaseAuditMock.mockResolvedValue(auditFixture());
  getReplayMock.mockImplementation((_id: string, cursor: number) =>
    Promise.resolve(cursor === 0 ? replayFirst() : replayFull())
  );
}

beforeEach(() => {
  getHealthMock.mockReset();
  getInvestigationMock.mockReset();
  getGraphMock.mockReset();
  getCaseMock.mockReset();
  getCaseAuditMock.mockReset();
  getReplayMock.mockReset();
});

describe("CommandPage", () => {
  it("renders the workflow navigation with real routes", async () => {
    mockAllReady();
    render(<CommandPage />);
    // Single status source: one "healthy" badge in the status panel.
    await waitFor(() =>
      expect(screen.getAllByText("healthy")).toHaveLength(1)
    );
    const nav = screen.getByRole("navigation", {
      name: "Investigation workflow",
    });
    expect(nav).toBeTruthy();
    const links = [...nav.querySelectorAll("a")].map((a) =>
      a.getAttribute("href")
    );
    expect(links).toEqual([
      "/investigations/inv_84721",
      "/network/txn_84721",
      "/investigations/inv_84721",
      "/investigations/inv_84721#ai-h",
      "/replay/scn_primary",
      "/cases/case_84721",
      "/cases/case_84721/audit",
    ]);
  });

  it("shows backend values from the live response only", async () => {
    mockAllReady();
    render(<CommandPage />);
    await waitFor(() =>
      expect(
        screen.getByText("scenario scn_primary", { exact: false })
      ).toBeTruthy()
    );
    expect(screen.getByText("run_test", { exact: false })).toBeTruthy();
  });

  it("shows the authoritative network and transaction scores distinctly", async () => {
    mockAllReady();
    render(<CommandPage />);
    await waitFor(() =>
      expect(screen.getByLabelText("Risk 84 of 100, HIGH")).toBeTruthy()
    );
    expect(screen.getByLabelText("Risk 35 of 100, MODERATE")).toBeTruthy();
    expect(screen.getByText("Transaction #84721")).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: "Transaction-only risk" })
    ).toBeTruthy();
  });

  it("shows evidence, rules, network preview, AI brief, and activity", async () => {
    mockAllReady();
    render(<CommandPage />);
    await waitFor(() =>
      expect(screen.getByLabelText("39 evidence records")).toBeTruthy()
    );
    for (const id of [
      "R-001",
      "R-002",
      "R-003",
      "R-004",
      "R-005",
      "R-006",
      "R-007",
      "R-008",
    ]) {
      expect(screen.getByText(id, { exact: false })).toBeTruthy();
    }
    expect(
      screen.getByTestId("network-preview-counts").textContent
    ).toContain("22 nodes");
    expect(
      screen.getByTestId("network-preview-counts").textContent
    ).toContain("30 edges");
    expect(
      screen.getByText("Network shows coordinated device sharing.", {
        exact: false,
      })
    ).toBeTruthy();
    expect(screen.getByText("evidence_edge_0002")).toBeTruthy();
    expect(screen.getByText("audit_0001")).toBeTruthy();
  });

  it("shows executive metrics from live responses only", async () => {
    mockAllReady();
    render(<CommandPage />);
    await waitFor(() =>
      expect(screen.getByLabelText("11 Transactions monitored")).toBeTruthy()
    );
    expect(screen.getByLabelText("1 Active investigations")).toBeTruthy();
    expect(screen.getByLabelText("1 High-risk investigations")).toBeTruthy();
    // Latest run ID appears in the exec card and the AI brief metadata.
    expect(screen.getAllByText("agentrun_0001")).toHaveLength(2);
    expect(screen.getByLabelText("0 Human decisions")).toBeTruthy();
  });

  it("links feature cards to real destinations", async () => {
    mockAllReady();
    const { container } = render(<CommandPage />);
    await waitFor(() =>
      expect(screen.getByText("Deterministic replay")).toBeTruthy()
    );
    const hrefs = [...container.querySelectorAll(".feature-card")].map((a) =>
      a.getAttribute("href")
    );
    expect(hrefs).toEqual([
      "/investigations/inv_84721",
      "/network/txn_84721",
      "/replay/scn_primary",
      "/investigations/inv_84721#evidence-h",
      "/cases/case_84721",
      "/cases/case_84721/audit",
    ]);
  });

  it("shows an honest error with recovery guidance when all calls fail", async () => {
    const failure = new ApiError("BACKEND_UNREACHABLE", "Failed to fetch", 0, "");
    getHealthMock.mockRejectedValue(failure);
    getInvestigationMock.mockRejectedValue(failure);
    getGraphMock.mockRejectedValue(failure);
    getCaseMock.mockRejectedValue(failure);
    getCaseAuditMock.mockRejectedValue(failure);
    getReplayMock.mockRejectedValue(failure);
    render(<CommandPage />);
    // The message also appears in the hero status slot; the global card
    // owns the alert role plus recovery.
    await waitFor(() =>
      expect(screen.getByRole("alert").textContent).toContain(
        "BACKEND_UNREACHABLE: Failed to fetch"
      )
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeTruthy();
  });

  it("keeps working sections when one section fails", async () => {
    mockAllReady();
    getGraphMock.mockRejectedValue(
      new ApiError("UNKNOWN_TRANSACTION", "txn_84721", 404, "")
    );
    render(<CommandPage />);
    await waitFor(() =>
      expect(screen.getByLabelText("Risk 84 of 100, HIGH")).toBeTruthy()
    );
    expect(screen.getByText("Network preview unavailable")).toBeTruthy();
  });

  it("retries only the failed section and recovers", async () => {
    mockAllReady();
    getGraphMock.mockRejectedValueOnce(
      new ApiError("UNKNOWN_TRANSACTION", "txn_84721", 404, "")
    );
    render(<CommandPage />);
    await waitFor(() =>
      expect(screen.getByText("Network preview unavailable")).toBeTruthy()
    );
    const healthCalls = getHealthMock.mock.calls.length;
    const graphCalls = getGraphMock.mock.calls.length;
    fireEvent.click(
      screen.getByRole("button", { name: "Retry Network preview unavailable" })
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("network-preview-counts").textContent
      ).toContain("22 nodes")
    );
    expect(screen.queryByText("Network preview unavailable")).toBeNull();
    // Only the failed section refetched; healthy sections untouched.
    expect(getGraphMock.mock.calls.length).toBe(graphCalls + 1);
    expect(getHealthMock.mock.calls.length).toBe(healthCalls);
    expect(getInvestigationMock.mock.calls.length).toBe(1);
  });
});
