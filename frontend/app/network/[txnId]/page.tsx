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
  type GraphEdge,
  type GraphNode,
  type GraphResponse,
  type OverlayResponse,
} from "../../../lib/api";

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
  if (!overlay) {
    return (
      <p className="muted" data-testid="overlay-status">
        Intelligence overlay unavailable.
      </p>
    );
  }
  const missing = Object.entries(overlay.unavailable);
  return (
    <p className="muted" data-testid="overlay-status">
      Intelligence overlay (derived, synthetic): {overlay.counts.overlay_nodes}{" "}
      nodes, {overlay.counts.overlay_edges} edges
      {missing.length > 0 && (
        <>
          {" "}· unavailable:{" "}
          {missing.map(([k, v]) => `${k} (${v})`).join(", ")}
        </>
      )}
    </p>
  );
}

export default function NetworkPage() {
  const params = useParams<{ txnId: string }>();
  const txnId = params.txnId;
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
          message:
            err instanceof ApiError
              ? `${err.code}: ${err.message}`
              : err instanceof Error
                ? err.message
                : "request failed",
        });
      });
    return () => controller.abort();
  }, [txnId]);

  return (
    <main className="main">
      <Breadcrumbs
        items={[
          { label: "Command Center", href: "/demo" },
          { label: `Network ${txnId}` },
        ]}
      />
      {state.kind === "loading" && (
        <section className="card" aria-live="polite">
          <h1>Network {txnId}</h1>
          <p className="muted">Loading network graph…</p>
        </section>
      )}
      {state.kind === "not-found" && (
        <section className="card" aria-live="assertive">
          <h1>Transaction not found</h1>
          <p className="muted">
            No transaction <code>{txnId}</code> exists in the backend.
          </p>
        </section>
      )}
      {state.kind === "error" && (
        <section className="card" aria-live="assertive">
          <h1>Network {txnId}</h1>
          <div className="alert error" role="alert">
            {state.message}
          </div>
          <p>
            <button type="button" onClick={() => window.location.reload()}>
              Retry
            </button>
          </p>
        </section>
      )}
      {state.kind === "ready" && (
        <>
          <div className="page-head">
            <h1>Network explorer — {state.graph.transaction_id}</h1>
            <p className="muted" data-testid="network-counts">
              {state.graph.counts.nodes} nodes, {state.graph.counts.edges}{" "}
              edges · provenance errors:{" "}
              {state.graph.provenance_errors.length}
            </p>
            <OverlayStatus overlay={state.overlay} />
            {state.graph.provenance_errors.length > 0 && (
              <div className="alert error" role="alert">
                Provenance errors:{" "}
                {state.graph.provenance_errors.join(", ")}
              </div>
            )}
          </div>
          {state.graph.counts.nodes === 0 ? (
            <section className="card" aria-live="polite">
              <p className="muted">
                This transaction has no network graph in the backend.
              </p>
            </section>
          ) : (
            <>
              <div className="chip-row" role="radiogroup" aria-label="Graph view">
                <label className="chip-label">
                  <input
                    type="radio"
                    name="graph-view"
                    value="orbital"
                    checked={view === "orbital"}
                    onChange={() => setView("orbital")}
                  />{" "}
                  Orbital
                </label>
                <label className="chip-label">
                  <input
                    type="radio"
                    name="graph-view"
                    value="flat"
                    checked={view === "flat"}
                    onChange={() => setView("flat")}
                  />{" "}
                  Flat (fallback)
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
