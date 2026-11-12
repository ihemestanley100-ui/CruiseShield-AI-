"use client";

/* Transaction monitoring section. Closed by default; shows the honest
 * evaluation mode, data window, alert counts and unalerted signals,
 * plus the tenant alert queue with legal transitions only. Evaluate
 * runs detection on demand and reports opened/duplicates verbatim. */

import type {
  FraudAlert,
  MonitoringRun,
  MonitoringStatus,
} from "../lib/api";
import {
  getFraudAlerts,
  getMonitoringStatus,
  patchFraudAlert,
  postFraudAlert,
  postMonitoringEvaluate,
  userErrorMessage,
} from "../lib/api";
import { useState } from "react";
import { useTranslation } from "../lib/i18n/context";

type PanelState =
  | { kind: "closed" }
  | { kind: "loading" }
  | {
      kind: "ready";
      status: MonitoringStatus;
      alerts: FraudAlert[];
      run: MonitoringRun | null;
      notice: string | null;
    }
  | { kind: "error"; message: string };

const NEXT: Record<string, string[]> = {
  NEW: ["TRIAGED", "UNDER_REVIEW"],
  TRIAGED: ["UNDER_REVIEW", "FALSE_POSITIVE"],
  UNDER_REVIEW: ["ESCALATED", "INVESTIGATION_OPENED", "RESOLVED", "FALSE_POSITIVE"],
  ESCALATED: ["INVESTIGATION_OPENED", "UNDER_REVIEW"],
  INVESTIGATION_OPENED: ["RESOLVED", "FALSE_POSITIVE"],
  RESOLVED: ["CLOSED"],
  FALSE_POSITIVE: ["CLOSED"],
  CLOSED: [],
};

export function MonitoringSection({ signalId }: { signalId?: string }) {
  const [panel, setPanel] = useState<PanelState>({ kind: "closed" });
  const { t: tCommon } = useTranslation("common");

  function open() {
    if (panel.kind !== "closed") {
      setPanel({ kind: "closed" });
      return;
    }
    setPanel({ kind: "loading" });
    Promise.all([getMonitoringStatus(), getFraudAlerts()])
      .then(([status, queue]) =>
        setPanel({
          kind: "ready",
          status,
          alerts: queue.alerts,
          run: null,
          notice: null,
        })
      )
      .catch((err: unknown) =>
        setPanel({ kind: "error", message: userErrorMessage(err, tCommon) })
      );
  }

  function refresh(notice: string | null, run: MonitoringRun | null) {
    Promise.all([getMonitoringStatus(), getFraudAlerts()])
      .then(([status, queue]) =>
        setPanel({ kind: "ready", status, alerts: queue.alerts, run, notice })
      )
      .catch((err: unknown) =>
        setPanel({ kind: "error", message: userErrorMessage(err, tCommon) })
      );
  }

  function evaluate() {
    setPanel({ kind: "loading" });
    postMonitoringEvaluate()
      .then((run) =>
        refresh(
          `${run.alerts_opened.length} opened, ${run.alerts_duplicate.length} already tracked.`,
          run
        )
      )
      .catch((err: unknown) =>
        setPanel({ kind: "error", message: userErrorMessage(err, tCommon) })
      );
  }

  function openForSignal() {
    if (!signalId) return;
    postFraudAlert(signalId)
      .then((out) => refresh(`Alert ${out.alert.id}: ${out.status}.`, null))
      .catch((err: unknown) =>
        setPanel({ kind: "error", message: userErrorMessage(err, tCommon) })
      );
  }

  function move(alertId: string, to: string) {
    patchFraudAlert(alertId, to)
      .then((alert) => refresh(`Alert ${alert.id} moved to ${alert.status}.`, null))
      .catch((err: unknown) =>
        setPanel({ kind: "error", message: userErrorMessage(err, tCommon) })
      );
  }

  return (
    <div>
      <h3>Transaction monitoring</h3>
      <button
        type="button"
        aria-expanded={panel.kind !== "closed"}
        onClick={open}
      >
        {panel.kind === "closed" ? "Show monitoring" : "Hide monitoring"}
      </button>
      {panel.kind === "loading" && <p role="status">Loading monitoring…</p>}
      {panel.kind === "error" && <p role="alert">{panel.message}</p>}
      {panel.kind === "ready" && (
        <div>
          <p>
            Mode: {panel.status.mode} — {panel.status.mode_note}
          </p>
          <p>
            {panel.status.transactions_visible} transaction(s),{" "}
            {panel.status.signals_visible} signal(s), {panel.status.alerts_open}{" "}
            open alert(s), {panel.status.signals_without_alerts} signal(s)
            without alerts.
          </p>
          <p>
            Data window: {panel.status.data_window.start ?? "—"} to{" "}
            {panel.status.data_window.end ?? "—"}.
          </p>
          <button type="button" onClick={evaluate}>
            Run evaluation
          </button>{" "}
          {signalId && (
            <button type="button" onClick={openForSignal}>
              Open alert for this signal
            </button>
          )}
          {panel.notice && <p role="status">{panel.notice}</p>}
          {panel.alerts.length === 0 ? (
            <p>No alerts recorded.</p>
          ) : (
            <ul>
              {panel.alerts.map((a) => (
                <li key={a.id}>
                  <strong>{a.id}</strong> ({a.detector_family ?? "—"},{" "}
                  {a.severity ?? "—"}): {a.status}
                  {(NEXT[a.status] ?? []).map((to) => (
                    <span key={to}>
                      {" "}
                      <button type="button" onClick={() => move(a.id, to)}>
                        {to}
                      </button>
                    </span>
                  ))}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
