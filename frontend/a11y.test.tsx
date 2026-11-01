/* Automated accessibility smoke checks (jsdom-level).
 * Proves: one h1 per page, every button named, every input labelled,
 * graph canvases carry role + label. Real contrast/AT behavior still
 * needs a browser; this file does not claim that. */
import { render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import CommandPage from "./app/demo/page";
import { DecisionForm } from "./components/decision-form";
import { GraphExplorer } from "./components/graph-explorer";
import type { GraphEdge, GraphNode } from "./lib/api";

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
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

vi.mock("./lib/api", async (importOriginal) => ({
  ...((await importOriginal()) as object),
  getHealth: getHealthMock,
  getInvestigation: getInvestigationMock,
  getGraph: getGraphMock,
  getCase: getCaseMock,
  getCaseAudit: getCaseAuditMock,
  getReplay: getReplayMock,
}));

function node(id: string, type = "account"): GraphNode {
  return {
    node_id: id,
    node_type: type,
    display_label: `Label ${id}`,
    synthetic_flag: true,
    source_record_ids: [`seed:scn_primary:${id}`],
  };
}

function edge(id: string, src: string, tgt: string): GraphEdge {
  return {
    edge_id: id,
    source_node_id: src,
    target_node_id: tgt,
    relationship_type: "SENT_TO",
    source_event_ids: ["evt_demo_84721"],
    evidence_ids: [`evidence_${id}`],
    valid_from: "2026-10-27T10:00:00Z",
    valid_to: null,
    synthetic_flag: true,
    trace_id: "trace_demo_84721",
  };
}

function risk(score: number, band: string, scope: string) {
  return {
    risk_assessment_id: `risk_${scope}_84721`,
    target_id: "txn_84721",
    target_type: scope,
    score,
    band,
    score_version: "risk-score-v1",
    computed_at: "2026-10-27T10:00:00Z",
    limitations: "Demo limitations.",
  };
}

beforeEach(() => {
  getHealthMock.mockReset();
  getInvestigationMock.mockReset();
  getGraphMock.mockReset();
  getCaseMock.mockReset();
  getCaseAuditMock.mockReset();
  getReplayMock.mockReset();
  getReplayMock.mockResolvedValue({
    total: 0,
    counts: { events: 0, transactions: 0, edges: 0 },
  });
  getHealthMock.mockResolvedValue({
    status: "healthy",
    version: "1.0.0-p0",
    scenario_id: "scn_primary",
    run_id: "run_test",
    checks: { store: "PASS" },
  });
  getInvestigationMock.mockResolvedValue({
    investigation: {
      investigation_id: "inv_84721",
      alert_id: "alert_84721",
      transaction_id: "txn_84721",
      status: "OPEN",
    },
    alert: { alert_id: "alert_84721", title: "t", status: "OPEN" },
    transaction: {
      transaction_id: "txn_84721",
      amount_minor: 48000000,
      currency: "NGN",
      channel: "MOBILE_APP",
      sender_account_id: "acct_A",
      receiver_account_id: "acct_B",
      occurred_at: "2026-10-27T10:00:00Z",
    },
    risk_transaction: risk(35, "MODERATE", "transaction"),
    risk_network: risk(84, "HIGH", "network"),
    rule_results: [],
    case: { case_id: "case_84721", status: "OPEN" },
    evidence_package_id: "evidence_pkg_scn_primary_1.0.0",
    evidence_count: 39,
  });
  getGraphMock.mockResolvedValue({
    transaction_id: "txn_84721",
    nodes: [node("acct_A"), node("acct_B")],
    edges: [edge("edge_0001", "acct_A", "acct_B")],
    provenance_errors: [],
    counts: { nodes: 22, edges: 30 },
  });
  getCaseMock.mockResolvedValue({
    case: {
      case_id: "case_84721",
      investigation_id: "inv_84721",
      status: "OPEN",
      created_at: "2026-10-27T10:00:00Z",
      updated_at: "2026-10-27T10:00:00Z",
      trace_id: "trace_demo_84721",
    },
    decisions: [],
    allowed_transitions: [],
    latest_ai_run: null,
  });
  getCaseAuditMock.mockResolvedValue({ audits: [] });
});

function expectButtonsNamed(scope: HTMLElement) {
  // queryAllByRole: some scopes legitimately have zero buttons.
  const buttons = within(scope).queryAllByRole("button");
  for (const b of buttons) {
    const name = (b.textContent ?? "").trim() || b.getAttribute("aria-label");
    expect(name, `unnamed button: ${b.outerHTML.slice(0, 120)}`).toBeTruthy();
  }
}

function expectInputsLabelled(scope: HTMLElement) {
  const inputs = scope.querySelectorAll("input, select, textarea");
  for (const el of inputs) {
    const labelled =
      (el as HTMLInputElement).labels?.length ||
      el.getAttribute("aria-label") ||
      el.getAttribute("aria-labelledby");
    expect(
      labelled,
      `unlabelled control: ${el.outerHTML.slice(0, 120)}`
    ).toBeTruthy();
  }
}

describe("accessibility smoke", () => {
  it("Command Center has one h1, named buttons, labelled controls", async () => {
    const { container } = render(<CommandPage />);
    await waitFor(() =>
      expect(screen.getAllByText("healthy")).toHaveLength(1)
    );
    await waitFor(() =>
      expect(screen.getByText("Risk intelligence")).toBeTruthy()
    );
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expectButtonsNamed(container);
    expectInputsLabelled(container);
    const preview = screen.getByRole("img", { name: /Network preview/ });
    expect(preview).toBeTruthy();
  });

  it("DecisionForm controls are all labelled and the submit is named", () => {
    const { container } = render(
      <DecisionForm
        caseId="case_84721"
        allowedTransitions={["INVESTIGATING"]}
        onDecided={() => {}}
      />
    );
    expectInputsLabelled(container);
    expect(
      screen.getByRole("button", { name: "Record decision" })
    ).toBeTruthy();
  });

  it("graph canvas exposes role, label, and named nodes", () => {
    const { container } = render(
      <GraphExplorer
        nodes={[node("acct_A"), node("acct_B")]}
        edges={[edge("edge_0001", "acct_A", "acct_B")]}
      />
    );
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("role")).toBe("img");
    expect(svg?.getAttribute("aria-label")).toContain("2 nodes");
    expectButtonsNamed(container);
  });
});
