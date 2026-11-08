"use client";

/* Fund recovery section. Closed by default; checks eligibility for
 * the case transaction, opens recovery cases, and lists tenant
 * cases with verbatim lifecycle states. Distinguishes prepared,
 * submitted, acknowledged and completed stages by their exact
 * state names; never implies money moved. */

import type {
  EligibilityResult,
  RecoveryCase,
  RecoveryMetrics,
} from "../lib/api";
import {
  getRecoveryCases,
  getRecoveryMetrics,
  postRecoveryAssess,
  postRecoveryCase,
  userErrorMessage,
} from "../lib/api";
import { useState } from "react";

type PanelState =
  | { kind: "closed" }
  | { kind: "loading" }
  | {
      kind: "ready";
      cases: RecoveryCase[];
      metrics: RecoveryMetrics;
      eligibility: EligibilityResult | null;
      notice: string | null;
    }
  | { kind: "error"; message: string };

const REASONS = ["unauthorized", "erroneous", "fraud", "duplicate"];

export function RecoverySection({ txnId }: { txnId: string }) {
  const [panel, setPanel] = useState<PanelState>({ kind: "closed" });
  const [reason, setReason] = useState("fraud");

  function open() {
    if (panel.kind !== "closed") {
      setPanel({ kind: "closed" });
      return;
    }
    setPanel({ kind: "loading" });
    Promise.all([getRecoveryCases(), getRecoveryMetrics()])
      .then(([queue, metrics]) =>
        setPanel({
          kind: "ready",
          cases: queue.cases,
          metrics,
          eligibility: null,
          notice: null,
        })
      )
      .catch((err: unknown) =>
        setPanel({ kind: "error", message: userErrorMessage(err) })
      );
  }

  function check() {
    if (panel.kind !== "ready") return;
    const snapshot = panel;
    postRecoveryAssess(txnId, reason)
      .then((eligibility) =>
        setPanel({ ...snapshot, eligibility, notice: null })
      )
      .catch((err: unknown) =>
        setPanel({ kind: "error", message: userErrorMessage(err) })
      );
  }

  function openCase() {
    if (panel.kind !== "ready") return;
    postRecoveryCase(txnId, reason)
      .then((out) =>
        Promise.all([getRecoveryCases(), getRecoveryMetrics()]).then(
          ([queue, metrics]) =>
            setPanel({
              kind: "ready",
              cases: queue.cases,
              metrics,
              eligibility: panel.eligibility,
              notice: `Case ${out.case.recovery_id}: ${out.status}.`,
            })
        )
      )
      .catch((err: unknown) =>
        setPanel({ kind: "error", message: userErrorMessage(err) })
      );
  }

  return (
    <div>
      <h3>Fund recovery</h3>
      <button
        type="button"
        aria-expanded={panel.kind !== "closed"}
        onClick={open}
      >
        {panel.kind === "closed" ? "Show recovery" : "Hide recovery"}
      </button>
      {panel.kind === "loading" && <p role="status">Loading recovery…</p>}
      {panel.kind === "error" && <p role="alert">{panel.message}</p>}
      {panel.kind === "ready" && (
        <div>
          <p>
            {panel.metrics.total} case(s) recorded. States:{" "}
            {Object.entries(panel.metrics.by_state)
              .map(([state, count]) => `${state}: ${count}`)
              .join(", ") || "none"}
            .
          </p>
          <label>
            Reason
            <select
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            >
              {REASONS.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </label>{" "}
          <button type="button" onClick={check}>
            Check eligibility
          </button>{" "}
          <button type="button" onClick={openCase}>
            Open recovery case
          </button>
          {panel.notice && <p role="status">{panel.notice}</p>}
          {panel.eligibility && (
            <p>
              Eligibility: <strong>{panel.eligibility.status}</strong> —{" "}
              {panel.eligibility.reason}
            </p>
          )}
          {panel.cases.length === 0 ? (
            <p>No recovery cases recorded.</p>
          ) : (
            <ul>
              {panel.cases.map((c) => (
                <li key={c.recovery_id}>
                  <strong>{c.recovery_id}</strong> ({c.reason}):{" "}
                  {c.state}
                  {c.channel ? ` via ${c.channel}` : ""}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
