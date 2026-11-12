"use client";

/* System status panel: renders exactly the checks returned by
 * GET /api/v1/health. No service is ever shown operational unless its
 * check passed; unconfigured or unknown checks say so in text. */

import type { HealthCheck } from "../lib/api";
import { useTranslation } from "../lib/i18n/context";

const ROWS: { key: "rowApi" | "rowSeed" | "rowGraph" | "rowAi"; check: string }[] = [
  { key: "rowApi", check: "store" },
  { key: "rowSeed", check: "seed_integrity" },
  { key: "rowGraph", check: "graph_provenance" },
  { key: "rowAi", check: "model_configured" },
];

type StatusKey = "stNotReported" | "stOperational" | "stNotConfigured" | "stDegraded";

function describe(result: string | undefined): {
  key: StatusKey;
  tone: "ok" | "warn" | "bad";
  detail: string;
} {
  if (result === undefined)
    return { key: "stNotReported", tone: "warn", detail: "" };
  const verdict = result.split(" ", 1)[0];
  const detail = result.slice(verdict.length).trim();
  if (verdict === "PASS") return { key: "stOperational", tone: "ok", detail };
  if (verdict === "NOT_CONFIGURED")
    return { key: "stNotConfigured", tone: "warn", detail };
  return { key: "stDegraded", tone: "bad", detail };
}

interface Props {
  health: HealthCheck;
  checkedAt: string;
}

/* Humanize machine check keys for display ("storage_backend" ->
 * "Storage backend", short acronyms uppercased). Raw keys stay in
 * API responses and tests of behavior; this is presentation only. */
function humanize(key: string): string {
  const words = key
    .split("_")
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ");
  return words.length <= 3 ? words.toUpperCase() : words;
}

export function SystemStatus({ health, checkedAt }: Props) {
  const { t } = useTranslation("system");
  // A-1: the headline keys off the backend's qualified status. Only a
  // fully-configured "healthy" earns "All systems operational"; gaps
  // get their own honest headline; degraded/unavailable get none.
  const fullyOk = health.status === "healthy";
  const gapsOk = health.status === "operational_with_gaps";
  const known = new Set(ROWS.map((row) => row.check));
  const extra = Object.keys(health.checks).filter((key) => !known.has(key));
  return (
    <section
      className="card glass command-section status-panel"
      aria-labelledby="sys-status-h"
    >
      <h2 id="sys-status-h">{t("sysTitle")}</h2>
      <p>
        <span className={`badge ${fullyOk || gapsOk ? "ok" : "bad"}`}>
          {health.status}
        </span>{" "}
        {fullyOk && <span className="muted">{t("allOk")}</span>}
        {gapsOk && <span className="muted">{t("gapsOk")}</span>}
      </p>
      <ul className="status-list">
        {ROWS.map((row) => {
          const result = health.checks[row.check];
          const state = describe(result);
          return (
            <li key={row.check}>
              <span
                className={`dot dot-${state.tone}`}
                aria-hidden="true"
              />
              <span>{t(row.key)}</span>
              <span className="muted">
                {t(state.key)}
                {state.detail !== "" ? `: ${state.detail}` : ""}
              </span>
            </li>
          );
        })}
        {extra.map((key) => {
          const state = describe(health.checks[key]);
          return (
            <li key={key}>
              <span
                className={`dot dot-${state.tone}`}
                aria-hidden="true"
              />
              <span>{humanize(key)}</span>
              <span className="muted">
                {t(state.key)}
                {state.detail !== "" ? `: ${state.detail}` : ""}
              </span>
            </li>
          );
        })}
      </ul>
      <p className="muted">
        {t("scenarioPre", { s: health.scenario_id })}
        <code>{health.run_id}</code>
      </p>
      <p className="muted">
        {t("checkedPre")}{" "}
        <bdi>{checkedAt}</bdi>
      </p>
    </section>
  );
}
