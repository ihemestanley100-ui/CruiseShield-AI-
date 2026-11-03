"use client";

/* Batch 3: network explorer route. Fetches the exact graph from
 * GET /api/v1/graph/{txn} and renders it visually plus a complete
 * accessible table. Never invents relationships or alters risk. */

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Breadcrumbs } from "../../../components/breadcrumbs";
import { GraphExplorer } from "../../../components/graph-explorer";
import { GraphTable } from "../../../components/graph-table";
import { OrbitalExplorer } from "../../../components/orbital-explorer";
import {
  ApiError,
  getGraph,
  getGraphOverlay,
  userErrorMessage,
  type GraphEdge,
  type GraphNode,
  type GraphResponse,
  type OverlayResponse,
} from "../../../lib/api";
import { useTranslation } from "../../../lib/i18n/context";

type State =
  | { kind: "loading" }
  | { kind: "ready"; graph: GraphResponse; overlay: OverlayResponse | null }
  | { kind: "not-found" }
  | { kind: "error"; message: string };

/* DI-07: overlay nodes/edges merge render-side only; base counts stay
 * separate and the base graph renders identically without an overlay. */
function mergedNodes(
  graph: GraphResponse,
  overlay: OverlayResponse | null
): GraphNode[] {
  if (!overlay) return graph.nodes;
  const seen = new Set(graph.nodes.map((n) => n.node_id));
  const extra = overlay.nodes.filter((n) => !seen.has(n.node_id));
  return [...graph.nodes, ...extra];
}

function mergedEdges(
  graph: GraphResponse,
  overlay: OverlayResponse | null
): GraphEdge[] {
  if (!overlay) return graph.edges;
  const seen = new Set(graph.edges.map((e) => e.edge_id));
  const extra = overlay.edges.filter((e) => !seen.has(e.edge_id));
  return [...graph.edges, ...extra];
}

function OverlayStatus({ overlay }: { overlay: OverlayResponse | null }) {
  const { t } = useTranslation("network");
  if (!overlay) {
    return (
      <p className="muted" data-testid="overlay-status">
        {t("overlayDown")}
      </p>
    );
  }
  const missing = Object.entries(overlay.unavailable);
  return (
    <p className="muted" data-testid="overlay-status">
      {t("overlayLine", {
        nodes: overlay.counts.overlay_nodes,
        edges: overlay.counts.overlay_edges,
      })}
      {missing.length > 0 && (
        <> {t("overlayMissing", { list: missing.map(([k, v]) => `${k} (${v})`).join(", ") })}</>
      )}
    </p>
  );
}

export default function NetworkPage() {
  const params = useParams<{ txnId: string }>();
  const txnId = params.txnId;
  const { t } = useTranslation("network");
  const { t: tCommon } = useTranslation("common");
  const { t: tNav } = useTranslation("nav");
  const [state, setState] = useState<State>({ kind: "loading" });
  const [view, setView] = useState<"orbital" | "flat">("orbital");

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    Promise.all([
      getGraph(txnId, controller.signal),
      /* DI-07 overlay is best-effort: the base graph renders even if
       * the overlay is missing or fails. */
      getGraphOverlay(txnId, controller.signal).catch(() => null),
    ])
      .then(([graph, overlay]) => setState({ kind: "ready", graph, overlay }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.code === "UNKNOWN_TRANSACTION") {
          setState({ kind: "not-found" });
          return;
        }
        setState({
          kind: "error",
          message: userErrorMessage(err, tCommon),
        });
      });
    return () => controller.abort();
  }, [txnId]);

  return (
    <main className="main">
      <Breadcrumbs
        items={[
          { label: tNav("commandCenter"), href: "/demo" },
          { label: t("crumb", { id: txnId }) },
        ]}
      />
      {state.kind === "loading" && (
        <section className="card" aria-live="polite">
          <h1>{t("title", { id: txnId })}</h1>
          <p className="muted">{t("loading")}</p>
        </section>
      )}
      {state.kind === "not-found" && (
        <section className="card" aria-live="assertive">
          <h1>{t("notFoundTitle")}</h1>
          <p className="muted">
            {t("notFoundPre")}
            <code>{txnId}</code>
            {t("notFoundPost")}
          </p>
        </section>
      )}
      {state.kind === "error" && (
        <section className="card" aria-live="assertive">
          <h1>{t("title", { id: txnId })}</h1>
          <div className="alert error" role="alert">
            {state.message}
          </div>
          <p>
            <button type="button" onClick={() => window.location.reload()}>
              {tCommon("retry")}
            </button>
          </p>
        </section>
      )}
      {state.kind === "ready" && (
        <>
          <div className="page-head">
            <h1>{t("headTitle", { id: state.graph.transaction_id })}</h1>
            <p className="muted" data-testid="network-counts">
              {t("countsLine", {
                nodes: state.graph.counts.nodes,
                edges: state.graph.counts.edges,
                n: state.graph.provenance_errors.length,
              })}
            </p>
            <OverlayStatus overlay={state.overlay} />
            {state.graph.provenance_errors.length > 0 && (
              <div className="alert error" role="alert">
                {t("provErrors", {
                  list: state.graph.provenance_errors.join(", "),
                })}
              </div>
            )}
          </div>
          {state.graph.counts.nodes === 0 ? (
            <section className="card" aria-live="polite">
              <p className="muted">{t("emptyGraph")}</p>
            </section>
          ) : (
            <>
              <div className="chip-row" role="radiogroup" aria-label={t("viewLabel")}>
                <label className="chip-label">
                  <input
                    type="radio"
                    name="graph-view"
                    value="orbital"
                    checked={view === "orbital"}
                    onChange={() => setView("orbital")}
                  />{" "}
                  {t("orbital")}
                </label>
                <label className="chip-label">
                  <input
                    type="radio"
                    name="graph-view"
                    value="flat"
                    checked={view === "flat"}
                    onChange={() => setView("flat")}
                  />{" "}
                  {t("flat")}
                </label>
              </div>
              {view === "orbital" ? (
                <OrbitalExplorer
                  nodes={mergedNodes(state.graph, state.overlay)}
                  edges={mergedEdges(state.graph, state.overlay)}
                />
              ) : (
                <GraphExplorer
                  nodes={mergedNodes(state.graph, state.overlay)}
                  edges={mergedEdges(state.graph, state.overlay)}
                />
              )}
              <GraphTable
                nodes={mergedNodes(state.graph, state.overlay)}
                edges={mergedEdges(state.graph, state.overlay)}
              />
            </>
          )}
        </>
      )}
    </main>
  );
}
