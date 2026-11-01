/* Command Center network preview. A small static SVG drawn from the
 * real graph response: a deterministic node subset (sorted by ID) with
 * honest "preview of N of M" labelling. The full explorer owns
 * interaction; this preview links to it. */

import Link from "next/link";
import type { GraphResponse } from "../lib/api";
import { defaultRoots, layoutGraph } from "../lib/graph-layout";

const PREVIEW_NODES = 12;

export function CommandNetworkPreview({ graph }: { graph: GraphResponse }) {
  const nodes = [...graph.nodes]
    .sort((a, b) => a.node_id.localeCompare(b.node_id))
    .slice(0, PREVIEW_NODES);
  const ids = new Set(nodes.map((n) => n.node_id));
  const edges = graph.edges.filter(
    (e) => ids.has(e.source_node_id) && ids.has(e.target_node_id)
  );
  const pos = layoutGraph(nodes, edges, defaultRoots(edges));
  const maxX = Math.max(400, ...[...pos.values()].map((p) => p.x)) + 150;
  const maxY = Math.max(160, ...[...pos.values()].map((p) => p.y)) + 60;

  return (
    <section className="card command-section" aria-labelledby="net-prev-h">
      <h2 id="net-prev-h">Network preview</h2>
      <p className="muted" data-testid="network-preview-counts">
        {graph.counts.nodes} nodes, {graph.counts.edges} edges in the
        investigation graph. Preview shows {nodes.length} nodes and{" "}
        {edges.length} relationships.
      </p>
      {graph.provenance_errors.length > 0 && (
        <div className="alert error" role="alert">
          Provenance errors: {graph.provenance_errors.join("; ")}
        </div>
      )}
      {nodes.length === 0 ? (
        <p className="muted">No relationships in this graph.</p>
      ) : (
        <svg
          className="graph-canvas"
          role="img"
          aria-label={`Network preview: ${nodes.length} of ${graph.counts.nodes} nodes shown`}
          viewBox={`0 0 ${maxX} ${maxY}`}
        >
          {edges.map((e) => {
            const a = pos.get(e.source_node_id) ?? { x: 0, y: 0 };
            const b = pos.get(e.target_node_id) ?? { x: 0, y: 0 };
            return (
              <g key={e.edge_id} className="graph-edge">
                <line
                  x1={a.x}
                  y1={a.y}
                  x2={b.x}
                  y2={b.y}
                  strokeWidth={1.5}
                />
              </g>
            );
          })}
          {nodes.map((n) => {
            const p = pos.get(n.node_id) ?? { x: 0, y: 0 };
            return (
              <g key={n.node_id} className="graph-node">
                <circle
                  className={`graph-dot graph-${n.node_type}`}
                  cx={p.x}
                  cy={p.y}
                  r={10}
                />
                <text className="graph-label" x={p.x + 15} y={p.y + 5}>
                  {n.display_label}
                </text>
              </g>
            );
          })}
        </svg>
      )}
      <p>
        <Link href={`/network/${graph.transaction_id}`}>
          Open full network explorer
        </Link>
      </p>
    </section>
  );
}
