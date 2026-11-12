"use client";

import { useEffect, useRef, useState } from "react";
import { CommandActivity } from "../../components/command-activity";
import { CommandAiBrief } from "../../components/command-ai-brief";
import { CommandKpis } from "../../components/command-kpis";
import { CommandNetworkPreview } from "../../components/command-network-preview";
import { CommandRuleSummary } from "../../components/command-rule-summary";
import { DetectionSection } from "../../components/detection-panels";
import { ExecKpis } from "../../components/exec-kpis";
import { FeatureCards } from "../../components/feature-cards";
import { SystemStatus } from "../../components/system-status";
import { TelecomConfigPanel } from "../../components/telecom-section";
import { IndustrySection } from "../../components/industry-section";
import {
  IntelCoveragePanel,
  IntelMetricsPanel,
  IntelProviderPanel,
} from "../../components/intel-admin-panels";
import { WorkflowStrip } from "../../components/workflow-strip";
import {
  apiBaseUrl,
  getCase,
  getCaseAudit,
  getChannelsSummary,
  getDetectionMatrix,
  getDetectors,
  getSignalsTimeSeries,
  getGraph,
  getSignalsSummary,
  getHealth,
  getInvestigation,
  getReplay,
  userErrorMessage,
  type AuditEntry,
  type CaseDetail,
  type DetectionBundle,
  type GraphResponse,
  type HealthCheck,
  type InvestigationDetail,
} from "../../lib/api";
import { useTranslation } from "../../lib/i18n/context";
import { formatDate } from "../../lib/i18n/format";

/* Signature identifiers. These select which seeded records to fetch;
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
  detection: Section<DetectionBundle>;
}

const INITIAL: Dashboard = {
  health: { kind: "loading" },
  investigation: { kind: "loading" },
  graph: { kind: "loading" },
  caseDetail: { kind: "loading" },
  audits: { kind: "loading" },
  replay: { kind: "loading" },
  detection: { kind: "loading" },
};

function SectionSkeleton({ label }: { label: string }) {
  const { t: tCommon } = useTranslation("common");
  return (
    <section className="card command-section" aria-live="polite">
      <h2>{label}</h2>
      <p className="muted">{tCommon("loading")}</p>
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
  const { t } = useTranslation("platform");
  return (
    <section className="card command-section" aria-live="polite">
      <h2>{title}</h2>
      <p className="muted">{message}</p>
      {onRetry && (
        <p>
          <button type="button" onClick={onRetry}>
            {t("retryTitle", { title })}
          </button>
        </p>
      )}
    </section>
  );
}

type FetchKey =
  | "health"
  | "investigation"
  | "graph"
  | "caseDetail"
  | "audits"
  | "detection";

const LOADERS: Record<FetchKey, (signal: AbortSignal) => Promise<unknown>> = {
  health: (signal) => getHealth(signal),
  investigation: (signal) => getInvestigation(INV_ID, signal),
  graph: (signal) => getGraph(TXN_ID, signal),
  caseDetail: (signal) => getCase(CASE_ID, signal),
  audits: (signal) => getCaseAudit(CASE_ID, signal).then((res) => res.audits),
  detection: (signal) =>
    Promise.all([
      getSignalsSummary(signal),
      getChannelsSummary(signal),
      getDetectors(signal),
      getDetectionMatrix(signal),
      getSignalsTimeSeries("day", signal),
    ]).then(([summary, channels, detectors, matrix, timeSeries]) => ({
      summary,
      channels,
      detectors,
      matrix,
      timeSeries,
    })),
};

export default function CommandPage() {
  const { t } = useTranslation("platform");
  const { t: tCommon, locale } = useTranslation("common");
  const { t: tLanding } = useTranslation("landing");
  const toMessage = (err: unknown): string =>
    userErrorMessage(err, tCommon);
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
    "detection",
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
          if (key === "health")
            setCheckedAt(
              formatDate(locale, new Date(), {
                dateStyle: "medium",
                timeStyle: "medium",
              })
            );
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

  const { health, investigation, graph, caseDetail, audits, replay, detection } =
    state;
  const { t: tDetection } = useTranslation("detection");

  /* Replay counts need the confirmed scenario, so they load after health.
   * Cursor 0 reports the total; cursor total reports full counts. */
  useEffect(() => {
    if (health.kind === "loading") return;
    if (health.kind === "error") {
      setState(
        (prev): Dashboard => ({
          ...prev,
          replay: { kind: "error", message: t("replayDown") },
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
            <h1>{tLanding("brandName")}</h1>
            <p className="hero-tag">{tLanding("tagline")}</p>
            <p>{t("heroP1")}</p>
            <p className="muted">{t("heroP2")}</p>
            <WorkflowStrip
              invId={invId}
              txnId={txnId}
              caseId={caseId}
              scenarioId={scenarioId}
            />
          </div>
          <div className="hero-side">
            {health.kind === "loading" && (
              <SectionSkeleton label={t("systemStatus")} />
            )}
            {health.kind === "error" && (
              <SectionError
                title={t("systemStatusDown")}
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
          <h2>{t("backendStatus")}</h2>
          <div className="alert error" role="alert">
            {health.kind === "error"
              ? health.message
              : tCommon("requestFailed")}
          </div>
          <p className="muted">
            {t("startBackendPre")}
            <code>.venv/Scripts/python -m uvicorn app.main:app</code>
            {t("startBackendPost")}
          </p>
          <p>
            <button type="button" onClick={() => window.location.reload()}>
              {tCommon("retry")}
            </button>
          </p>
          <p className="muted">{t("checkedAt", { url: apiBaseUrl() })}</p>
        </section>
      ) : (
        <>
          {(investigation.kind === "loading" ||
            caseDetail.kind === "loading") && (
            <SectionSkeleton label={t("execOverview")} />
          )}
          {(investigation.kind === "error" ||
            caseDetail.kind === "error") && (
            <SectionError
              title={t("execOverviewDown")}
              message={
                investigation.kind === "error"
                  ? investigation.message
                  : caseDetail.kind === "error"
                    ? caseDetail.message
                    : tCommon("requestFailed")
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
                <SectionSkeleton label={t("riskIntel")} />
              )}
              {investigation.kind === "error" && (
                <SectionError
                  title={t("riskIntelDown")}
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
                <SectionSkeleton label={t("networkPreview")} />
              )}
              {graph.kind === "error" && (
                <SectionError
                  title={t("networkPreviewDown")}
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
                <SectionSkeleton label={t("museBrief")} />
              )}
              {caseDetail.kind === "error" && (
                <SectionError
                  title={t("aiBriefDown")}
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
                <SectionSkeleton label={t("recentActivity")} />
              )}
              {audits.kind === "error" && (
                <SectionError
                  title={t("activityDown")}
                  message={audits.message}
                  onRetry={() => retry(["audits"])}
                />
              )}
              {audits.kind === "ready" && (
                <CommandActivity audits={audits.data} caseId={caseId} />
              )}
            </div>
          </div>

          {detection.kind === "loading" && (
            <SectionSkeleton label={tDetection("title")} />
          )}
          {detection.kind === "error" && (
            <SectionError
              title={tDetection("title")}
              message={detection.message}
              onRetry={() => retry(["detection"])}
            />
          )}
          {detection.kind === "ready" && (
            <DetectionSection bundle={detection.data} />
          )}

          <section className="card" aria-live="polite">
            <h2>Telecom provider status</h2>
            <TelecomConfigPanel />
          </section>

          <section className="card" aria-live="polite">
            <h2>Intelligence providers</h2>
            <IntelProviderPanel />
          </section>

          <section className="card" aria-live="polite">
            <h2>Coverage and activity</h2>
            <IntelCoveragePanel />
            <IntelMetricsPanel />
          </section>

          <section className="card" aria-live="polite">
            <IndustrySection />
          </section>

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
