"use client";

/* Identity + address verification sections. Mirror TelecomSection:
 * lazy closed-by-default, request forms for authorized roles,
 * masked display, factor/match evidence, verbatim API states.
 * Zero new i18n keys (translator review pending with I18N-02). */

import type {
  AddressVerification,
  IdentityVerification,
} from "../lib/api";
import {
  getAddressVerification,
  getIdentityVerification,
  requestAddressVerification,
  requestIdentityVerification,
  userErrorMessage,
} from "../lib/api";
import { useState } from "react";
import { useTranslation } from "../lib/i18n/context";

const IDENTITY_TYPES = [
  "gov_id",
  "national_id",
  "passport",
  "drivers_licence",
  "business_identity",
  "bank_kyc",
  "name_match",
  "dob_match",
  "address_match",
  "phone_match",
  "document_authenticity",
  "record_consistency",
];

type IdentityState =
  | { kind: "closed" }
  | { kind: "form" }
  | { kind: "sending" }
  | { kind: "ready"; data: IdentityVerification }
  | { kind: "error"; message: string };

export function IdentitySection({
  investigationId,
}: {
  investigationId?: string;
}) {
  const { t: tCommon } = useTranslation("common");
  const [state, setState] = useState<IdentityState>({ kind: "closed" });
  const [verifyType, setVerifyType] = useState("passport");
  const [subjectRef, setSubjectRef] = useState("");
  const [country, setCountry] = useState("NG");
  const [purpose, setPurpose] = useState("AUTHORIZED_FRAUD_INVESTIGATION");
  const submit = () => {
    setState({ kind: "sending" });
    requestIdentityVerification({
      verify_type: verifyType,
      subject_ref: subjectRef,
      country,
      purpose,
      investigation_id: investigationId,
    }).then(
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
        <h3>Identity verification</h3>
        <p>
          <button
            type="button"
            onClick={() => setState({ kind: "form" })}
            aria-expanded={false}
          >
            Verify identity
          </button>
        </p>
      </div>
    );
  }
  return (
    <div>
      <h3>Identity verification</h3>
      {(state.kind === "form" || state.kind === "error") && (
        <>
          <p>
            <label>
              Check{" "}
              <select
                value={verifyType}
                onChange={(e) => setVerifyType(e.target.value)}
              >
                {IDENTITY_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </label>
          </p>
          <p>
            <label>
              Subject reference{" "}
              <input
                value={subjectRef}
                onChange={(e) => setSubjectRef(e.target.value)}
                placeholder="case subject reference"
              />
            </label>
          </p>
          <p>
            <label>
              Country{" "}
              <input
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                maxLength={2}
              />
            </label>
          </p>
          <p>
            <label>
              Purpose{" "}
              <input
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
              />
            </label>
          </p>
          <p>
            <button type="button" onClick={submit}>
              Submit
            </button>
          </p>
        </>
      )}
      {state.kind === "sending" && (
        <p className="muted">{tCommon("loading")}</p>
      )}
      {state.kind === "error" && (
        <div className="alert error" role="alert">
          {state.message}
        </div>
      )}
      {state.kind === "ready" && (
        <>
          <p>
            Result: <strong>{state.data.verification_status}</strong> ·{" "}
            {state.data.subject_masked}
          </p>
          {state.data.factors.length > 0 && (
            <ul className="stack">
              {state.data.factors.map((f, i) => (
                <li key={i} className="rule-row">
                  {f.factor} · {f.result} · ref {f.evidence_ref}
                </li>
              ))}
            </ul>
          )}
          {state.data.missing.length > 0 && (
            <p className="muted">
              Missing: {state.data.missing.join("; ")}
            </p>
          )}
          {state.data.limitations.length > 0 && (
            <p className="muted">{state.data.limitations.join(" ")}</p>
          )}
          <p>
            <button
              type="button"
              onClick={() =>
                getIdentityVerification(
                  state.data.verification_id
                ).then(
                  (data) => setState({ kind: "ready", data }),
                  (err: unknown) =>
                    setState({
                      kind: "error",
                      message: userErrorMessage(err, tCommon),
                    })
                )
              }
            >
              Refresh
            </button>
          </p>
        </>
      )}
    </div>
  );
}

type AddressState =
  | { kind: "closed" }
  | { kind: "form" }
  | { kind: "sending" }
  | { kind: "ready"; data: AddressVerification }
  | { kind: "error"; message: string };

export function AddressSection({
  investigationId,
}: {
  investigationId?: string;
}) {
  const { t: tCommon } = useTranslation("common");
  const [state, setState] = useState<AddressState>({ kind: "closed" });
  const [subjectRef, setSubjectRef] = useState("");
  const [country, setCountry] = useState("NG");
  const [city, setCity] = useState("");
  const [street, setStreet] = useState("");
  const [method, setMethod] = useState("kyc-record-match");
  const [purpose, setPurpose] = useState("CUSTOMER_IDENTITY_VERIFICATION");
  const submit = () => {
    setState({ kind: "sending" });
    requestAddressVerification({
      address: { country, city, street },
      subject_ref: subjectRef,
      method,
      purpose,
      investigation_id: investigationId,
    }).then(
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
        <h3>Address verification</h3>
        <p>
          <button
            type="button"
            onClick={() => setState({ kind: "form" })}
            aria-expanded={false}
          >
            Verify address
          </button>
        </p>
      </div>
    );
  }
  return (
    <div>
      <h3>Address verification</h3>
      {(state.kind === "form" || state.kind === "error") && (
        <>
          <p>
            <label>
              Subject reference{" "}
              <input
                value={subjectRef}
                onChange={(e) => setSubjectRef(e.target.value)}
                placeholder="case subject reference"
              />
            </label>
          </p>
          <p>
            <label>
              Country{" "}
              <input
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                maxLength={2}
              />
            </label>
          </p>
          <p>
            <label>
              City{" "}
              <input
                value={city}
                onChange={(e) => setCity(e.target.value)}
              />
            </label>
          </p>
          <p>
            <label>
              Street{" "}
              <input
                value={street}
                onChange={(e) => setStreet(e.target.value)}
              />
            </label>
          </p>
          <p>
            <label>
              Method{" "}
              <input
                value={method}
                onChange={(e) => setMethod(e.target.value)}
              />
            </label>
          </p>
          <p>
            <label>
              Purpose{" "}
              <input
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
              />
            </label>
          </p>
          <p>
            <button type="button" onClick={submit}>
              Submit
            </button>
          </p>
        </>
      )}
      {state.kind === "sending" && (
        <p className="muted">{tCommon("loading")}</p>
      )}
      {state.kind === "error" && (
        <div className="alert error" role="alert">
          {state.message}
        </div>
      )}
      {state.kind === "ready" && (
        <>
          <p>
            Result: <strong>{state.data.verification_status}</strong> ·{" "}
            {state.data.subject_masked}
          </p>
          <p className="muted">
            {state.data.address_masked.city},{" "}
            {state.data.address_masked.country} ·{" "}
            {state.data.address_masked.street_masked}
          </p>
          {state.data.limitations.length > 0 && (
            <p className="muted">{state.data.limitations.join(" ")}</p>
          )}
          <p>
            <button
              type="button"
              onClick={() =>
                getAddressVerification(
                  state.data.verification_id
                ).then(
                  (data) => setState({ kind: "ready", data }),
                  (err: unknown) =>
                    setState({
                      kind: "error",
                      message: userErrorMessage(err, tCommon),
                    })
                )
              }
            >
              Refresh
            </button>
          </p>
        </>
      )}
    </div>
  );
}
