import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { GraphResponse, InvestigationDetail } from "../lib/api";
import { CommandKpis } from "./command-kpis";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

function detailFixture(): InvestigationDetail {
  return {
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
    risk_transaction: {
      risk_assessment_id: "risk_transaction_84721",
      target_id: "txn_84721",
      target_type: "transaction",
      score: 35,
      band: "MODERATE",
      score_version: "risk-score-v1",
      computed_at: "2026-10-27T10:00:00Z",
      limitations: "Demo limitations.",
    },
    risk_network: {
      risk_assessment_id: "risk_network_84721",
      target_id: "txn_84721",
      target_type: "network",
      score: 84,
      band: "HIGH",
      score_version: "risk-score-v1",
      computed_at: "2026-10-27T10:00:00Z",
      limitations: "Demo limitations.",
    },
    rule_results: ["R-001", "R-002"].map((rule_id) => ({
      rule_result_id: `rr_${rule_id}_84721`,
      rule_id,
      rule_version: "1.0",
      triggered: true,
      threshold: "seeded",
      explanation: "seeded",
      source_record_ids: ["txn_84721"],
      evidence_ids: [`evidence_rr_${rule_id}_84721`],
      trace_id: "trace_demo_84721",
    })),
    case: { case_id: "case_84721", status: "OPEN" },
    evidence_package_id: "evidence_pkg_scn_primary_1.0.0",
    evidence_count: 39,
  };
}

function graphFixture(): GraphResponse {
  return {
    transaction_id: "txn_84721",
    nodes: [],
    edges: [],
    provenance_errors: [],
    counts: { nodes: 22, edges: 30 },
  };
}

describe("CommandKpis", () => {
  it("renders authoritative scores, evidence, network, and rules", () => {
    render(
      <CommandKpis
        detail={detailFixture()}
        graph={graphFixture()}
        graphPending={false}
      />
    );
    expect(screen.getByLabelText("Risk 84 of 100, HIGH")).toBeTruthy();
    expect(screen.getByLabelText("Risk 35 of 100, MODERATE")).toBeTruthy();
    expect(screen.getByText("Transaction #84721")).toBeTruthy();
    expect(screen.getByLabelText("39 evidence records")).toBeTruthy();
    expect(screen.getByLabelText("22 nodes")).toBeTruthy();
    expect(screen.getByLabelText("30 edges")).toBeTruthy();
    expect(screen.getByLabelText("2 of 2 rules triggered")).toBeTruthy();
    expect(
      screen.getByRole("link", { name: "Open network explorer" }).getAttribute("href")
    ).toBe("/network/txn_84721");
  });

  it("shows honest states when the graph is pending or missing", () => {
    const { rerender } = render(
      <CommandKpis
        detail={detailFixture()}
        graph={null}
        graphPending={true}
      />
    );
    expect(screen.getByText("Loading network…")).toBeTruthy();
    rerender(
      <CommandKpis
        detail={detailFixture()}
        graph={null}
        graphPending={false}
      />
    );
    expect(screen.getByText("Network data unavailable.")).toBeTruthy();
  });
});
