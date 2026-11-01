import { describe, expect, it } from "vitest";
import type { GraphEdge, GraphNode } from "./api";
import { defaultRoots, layoutGraph } from "./graph-layout";

function node(id: string, type = "account"): GraphNode {
  return {
    node_id: id,
    node_type: type,
    display_label: `Label ${id}`,
    synthetic_flag: true,
    source_record_ids: [`seed:scn_primary:${id}`],
  };
}

function edge(
  id: string,
  src: string,
  tgt: string,
  rel = "SENT_TO"
): GraphEdge {
  return {
    edge_id: id,
    source_node_id: src,
    target_node_id: tgt,
    relationship_type: rel,
    source_event_ids: ["evt_demo_84721"],
    evidence_ids: [`evidence_${id}`],
    valid_from: "2026-10-27T10:00:00Z",
    valid_to: null,
    synthetic_flag: true,
    trace_id: "trace_demo_84721",
  };
}

describe("layoutGraph", () => {
  it("places roots at layer 0 and neighbors in order", () => {
    const nodes = [node("acct_A"), node("acct_B"), node("acct_C")];
    const edges = [
      edge("edge_0001", "acct_A", "acct_B"),
      edge("edge_0002", "acct_A", "acct_C"),
    ];
    const pos = layoutGraph(nodes, edges, ["acct_A"]);
    expect(pos.get("acct_A")).toEqual({ x: 90, y: 60 });
    expect(pos.get("acct_B")).toEqual({ x: 260, y: 60 });
    expect(pos.get("acct_C")).toEqual({ x: 260, y: 122 });
  });

  it("is deterministic regardless of input order", () => {
    const nodes = [node("acct_C"), node("acct_A"), node("acct_B")];
    const edges = [
      edge("edge_0002", "acct_A", "acct_C"),
      edge("edge_0001", "acct_A", "acct_B"),
    ];
    const a = layoutGraph(nodes, edges, ["acct_A"]);
    const b = layoutGraph(
      [...nodes].reverse(),
      [...edges].reverse(),
      ["acct_A"]
    );
    expect([...a.entries()]).toEqual([...b.entries()]);
  });

  it("puts unreachable nodes in the fallback layer", () => {
    const nodes = [node("acct_A"), node("acct_B"), node("acct_Z")];
    const edges = [edge("edge_0001", "acct_A", "acct_B")];
    const pos = layoutGraph(nodes, edges, ["acct_A"]);
    const z = pos.get("acct_Z");
    expect(z?.x).toBeGreaterThan(pos.get("acct_B")?.x ?? 0);
  });

  it("falls back to the first node when no roots resolve", () => {
    const nodes = [node("acct_A"), node("acct_B")];
    const pos = layoutGraph(nodes, [], ["missing"]);
    expect(pos.get("acct_A")).toEqual({ x: 90, y: 60 });
  });
});

describe("defaultRoots", () => {
  it("uses the first SENT_TO edge endpoints", () => {
    const edges = [
      edge("edge_0001", "acct_X", "dev_04", "USES_DEVICE"),
      edge("edge_0002", "acct_A", "acct_B", "SENT_TO"),
    ];
    expect(defaultRoots(edges)).toEqual(["acct_A", "acct_B"]);
  });

  it("returns no roots when no SENT_TO edge exists", () => {
    expect(
      defaultRoots([edge("edge_0001", "acct_X", "dev_04", "USES_DEVICE")])
    ).toEqual([]);
  });
});
