/* Deterministic SVG graph layout: BFS layers left-to-right from the
 * roots (first SENT_TO edge endpoints, same rule as static/graph.js).
 * Pure function, no DOM: positions derive only from node/edge IDs. */

import type { GraphEdge, GraphNode } from "./api";

export interface NodePosition {
  x: number;
  y: number;
}

const LAYER_X0 = 90;
const LAYER_DX = 170;
const LAYER_Y0 = 60;
const LAYER_DY = 62;

export function layoutGraph(
  nodes: GraphNode[],
  edges: GraphEdge[],
  roots: string[]
): Map<string, NodePosition> {
  const adj = new Map(nodes.map((n) => [n.node_id, [] as string[]]));
  for (const e of edges) {
    if (adj.has(e.source_node_id)) {
      adj.get(e.source_node_id)?.push(e.target_node_id);
    }
    if (adj.has(e.target_node_id)) {
      adj.get(e.target_node_id)?.push(e.source_node_id);
    }
  }
  const depth = new Map<string, number>();
  const queue = roots.filter((r) => adj.has(r));
  queue.forEach((r) => depth.set(r, 0));
  if (queue.length === 0 && nodes.length > 0) {
    queue.push(nodes[0].node_id);
    depth.set(nodes[0].node_id, 0);
  }
  while (queue.length > 0) {
    const cur = queue.shift() as string;
    for (const nxt of (adj.get(cur) ?? []).sort()) {
      if (!depth.has(nxt)) {
        depth.set(nxt, (depth.get(cur) as number) + 1);
        queue.push(nxt);
      }
    }
  }
  const layers = new Map<number, string[]>();
  for (const n of nodes) {
    const d = depth.has(n.node_id) ? (depth.get(n.node_id) as number) : 99;
    if (!layers.has(d)) layers.set(d, []);
    (layers.get(d) as string[]).push(n.node_id);
  }
  const pos = new Map<string, NodePosition>();
  const ordered = [...layers.keys()].sort((a, b) => a - b);
  ordered.forEach((d, li) => {
    const ids = (layers.get(d) as string[]).sort();
    ids.forEach((id, i) => {
      pos.set(id, { x: LAYER_X0 + li * LAYER_DX, y: LAYER_Y0 + i * LAYER_DY });
    });
  });
  return pos;
}

/* Root rule shared with static/graph.js: the endpoints of the first
 * SENT_TO edge (edge order), so the layout matches the backend UI. */
export function defaultRoots(edges: GraphEdge[]): string[] {
  const first = edges.find((e) => e.relationship_type === "SENT_TO");
  return first ? [first.source_node_id, first.target_node_id] : [];
}
