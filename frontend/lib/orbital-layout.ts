/* Deterministic orbital layout for the graph explorer.
 *
 * VISUAL METAPHOR ONLY: ring depth, angle, node size, and animation carry
 * NO meaning about risk, guilt, ownership, timing, causation, or
 * investigative priority. Rings are BFS depth from the focus node (a
 * layout convenience for a readable demo); angles are alphabetical.
 *
 * Pure functions, no DOM. Positions derive only from node/edge IDs. */

import type { GraphEdge, GraphNode } from "./api";

export interface OrbitalPosition {
  x: number;
  y: number;
  ring: number;
  angle: number;
}

/* Fixed viewBox geometry; the SVG scales responsively around it. */
export const ORBIT_WIDTH = 800;
export const ORBIT_HEIGHT = 600;
export const ORBIT_CX = ORBIT_WIDTH / 2;
export const ORBIT_CY = ORBIT_HEIGHT / 2;
/* Ring radii: focus at center, BFS depth outward, clamped past depth 3. */
export const RING_RADII = [0, 120, 200, 260, 300];

export function ringForDepth(depth: number): number {
  return Math.min(Math.max(depth, 0), RING_RADII.length - 1);
}

/* Default focus: highest-degree node, ties broken lexicographically, so
 * the initial view is deterministic for any graph. */
export function defaultFocus(nodes: GraphNode[], edges: GraphEdge[]): string {
  const degree = new Map(nodes.map((n) => [n.node_id, 0]));
  for (const e of edges) {
    if (degree.has(e.source_node_id)) {
      degree.set(e.source_node_id, (degree.get(e.source_node_id) as number) + 1);
    }
    if (degree.has(e.target_node_id)) {
      degree.set(e.target_node_id, (degree.get(e.target_node_id) as number) + 1);
    }
  }
  const sorted = [...nodes.map((n) => n.node_id)].sort();
  let best = sorted[0] ?? "";
  for (const id of sorted) {
    if ((degree.get(id) as number) > (degree.get(best) as number)) best = id;
  }
  return best;
}

export function bfsDepths(
  nodes: GraphNode[],
  edges: GraphEdge[],
  focus: string
): Map<string, number> {
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
  if (!adj.has(focus)) return depth;
  const queue = [focus];
  depth.set(focus, 0);
  while (queue.length > 0) {
    const cur = queue.shift() as string;
    for (const nxt of (adj.get(cur) ?? []).sort()) {
      if (!depth.has(nxt)) {
        depth.set(nxt, (depth.get(cur) as number) + 1);
        queue.push(nxt);
      }
    }
  }
  return depth;
}

export function layoutOrbital(
  nodes: GraphNode[],
  edges: GraphEdge[],
  focus: string
): Map<string, OrbitalPosition> {
  const depths = bfsDepths(nodes, edges, focus);
  const rings = new Map<number, string[]>();
  for (const n of nodes) {
    const ring = depths.has(n.node_id)
      ? ringForDepth(depths.get(n.node_id) as number)
      : RING_RADII.length - 1;
    if (!rings.has(ring)) rings.set(ring, []);
    (rings.get(ring) as string[]).push(n.node_id);
  }
  const pos = new Map<string, OrbitalPosition>();
  for (const [ring, ids] of rings) {
    const ordered = ids.sort();
    const radius = RING_RADII[ring];
    /* Per-ring phase offset avoids radial alignment; purely aesthetic. */
    const phase = ring * 0.5;
    ordered.forEach((id, i) => {
      const angle =
        ring === 0 ? 0 : phase - Math.PI / 2 + (2 * Math.PI * i) / ordered.length;
      pos.set(id, {
        x: ORBIT_CX + radius * Math.cos(angle),
        y: ORBIT_CY + radius * Math.sin(angle) * 0.72,
        ring,
        angle,
      });
    });
  }
  return pos;
}

export interface AdaptedGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  /* Edge IDs dropped because an endpoint is not a known node. Displayed,
   * never silently hidden. */
  droppedEdgeIds: string[];
}

/* Real-data adapter: keeps only edges whose endpoints resolve to valid
 * nodes; tolerates missing/unknown fields without inventing data. */
export function adaptGraph(
  nodes: GraphNode[],
  edges: GraphEdge[]
): AdaptedGraph {
  const known = new Set(nodes.map((n) => n.node_id));
  const kept: GraphEdge[] = [];
  const dropped: string[] = [];
  for (const e of edges) {
    if (!e || known.has(e.source_node_id) === false) {
      dropped.push(e?.edge_id ?? "?");
      continue;
    }
    if (known.has(e.target_node_id) === false) {
      dropped.push(e.edge_id);
      continue;
    }
    kept.push(e);
  }
  return { nodes, edges: kept, droppedEdgeIds: dropped };
}
