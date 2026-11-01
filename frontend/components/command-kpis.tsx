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
import { RiskBadge } from "./risk-badge";

interface Props {
  detail: InvestigationDetail;
  graph: GraphResponse | null;
  graphPending: boolean;
}

function KpiValue({ value, label }: { value: number; label: string }) {
  const display = useCountUp(value);
  return (
    <span className="kpi-value" aria-label={`${value} ${label}`}>
      <span aria-hidden="true">{display}</span>
    </span>
  );
}

export function CommandKpis({ detail, graph, graphPending }: Props) {
  const txn = detail.transaction;
  const txnNumber = txn.transaction_id.split("_")[1] ?? txn.transaction_id;
  const invId = detail.investigation.investigation_id;
  const triggered = detail.rule_results.filter((r) => r.triggered).length;
  const uplift = detail.risk_network.score - detail.risk_transaction.score;

  return (
    <section aria-labelledby="risk-intel-h" className="command-section">
      <h2 id="risk-intel-h">Risk intelligence</h2>
      <div className="spot-grid">
        <article
          className="card glass kpi-card risk-spotlight"
          aria-labelledby="net-risk-h"
        >
          <h3 id="net-risk-h">Network risk</h3>
          <p>
            <strong>Transaction #{txnNumber}</strong>{" "}
            <span className="muted">
              {formatKobo(txn.amount_minor, txn.currency)} ·{" "}
              {txn.sender_account_id} → {txn.receiver_account_id} ·{" "}
              {txn.channel}
            </span>
          </p>
          <RiskBadge
            score={detail.risk_network.score}
            band={detail.risk_network.band}
          />
          <p className="muted">
            {detail.risk_network.score_version} · network scope ·{" "}
            {uplift >= 0 ? "+" : ""}
            {uplift} vs transaction-only (derived difference)
          </p>
          <p className="muted">{detail.risk_network.limitations}</p>
        </article>
        <article className="card kpi-card" aria-labelledby="txn-risk-h">
          <h3 id="txn-risk-h">Transaction-only risk</h3>
          <RiskBadge
            score={detail.risk_transaction.score}
            band={detail.risk_transaction.band}
          />
          <p className="muted">
            {detail.risk_transaction.score_version} · single-transfer scope
          </p>
          <p className="muted">
            This transfer on its own, before network context. The network
            score above is authoritative for the investigation.
          </p>
        </article>
      </div>
      <div className="kpi-grid">
        <article className="card kpi-card" aria-labelledby="ev-kpi-h">
          <h3 id="ev-kpi-h">Evidence package</h3>
          <KpiValue value={detail.evidence_count} label="evidence records" />
          <p className="muted">
            Package <code>{detail.evidence_package_id}</code>
          </p>
          <p>
            <Link href={`/investigations/${invId}`}>Open evidence</Link>
          </p>
        </article>
        <article className="card kpi-card" aria-labelledby="net-kpi-h">
          <h3 id="net-kpi-h">Investigation network</h3>
          {graph === null ? (
            <p className="muted">
              {graphPending ? "Loading network…" : "Network data unavailable."}
            </p>
          ) : (
            <>
              <p>
                <KpiValue value={graph.counts.nodes} label="nodes" /> ·{" "}
                <KpiValue value={graph.counts.edges} label="edges" />
              </p>
              <p className="muted">
                Provenance errors: {graph.provenance_errors.length}
              </p>
              <p>
                <Link href={`/network/${graph.transaction_id}`}>
                  Open network explorer
                </Link>
              </p>
            </>
          )}
        </article>
        <article className="card kpi-card" aria-labelledby="rule-kpi-h">
          <h3 id="rule-kpi-h">Rules triggered</h3>
          <span
            className="kpi-value"
            aria-label={`${triggered} of ${detail.rule_results.length} rules triggered`}
          >
            {triggered} of {detail.rule_results.length}
          </span>
          <p className="muted">Versioned deterministic rules</p>
          <p>
            <Link href={`/investigations/${invId}`}>Why this risk</Link>
          </p>
        </article>
      </div>
    </section>
  );
}
