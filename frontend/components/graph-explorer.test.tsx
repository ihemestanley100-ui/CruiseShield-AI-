import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { GraphEdge, GraphNode } from "../lib/api";
import { GraphExplorer } from "./graph-explorer";

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
  {
    node_id: "dev_04",
    node_type: "device",
    display_label: "Device 04",
    synthetic_flag: true,
    source_record_ids: ["seed:scn_primary:dev_04"],
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
    target_node_id: "dev_04",
    relationship_type: "USES_DEVICE",
    source_event_ids: ["evt_demo_84721"],
    evidence_ids: ["evidence_edge_0002"],
    valid_from: "2026-10-27T10:00:00Z",
    valid_to: null,
    synthetic_flag: true,
    trace_id: "trace_demo_84721",
  },
];

describe("GraphExplorer", () => {
  it("renders all and only the supplied nodes and edges", () => {
    const { container } = render(
      <GraphExplorer nodes={NODES} edges={EDGES} />
    );
    expect(screen.getByTestId("graph-counts")).toHaveTextContent(
      "Showing 3 of 3 nodes, 2 of 2 edges."
    );
    expect(container.querySelectorAll("[data-node]")).toHaveLength(3);
    expect(container.querySelectorAll("[data-edge]")).toHaveLength(2);
  });

  it("shows node detail with source records and relationships", () => {
    const { container } = render(
      <GraphExplorer nodes={NODES} edges={EDGES} />
    );
    const node = container.querySelector('[data-node="acct_B"]');
    expect(node).toBeTruthy();
    fireEvent.click(node as Element);
    const detail = screen.getByTestId("graph-detail");
    expect(detail).toHaveTextContent("Account B");
    expect(detail).toHaveTextContent("seed:scn_primary:acct_B");
    expect(detail).toHaveTextContent("edge_0001");
    expect(detail).toHaveTextContent("edge_0002");
  });

  it("shows edge provenance and evidence on keyboard select", () => {
    const { container } = render(
      <GraphExplorer nodes={NODES} edges={EDGES} />
    );
    const edge = container.querySelector('[data-edge="edge_0002"]');
    expect(edge).toBeTruthy();
    fireEvent.keyDown(edge as Element, { key: "Enter" });
    const detail = screen.getByTestId("graph-detail");
    expect(detail).toHaveTextContent("edge_0002");
    expect(detail).toHaveTextContent("USES_DEVICE");
    expect(detail).toHaveTextContent("evt_demo_84721");
    expect(detail).toHaveTextContent("evidence_edge_0002");
  });

  it("filters hide nodes and connected edges without inventing data", () => {
    const { container } = render(
      <GraphExplorer nodes={NODES} edges={EDGES} />
    );
    fireEvent.click(screen.getByLabelText("device"));
    expect(screen.getByTestId("graph-counts")).toHaveTextContent(
      "Showing 2 of 3 nodes, 1 of 2 edges."
    );
    expect(container.querySelectorAll("[data-node]")).toHaveLength(2);
    expect(
      container.querySelector('[data-edge="edge_0002"]')
    ).toBeNull();
  });

  it("zoom controls change the viewport transform", () => {
    render(<GraphExplorer nodes={NODES} edges={EDGES} />);
    const viewport = screen.getByTestId("graph-viewport");
    expect(viewport.getAttribute("transform")).toBe(
      "translate(0,0) scale(1)"
    );
    fireEvent.click(screen.getByRole("button", { name: "Zoom in" }));
    expect(viewport.getAttribute("transform")).toBe(
      "translate(0,0) scale(1.25)"
    );
    fireEvent.click(screen.getByRole("button", { name: "Fit to screen" }));
    expect(viewport.getAttribute("transform")).toBe(
      "translate(0,0) scale(1)"
    );
  });

  it("arrow keys pan the graph for keyboard users", () => {
    render(<GraphExplorer nodes={NODES} edges={EDGES} />);
    const svg = screen.getByTestId("graph-svg");
    fireEvent.keyDown(svg, { key: "ArrowLeft" });
    expect(screen.getByTestId("graph-viewport").getAttribute("transform")).toBe(
      "translate(40,0) scale(1)"
    );
  });
});
