import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { WorkflowStrip } from "./workflow-strip";

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

describe("WorkflowStrip", () => {
  it("links every stage to its real destination", () => {
    render(
      <WorkflowStrip
        invId="inv_84721"
        txnId="txn_84721"
        caseId="case_84721"
        scenarioId="scn_primary"
      />
    );
    const nav = screen.getByRole("navigation", {
      name: "Investigation workflow",
    });
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
    for (const label of [
      "Detect",
      "Connect",
      "Investigate",
      "Explain",
      "Simulate",
      "Human Decision",
      "Audit",
    ]) {
      expect(screen.getByText(label)).toBeTruthy();
    }
  });
});
