import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { EvidenceItem } from "../lib/api";
import { EvidenceList } from "./evidence-list";

function item(id: string, type: string): EvidenceItem {
  return {
    evidence_id: id,
    evidence_type: type,
    title: `Title ${id}`,
    description: `Description ${id}`,
    event_ids: [],
    graph_edge_ids: [],
    rule_result_ids: [],
  };
}

const ITEMS = [
  item("evidence_txn_84721", "transaction"),
  item("evidence_rr_R-001_84721", "rule_result"),
  item("evidence_edge_0001", "graph_relationship"),
];

describe("EvidenceList", () => {
  it("renders all items with counts", () => {
    render(<EvidenceList items={ITEMS} />);
    expect(screen.getByText(/3 of 3/)).toBeTruthy();
    for (const entry of ITEMS) {
      expect(screen.getByText(entry.evidence_id)).toBeTruthy();
    }
  });

  it("filters by evidence type", () => {
    render(<EvidenceList items={ITEMS} />);
    fireEvent.click(screen.getByRole("button", { name: /rule_result/ }));
    expect(screen.getByText(/1 of 3/)).toBeTruthy();
    expect(screen.getByText("evidence_rr_R-001_84721")).toBeTruthy();
    expect(screen.queryByText("evidence_edge_0001")).toBeNull();
  });

  it("opens a row to reveal per-item provenance", () => {
    const rich: EvidenceItem = {
      ...item("evidence_edge_0001", "graph_relationship"),
      event_ids: ["evt_1", "evt_2"],
      graph_edge_ids: ["edge_0001"],
      rule_result_ids: ["rr_R-001"],
    };
    render(<EvidenceList items={[rich]} />);
    expect(screen.queryByText("evt_1")).toBeNull();
    const toggle = screen.getByRole("button", { name: "Show provenance" });
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(toggle);
    expect(toggle.getAttribute("aria-expanded")).toBe("true");
    for (const id of ["evt_1", "evt_2", "edge_0001", "rr_R-001"]) {
      expect(screen.getByText(id)).toBeTruthy();
    }
    fireEvent.click(screen.getByRole("button", { name: "Hide provenance" }));
    expect(screen.queryByText("evt_1")).toBeNull();
  });

  it("searches across id, type, title, and description", () => {
    render(<EvidenceList items={ITEMS} />);
    const box = screen.getByLabelText("Search evidence");
    fireEvent.change(box, { target: { value: "edge_0001" } });
    expect(screen.getByText(/1 of 3/)).toBeTruthy();
    expect(screen.getByText("evidence_edge_0001")).toBeTruthy();
    expect(screen.queryByText("evidence_txn_84721")).toBeNull();
    fireEvent.change(box, { target: { value: "RULE_RESULT" } });
    expect(screen.getByText(/1 of 3/)).toBeTruthy();
    expect(screen.getByText("evidence_rr_R-001_84721")).toBeTruthy();
  });

  it("combines search with the type filter and clears both", () => {
    render(<EvidenceList items={ITEMS} />);
    fireEvent.click(screen.getByRole("button", { name: /graph_relationship/ }));
    fireEvent.change(screen.getByLabelText("Search evidence"), {
      target: { value: "txn_84721" },
    });
    expect(screen.getByText("No evidence items match this search.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Clear search" }));
    expect(screen.getByText(/3 of 3/)).toBeTruthy();
    expect(
      (screen.getByLabelText("Search evidence") as HTMLInputElement).value
    ).toBe("");
  });

  it("shows an honest empty state for missing provenance", () => {
    render(<EvidenceList items={[ITEMS[0]]} />);
    fireEvent.click(screen.getByRole("button", { name: "Show provenance" }));
    expect(screen.getAllByText("none").length).toBe(3);
  });
});
