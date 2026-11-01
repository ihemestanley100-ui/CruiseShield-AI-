import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { RuleResult } from "../lib/api";
import { CommandRuleSummary } from "./command-rule-summary";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

function rule(rule_id: string, triggered: boolean): RuleResult {
  return {
    rule_result_id: `rr_${rule_id}_84721`,
    rule_id,
    rule_version: "1.0",
    triggered,
    threshold: "seeded",
    explanation: "seeded",
    source_record_ids: ["txn_84721"],
    evidence_ids: [`evidence_rr_${rule_id}_84721`],
    trace_id: "trace_demo_84721",
  };
}

describe("CommandRuleSummary", () => {
  it("shows every rule with text state, never color alone", () => {
    render(
      <CommandRuleSummary
        rules={[rule("R-001", true), rule("R-002", false)]}
        invId="inv_84721"
      />
    );
    expect(screen.getByTestId("rule-summary-counts").textContent).toContain(
      "1 of 2 rules triggered"
    );
    const items = screen.getAllByRole("listitem");
    expect(items[0].textContent).toContain("R-001");
    expect(items[0].textContent).toContain("triggered");
    expect(items[1].textContent).toContain("R-002");
    expect(items[1].textContent).toContain("not triggered");
    expect(
      screen
        .getByRole("link", { name: "Full explanations on the investigation" })
        .getAttribute("href")
    ).toBe("/investigations/inv_84721");
  });

  it("shows an honest empty state", () => {
    render(<CommandRuleSummary rules={[]} invId="inv_84721" />);
    expect(
      screen.getByText("No rule results returned for this assessment.")
    ).toBeTruthy();
  });
});
