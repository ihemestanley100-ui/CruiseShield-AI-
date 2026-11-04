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
  userErrorMessage,
  type EvidencePackage,
  type IntelEvidence,
  type InvIntel,
  type InvestigationDetail,
  type RiskIntelResult,
} from "../../../lib/api";
import { formatKobo } from "../../../lib/format";
import { useTranslation } from "../../../lib/i18n/context";
import { formatDate } from "../../../lib/i18n/format";

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
  const { t, locale } = useTranslation("investigation");
  const { t: tCommon } = useTranslation("common");
  const { t: tNav } = useTranslation("nav");
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
          message: userErrorMessage(err, tCommon),
        });
      });
    return () => controller.abort();
  }, [invId]);

  return (
    <main className="main">
      <Breadcrumbs
        items={[
          { label: tNav("commandCenter"), href: "/demo" },
          { label: t("crumb", { id: invId }) },
        ]}
      />
      {state.kind === "loading" && (
        <section className="card" aria-live="polite">
          <h1>{t("title", { id: invId })}</h1>
          <p className="muted">{t("loading")}</p>
        </section>
      )}
      {state.kind === "not-found" && (
        <section className="card" aria-live="assertive">
          <h1>{t("notFoundTitle")}</h1>
          <p className="muted">
            {t("notFoundPre")}
            <code>{invId}</code>
            {t("notFoundPost")}
          </p>
        </section>
      )}
      {state.kind === "error" && (
        <section className="card" aria-live="assertive">
          <h1>{t("title", { id: invId })}</h1>
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
              { id: "why-risk-h", label: t("whyRisk") },
              { id: "evidence-h", label: t("evidence") },
              { id: "intel-h", label: t("intelligence") },
              { id: "ai-h", label: t("aiAnalysis") },
            ]}
          />
          <div className="page-head">
            <h1 id="overview-h">
              {t("txnTitle", {
                n: state.detail.transaction.transaction_id.split("_")[1],
              })}{" "}
              —{" "}
              {formatKobo(
                state.detail.transaction.amount_minor,
                state.detail.transaction.currency,
                locale
              )}
            </h1>
            <p>
              {t("overviewLinePre", {
                sender: state.detail.transaction.sender_account_id,
                receiver: state.detail.transaction.receiver_account_id,
                channel: state.detail.transaction.channel,
              })}{" "}
              <bdi>
                {formatDate(locale, state.detail.transaction.occurred_at, {
                  dateStyle: "medium",
                  timeStyle: "short",
                })}
              </bdi>
            </p>
            <p>
              <RiskBadge
                score={state.detail.risk_network.score}
                band={state.detail.risk_network.band}
              />{" "}
              <span className="muted">
                {t("riskLine", {
                  score: state.detail.risk_transaction.score,
                  band: state.detail.risk_transaction.band,
                  version: state.detail.risk_network.score_version,
                })}
              </span>
            </p>
            <p className="muted">{state.detail.risk_network.limitations}</p>
            <p className="muted">
              {t("casePre")}
              <code>{state.detail.case?.case_id ?? "none"}</code>{" "}
              {t("casePost", {
                status: state.detail.case?.status ?? "—",
              })}
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
