"use client";

/* Batch 4: case route. Case state, human decisions, and the audit trail
 * all come from GET /api/v1/cases/{id}[/audit]; decisions post to
 * POST /api/v1/cases/{id}/decisions and the server validates them. */

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AuditList } from "../../../components/audit-list";
import { Breadcrumbs } from "../../../components/breadcrumbs";
import { DecisionForm } from "../../../components/decision-form";
import { RiskBadge } from "../../../components/risk-badge";
import { SectionNav } from "../../../components/section-nav";
import {
  ApiError,
  getCase,
  getCaseAudit,
  getInvestigation,
  type AiAssessment,
  type AuditEntry,
  type CaseDetail,
  type DecisionResponse,
} from "../../../lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ready"; detail: CaseDetail; audits: AuditEntry[] }
  | { kind: "not-found" }
  | { kind: "error"; message: string };

/* Hotfix: tolerate backends predating F2 (no latest_ai_run key at all)
 * and partial payloads. Renders only when a valid assessment object
 * exists; every field access is guarded. API errors still surface via
 * the page-level error state, never as this empty state. */
function AiAssessmentSection({ detail }: { detail: CaseDetail }) {
  const assessment: AiAssessment | null | undefined =
    detail?.latest_ai_run ?? null;
  const findings = Array.isArray(assessment?.key_findings)
    ? (assessment?.key_findings as AiAssessment["key_findings"])
    : [];
  const missing = Array.isArray(assessment?.missing_information)
    ? (assessment?.missing_information as string[])
    : [];
  return (
    <section className="card" aria-label="AI Investigation Assessment">
      <h2 id="ai-assessment-h">AI Investigation Assessment</h2>
      <p className="muted">
        Advisory only: Muse Spark analysis explains evidence and never
        constitutes a human decision, nor changes risk scores or case
        status.
      </p>
      {assessment === null || assessment === undefined ? (
        <p className="muted" data-testid="ai-assessment-empty">
          No AI investigation assessment is available yet.
        </p>
      ) : (
        <div data-testid="ai-assessment">
          <p>
            <strong>
              Conclusion: {assessment.conclusion || "—"}
            </strong>{" "}
            <span className="muted">
              ({assessment.model_id || "unknown model"} · run{" "}
              <code>{assessment.agent_run_id || "—"}</code> ·{" "}
              {assessment.latency_ms ?? "—"} ms · schema{" "}
              {assessment.schema_validation_status || "—"} · refs{" "}
              {assessment.evidence_reference_validation_status || "—"})
            </span>
          </p>
          <ul className="stack">
            {findings.map((finding, index) => (
              <li key={index} className="finding">
                <div>{finding?.finding || "—"}</div>
                <p className="muted">
                  Confidence: {finding?.confidence_label || "—"} ·{" "}
                  {(finding?.evidence_ids ?? []).join(", ")}
                </p>
              </li>
            ))}
          </ul>
          {missing.length > 0 && (
            <p className="muted">
              Missing information: {missing.join("; ")}
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
          message:
            err instanceof ApiError
              ? `${err.code}: ${err.message}`
              : err instanceof Error
                ? err.message
                : "request failed",
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
          { label: "Command Center", href: "/demo" },
          { label: `Case ${caseId}` },
        ]}
      />
      {state.kind === "loading" && (
        <section className="card" aria-live="polite">
          <h1>Case {caseId}</h1>
          <p className="muted">Loading case…</p>
        </section>
      )}
      {state.kind === "not-found" && (
        <section className="card" aria-live="assertive">
          <h1>Case not found</h1>
          <p className="muted">
            No case <code>{caseId}</code> exists in the backend.
          </p>
        </section>
      )}
      {state.kind === "error" && (
        <section className="card" aria-live="assertive">
          <h1>Case {caseId}</h1>
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
          <SectionNav
            items={[
              { id: "overview-h", label: "Overview" },
              { id: "ai-assessment-h", label: "AI assessment" },
              { id: "decision-history-h", label: "Decision history" },
              { id: "human-decision-h", label: "Human decision" },
              { id: "audit-h", label: "Audit trail" },
            ]}
          />
          <div className="page-head">
            <h1 id="overview-h">
              Case <code>{state.detail.case.case_id}</code> —{" "}
              <span data-testid="case-status">{state.detail.case.status}</span>
            </h1>
            <p className="muted">
              Investigation{" "}
              <Link
                href={`/investigations/${state.detail.case.investigation_id}`}
                className="back-link"
              >
                {state.detail.case.investigation_id}
              </Link>{" "}
              · updated {state.detail.case.updated_at}
            </p>
            <p className="muted" data-testid="case-transitions">
              Allowed transitions:{" "}
              {state.detail.allowed_transitions.length === 0
                ? "none (terminal state, or refreshing…)"
                : state.detail.allowed_transitions.join(", ")}
            </p>
            {risk.kind === "ready" && (
              <p data-testid="case-risk">
                <RiskBadge
                  score={risk.networkScore}
                  band={risk.networkBand}
                />{" "}
                <span className="muted">
                  network risk · transaction-only {risk.txnScore}/100{" "}
                  {risk.txnBand} · {risk.version}
                </span>
              </p>
            )}
          </div>
          <AiAssessmentSection detail={state.detail} />
          <section className="card" aria-label="Decision history">
            <h2 id="decision-history-h">Decision history</h2>
            {state.detail.decisions.length === 0 ? (
              <p className="muted">No human decisions recorded yet.</p>
            ) : (
              <ul className="stack" data-testid="decision-history">
                {state.detail.decisions.map((d) => (
                  <li key={d.decision_id} className="finding">
                    <p>
                      <strong>{d.decision}</strong> by {d.actor_id} ·{" "}
                      {d.created_at}
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
              Open full audit trail
            </Link>
          </p>
          <AuditList audits={state.audits} />
        </>
      )}
    </main>
  );
}
