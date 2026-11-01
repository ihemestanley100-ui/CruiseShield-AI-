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

function StatusLine({ label, value }: { label: string; value: string }) {
  return (
    <p className="muted">
      {label}: <strong>{value || "unknown"}</strong>
    </p>
  );
}

function DeviceBlock({ intel }: { intel: TxnIntel }) {
  const obs = intel.device_observations;
  if (obs.length === 0) {
    return <p className="muted">No device observations. (unknown)</p>;
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
              {accounts.length >= 2 ? " — shared device" : " — observed"}
            </strong>
            <p className="muted">
              {mine.length} observation(s) · {accounts.length} account(s):{" "}
              {accounts.join(", ")}
            </p>
            <p className="muted">
              Fixture reference, not a verified fingerprint. Attributes:{" "}
              declared synthetic demo values only.
            </p>
          </li>
        );
      })}
    </ul>
  );
}

function IpBlock({ intel }: { intel: TxnIntel }) {
  const obs = intel.ip_observations;
  return (
    <>
      <StatusLine label="ISP/ASN" value="NOT_CONFIGURED" />
      <StatusLine label="VPN/proxy/Tor" value="UNKNOWN" />
      <StatusLine label="Reputation" value="NOT_AVAILABLE" />
      {obs.length === 0 ? (
        <p className="muted">No IP observations. (unknown)</p>
      ) : (
        <ul className="stack">
          {obs.map((o) => (
            <li key={o.obs_id} className="rule-row">
              <strong>{o.ip_label}</strong> · address:{" "}
              {maskIp(o.address)} ({o.address_status})
              <p className="muted">
                Observed {o.observed_at || "unknown time"} · source{" "}
                {o.source_ref || "unknown"}
              </p>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

function GeoBlock({ intel }: { intel: TxnIntel }) {
  const obs = intel.geolocation_observations;
  return (
    <>
      <p className="muted">
        IP-derived locations are approximate and never proof of physical
        presence. No GPS collection exists (permission: unavailable).
      </p>
      {obs.length === 0 ? (
        <p className="muted">No location observations. (unknown)</p>
      ) : (
        <ul className="stack">
          {obs.map((o) => (
            <li key={o.obs_id} className="rule-row">
              <strong>{o.location_label}</strong> · {o.geo_status} (
              {o.reason})
              <p className="muted">
                Observed {o.observed_at || "unknown time"} · source{" "}
                {o.source_ref || "unknown"}
              </p>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

function FindingRow({ finding }: { finding: IntelFinding }) {
  return (
    <li className="rule-row">
      <strong>
        {finding.finding_id} · {finding.category} · {finding.status}
      </strong>
      <p className="muted">{finding.explanation}</p>
      <p className="muted">
        Evidence:{" "}
        <code>
          {finding.evidence_refs.length > 0
            ? finding.evidence_refs.join(", ")
            : "none"}
        </code>{" "}
        · provenance {finding.provenance} · confidence {finding.confidence}{" "}
        · freshness {finding.freshness}
        {finding.synthetic ? " · synthetic demo" : ""}
      </p>
      {finding.limitations.length > 0 && (
        <p className="muted">Limits: {finding.limitations.join(" ")}</p>
      )}
      <p className="muted">Human review: {finding.human_review}</p>
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
  if (!intel || !evidence) {
    return (
      <section className="card" aria-labelledby="intel-h">
        <h2 id="intel-h">Device, IP &amp; location intelligence</h2>
        <p className="muted" data-testid="intel-status">
          Intelligence unavailable for this investigation.
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
      <h2 id="intel-h">Device, IP &amp; location intelligence</h2>
      <p className="muted" data-testid="intel-status">
        {evidence.findings.length} finding(s) · {intel.isolation} ·
        synthetic demo data.
      </p>
      <h3>Device</h3>
      {txn ? (
        <DeviceBlock intel={txn} />
      ) : (
        <p className="muted">No transaction linkage. (unknown)</p>
      )}
      <h3>IP &amp; network</h3>
      {txn ? <IpBlock intel={txn} /> : <p className="muted">(unknown)</p>}
      <h3>Geolocation</h3>
      {txn ? (
        <GeoBlock intel={txn} />
      ) : (
        <p className="muted">(unknown)</p>
      )}
      <h3>Intelligence findings</h3>
      {evidence.findings.length === 0 ? (
        <p className="muted">No findings. (insufficient evidence)</p>
      ) : (
        <ul className="stack">
          {evidence.findings.map((f) => (
            <FindingRow key={f.finding_id} finding={f} />
          ))}
        </ul>
      )}
      <h3>Candidate risk intelligence</h3>
      {!risk || !risk.enabled ? (
        <p className="muted">
          Candidate engine risk-intelligence-v2-candidate is OFF (default).
          Authoritative engine: risk-score-v1. Candidate findings never
          replace v1 scores.
        </p>
      ) : (
        <p className="muted">
          Candidate engine enabled: {risk.finding_count ?? 0} finding(s), no
          numeric score ({risk.score_note ?? "see backend"}). v1 remains
          authoritative.
        </p>
      )}
    </section>
  );
}
