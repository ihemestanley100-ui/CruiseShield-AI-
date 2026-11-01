import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { GraphEdge, GraphNode } from "../lib/api";
import { GraphTable } from "./graph-table";

const NODES: GraphNode[] = [
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
];

const EDGES: GraphEdge[] = [
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
    target_node_id: "acct_A",
    relationship_type: "SENT_TO",
    source_event_ids: ["evt_demo_84722"],
    evidence_ids: ["evidence_edge_0002"],
    valid_from: "2026-10-27T10:00:00Z",
    valid_to: null,
    synthetic_flag: true,
    trace_id: "trace_demo_84722",
  },
];

describe("GraphTable", () => {
  it("lists every edge with provenance and evidence", () => {
    const { container } = render(
      <GraphTable nodes={NODES} edges={EDGES} />
    );
    expect(screen.getByTestId("graph-table-counts")).toHaveTextContent(
      "2 nodes, 2 edges"
    );
    expect(container.querySelectorAll("[data-edge-row]")).toHaveLength(2);
    const row = container.querySelector('[data-edge-row="edge_0002"]');
    expect(row?.textContent).toContain("evt_demo_84722");
    expect(row?.textContent).toContain("evidence_edge_0002");
    expect(row?.textContent).toContain("SENT_TO");
  });

  it("shows an empty message when the graph has no edges", () => {
    render(<GraphTable nodes={NODES} edges={[]} />);
    expect(
      screen.getByText("No relationships in this graph.")
    ).toBeTruthy();
  });
});
