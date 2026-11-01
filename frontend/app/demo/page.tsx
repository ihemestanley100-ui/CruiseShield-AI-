"use client";

import { useEffect, useRef, useState } from "react";
import { CommandActivity } from "../../components/command-activity";
import { CommandAiBrief } from "../../components/command-ai-brief";
import { CommandKpis } from "../../components/command-kpis";
import { CommandNetworkPreview } from "../../components/command-network-preview";
import { CommandRuleSummary } from "../../components/command-rule-summary";
import { ExecKpis } from "../../components/exec-kpis";
import { FeatureCards } from "../../components/feature-cards";
import { SystemStatus } from "../../components/system-status";
import { WorkflowStrip } from "../../components/workflow-strip";
import {
  ApiError,
  apiBaseUrl,
  getCase,
  getCaseAudit,
  getGraph,
  getHealth,
  getInvestigation,
  getReplay,
  type AuditEntry,
  type CaseDetail,
  type GraphResponse,
  type HealthCheck,
  type InvestigationDetail,
} from "../../lib/api";

/* Signature demo identifiers. These select which seeded records to fetch;
 * every value rendered comes from the backend responses, never from
 * these constants. */
const INV_ID = "inv_84721";
const TXN_ID = "txn_84721";
const CASE_ID = "case_84721";
const SCENARIO_FALLBACK = "scn_primary";

type Section<T> =
  | { kind: "loading" }
  | { kind: "ready"; data: T }
  | { kind: "error"; message: string };

interface Counts {
  transactions: number;
  events: number;
  edges: number;
}

interface Dashboard {
  health: Section<HealthCheck>;
  investigation: Section<InvestigationDetail>;
  graph: Section<GraphResponse>;
  caseDetail: Section<CaseDetail>;
  audits: Section<AuditEntry[]>;
  replay: Section<Counts>;
}

const INITIAL: Dashboard = {
  health: { kind: "loading" },
  investigation: { kind: "loading" },
  graph: { kind: "loading" },
  caseDetail: { kind: "loading" },
  audits: { kind: "loading" },
  replay: { kind: "loading" },
};

function toMessage(err: unknown): string {
  if (err instanceof ApiError) return `${err.code}: ${err.message}`;
  if (err instanceof Error) return err.message;
  return "request failed";
}

function SectionSkeleton({ label }: { label: string }) {
  return (
    <section className="card command-section" aria-live="polite">
      <h2>{label}</h2>
      <p className="muted">Loading…</p>
      <div
        className="skeleton"
        style={{ height: "4.5rem" }}
        aria-hidden="true"
      />
    </section>
  );
}

function SectionError({
  title,
  message,
  onRetry,
}: {
  title: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <section className="card command-section" aria-live="polite">
      <h2>{title}</h2>
      <p className="muted">{message}</p>
      {onRetry && (
        <p>
          <button type="button" onClick={onRetry}>
            Retry {title}
          </button>
        </p>
      )}
    </section>
  );
}

type FetchKey = "health" | "investigation" | "graph" | "caseDetail" | "audits";

const LOADERS: Record<FetchKey, (signal: AbortSignal) => Promise<unknown>> = {
  health: (signal) => getHealth(signal),
  investigation: (signal) => getInvestigation(INV_ID, signal),
  graph: (signal) => getGraph(TXN_ID, signal),
  caseDetail: (signal) => getCase(CASE_ID, signal),
  audits: (signal) => getCaseAudit(CASE_ID, signal).then((res) => res.audits),
};

export default function CommandPage() {
  const [state, setState] = useState<Dashboard>(INITIAL);
  const [checkedAt, setCheckedAt] = useState<string | null>(null);
  /* Sections queued for (re)load. Initial mount queues all five; each
   * section Retry re-queues only its failed key. All loads are read-only
   * GETs, so retries can never duplicate investigations or decisions. */
  const [queued, setQueued] = useState<FetchKey[]>([
    "health",
    "investigation",
    "graph",
    "caseDetail",
    "audits",
  ]);
  /* Duplicate-request guard: a key already in flight is never refetched. */
  const inflight = useRef<Set<FetchKey>>(new Set());

  const patch = (key: FetchKey, section: Dashboard[FetchKey]) =>
    setState((prev) => ({ ...prev, [key]: section }) as Dashboard);

  const retry = (keys: FetchKey[]) => {
    const failed = keys.filter((key) => state[key].kind === "error");
    if (failed.length === 0) return;
    for (const key of failed) {
      patch(key, { kind: "loading" });
    }
    setQueued((prev) => Array.from(new Set([...prev, ...failed])));
  };

  useEffect(() => {
    if (queued.length === 0) return;
    const controller = new AbortController();
    const { signal } = controller;
    /* Each section loads independently so one failed endpoint degrades
     * to an honest inline message instead of blanking the dashboard. */
    for (const key of queued) {
      if (inflight.current.has(key)) continue;
      inflight.current.add(key);
      LOADERS[key](signal).then(
        (data) => {
          inflight.current.delete(key);
          if (signal.aborted) {
            // StrictMode remount: nudge the effect so a live controller
            // picks the key up (no-op after a real unmount).
            setQueued((prev) => (prev.includes(key) ? [...prev] : prev));
            return;
          }
          if (key === "health") setCheckedAt(new Date().toLocaleString());
          patch(key, { kind: "ready", data } as Dashboard[FetchKey]);
          setQueued((prev) => prev.filter((k) => k !== key));
        },
        (err: unknown) => {
          inflight.current.delete(key);
          if (signal.aborted) {
            setQueued((prev) => (prev.includes(key) ? [...prev] : prev));
            return;
          }
          patch(key, { kind: "error", message: toMessage(err) });
          setQueued((prev) => prev.filter((k) => k !== key));
        }
      );
    }
    return () => controller.abort();
  }, [queued]);

  const { health, investigation, graph, caseDetail, audits, replay } = state;

  /* Replay counts need the confirmed scenario, so they load after health.
   * Cursor 0 reports the total; cursor total reports full counts. */
  useEffect(() => {
    if (health.kind === "loading") return;
    if (health.kind === "error") {
      setState(
        (prev): Dashboard => ({
          ...prev,
          replay: { kind: "error", message: "Replay unavailable." },
        })
      );
      return;
    }
    const controller = new AbortController();
    const scenario = health.data.scenario_id;
    getReplay(scenario, 0, controller.signal)
      .then((first) => {
        if (controller.signal.aborted) return null;
        if (first.total <= 0) return first;
        return getReplay(scenario, first.total, controller.signal);
      })
      .then((full) => {
        if (full === null || controller.signal.aborted) return;
        setState(
          (prev): Dashboard => ({
            ...prev,
            replay: { kind: "ready", data: full.counts },
          })
        );
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setState(
          (prev): Dashboard => ({
            ...prev,
            replay: { kind: "error", message: toMessage(err) },
          })
        );
      });
    return () => controller.abort();
  }, [health]);

  const allFailed =
    health.kind === "error" &&
    investigation.kind === "error" &&
    graph.kind === "error" &&
    caseDetail.kind === "error" &&
    audits.kind === "error";

  const invId =
    investigation.kind === "ready"
      ? investigation.data.investigation.investigation_id
      : INV_ID;
  const txnId =
    investigation.kind === "ready"
      ? investigation.data.investigation.transaction_id
      : TXN_ID;
  const scenarioId =
    health.kind === "ready" ? health.data.scenario_id : SCENARIO_FALLBACK;
  const caseId =
    caseDetail.kind === "ready"
      ? caseDetail.data.case.case_id
      : investigation.kind === "ready"
        ? (investigation.data.case?.case_id ?? CASE_ID)
        : CASE_ID;
  const invStatus =
    investigation.kind === "ready" ? investigation.data.investigation.status : "—";
  const caseStatus =
    caseDetail.kind === "ready"
      ? caseDetail.data.case.status
      : (investigation.kind === "ready"
          ? (investigation.data.case?.status ?? "—")
          : "—");

  return (
    <main className="main command-main">
      <div className="hero glass">
        <div className="hero-grid">
          <div>
            <h1>CruiseShield AI™</h1>
            <p className="hero-tag">The Financial Crime Immune System™</p>
            <p>
              Financial crime rarely appears in one transaction. CruiseShield
              AI connects suspicious transactions, accounts, devices,
              beneficiaries and merchants into an explainable intelligence
              network.
            </p>
            <p className="muted">
              Its deterministic risk engine identifies signals, Meta AI helps
              investigators interpret evidence, replay and simulation explore
              hypothetical scenarios, and human decisions remain accountable
              and auditable.
            </p>
            <WorkflowStrip
              invId={invId}
              txnId={txnId}
              caseId={caseId}
              scenarioId={scenarioId}
            />
          </div>
          <div className="hero-side">
            {health.kind === "loading" && (
              <SectionSkeleton label="System Status" />
            )}
            {health.kind === "error" && (
              <SectionError
                title="System status unavailable"
                message={health.message}
                onRetry={() => retry(["health"])}
              />
            )}
            {health.kind === "ready" && (
              <SystemStatus
                health={health.data}
                checkedAt={checkedAt ?? "—"}
              />
            )}
          </div>
        </div>
      </div>

      {allFailed ? (
        <section className="card" aria-live="assertive">
          <h2>Backend status</h2>
          <div className="alert error" role="alert">
            {health.kind === "error" ? health.message : "request failed"}
          </div>
          <p className="muted">
            Start the backend (
            <code>.venv/Scripts/python -m uvicorn app.main:app</code>) and
            press retry.
          </p>
          <p>
            <button type="button" onClick={() => window.location.reload()}>
              Retry
            </button>
          </p>
          <p className="muted">Checked {apiBaseUrl()}…</p>
        </section>
      ) : (
        <>
          {(investigation.kind === "loading" ||
            caseDetail.kind === "loading") && (
            <SectionSkeleton label="Executive overview" />
          )}
          {(investigation.kind === "error" ||
            caseDetail.kind === "error") && (
            <SectionError
              title="Executive overview unavailable"
              message={
                investigation.kind === "error"
                  ? investigation.message
                  : caseDetail.kind === "error"
                    ? caseDetail.message
                    : "request failed"
              }
              onRetry={() =>
                retry([
                  ...(investigation.kind === "error"
                    ? (["investigation"] as const)
                    : []),
                  ...(caseDetail.kind === "error"
                    ? (["caseDetail"] as const)
                    : []),
                ])
              }
            />
          )}
          {investigation.kind === "ready" && caseDetail.kind === "ready" && (
            <ExecKpis
              invId={invId}
              invStatus={invStatus}
              networkBand={investigation.data.risk_network.band}
              evidenceCount={investigation.data.evidence_count}
              latestRun={caseDetail.data.latest_ai_run}
              decisionsCount={caseDetail.data.decisions.length}
              caseId={caseId}
              caseStatus={caseStatus}
              txnCount={
                replay.kind === "ready" ? replay.data.transactions : null
              }
              txnPending={replay.kind === "loading"}
            />
          )}

          <div className="dash-grid">
            <div className="dash-col">
              {investigation.kind === "loading" && (
                <SectionSkeleton label="Risk intelligence" />
              )}
              {investigation.kind === "error" && (
                <SectionError
                  title="Risk intelligence unavailable"
                  message={investigation.message}
                  onRetry={() => retry(["investigation"])}
                />
              )}
              {investigation.kind === "ready" && (
                <>
                  <CommandKpis
                    detail={investigation.data}
                    graph={graph.kind === "ready" ? graph.data : null}
                    graphPending={graph.kind === "loading"}
                  />
                  <CommandRuleSummary
                    rules={investigation.data.rule_results}
                    invId={invId}
                  />
                </>
              )}
            </div>

            <div className="dash-col">
              {graph.kind === "loading" && (
                <SectionSkeleton label="Network preview" />
              )}
              {graph.kind === "error" && (
                <SectionError
                  title="Network preview unavailable"
                  message={graph.message}
                  onRetry={() => retry(["graph"])}
                />
              )}
              {graph.kind === "ready" && (
                <CommandNetworkPreview graph={graph.data} />
              )}
            </div>

            <div className="dash-col">
              {caseDetail.kind === "loading" && (
                <SectionSkeleton label="Muse Spark brief" />
              )}
              {caseDetail.kind === "error" && (
                <SectionError
                  title="AI brief unavailable"
                  message={caseDetail.message}
                  onRetry={() => retry(["caseDetail"])}
                />
              )}
              {caseDetail.kind === "ready" && (
                <CommandAiBrief
                  assessment={caseDetail.data.latest_ai_run}
                  invId={invId}
                />
              )}
              {audits.kind === "loading" && (
                <SectionSkeleton label="Recent activity" />
              )}
              {audits.kind === "error" && (
                <SectionError
                  title="Activity unavailable"
                  message={audits.message}
                  onRetry={() => retry(["audits"])}
                />
              )}
              {audits.kind === "ready" && (
                <CommandActivity audits={audits.data} caseId={caseId} />
              )}
            </div>
          </div>

          <FeatureCards
            invId={invId}
            invStatus={invStatus}
            txnId={txnId}
            caseId={caseId}
            caseStatus={caseStatus}
            scenarioId={scenarioId}
            graphCounts={graph.kind === "ready" ? graph.data.counts : null}
            evidenceCount={
              investigation.kind === "ready"
                ? investigation.data.evidence_count
                : null
            }
          />
        </>
      )}
    </main>
  );
}
