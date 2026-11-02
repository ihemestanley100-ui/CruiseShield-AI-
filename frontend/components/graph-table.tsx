"use client";

/* Batch 3: complete relationship table — the accessible alternative to
 * the visual graph. Lists every edge exactly as returned by the backend. */

import type { GraphEdge, GraphNode } from "../lib/api";
import { useTranslation } from "../lib/i18n/context";

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export function GraphTable({ nodes, edges }: Props) {
  const { t } = useTranslation("graph");
  const label = new Map(nodes.map((n) => [n.node_id, n.display_label]));
  return (
    <section className="card" aria-label={t("tableLabel")}>
      <h2>{t("tableTitle")}</h2>
      <p className="muted" data-testid="graph-table-counts">
        {t("tableCounts", { a: nodes.length, b: edges.length })}
      </p>
      {edges.length === 0 ? (
        <p className="muted">{t("tableEmpty")}</p>
      ) : (
        <div className="table-scroll">
          <table>
            <caption className="muted">{t("tableCaption")}</caption>
            <thead>
              <tr>
                <th scope="col">{t("thEdge")}</th>
                <th scope="col">{t("thSource")}</th>
                <th scope="col">{t("thRel")}</th>
                <th scope="col">{t("thTarget")}</th>
                <th scope="col">{t("thProv")}</th>
                <th scope="col">{t("thEvidence")}</th>
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
