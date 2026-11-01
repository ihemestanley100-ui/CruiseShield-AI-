"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AiPanel } from "../../../components/ai-panel";
import { Breadcrumbs } from "../../../components/breadcrumbs";
import { EvidenceList } from "../../../components/evidence-list";
import { IntelSection } from "../../../components/intel-panels";
import { RiskBadge } from "../../../components/risk-badge";
import { SectionNav } from "../../../components/section-nav";
import { WhyRiskPanel } from "../../../components/why-risk-panel";
import {
  ApiError,
  getEvidencePackage,
  getIntelEvidence,
  getInvestigation,
  getInvestigationIntel,
  getRiskIntel,
  type EvidencePackage,
  type IntelEvidence,
  type InvIntel,
  type InvestigationDetail,
  type RiskIntelResult,
} from "../../../lib/api";
import { formatKobo } from "../../../lib/format";

type State =
  | { kind: "loading" }
  | {
      kind: "ready";
      detail: InvestigationDetail;
      pkg: EvidencePackage;
      intel: InvIntel | null;
      diEvidence: IntelEvidence | null;
      risk: RiskIntelResult | null;
    }
  | { kind: "not-found" }
  | { kind: "error"; message: string };

export default function InvestigationPage() {
  const params = useParams<{ id: string }>();
  const invId = params.id;
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    Promise.all([
      getInvestigation(invId, controller.signal),
      getEvidencePackage(invId, controller.signal),
      /* DI-10 intel is best-effort: the page renders fully if it fails. */
      getInvestigationIntel(invId, controller.signal).catch(() => null),
      getIntelEvidence(invId, controller.signal).catch(() => null),
      getRiskIntel(invId, controller.signal).catch(() => null),
    ])
      .then(([detail, pkg, intel, diEvidence, risk]) =>
        setState({ kind: "ready", detail, pkg, intel, diEvidence, risk })
      )
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (
          err instanceof ApiError &&
          err.code === "UNKNOWN_INVESTIGATION"
        ) {
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
  }, [invId]);

  return (
    <main className="main">
      <Breadcrumbs
        items={[
          { label: "Command Center", href: "/demo" },
          { label: `Investigation ${invId}` },
        ]}
      />
      {state.kind === "loading" && (
        <section className="card" aria-live="polite">
          <h1>Investigation {invId}</h1>
          <p className="muted">Loading investigation…</p>
        </section>
      )}
      {state.kind === "not-found" && (
        <section className="card" aria-live="assertive">
          <h1>Investigation not found</h1>
          <p className="muted">
            No investigation <code>{invId}</code> exists in the backend.
          </p>
        </section>
      )}
      {state.kind === "error" && (
        <section className="card" aria-live="assertive">
          <h1>Investigation {invId}</h1>
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
              { id: "why-risk-h", label: "Why this risk?" },
              { id: "evidence-h", label: "Evidence" },
              { id: "intel-h", label: "Intelligence" },
              { id: "ai-h", label: "AI analysis" },
            ]}
          />
          <div className="page-head">
            <h1 id="overview-h">
              Transaction #{state.detail.transaction.transaction_id.split("_")[1]}{" "}
              —{" "}
              {formatKobo(
                state.detail.transaction.amount_minor,
                state.detail.transaction.currency
              )}
            </h1>
            <p>
              {state.detail.transaction.sender_account_id} →{" "}
              {state.detail.transaction.receiver_account_id} · channel{" "}
              {state.detail.transaction.channel} ·{" "}
              {state.detail.transaction.occurred_at}
            </p>
            <p>
              <RiskBadge
                score={state.detail.risk_network.score}
                band={state.detail.risk_network.band}
              />{" "}
              <span className="muted">
                network risk · transaction-only{" "}
                {state.detail.risk_transaction.score}/100{" "}
                {state.detail.risk_transaction.band} ·{" "}
                {state.detail.risk_network.score_version}
              </span>
            </p>
            <p className="muted">{state.detail.risk_network.limitations}</p>
            <p className="muted">
              Case{" "}
              <code>{state.detail.case?.case_id ?? "none"}</code> · status{" "}
              {state.detail.case?.status ?? "—"} (read-only in this batch)
            </p>
          </div>
          <WhyRiskPanel rules={state.detail.rule_results} />
          <EvidenceList items={state.pkg.items} />
          <IntelSection
            intel={state.intel}
            evidence={state.diEvidence}
            risk={state.risk}
          />
          <AiPanel invId={invId} />
        </>
      )}
    </main>
  );
}
