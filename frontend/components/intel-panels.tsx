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
  AcctIntel,
  DeviceProfile,
  GeoObservationResult,
  IpObservationList,
} from "../lib/api";
import {
  getDevice,
  getGeoObservations,
  getIpObservations,
  userErrorMessage,
} from "../lib/api";
import Link from "next/link";
import { useState } from "react";
import { formatDate } from "../lib/i18n/format";
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

export function DeviceBlock({ intel }: { intel: TxnIntel }) {
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
            <DeviceDetail deviceId={label} />
          </li>
        );
      })}
    </ul>
  );
}

export function IpBlock({ intel }: { intel: TxnIntel }) {
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
              <IpDetail label={o.ip_label} />
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

export function GeoBlock({ intel }: { intel: TxnIntel }) {
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
              <GeoDetail identifier={o.location_label} />
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

/* GAP-013: label/device drill-downs. The aggregate blocks above show
 * this transaction's observations; expanding a row fetches the
 * label-level view (cross-transaction sightings, first/last seen,
 * linked accounts) from DI-03..DI-05. Closed by default, fetched
 * lazily, honest loading/error states, no invented fields. */

type DetailState<T> =
  | { kind: "closed" }
  | { kind: "loading" }
  | { kind: "ready"; data: T }
  | { kind: "error"; message: string };

function DetailToggle({
  open,
  onToggle,
}: {
  open: boolean;
  onToggle: () => void;
}) {
  const { t } = useTranslation("evidence");
  return (
    <p>
      <button type="button" onClick={onToggle} aria-expanded={open}>
        {open ? t("hideProv") : t("showProv")}
      </button>
    </p>
  );
}

function DetailError({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  const { t: tCommon } = useTranslation("common");
  return (
    <>
      <div className="alert error" role="alert">
        {message}
      </div>
      <p>
        <button type="button" onClick={onRetry}>
          {tCommon("retry")}
        </button>
      </p>
    </>
  );
}

function DeviceDetail({ deviceId }: { deviceId: string }) {
  const { t: tIntel, tp } = useTranslation("intel");
  const { t: tCommon, locale } = useTranslation("common");
  const [state, setState] = useState<DetailState<DeviceProfile>>({
    kind: "closed",
  });
  const load = () => {
    setState({ kind: "loading" });
    getDevice(deviceId).then(
      (data) => setState({ kind: "ready", data }),
      (err: unknown) =>
        setState({
          kind: "error",
          message: userErrorMessage(err, tCommon),
        })
    );
  };
  if (state.kind === "closed") {
    return <DetailToggle open={false} onToggle={load} />;
  }
  const close = () => setState({ kind: "closed" });
  return (
    <div>
      <DetailToggle open={true} onToggle={close} />
      {state.kind === "loading" && (
        <p className="muted">{tCommon("loading")}</p>
      )}
      {state.kind === "error" && (
        <DetailError message={state.message} onRetry={load} />
      )}
      {state.kind === "ready" && (
        <>
          <p className="muted">
            {state.data.shared
              ? tIntel("sharedDevice")
              : tIntel("observedOnly")}{" "}
            · {state.data.identity_status}
          </p>
          <p className="muted">
            <bdi>
              {state.data.first_seen
                ? formatDate(locale, state.data.first_seen, {
                    dateStyle: "medium",
                  })
                : tCommon("unknownTime")}
            </bdi>{" "}
            —{" "}
            <bdi>
              {state.data.last_seen
                ? formatDate(locale, state.data.last_seen, {
                    dateStyle: "medium",
                  })
                : tCommon("unknownTime")}
            </bdi>
          </p>
          <p className="muted">
            {tp("obsCount", state.data.observation_count)} ·{" "}
            {tp("accountCount", state.data.account_ids.length)}:{" "}
            {state.data.account_ids.join(", ")}
          </p>
        </>
      )}
    </div>
  );
}

function IpDetail({ label }: { label: string }) {
  const { t: tIntel } = useTranslation("intel");
  const { t: tCommon } = useTranslation("common");
  const { t: tCommand } = useTranslation("command");
  const [state, setState] = useState<DetailState<IpObservationList>>({
    kind: "closed",
  });
  const load = () => {
    setState({ kind: "loading" });
    getIpObservations(label).then(
      (data) => setState({ kind: "ready", data }),
      (err: unknown) =>
        setState({
          kind: "error",
          message: userErrorMessage(err, tCommon),
        })
    );
  };
  if (state.kind === "closed") {
    return <DetailToggle open={false} onToggle={load} />;
  }
  const close = () => setState({ kind: "closed" });
  return (
    <div>
      <DetailToggle open={true} onToggle={close} />
      {state.kind === "loading" && (
        <p className="muted">{tCommon("loading")}</p>
      )}
      {state.kind === "error" && (
        <DetailError message={state.message} onRetry={load} />
      )}
      {state.kind === "ready" && (
        <>
          <p className="muted">{state.data.address_status}</p>
          {state.data.observations.length === 0 ? (
            <p className="muted">{tIntel("noIp")}</p>
          ) : (
            <ul className="stack">
              {state.data.observations.map((o) => (
                <li key={o.obs_id} className="rule-row">
                  <strong>
                    {maskIp(o.address)} ({o.address_status})
                  </strong>
                  <p className="muted">
                    {tIntel("observedPre")}{" "}
                    <bdi>{o.observed_at || tCommon("unknownTime")}</bdi>{" "}
                    {tIntel("observedPost", {
                      s: o.source_ref || tCommon("unknown"),
                    })}
                  </p>
                  {o.txn_id && (
                    <p>
                      <Link
                        href={`/network/${o.txn_id}`}
                        className="back-link"
                      >
                        {tCommand("openNetExplorer")} {o.txn_id}
                      </Link>
                    </p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}

function GeoDetail({ identifier }: { identifier: string }) {
  const { t: tIntel } = useTranslation("intel");
  const { t: tCommon } = useTranslation("common");
  const { t: tCommand } = useTranslation("command");
  const [state, setState] = useState<DetailState<GeoObservationResult>>({
    kind: "closed",
  });
  const load = () => {
    setState({ kind: "loading" });
    getGeoObservations(identifier).then(
      (data) => setState({ kind: "ready", data }),
      (err: unknown) =>
        setState({
          kind: "error",
          message: userErrorMessage(err, tCommon),
        })
    );
  };
  if (state.kind === "closed") {
    return <DetailToggle open={false} onToggle={load} />;
  }
  const close = () => setState({ kind: "closed" });
  const lookup =
    state.kind === "ready" ? (state.data.lookup ?? null) : null;
  const observations =
    state.kind === "ready" ? (state.data.observations ?? []) : [];
  return (
    <div>
      <DetailToggle open={true} onToggle={close} />
      {state.kind === "loading" && (
        <p className="muted">{tCommon("loading")}</p>
      )}
      {state.kind === "error" && (
        <DetailError message={state.message} onRetry={load} />
      )}
      {state.kind === "ready" && lookup && (
        <>
          <p className="muted">{lookup.reason}</p>
          <p className="muted">
            <code>
              {lookup.country_code} · {lookup.city} · {lookup.confidence}
            </code>
          </p>
        </>
      )}
      {state.kind === "ready" && !lookup && observations.length === 0 && (
        <p className="muted">{tIntel("noGeo")}</p>
      )}
      {state.kind === "ready" && !lookup && observations.length > 0 && (
        <ul className="stack">
          {observations.map((o) => (
            <li key={o.obs_id} className="rule-row">
              <strong>
                {o.location_label} · {o.geo_status}
              </strong>
              <p className="muted">
                {tIntel("observedPre")}{" "}
                <bdi>{o.observed_at || tCommon("unknownTime")}</bdi>{" "}
                {tIntel("observedPost", {
                  s: o.source_ref || tCommon("unknown"),
                })}
              </p>
              {o.txn_id && (
                <p>
                  <Link href={`/network/${o.txn_id}`} className="back-link">
                    {tCommand("openNetExplorer")} {o.txn_id}
                  </Link>
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* GAP-012: per-account intelligence. Sender/receiver drill-down on the
 * investigation page: known devices/IPs/locations, shared
 * infrastructure, linked transactions and investigations. */

function AccountBlock({ data }: { data: AcctIntel }) {
  const { t } = useTranslation("intel");
  const { t: tNotify } = useTranslation("notify");
  const { t: tCommand } = useTranslation("command");
  return (
    <>
      <h3>{data.account_id}</h3>
      {data.limitations.map((line, index) => (
        <p key={index} className="muted">
          {line}
        </p>
      ))}
      <p>
        <strong>{t("deviceH")}</strong>
      </p>
      <p className="muted">
        <code>{data.known_devices.join(", ")}</code>
      </p>
      <p>
        <strong>{t("ipH")}</strong>
      </p>
      <p className="muted">
        <code>{data.known_ip_labels.join(", ")}</code>
      </p>
      <p>
        <strong>{t("geoH")}</strong>
      </p>
      <p className="muted">
        <code>{data.known_geo_labels.join(", ")}</code>
      </p>
      {data.shared_devices.map((s) => (
        <p key={s.device_id} className="muted">
          <strong>{s.device_id}</strong>
          {t("sharedDevice")} · {s.account_ids.join(", ")}
        </p>
      ))}
      {data.shared_ips.map((s) => (
        <p key={s.ip_label} className="muted">
          <strong>{s.ip_label}</strong> · {s.account_ids.join(", ")}
        </p>
      ))}
      {data.investigation_ids.map((id) => (
        <p key={id}>
          <Link href={`/investigations/${id}`} className="back-link">
            {tNotify("openInv")} {id}
          </Link>
        </p>
      ))}
      {data.transaction_ids.map((id) => (
        <p key={id}>
          <Link href={`/network/${id}`} className="back-link">
            {tCommand("openNetExplorer")} {id}
          </Link>
        </p>
      ))}
    </>
  );
}

export function IntelSection({
  intel,
  evidence,
  risk,
  accounts = null,
}: {
  intel: InvIntel | null;
  evidence: IntelEvidence | null;
  risk: RiskIntelResult | null;
  accounts?: {
    sender: AcctIntel | null;
    receiver: AcctIntel | null;
  } | null;
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
      {accounts && (accounts.sender || accounts.receiver) && (
        <>
          {accounts.sender && <AccountBlock data={accounts.sender} />}
          {accounts.receiver && <AccountBlock data={accounts.receiver} />}
        </>
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
