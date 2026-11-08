"use client";

/* Telecom Identity section. Presentational + lazy fetch, mirroring
 * intel-panels DeviceDetail: closed by default, honest loading/error
 * states, no invented fields. Subjects render masked; API result
 * states render verbatim. Headings are literal English (zero new i18n
 * keys per repo precedent; translator review pending with I18N-02). */

import type { TelecomSummary, TelecomVerification } from "../lib/api";
import {
  getTelecomSummary,
  getTelecomVerification,
  requestTelecomVerification,
  userErrorMessage,
} from "../lib/api";
import { useState } from "react";
import { useTranslation } from "../lib/i18n/context";

type SummaryState =
  | { kind: "closed" }
  | { kind: "loading" }
  | { kind: "ready"; data: TelecomSummary }
  | { kind: "error"; message: string };

type DetailState =
  | { kind: "closed" }
  | { kind: "loading" }
  | { kind: "ready"; data: TelecomVerification }
  | { kind: "error"; message: string };

type RequestState =
  | { kind: "idle" }
  | { kind: "sending" }
  | { kind: "done"; data: TelecomVerification }
  | { kind: "error"; message: string };

const VERIFY_TYPES = [
  "carrier_identification",
  "current_network",
  "number_verification",
  "sim_ownership",
  "sim_swap",
  "number_recycling",
  "device_swap",
  "kyc_match",
  "tenure",
  "roaming",
  "network_type",
];

function ListOrNone({ items }: { items: string[] }) {
  const { t: tCommon } = useTranslation("common");
  if (items.length === 0) return <>{tCommon("none")}</>;
  return <>{items.join(", ")}</>;
}

function VerificationDetail({
  verificationId,
}: {
  verificationId: string;
}) {
  const { t: tEvidence } = useTranslation("evidence");
  const { t: tCommon } = useTranslation("common");
  const { t: tIntel } = useTranslation("intel");
  const [state, setState] = useState<DetailState>({ kind: "closed" });
  const load = () => {
    setState({ kind: "loading" });
    getTelecomVerification(verificationId).then(
      (data) => setState({ kind: "ready", data }),
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
          {tEvidence("showProv")}
        </button>
      </p>
    );
  }
  const close = () => setState({ kind: "closed" });
  return (
    <div>
      <p>
        <button type="button" onClick={close} aria-expanded={true}>
          {tEvidence("hideProv")}
        </button>
      </p>
      {state.kind === "loading" && (
        <p className="muted">{tCommon("loading")}</p>
      )}
      {state.kind === "error" && (
        <div className="alert error" role="alert">
          {state.message}
        </div>
      )}
      {state.kind === "ready" && (
        <dl>
          <dt>State</dt>
          <dd>
            <strong>{state.data.state}</strong>
            {state.data.previous_state
              ? ` (was ${state.data.previous_state})`
              : ""}
          </dd>
          <dt>Source</dt>
          <dd>{state.data.source}</dd>
          <dt>Provider</dt>
          <dd>
            {state.data.provider}
            {state.data.provider_ref
              ? ` · ref ${state.data.provider_ref}`
              : ""}
          </dd>
          <dt>API</dt>
          <dd>
            {state.data.api || tCommon("none")}{" "}
            {state.data.api_version}
          </dd>
          <dt>Confidence</dt>
          <dd>{state.data.confidence}</dd>
          <dt>Verified at</dt>
          <dd>{state.data.verified_at}</dd>
          {state.data.integrity && (
            <>
              <dt>Integrity</dt>
              <dd>{state.data.integrity}</dd>
            </>
          )}
        </dl>
      )}
      {state.kind === "ready" && state.data.limitations.length > 0 && (
        <p className="muted">
          {tIntel("limitsLine", {
            list: state.data.limitations.join(" "),
          })}
        </p>
      )}
    </div>
  );
}

function VerificationRequest({
  defaultSubject,
  onDone,
}: {
  defaultSubject: string;
  onDone: () => void;
}) {
  const { t: tCommon } = useTranslation("common");
  const [verifyType, setVerifyType] = useState("carrier_identification");
  const [e164, setE164] = useState(defaultSubject);
  const [purpose, setPurpose] = useState("");
  const [state, setState] = useState<RequestState>({ kind: "idle" });
  const submit = () => {
    setState({ kind: "sending" });
    requestTelecomVerification({
      verify_type: verifyType,
      e164,
      purpose,
    }).then(
      (data) => {
        setState({ kind: "done", data });
        onDone();
      },
      (err: unknown) =>
        setState({
          kind: "error",
          message: userErrorMessage(err, tCommon),
        })
    );
  };
  return (
    <div>
      <h4>Request verification</h4>
      <p>
        <label>
          Check{" "}
          <select
            value={verifyType}
            onChange={(e) => setVerifyType(e.target.value)}
          >
            {VERIFY_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
      </p>
      <p>
        <label>
          Number (E.164){" "}
          <input
            value={e164}
            onChange={(e) => setE164(e.target.value)}
            placeholder="+2348031234567"
            inputMode="tel"
          />
        </label>
      </p>
      <p>
        <label>
          Lawful purpose{" "}
          <input
            value={purpose}
            onChange={(e) => setPurpose(e.target.value)}
            placeholder="fraud-investigation-case-…"
          />
        </label>
      </p>
      <p>
        <button
          type="button"
          onClick={submit}
          disabled={state.kind === "sending"}
        >
          {state.kind === "sending" ? tCommon("loading") : "Verify"}
        </button>
      </p>
      {state.kind === "error" && (
        <div className="alert error" role="alert">
          {state.message}
        </div>
      )}
      {state.kind === "done" && (
        <p>
          Result: <strong>{state.data.state}</strong> ·{" "}
          {state.data.subject_masked}
          {state.data.limitations.length > 0 && (
            <> · {state.data.limitations.join(" ")}</>
          )}
        </p>
      )}
    </div>
  );
}

export function TelecomSection({
  phoneLabel,
  subject,
}: {
  phoneLabel?: string;
  subject?: string;
}) {
  const { t: tEvidence } = useTranslation("evidence");
  const { t: tCommon } = useTranslation("common");
  const { t: tIntel } = useTranslation("intel");
  const [state, setState] = useState<SummaryState>({ kind: "closed" });
  const [showForm, setShowForm] = useState(false);
  const load = () => {
    setState({ kind: "loading" });
    getTelecomSummary({ phone_label: phoneLabel, subject }).then(
      (data) => setState({ kind: "ready", data }),
      (err: unknown) =>
        setState({
          kind: "error",
          message: userErrorMessage(err, tCommon),
        })
    );
  };
  if (state.kind === "closed") {
    return (
      <div>
        <h3>Telecom identity</h3>
        <p>
          <button type="button" onClick={load} aria-expanded={false}>
            {tEvidence("showProv")}
          </button>
        </p>
      </div>
    );
  }
  const close = () => setState({ kind: "closed" });
  return (
    <div>
      <h3>Telecom identity</h3>
      <p>
        <button type="button" onClick={close} aria-expanded={true}>
          {tEvidence("hideProv")}
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
          <dl>
            <dt>Number</dt>
            <dd>{state.data.subject_masked || tCommon("unknown")}</dd>
            <dt>Allocation</dt>
            <dd>
              <strong>
                {state.data.allocation.operator_id || tCommon("unknown")}
              </strong>{" "}
              {state.data.allocation.country
                ? `(${state.data.allocation.country})`
                : ""}
            </dd>
          </dl>
          <p className="muted">
            {state.data.allocation.basis} ·{" "}
            {state.data.allocation.limitation}
          </p>
          <h4>Verification history ({state.data.history_count})</h4>
          {state.data.history.length === 0 ? (
            <p className="muted">{tCommon("noneYet")}</p>
          ) : (
            <ul className="stack">
              {state.data.history.map((h) => (
                <li key={h.verification_id} className="rule-row">
                  <strong>
                    {h.verify_type} · {h.state}
                    {h.stale ? " · STALE" : ""}
                  </strong>
                  <p className="muted">
                    {tIntel("observedPre")}{" "}
                    <bdi>{h.verified_at || tCommon("unknownTime")}</bdi>
                  </p>
                  <VerificationDetail
                    verificationId={h.verification_id}
                  />
                </li>
              ))}
            </ul>
          )}
          <h4>Correlated platform signals</h4>
          <dl>
            <dt>Devices</dt>
            <dd>
              <ListOrNone items={state.data.co_signals.devices} />
            </dd>
            <dt>Accounts</dt>
            <dd>
              <ListOrNone items={state.data.co_signals.accounts} />
            </dd>
            <dt>Beneficiaries</dt>
            <dd>
              <ListOrNone items={state.data.co_signals.beneficiaries} />
            </dd>
            <dt>Locations</dt>
            <dd>
              <ListOrNone items={state.data.co_signals.geo_labels} />
            </dd>
            <dt>Transactions</dt>
            <dd>{state.data.co_signals.transaction_count}</dd>
          </dl>
          <p>
            <button
              type="button"
              onClick={() => setShowForm((v) => !v)}
              aria-expanded={showForm}
            >
              {showForm ? "Hide request form" : "Request verification"}
            </button>
          </p>
          {showForm && (
            <VerificationRequest
              defaultSubject={subject ?? ""}
              onDone={load}
            />
          )}
        </>
      )}
    </div>
  );
}

export function TelecomConfigPanel() {
  const { t: tCommon } = useTranslation("common");
  const { t: tEvidence } = useTranslation("evidence");
  const [state, setState] = useState<
    | { kind: "closed" }
    | { kind: "loading" }
    | { kind: "ready"; registry: string; rows: string }
    | { kind: "error"; message: string }
  >({ kind: "closed" });
  const load = () => {
    setState({ kind: "loading" });
    import("../lib/api").then((api) =>
      api.getTelecomConfig().then(
        (cfg) =>
          setState({
            kind: "ready",
            registry: `v${cfg.registry.version} · ${cfg.registry.operators} operators`,
            rows: cfg.providers
              .map(
                (p) =>
                  `${p.adapter}: ${p.status}${p.live ? " (LIVE)" : ""}`
              )
              .join(" | "),
          }),
        (err: unknown) =>
          setState({
            kind: "error",
            message: userErrorMessage(err, tCommon),
          })
      )
    );
  };
  if (state.kind === "closed") {
    return (
      <p>
        <button type="button" onClick={load} aria-expanded={false}>
          {tEvidence("showProv")}
        </button>
      </p>
    );
  }
  if (state.kind === "loading")
    return <p className="muted">{tCommon("loading")}</p>;
  if (state.kind === "error")
    return (
      <div className="alert error" role="alert">
        {state.message}
      </div>
    );
  return (
    <div>
      <p className="muted">Registry {state.registry}</p>
      <p className="muted">{state.rows}</p>
    </div>
  );
}
