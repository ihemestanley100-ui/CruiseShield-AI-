import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { AiAssessment } from "../lib/api";
import { ExecKpis } from "./exec-kpis";

function runFixture(): AiAssessment {
  return {
    agent_run_id: "agentrun_0002",
    model_id: "muse-spark-1.3",
    status: "SUCCEEDED",
    prompt_version: "v1",
    conclusion: "c",
    missing_information: [],
    key_findings: [],
    schema_validation_status: "PASS",
    evidence_reference_validation_status: "PASS",
    latency_ms: 1200,
    completed_at: "2026-10-27T10:05:00Z",
  };
}

const BASE = {
  invId: "inv_84721",
  invStatus: "OPEN",
  networkBand: "HIGH",
  evidenceCount: 39,
  decisionsCount: 0,
  caseId: "case_84721",
  caseStatus: "NEW",
};

describe("ExecKpis", () => {
  it("renders six real metrics with transparent captions", () => {
    render(
      <ExecKpis {...BASE} latestRun={runFixture()} txnCount={11} txnPending={false} />
    );
    expect(screen.getByLabelText("1 Active investigations")).toBeTruthy();
    expect(screen.getByLabelText("11 Transactions monitored")).toBeTruthy();
    expect(screen.getByLabelText("1 High-risk investigations")).toBeTruthy();
    expect(screen.getByLabelText("39 Evidence records")).toBeTruthy();
    expect(screen.getByText("agentrun_0002")).toBeTruthy();
    expect(screen.getByLabelText("0 Human decisions")).toBeTruthy();
    expect(screen.getByText("requires analyst action", { exact: false })).toBeTruthy();
  });

  it("shows honest states for missing metrics", () => {
    render(
      <ExecKpis
        {...BASE}
        latestRun={null}
        txnCount={null}
        txnPending={false}
      />
    );
    expect(screen.getByText("Not available")).toBeTruthy();
    expect(screen.getByText("None yet")).toBeTruthy();
  });
});
