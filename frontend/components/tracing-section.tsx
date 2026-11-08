"use client";

/* Fund tracing section. Closed by default; builds a trace from the live
 * API and renders movements, per-leg evidence, visited transactions and
 * limitations verbatim. Includes the masked party summary for the same
 * transaction. No invented links: empty movement lists render as-is. */

import type { FundTrace, TxnParties, Typology } from "../lib/api";
import {
  getTrace,
  getTxnParties,
  getTypologies,
  postTrace,
  userErrorMessage,
} from "../lib/api";
import { useState } from "react";
import { useTranslation } from "../lib/i18n/context";

type TraceState =
  | { kind: "closed" }
  | { kind: "building" }
  | { kind: "ready"; data: FundTrace }
  | { kind: "error"; message: string };

type PartyState =
  | { kind: "closed" }
  | { kind: "loading" }
  | { kind: "ready"; data: TxnParties }
  | { kind: "error"; message: string };

type TypologyState =
  | { kind: "closed" }
  | { kind: "loading" }
  | { kind: "ready"; data: Typology[] }
  | { kind: "error"; message: string };

export function TracingSection({ txnId }: { txnId: string }) {
  const { t: tCommon } = useTranslation("common");
  const [trace, setTrace] = useState<TraceState>({ kind: "closed" });
  const [parties, setParties] = useState<PartyState>({ kind: "closed" });
  const [typos, setTypos] = useState<TypologyState>({ kind: "closed" });

  function toggleTrace() {
    if (trace.kind !== "closed") {
      setTrace({ kind: "closed" });
      return;
    }
    setTrace({ kind: "building" });
    postTrace(txnId)
      .then((data) => getTrace(data.trace_id).then(() => data))
      .then((data) => setTrace({ kind: "ready", data }))
      .catch((err: unknown) =>
        setTrace({ kind: "error", message: userErrorMessage(err) })
      );
  }

  function toggleParties() {
    if (parties.kind !== "closed") {
      setParties({ kind: "closed" });
      return;
    }
    setParties({ kind: "loading" });
    getTxnParties(txnId)
      .then((data) => setParties({ kind: "ready", data }))
      .catch((err: unknown) =>
        setParties({ kind: "error", message: userErrorMessage(err) })
      );
  }

  function toggleTypos() {
    if (typos.kind !== "closed") {
      setTypos({ kind: "closed" });
      return;
    }
    setTypos({ kind: "loading" });
    getTypologies()
      .then((data) => setTypos({ kind: "ready", data: data.typologies }))
      .catch((err: unknown) =>
        setTypos({ kind: "error", message: userErrorMessage(err) })
      );
  }

  return (
    <div>
      <h3>Fund tracing</h3>
      <button
        type="button"
        aria-expanded={trace.kind !== "closed"}
        onClick={toggleTrace}
      >
        {trace.kind === "closed" ? "Build trace" : "Hide trace"}
      </button>
      {trace.kind === "building" && <p role="status">Building trace…</p>}
      {trace.kind === "error" && <p role="alert">{trace.message}</p>}
      {trace.kind === "ready" && (
        <div>
          <p>
            Trace <code>{trace.data.trace_id}</code> from{" "}
            <code>{trace.data.origin_transaction}</code>;{" "}
            {trace.data.movements.length} movement(s).
          </p>
          {trace.data.movements.length === 0 ? (
            <p>No evidenced onward movements.</p>
          ) : (
            <ol>
              {trace.data.movements.map((m) => (
                <li key={`${m.from_transaction}-${m.to_transaction}`}>
                  <code>{m.from_transaction}</code> →{" "}
                  <code>{m.to_transaction}</code>: <strong>{m.status}</strong>{" "}
                  — {m.evidence}
                </li>
              ))}
            </ol>
          )}
          <p>
            Limitations:{" "}
            {trace.data.limitations.length === 0
              ? tCommon("none")
              : trace.data.limitations.join("; ")}
          </p>
        </div>
      )}

      <h3>Transaction parties</h3>
      <button
        type="button"
        aria-expanded={parties.kind !== "closed"}
        onClick={toggleParties}
      >
        {parties.kind === "closed" ? "Show parties" : "Hide parties"}
      </button>
      {parties.kind === "loading" && <p role="status">Loading parties…</p>}
      {parties.kind === "error" && <p role="alert">{parties.message}</p>}
      {parties.kind === "ready" && (
        <div>
          <ul>
            {parties.data.parties.map((p) => (
              <li key={p.role}>
                {p.role}: {p.reference_masked ?? "—"} ({p.verification})
              </li>
            ))}
          </ul>
          <p>
            Method: {parties.data.classification.method_id} (
            {parties.data.classification.confidence}); network:{" "}
            {parties.data.network.institution_id}.
          </p>
        </div>
      )}

      <h3>Fraud typologies</h3>
      <button
        type="button"
        aria-expanded={typos.kind !== "closed"}
        onClick={toggleTypos}
      >
        {typos.kind === "closed" ? "Show typologies" : "Hide typologies"}
      </button>
      {typos.kind === "loading" && <p role="status">Loading typologies…</p>}
      {typos.kind === "error" && <p role="alert">{typos.message}</p>}
      {typos.kind === "ready" && (
        <ul>
          {typos.data.map((t) => (
            <li key={t.typology_id}>
              <strong>{t.typology_id}</strong> {t.label}
              {t.detection_gap ? " (detection gap)" : ""}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
