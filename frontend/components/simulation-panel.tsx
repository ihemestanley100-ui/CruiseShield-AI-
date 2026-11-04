"use client";

/* Batch 4: bounded what-if simulation. Loads the real edge list for the
 * target transaction from GET /api/v1/graph, takes the authoritative
 * baseline from GET /api/v1/risk (never computed here); the simulated
 * result is labelled hypothetical and never overwrites the baseline. */

import { useCallback, useEffect, useState } from "react";
import {
  getGraph,
  getRisk,
  postSimulation,
  userErrorMessage,
  type GraphEdge,
  type SimulationResult,
} from "../lib/api";
import { useTranslation } from "../lib/i18n/context";
import { useCan } from "../lib/session";

interface Props {
  defaultTxnId: string;
}

type RunState =
  | { kind: "idle" }
  | { kind: "running" }
  | { kind: "done"; result: SimulationResult }
  | { kind: "error"; message: string };

export function SimulationPanel({ defaultTxnId }: Props) {
  // J4: read-only roles see the run disabled (backend enforces too).
  const writable = useCan("write");
  const { t } = useTranslation("sim");
  const { t: tCommon } = useTranslation("common");
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
      setLoadError(userErrorMessage(err, tCommon));
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
        message: userErrorMessage(err, tCommon),
      });
    }
  }

  return (
    <section className="card" aria-label={t("simLabel")}>
      <h2>{t("simTitle")}</h2>
      <p>
        <label htmlFor="sim-txn">{t("targetLabel")}</label>{" "}
        <input
          id="sim-txn"
          type="text"
          value={txnId}
          onChange={(ev) => setTxnId(ev.target.value)}
          className="text-input"
        />{" "}
        <button type="button" className="chip" onClick={() => load(txnId)}>
          {t("loadEdges")}
        </button>
      </p>
      <p className="muted" data-testid="sim-baseline" aria-live="polite">
        {loading && t("loadingTarget")}
        {!loading &&
          baseline !== null &&
          t("baselineLine", {
            s: baseline.score,
            b: baseline.band,
          })}
        {!loading &&
          loadError !== "" &&
          t("targetDown", { err: loadError })}
      </p>
      {edges !== null && (
        <fieldset>
          <legend>
            {t("legendLine", { a: ignored.size, b: edges.length })}
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
        <label htmlFor="sim-assumption">{t("assumptionLabel")}</label>
        <br />
        <input
          id="sim-assumption"
          type="text"
          value={assumption}
          onChange={(ev) => setAssumption(ev.target.value)}
          placeholder={t("assumptionPh")}
          className="text-input"
        />
      </p>
      {!writable && (
        <p className="muted" role="note">
          {t("readOnlySim")}
        </p>
      )}
      <p>
        <button
          type="button"
          disabled={baseline === null || run.kind === "running" || !writable}
          onClick={onRun}
        >
          {run.kind === "running" ? t("running") : t("runSim")}
        </button>
      </p>
      {run.kind === "error" && (
        <div className="alert error" role="alert">
          {run.message}
        </div>
      )}
      {run.kind === "done" && (
        <div className="alert warn" role="status" data-testid="sim-result">
          <strong>{t("simBanner")}</strong>
          <br />
          {t("simRunPre")}
          <code>{run.result.simulation_id}</code>
          {t("simRunPost", {
            a: run.result.baseline_score,
            b: run.result.baseline_band,
            c: run.result.simulated_score,
            d: run.result.simulated_band,
          })}
          <br />
          {t("ignoredPre")}
          {run.result.ignored_edge_ids.length === 0
            ? tCommon("none")
            : run.result.ignored_edge_ids.join(", ")}
          <br />
          {t("assumptionLine", { a: run.result.assumption })}
          <br />
          <span className="muted">{run.result.limitations}</span>
        </div>
      )}
    </section>
  );
}
