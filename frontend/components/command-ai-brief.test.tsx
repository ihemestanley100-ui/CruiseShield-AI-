import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { AiAssessment } from "../lib/api";
import { CommandAiBrief } from "./command-ai-brief";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

function assessmentFixture(): AiAssessment {
  return {
    agent_run_id: "agentrun_0001",
    model_id: "muse-spark-1.3",
    status: "SUCCEEDED",
    prompt_version: "v1",
    conclusion: "Network shows coordinated device sharing.",
    missing_information: ["IP history"],
    key_findings: [
      {
        finding: "Device dev_04 shared by three accounts.",
        confidence_label: "high",
        evidence_ids: ["evidence_edge_0002", "evidence_edge_0004"],
      },
    ],
    schema_validation_status: "PASS",
    evidence_reference_validation_status: "PASS",
    latency_ms: 1200,
    completed_at: "2026-10-27T10:05:00Z",
  };
}

describe("CommandAiBrief", () => {
  it("shows the conclusion with evidence references, advisory only", () => {
    render(<CommandAiBrief assessment={assessmentFixture()} invId="inv_84721" />);
    expect(
      screen.getByText("Network shows coordinated device sharing.", {
        exact: false,
      })
    ).toBeTruthy();
    expect(screen.getByText("evidence_edge_0002")).toBeTruthy();
    expect(screen.getByText("evidence_edge_0004")).toBeTruthy();
    expect(screen.getByText("Advisory only", { exact: false })).toBeTruthy();
    expect(screen.getByText("muse-spark-1.3", { exact: false })).toBeTruthy();
  });

  it("shows an honest empty state when no run exists", () => {
    render(<CommandAiBrief assessment={null} invId="inv_84721" />);
    expect(screen.getByTestId("ai-brief-empty")).toBeTruthy();
    expect(
      screen
        .getByRole("link", { name: "Run analysis from the investigation" })
        .getAttribute("href")
    ).toBe("/investigations/inv_84721");
  });
});
