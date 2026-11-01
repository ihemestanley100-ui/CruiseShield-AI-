import { describe, expect, it } from "vitest";
import type { GraphEdge, GraphNode } from "./api";
import {
  adaptGraph,
  bfsDepths,
  defaultFocus,
  layoutOrbital,
  ORBIT_CX,
  ORBIT_CY,
  RING_RADII,
} from "./orbital-layout";

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

const NODES = [node("acct_A"), node("acct_B"), node("acct_C"), node("dev_04")];
const EDGES = [
  edge("edge_0001", "acct_A", "acct_B"),
  edge("edge_0002", "acct_B", "dev_04"),
  edge("edge_0003", "acct_B", "acct_C"),
];

describe("defaultFocus", () => {
  it("picks the highest-degree node deterministically", () => {
    expect(defaultFocus(NODES, EDGES)).toBe("acct_B");
  });

  it("breaks degree ties lexicographically", () => {
    const nodes = [node("acct_B"), node("acct_A")];
    const edges = [edge("edge_0001", "acct_A", "acct_B")];
    expect(defaultFocus(nodes, edges)).toBe("acct_A");
  });
});

describe("bfsDepths", () => {
  it("measures undirected depth from the focus", () => {
    const depths = bfsDepths(NODES, EDGES, "acct_B");
    expect(depths.get("acct_B")).toBe(0);
    expect(depths.get("acct_A")).toBe(1);
    expect(depths.get("dev_04")).toBe(1);
    expect(depths.get("acct_C")).toBe(1);
  });

  it("returns empty depths for an unknown focus", () => {
    expect(bfsDepths(NODES, EDGES, "missing")).toEqual(new Map());
  });
});

describe("layoutOrbital", () => {
  it("centers the focus and rings neighbors by depth", () => {
    const pos = layoutOrbital(NODES, EDGES, "acct_B");
    expect(pos.get("acct_B")).toMatchObject({ x: ORBIT_CX, y: ORBIT_CY, ring: 0 });
    for (const id of ["acct_A", "acct_C", "dev_04"]) {
      expect(pos.get(id)?.ring).toBe(1);
    }
    const dx = (pos.get("acct_A")?.x as number) - ORBIT_CX;
    const dy = ((pos.get("acct_A")?.y as number) - ORBIT_CY) / 0.72;
    expect(Math.hypot(dx, dy)).toBeCloseTo(RING_RADII[1], 6);
  });

  it("is deterministic regardless of input order", () => {
    const a = layoutOrbital(NODES, EDGES, "acct_B");
    const b = layoutOrbital(
      [...NODES].reverse(),
      [...EDGES].reverse(),
      "acct_B"
    );
    expect([...a.entries()]).toEqual([...b.entries()]);
  });

  it("parks unreachable nodes on the outer ring", () => {
    const nodes = [...NODES, node("acct_Z")];
    const pos = layoutOrbital(nodes, EDGES, "acct_B");
    expect(pos.get("acct_Z")?.ring).toBe(RING_RADII.length - 1);
  });
});

describe("adaptGraph", () => {
  it("keeps valid edges and reports dangling ones", () => {
    const edges = [...EDGES, edge("edge_bad", "acct_A", "ghost")];
    const adapted = adaptGraph(NODES, edges);
    expect(adapted.edges.map((e) => e.edge_id)).toEqual([
      "edge_0001",
      "edge_0002",
      "edge_0003",
    ]);
    expect(adapted.droppedEdgeIds).toEqual(["edge_bad"]);
  });

  it("reports nothing dropped for clean data", () => {
    expect(adaptGraph(NODES, EDGES).droppedEdgeIds).toEqual([]);
  });
});
