"use client";

/* DI-10 investigator intelligence panels. Presentational only: all
 * data arrives via props from the page fetch. Unknown stays unknown;
 * provider-dependent fields render explicit unavailable states; no
 * raw IPs (masked), no precise coordinates, no fraud verdicts. */

import type {
  IntelEvidence,
  IntelFinding,
  InvIntel,
  RiskIntelResult,
  TxnIntel,
} from "../lib/api";
import { maskIp } from "../lib/privacy";
import { useTranslation } from "../lib/i18n/context";

function StatusLine({ label, value }: { label: string; value: string }) {
  const { t: tCommon } = useTranslation("common");
  return (
    <p className="muted">
      {label}: <strong>{value || tCommon("unknown")}</strong>
    </p>
  );
}

function DeviceBlock({ intel }: { intel: TxnIntel }) {
  const { t, tp } = useTranslation("intel");
  const obs = intel.device_observations;
  if (obs.length === 0) {
    return <p className="muted">{t("noDevice")}</p>;
  }
  const labels = [...new Set(obs.map((o) => o.device_id))];
  return (
    <ul className="stack">
      {labels.map((label) => {
        const mine = obs.filter((o) => o.device_id === label);
        const accounts = [...new Set(mine.map((o) => o.account_id ?? "?"))];
        return (
          <li key={label} className="rule-row">
            <strong>
              {label}
              {accounts.length >= 2 ? t("sharedDevice") : t("observedOnly")}
            </strong>
            <p className="muted">
              {tp("obsCount", mine.length)} ·{" "}
              {tp("accountCount", accounts.length)}: {accounts.join(", ")}
            </p>
            <p className="muted">{t("fixtureNote")}</p>
          </li>
        );
      })}
    </ul>
  );
}

function IpBlock({ intel }: { intel: TxnIntel }) {
  const { t } = useTranslation("intel");
  const { t: tCommon } = useTranslation("common");
  const obs = intel.ip_observations;
  return (
    <>
      <StatusLine label={t("ispLabel")} value="NOT_CONFIGURED" />
      <StatusLine label={t("vpnLabel")} value="UNKNOWN" />
      <StatusLine label={t("repLabel")} value="NOT_AVAILABLE" />
      {obs.length === 0 ? (
        <p className="muted">{t("noIp")}</p>
      ) : (
        <ul className="stack">
          {obs.map((o) => (
            <li key={o.obs_id} className="rule-row">
              <strong>{o.ip_label}</strong> · {t("addressPre")}
              {maskIp(o.address)} ({o.address_status})
              <p className="muted">
                {t("observedPre")}{" "}
                <bdi>{o.observed_at || tCommon("unknownTime")}</bdi>{" "}
                {t("observedPost", {
                  s: o.source_ref || tCommon("unknown"),
                })}
              </p>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

function GeoBlock({ intel }: { intel: TxnIntel }) {
  const { t } = useTranslation("intel");
  const { t: tCommon } = useTranslation("common");
  const obs = intel.geolocation_observations;
  return (
    <>
      <p className="muted">{t("geoDisclaimer")}</p>
      {obs.length === 0 ? (
        <p className="muted">{t("noGeo")}</p>
      ) : (
        <ul className="stack">
          {obs.map((o) => (
            <li key={o.obs_id} className="rule-row">
              <strong>{o.location_label}</strong> · {o.geo_status} (
              {o.reason})
              <p className="muted">
                {t("observedPre")}{" "}
                <bdi>{o.observed_at || tCommon("unknownTime")}</bdi>{" "}
                {t("observedPost", {
                  s: o.source_ref || tCommon("unknown"),
                })}
              </p>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

function FindingRow({ finding }: { finding: IntelFinding }) {
  const { t } = useTranslation("intel");
  const { t: tCommon } = useTranslation("common");
  return (
    <li className="rule-row">
      <strong>
        {finding.finding_id} · {finding.category} · {finding.status}
      </strong>
      <p className="muted">{finding.explanation}</p>
      <p className="muted">
        {t("evidencePre")}
        <code>
          {finding.evidence_refs.length > 0
            ? finding.evidence_refs.join(", ")
            : tCommon("none")}
        </code>{" "}
        {t("provMeta", {
          p: finding.provenance,
          c: finding.confidence,
          f: finding.freshness,
        })}
        {finding.synthetic ? t("syntheticTag") : ""}
      </p>
      {finding.limitations.length > 0 && (
        <p className="muted">
          {t("limitsLine", { list: finding.limitations.join(" ") })}
        </p>
      )}
      <p className="muted">
        {t("reviewLine", { r: finding.human_review })}
      </p>
    </li>
  );
}

export function IntelSection({
  intel,
  evidence,
  risk,
}: {
  intel: InvIntel | null;
  evidence: IntelEvidence | null;
  risk: RiskIntelResult | null;
}) {
  const { t, tp } = useTranslation("intel");
  if (!intel || !evidence) {
    return (
      <section className="card" aria-labelledby="intel-h">
        <h2 id="intel-h">{t("intelTitle")}</h2>
        <p className="muted" data-testid="intel-status">
          {t("intelDown")}
        </p>
      </section>
    );
  }
  const txn =
    "transaction_id" in intel.transaction_intel
      ? intel.transaction_intel
      : null;
  return (
    <section className="card" aria-labelledby="intel-h">
      <h2 id="intel-h">{t("intelTitle")}</h2>
      <p className="muted" data-testid="intel-status">
        {t("statusLine", {
          findings: tp("findingsCount", evidence.findings.length),
          iso: intel.isolation,
        })}
      </p>
      <h3>{t("deviceH")}</h3>
      {txn ? (
        <DeviceBlock intel={txn} />
      ) : (
        <p className="muted">{t("noLinkage")}</p>
      )}
      <h3>{t("ipH")}</h3>
      {txn ? <IpBlock intel={txn} /> : <p className="muted">{t("unknownShort")}</p>}
      <h3>{t("geoH")}</h3>
      {txn ? (
        <GeoBlock intel={txn} />
      ) : (
        <p className="muted">{t("unknownShort")}</p>
      )}
      <h3>{t("findingsH")}</h3>
      {evidence.findings.length === 0 ? (
        <p className="muted">{t("noFindings")}</p>
      ) : (
        <ul className="stack">
          {evidence.findings.map((f) => (
            <FindingRow key={f.finding_id} finding={f} />
          ))}
        </ul>
      )}
      <h3>{t("candidateH")}</h3>
      {!risk || !risk.enabled ? (
        <p className="muted">{t("candidateOff")}</p>
      ) : (
        <p className="muted">
          {t("candidateOnPre")}
          {tp("candidateFindings", risk.finding_count ?? 0)}
          {t("candidateOnPost", {
            note: risk.score_note ?? t("seeBackend"),
          })}
        </p>
      )}
    </section>
  );
}
