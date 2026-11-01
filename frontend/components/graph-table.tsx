"use client";

/* Batch 3: complete relationship table — the accessible alternative to
 * the visual graph. Lists every edge exactly as returned by the backend. */

import type { GraphEdge, GraphNode } from "../lib/api";

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export function GraphTable({ nodes, edges }: Props) {
  const label = new Map(nodes.map((n) => [n.node_id, n.display_label]));
  return (
    <section className="card" aria-label="Relationship table">
      <h2>All relationships</h2>
      <p className="muted" data-testid="graph-table-counts">
        {nodes.length} nodes, {edges.length} edges — the complete record
        behind the graph above.
      </p>
      {edges.length === 0 ? (
        <p className="muted">No relationships in this graph.</p>
      ) : (
        <div className="table-scroll">
          <table>
            <caption className="muted">
              Every relationship with provenance and evidence references.
            </caption>
            <thead>
              <tr>
                <th scope="col">Edge</th>
                <th scope="col">Source</th>
                <th scope="col">Relationship</th>
                <th scope="col">Target</th>
                <th scope="col">Provenance events</th>
                <th scope="col">Evidence</th>
              </tr>
            </thead>
            <tbody>
              {edges.map((e) => (
                <tr key={e.edge_id} data-edge-row={e.edge_id}>
                  <td>
                    <code>{e.edge_id}</code>
                  </td>
                  <td>
                    <code>{e.source_node_id}</code>{" "}
                    <span className="muted">
                      {label.get(e.source_node_id) ?? ""}
                    </span>
                  </td>
                  <td>{e.relationship_type}</td>
                  <td>
                    <code>{e.target_node_id}</code>{" "}
                    <span className="muted">
                      {label.get(e.target_node_id) ?? ""}
                    </span>
                  </td>
                  <td>
                    <code>{e.source_event_ids.join(", ")}</code>
                  </td>
                  <td>
                    <code>{e.evidence_ids.join(", ")}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
