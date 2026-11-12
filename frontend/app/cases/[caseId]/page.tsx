"use client";

/* Batch 4: case route. Case state, human decisions, and the audit trail
 * all come from GET /api/v1/cases/{id}[/audit]; decisions post to
 * POST /api/v1/cases/{id}/decisions and the server validates them. */

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { useTranslation } from "../../../lib/i18n/context";
import { AuditList } from "../../../components/audit-list";
import { Breadcrumbs } from "../../../components/breadcrumbs";
import { DecisionForm } from "../../../components/decision-form";
import { RiskBadge } from "../../../components/risk-badge";
import { SectionNav } from "../../../components/section-nav";
import { TelecomSection } from "../../../components/telecom-section";
import {
  ApiError,
  getAiRun,
  getCase,
  getCaseAudit,
  getInvestigation,
  userErrorMessage,
  type AiAssessment,
  type AgentRun,
  type AuditEntry,
  type CaseDetail,
  type DecisionResponse,
} from "../../../lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ready"; detail: CaseDetail; audits: AuditEntry[] }
  | { kind: "not-found" }
  | { kind: "error"; message: string };

/* GAP-012: full persisted-run expander. The assessment above shows
 * the conclusion, findings, and missing information; expanding fetches
 * the stored run receipt (summary, alternatives, disclaimer) from
 * GET /api/v1/ai-runs/{id}. Lazy, best-effort, read-only. */
function RunDetail({ runId }: { runId: string }) {
  const { t } = useTranslation("evidence");
  const { t: tAi } = useTranslation("ai");
  const { t: tCommon } = useTranslation("common");
  const [state, setState] = useState<
    | { kind: "closed" }
    | { kind: "loading" }
    | { kind: "ready"; run: AgentRun }
    | { kind: "error"; message: string }
  >({ kind: "closed" });
  const load = () => {
    setState({ kind: "loading" });
    getAiRun(runId).then(
      (run) => setState({ kind: "ready", run }),
      (err: unknown) =>
        setState({
          kind: "error",
          message: userErrorMessage(err, tCommon),
        })
    );
  };
  if (state.kind === "closed") {
    return (
      <p>
        <button type="button" onClick={load} aria-expanded={false}>
          {t("showProv")}
        </button>
      </p>
    );
  }
  return (
    <div>
      <p>
        <button
          type="button"
          onClick={() => setState({ kind: "closed" })}
          aria-expanded={true}
        >
          {t("hideProv")}
        </button>
      </p>
      {state.kind === "loading" && (
        <p className="muted">{tCommon("loading")}</p>
      )}
      {state.kind === "error" && (
        <>
          <div className="alert error" role="alert">
            {state.message}
          </div>
          <p>
            <button type="button" onClick={load}>
              {tCommon("retry")}
            </button>
          </p>
        </>
      )}
      {state.kind === "ready" && (
        <>
          <p>{state.run.result.summary}</p>
          {(state.run.result.alternative_explanations ?? []).length > 0 && (
            <>
              <p className="muted">{tAi("altTitle")}</p>
              <ul className="stack">
                {(state.run.result.alternative_explanations ?? []).map(
                  (item, index) => (
                    <li key={index} className="muted">
                      {item}
                    </li>
                  )
                )}
              </ul>
            </>
          )}
          <p className="muted">{state.run.result.disclaimer}</p>
        </>
      )}
    </div>
  );
}

/* Hotfix: tolerate backends predating F2 (no latest_ai_run key at all)
 * and partial payloads. Renders only when a valid assessment object
 * exists; every field access is guarded. API errors still surface via
 * the page-level error state, never as this empty state. */
function AiAssessmentSection({ detail }: { detail: CaseDetail }) {
  const { t } = useTranslation("case");
  const { t: tCommon } = useTranslation("common");
  const assessment: AiAssessment | null | undefined =
    detail?.latest_ai_run ?? null;
  const findings = Array.isArray(assessment?.key_findings)
    ? (assessment?.key_findings as AiAssessment["key_findings"])
    : [];
  const missing = Array.isArray(assessment?.missing_information)
    ? (assessment?.missing_information as string[])
    : [];
  return (
    <section className="card" aria-label={t("assessLabel")}>
      <h2 id="ai-assessment-h">{t("assessTitle")}</h2>
      <p className="muted">{t("advisory")}</p>
      {assessment === null || assessment === undefined ? (
        <p className="muted" data-testid="ai-assessment-empty">
          {t("assessEmpty")}
        </p>
      ) : (
        <div data-testid="ai-assessment">
          <p>
            <strong>
              {t("conclusionPre")}
              {assessment.conclusion || "—"}
            </strong>{" "}
            <span className="muted">
              {t("runMetaPre", {
                model: assessment.model_id || tCommon("unknownModel"),
              })}
              <code>{assessment.agent_run_id || "—"}</code>{" "}
              {t("runMetaPost", {
                ms: assessment.latency_ms ?? "—",
                s: assessment.schema_validation_status || "—",
                r: assessment.evidence_reference_validation_status || "—",
              })}
            </span>
          </p>
          <ul className="stack">
            {findings.map((finding, index) => (
              <li key={index} className="finding">
                <div>{finding?.finding || "—"}</div>
                <p className="muted">
                  {t("confidencePre")}
                  {finding?.confidence_label || "—"} ·{" "}
                  {(finding?.evidence_ids ?? []).join(", ")}
                </p>
              </li>
            ))}
          </ul>
          {assessment.agent_run_id ? (
            <RunDetail runId={assessment.agent_run_id} />
          ) : null}
          {missing.length > 0 && (
            <p className="muted">
              {t("missingInfo", { list: missing.join("; ") })}
            </p>
          )}
        </div>
      )}
    </section>
  );
}

export default function CasePage() {
  const params = useParams<{ caseId: string }>();
  const caseId = params.caseId;
  const { t } = useTranslation("case");
  const { t: tCommon } = useTranslation("common");
  const { t: tInv } = useTranslation("investigation");
  const { t: tNav } = useTranslation("nav");
  const [state, setState] = useState<State>({ kind: "loading" });
  // Best-effort risk summary (Phase 4): the investigation behind this
  // case carries the authoritative scores. A failure here never breaks
  // the case page; the strip simply stays hidden (DI-10 pattern).
  const [risk, setRisk] = useState<
    | { kind: "loading" }
    | {
        kind: "ready";
        networkScore: number;
        networkBand: string;
        txnScore: number;
        txnBand: string;
        version: string;
      }
    | { kind: "hidden" }
  >({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    setRisk({ kind: "loading" });
    Promise.all([
      getCase(caseId, controller.signal),
      getCaseAudit(caseId, controller.signal),
    ])
      // Pass the whole CaseDetail through: destructuring only some keys
      // here silently dropped latest_ai_run (always undefined at runtime).
      .then(([detail, { audits }]) => {
        setState({ kind: "ready", detail, audits });
        getInvestigation(detail.case.investigation_id, controller.signal)
          .then((inv) =>
            setRisk({
              kind: "ready",
              networkScore: inv.risk_network.score,
              networkBand: inv.risk_network.band,
              txnScore: inv.risk_transaction.score,
              txnBand: inv.risk_transaction.band,
              version: inv.risk_network.score_version,
            })
          )
          .catch(() => {
            if (!controller.signal.aborted) setRisk({ kind: "hidden" });
          });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError && err.code === "CASE_NOT_FOUND") {
          setState({ kind: "not-found" });
          return;
        }
        setState({
          kind: "error",
          message: userErrorMessage(err, tCommon),
        });
      });
    return () => controller.abort();
  }, [caseId]);

  function onDecided(response: DecisionResponse) {
    setState((prev) => {
      if (prev.kind !== "ready") return prev;
      return {
        kind: "ready",
        detail: {
          case: response.case,
          decisions: [...prev.detail.decisions, response.decision],
          // Allowed transitions depend on the new status; refetch the
          // case to get the authoritative list rather than guessing it.
          allowed_transitions: [],
          latest_ai_run: prev.detail.latest_ai_run,
        },
        audits: [...prev.audits, response.audit],
      };
    });
    getCase(caseId)
      .then(({ allowed_transitions }) =>
        setState((prev) =>
          prev.kind === "ready"
            ? {
                ...prev,
                detail: { ...prev.detail, allowed_transitions },
              }
            : prev
        )
      )
      .catch(() => {});
  }

  return (
    <main className="main">
      <Breadcrumbs
        items={[
          { label: tNav("commandCenter"), href: "/platform" },
          { label: t("crumb", { id: caseId }) },
        ]}
      />
      {state.kind === "loading" && (
        <section className="card" aria-live="polite">
          <h1>{t("title", { id: caseId })}</h1>
          <p className="muted">{t("loading")}</p>
        </section>
      )}
      {state.kind === "not-found" && (
        <section className="card" aria-live="assertive">
          <h1>{t("notFoundTitle")}</h1>
          <p className="muted">
            {t("notFoundPre")}
            <code>{caseId}</code>
            {t("notFoundPost")}
          </p>
        </section>
      )}
      {state.kind === "error" && (
        <section className="card" aria-live="assertive">
          <h1>{t("title", { id: caseId })}</h1>
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
          <SectionNav
            items={[
              { id: "overview-h", label: t("overview") },
              { id: "ai-assessment-h", label: t("aiAssessment") },
              { id: "decision-history-h", label: t("decisionHistory") },
              { id: "human-decision-h", label: t("humanDecision") },
              { id: "audit-h", label: t("auditTrail") },
            ]}
          />
          <div className="page-head">
            <h1 id="overview-h">
              {t("caseTitlePre")}
              <code>{state.detail.case.case_id}</code> {t("caseTitleDash")}
              <span data-testid="case-status">{state.detail.case.status}</span>
            </h1>
            <p className="muted">
              {t("invPre")}
              <Link
                href={`/investigations/${state.detail.case.investigation_id}`}
                className="back-link"
              >
                {state.detail.case.investigation_id}
              </Link>{" "}
              {t("updatedPre")}{" "}
              <bdi>{state.detail.case.updated_at}</bdi>
            </p>
            <p className="muted" data-testid="case-transitions">
              {t("transitionsPre")}
              {state.detail.allowed_transitions.length === 0
                ? t("transitionsEmpty")
                : state.detail.allowed_transitions.join(", ")}
            </p>
            {risk.kind === "ready" && (
              <p data-testid="case-risk">
                <RiskBadge
                  score={risk.networkScore}
                  band={risk.networkBand}
                />{" "}
                <span className="muted">
                  {tInv("riskLine", {
                    score: risk.txnScore,
                    band: risk.txnBand,
                    version: risk.version,
                  })}
                </span>
              </p>
            )}
          </div>
          <AiAssessmentSection detail={state.detail} />
          <section className="card" aria-label={t("histLabel")}>
            <h2 id="decision-history-h">{t("histTitle")}</h2>
            {state.detail.decisions.length === 0 ? (
              <p className="muted">{t("histEmpty")}</p>
            ) : (
              <ul className="stack" data-testid="decision-history">
                {state.detail.decisions.map((d) => (
                  <li key={d.decision_id} className="finding">
                    <p>
                      <strong>{d.decision}</strong>{" "}
                      {t("decidedByPre", { actor: d.actor_id })}{" "}
                      <bdi>{d.created_at}</bdi>
                    </p>
                    <p className="muted">{d.reason}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
          <DecisionForm
            caseId={caseId}
            allowedTransitions={state.detail.allowed_transitions}
            onDecided={onDecided}
          />
          <p>
            <Link
              href={`/cases/${caseId}/audit`}
              className="back-link"
            >
              {t("openAudit")}
            </Link>
          </p>
          <AuditList audits={state.audits} />
          <section className="card" aria-live="polite">
            <TelecomSection />
          </section>
        </>
      )}
    </main>
  );
}
