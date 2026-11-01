import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { FeatureCards } from "./feature-cards";

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

const BASE = {
  invId: "inv_84721",
  invStatus: "OPEN",
  txnId: "txn_84721",
  caseId: "case_84721",
  caseStatus: "NEW",
  scenarioId: "scn_primary",
};

describe("FeatureCards", () => {
  it("links every card to a real destination with live footers", () => {
    render(
      <FeatureCards
        {...BASE}
        graphCounts={{ nodes: 22, edges: 30 }}
        evidenceCount={39}
      />
    );
    for (const title of [
      "Investigations",
      "Network Explorer",
      "Replay & Simulation",
      "Evidence",
      "Cases",
      "Audit Trail",
    ]) {
      expect(screen.getByText(title)).toBeTruthy();
    }
    expect(screen.getByText("22 nodes · 30 edges")).toBeTruthy();
    expect(screen.getByText("39 records")).toBeTruthy();
    const links = [...document.querySelectorAll(".feature-card")].map((a) =>
      a.getAttribute("href")
    );
    expect(links).toEqual([
      "/investigations/inv_84721",
      "/network/txn_84721",
      "/replay/scn_primary",
      "/investigations/inv_84721#evidence-h",
      "/cases/case_84721",
      "/cases/case_84721/audit",
    ]);
  });

  it("labels unavailable footers honestly", () => {
    render(<FeatureCards {...BASE} graphCounts={null} evidenceCount={null} />);
    expect(screen.getByText("Graph unavailable")).toBeTruthy();
    expect(screen.getByText("Unavailable")).toBeTruthy();
  });
});
