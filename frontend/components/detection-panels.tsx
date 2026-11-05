"use client";

/* Detection intelligence panels. Presentational only: all data
 * arrives via props from the page fetch. Measured zeros render with
 * their honesty note; unimplemented detectors and unmapped channels
 * are labeled, never hidden. Counts use tabular figures for
 * scanability; the matrix is a real table with a caption. */

import Link from "next/link";
import type {
  ChannelRow,
  ChannelsSummary,
  DetectionBundle,
  DetectionMatrix,
  DetectorInfo,
  SignalsSummary,
  TxnSignals,
} from "../lib/api";
import { useTranslation } from "../lib/i18n/context";

function CountList({ entries }: { entries: [string, number][] }) {
  if (entries.length === 0) return null;
  return (
    <ul className="stack">
      {entries.map(([label, count]) => (
        <li key={label} className="rule-row">
          <strong>{label}</strong>{" "}
          <span className="tabular">{count}</span>
        </li>
      ))}
    </ul>
  );
}

export function SignalFrequencyPanel({
  summary,
}: {
  summary: SignalsSummary;
}) {
  const { t } = useTranslation("detection");
  const families = Object.entries(summary.by_family).sort(([a], [b]) =>
    a.localeCompare(b)
  );
  const severities = Object.entries(summary.by_severity).sort(([a], [b]) =>
    a.localeCompare(b)
  );
  return (
    <section className="card" aria-labelledby="sig-freq-h">
      <h3 id="sig-freq-h">{t("frequencyTitle")}</h3>
      {summary.total_signals === 0 ? (
        <p className="muted">{t("noSignals")}</p>
      ) : (
        <>
          <p>
            <strong className="tabular">{summary.total_signals}</strong>{" "}
            <span className="muted">
              {summary.unique_transactions_flagged} txns ·{" "}
              {summary.unique_entities_flagged} entities
            </span>
          </p>
          <CountList entries={families} />
          <CountList entries={severities} />
        </>
      )}
      <p className="muted">
        {t("measuredAt")}: {summary.generated_at || "—"}
      </p>
      <p className="muted">{t("zeroNote")}</p>
    </section>
  );
}

export function DetectorHealthPanel({
  detectors,
}: {
  detectors: DetectorInfo[];
}) {
  const { t } = useTranslation("detection");
  return (
    <section className="card" aria-labelledby="det-health-h">
      <h3 id="det-health-h">{t("detectorsTitle")}</h3>
      <ul className="stack">
        {detectors.map((detector) => (
          <li key={detector.family} className="rule-row">
            <strong>{detector.family}</strong>{" "}
            <span className="muted">v{detector.version}</span>{" "}
            <span>{detector.status}</span>
            <p className="muted">
              {detector.status === "NOT_IMPLEMENTED"
                ? t("notImplemented")
                : detector.description}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}

export function ChannelActivityPanel({
  summary,
}: {
  summary: ChannelsSummary;
}) {
  const { t } = useTranslation("detection");
  return (
    <section className="card" aria-labelledby="chan-act-h">
      <h3 id="chan-act-h">{t("channelsTitle")}</h3>
      {summary.unmapped_alert && (
        <div className="alert warn" role="alert">
          {t("unmappedAlert")} {summary.unmapped_raw_codes.join(", ")}
        </div>
      )}
      <ul className="stack">
        {summary.channels.map((row: ChannelRow) => (
          <li key={row.channel} className="rule-row">
            <strong>{row.channel}</strong>{" "}
            <span className="tabular">
              {row.transactions} txns · {row.signals} signals
            </span>
            {row.transactions === 0 && (
              <p className="muted">{row.note}</p>
            )}
          </li>
        ))}
      </ul>
      <p className="muted">{t("seedFeedNote")}</p>
    </section>
  );
}

const MATRIX_CHANNELS = [
  "POS",
  "MOBILE_APP",
  "USSD",
  "NIP",
  "WEB",
  "ATM",
  "TRANSFER",
  "AGENT",
];

export function DetectorChannelMatrix({
  matrix,
}: {
  matrix: DetectionMatrix;
}) {
  const { t } = useTranslation("detection");
  const families = [...new Set(matrix.cells.map((c) => c.family))].sort();
  const byKey = new Map(matrix.cells.map((c) => [`${c.family}|${c.channel}`, c]));
  return (
    <section className="card" aria-labelledby="det-matrix-h">
      <h3 id="det-matrix-h">{t("matrixTitle")}</h3>
      <div className="table-scroll">
        <table>
          <caption className="muted">
            {t("matrixTitle")}: {families.length} families ×{" "}
            {MATRIX_CHANNELS.length} channels
          </caption>
          <thead>
            <tr>
              <th scope="col">Detector</th>
              {MATRIX_CHANNELS.map((channel) => (
                <th key={channel} scope="col">
                  {channel}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {families.map((family) => (
              <tr key={family}>
                <th scope="row">{family}</th>
                {MATRIX_CHANNELS.map((channel) => {
                  const cell = byKey.get(`${family}|${channel}`);
                  if (!cell) return <td key={channel}>—</td>;
                  return (
                    <td key={channel}>
                      <span>{cell.status}</span>{" "}
                      <span className="tabular muted">{cell.signals}</span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted">{t("zeroNote")}</p>
    </section>
  );
}

export function TxnSignalsPanel({ data }: { data: TxnSignals }) {
  const { t } = useTranslation("detection");
  return (
    <section className="card" aria-labelledby="txn-signals-h">
      <h2 id="txn-signals-h">{t("txnSignalsTitle")}</h2>
      {data.signal_count === 0 ? (
        <p className="muted">{t("noSignals")}</p>
      ) : (
        <ul className="stack">
          {data.signals.map((sig) => (
            <li key={sig.signal_id} className="rule-row">
              <strong>{sig.detector_family}</strong>{" "}
              <span className="muted">
                {sig.severity}
                {sig.rule_id ? ` · ${sig.rule_id} v${sig.rule_version}` : ""}
              </span>
              <p className="muted">{sig.reason}</p>
            </li>
          ))}
        </ul>
      )}
      {data.investigation ? (
        <p>
          <Link
            href={`/investigations/${encodeURIComponent(
              data.investigation.investigation_id
            )}`}
          >
            {t("viewInvestigation")}: {data.investigation.investigation_id}
          </Link>
        </p>
      ) : (
        <p className="muted">{t("noLinkedInvestigation")}</p>
      )}
      <p className="muted">{t("zeroNote")}</p>
    </section>
  );
}

export function DetectionSection({ bundle }: { bundle: DetectionBundle }) {
  const { t } = useTranslation("detection");
  return (
    <section className="card command-section" aria-labelledby="detection-h">
      <h2 id="detection-h">{t("title")}</h2>
      <div className="dash-grid">
        <SignalFrequencyPanel summary={bundle.summary} />
        <DetectorHealthPanel detectors={bundle.detectors.detectors} />
        <ChannelActivityPanel summary={bundle.channels} />
      </div>
      <DetectorChannelMatrix matrix={bundle.matrix} />
    </section>
  );
}
