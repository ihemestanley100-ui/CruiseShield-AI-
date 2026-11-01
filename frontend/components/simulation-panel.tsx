"use client";

/* Batch 4: bounded what-if simulation. Loads the real edge list for the
 * target transaction from GET /api/v1/graph, takes the authoritative
 * baseline from GET /api/v1/risk (never computed here); the simulated
 * result is labelled hypothetical and never overwrites the baseline. */

import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  getGraph,
  getRisk,
  postSimulation,
  type GraphEdge,
  type SimulationResult,
} from "../lib/api";

interface Props {
  defaultTxnId: string;
}

type RunState =
  | { kind: "idle" }
  | { kind: "running" }
  | { kind: "done"; result: SimulationResult }
  | { kind: "error"; message: string };

export function SimulationPanel({ defaultTxnId }: Props) {
  const [txnId, setTxnId] = useState(defaultTxnId);
  const [edges, setEdges] = useState<GraphEdge[] | null>(null);
  const [baseline, setBaseline] = useState<{
    score: number;
    band: string;
  } | null>(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);
  const [ignored, setIgnored] = useState<Set<string>>(new Set());
  const [assumption, setAssumption] = useState("");
  const [run, setRun] = useState<RunState>({ kind: "idle" });

  const load = useCallback(async (txn: string) => {
    setLoading(true);
    setLoadError("");
    setRun({ kind: "idle" });
    setIgnored(new Set());
    try {
      const [graph, risk] = await Promise.all([
        getGraph(txn),
        getRisk(txn, "network"),
      ]);
      setEdges(graph.edges);
      setBaseline({ score: risk.assessment.score, band: risk.assessment.band });
    } catch (err: unknown) {
      setEdges(null);
      setBaseline(null);
      setLoadError(
        err instanceof ApiError
          ? `${err.code}: ${err.message}`
          : err instanceof Error
            ? err.message
            : "request failed"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(defaultTxnId);
  }, [defaultTxnId, load]);

  function toggle(edgeId: string) {
    setIgnored((prev) => {
      const next = new Set(prev);
      if (next.has(edgeId)) next.delete(edgeId);
      else next.add(edgeId);
      return next;
    });
  }

  async function onRun() {
    if (edges === null) return;
    setRun({ kind: "running" });
    try {
      const result = await postSimulation(txnId, [...ignored].sort(), assumption);
      setRun({ kind: "done", result });
    } catch (err: unknown) {
      setRun({
        kind: "error",
        message:
          err instanceof ApiError
            ? `${err.code}: ${err.message}`
            : err instanceof Error
              ? err.message
              : "request failed",
      });
    }
  }

  return (
    <section className="card" aria-label="What-if simulation">
      <h2>What-if simulation</h2>
      <p>
        <label htmlFor="sim-txn">Target transaction</label>{" "}
        <input
          id="sim-txn"
          type="text"
          value={txnId}
          onChange={(ev) => setTxnId(ev.target.value)}
          className="text-input"
        />{" "}
        <button type="button" className="chip" onClick={() => load(txnId)}>
          Load edges
        </button>
      </p>
      <p className="muted" data-testid="sim-baseline" aria-live="polite">
        {loading && "Loading target…"}
        {!loading && baseline !== null &&
          `Authoritative baseline (network): ${baseline.score}/100 ${baseline.band}. This value never changes.`}
        {!loading && loadError !== "" && `Target unavailable: ${loadError}`}
      </p>
      {edges !== null && (
        <fieldset>
          <legend>
            Relationships to ignore ({ignored.size} of {edges.length} selected)
          </legend>
          <div className="chip-row" data-testid="sim-edges">
            {edges.map((e) => (
              <label key={e.edge_id} className="chip-label">
                <input
                  type="checkbox"
                  checked={ignored.has(e.edge_id)}
                  onChange={() => toggle(e.edge_id)}
                />{" "}
                <code>{e.edge_id}</code> {e.relationship_type}
              </label>
            ))}
          </div>
        </fieldset>
      )}
      <p>
        <label htmlFor="sim-assumption">
          Assumption (recorded with the run)
        </label>
        <br />
        <input
          id="sim-assumption"
          type="text"
          value={assumption}
          onChange={(ev) => setAssumption(ev.target.value)}
          placeholder="e.g. Shared devices are coincidental, not shared control."
          className="text-input"
        />
      </p>
      <p>
        <button
          type="button"
          disabled={baseline === null || run.kind === "running"}
          onClick={onRun}
        >
          {run.kind === "running" ? "Running…" : "Run simulation"}
        </button>
      </p>
      {run.kind === "error" && (
        <div className="alert error" role="alert">
          {run.message}
        </div>
      )}
      {run.kind === "done" && (
        <div className="alert warn" role="status" data-testid="sim-result">
          <strong>
            SIMULATED — hypothetical, not a real-world prediction.
          </strong>
          <br />
          Run <code>{run.result.simulation_id}</code>: baseline{" "}
          {run.result.baseline_score}/100 {run.result.baseline_band} →
          simulated {run.result.simulated_score}/100{" "}
          {run.result.simulated_band}
          <br />
          Ignored:{" "}
          {run.result.ignored_edge_ids.length === 0
            ? "none"
            : run.result.ignored_edge_ids.join(", ")}
          <br />
          Assumption: {run.result.assumption}
          <br />
          <span className="muted">{run.result.limitations}</span>
        </div>
      )}
    </section>
  );
}
