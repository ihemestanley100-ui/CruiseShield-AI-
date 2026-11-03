"use client";

/* Command Center KPI cards. Every value renders from the live backend
 * responses passed in as props; nothing is invented here. Scores reuse
 * RiskBadge so the authoritative bands match the investigation route
 * exactly, and counts announce their final value for assistive tech
 * while animating visually (reduced-motion safe via useCountUp). */

import Link from "next/link";
import type { GraphResponse, InvestigationDetail } from "../lib/api";
import { formatKobo } from "../lib/format";
import { useCountUp } from "../lib/use-count-up";
import { useLocale, useTranslation } from "../lib/i18n/context";
import { formatNumber } from "../lib/i18n/format";
import { RiskBadge } from "./risk-badge";

interface Props {
  detail: InvestigationDetail;
  graph: GraphResponse | null;
  graphPending: boolean;
}

function KpiValue({ value, label }: { value: number; label: string }) {
  const { locale } = useLocale();
  const display = useCountUp(value);
  return (
    <span
      className="kpi-value"
      aria-label={`${formatNumber(locale, value)} ${label}`}
    >
      <span aria-hidden="true">{formatNumber(locale, display)}</span>
    </span>
  );
}

export function CommandKpis({ detail, graph, graphPending }: Props) {
  const { t, locale } = useTranslation("command");
  const { t: tInv } = useTranslation("investigation");
  const txn = detail.transaction;
  const txnNumber = txn.transaction_id.split("_")[1] ?? txn.transaction_id;
  const invId = detail.investigation.investigation_id;
  const triggered = detail.rule_results.filter((r) => r.triggered).length;
  const uplift = detail.risk_network.score - detail.risk_transaction.score;

  return (
    <section aria-labelledby="risk-intel-h" className="command-section">
      <h2 id="risk-intel-h">{t("kpiRiskTitle")}</h2>
      <div className="spot-grid">
        <article
          className="card glass kpi-card risk-spotlight"
          aria-labelledby="net-risk-h"
        >
          <h3 id="net-risk-h">{t("netRiskH")}</h3>
          <p>
            <strong>{t("txnTitleLine", { n: txnNumber })}</strong>{" "}
            <span className="muted">
              {formatKobo(txn.amount_minor, txn.currency, locale)} ·{" "}
              {txn.sender_account_id} → {txn.receiver_account_id} ·{" "}
              {txn.channel}
            </span>
          </p>
          <RiskBadge
            score={detail.risk_network.score}
            band={detail.risk_network.band}
          />
          <p className="muted">
            {t("upliftLine", {
              v: detail.risk_network.score_version,
              sign: uplift >= 0 ? "+" : "",
              u: uplift,
            })}
          </p>
          <p className="muted">{detail.risk_network.limitations}</p>
        </article>
        <article className="card kpi-card" aria-labelledby="txn-risk-h">
          <h3 id="txn-risk-h">{t("txnOnlyH")}</h3>
          <RiskBadge
            score={detail.risk_transaction.score}
            band={detail.risk_transaction.band}
          />
          <p className="muted">
            {t("txnOnlyScope", { v: detail.risk_transaction.score_version })}
          </p>
          <p className="muted">{t("txnOnlyNote")}</p>
        </article>
      </div>
      <div className="kpi-grid">
        <article className="card kpi-card" aria-labelledby="ev-kpi-h">
          <h3 id="ev-kpi-h">{t("evPackH")}</h3>
          <KpiValue value={detail.evidence_count} label={t("evRecords")} />
          <p className="muted">
            {t("packagePre")}
            <code>{detail.evidence_package_id}</code>
          </p>
          <p>
            <Link href={`/investigations/${invId}`}>{t("openEvidence")}</Link>
          </p>
        </article>
        <article className="card kpi-card" aria-labelledby="net-kpi-h">
          <h3 id="net-kpi-h">{t("netH")}</h3>
          {graph === null ? (
            <p className="muted">
              {graphPending ? t("loadingNet") : t("netDown")}
            </p>
          ) : (
            <>
              <p>
                <KpiValue value={graph.counts.nodes} label={t("nodesLabel")} /> ·{" "}
                <KpiValue value={graph.counts.edges} label={t("edgesLabel")} />
              </p>
              <p className="muted">
                {t("provErrors", { n: graph.provenance_errors.length })}
              </p>
              <p>
                <Link href={`/network/${graph.transaction_id}`}>
                  {t("openNetExplorer")}
                </Link>
              </p>
            </>
          )}
        </article>
        <article className="card kpi-card" aria-labelledby="rule-kpi-h">
          <h3 id="rule-kpi-h">{t("rulesH")}</h3>
          <span
            className="kpi-value"
            aria-label={t("rulesAria", {
              a: triggered,
              b: detail.rule_results.length,
            })}
          >
            {t("rulesOf", { a: triggered, b: detail.rule_results.length })}
          </span>
          <p className="muted">{t("versionedRules")}</p>
          <p>
            <Link href={`/investigations/${invId}`}>{tInv("whyRiskLink")}</Link>
          </p>
        </article>
      </div>
    </section>
  );
}
