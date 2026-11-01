/* System status panel: renders exactly the checks returned by
 * GET /api/v1/health. No service is ever shown operational unless its
 * check passed; unconfigured or unknown checks say so in text. */

import type { HealthCheck } from "../lib/api";

const ROWS: { label: string; check: string }[] = [
  { label: "API Services", check: "store" },
  { label: "Seed Integrity", check: "seed_integrity" },
  { label: "Graph Provenance", check: "graph_provenance" },
  { label: "AI Engine (Muse Spark)", check: "model_configured" },
];

function describe(result: string | undefined): {
  text: string;
  tone: "ok" | "warn" | "bad";
  detail: string;
} {
  if (result === undefined)
    return { text: "Not reported", tone: "warn", detail: "" };
  const verdict = result.split(" ", 1)[0];
  const detail = result.slice(verdict.length).trim();
  if (verdict === "PASS") return { text: "Operational", tone: "ok", detail };
  if (verdict === "NOT_CONFIGURED")
    return { text: "Not configured", tone: "warn", detail };
  return { text: "Degraded", tone: "bad", detail };
}

interface Props {
  health: HealthCheck;
  checkedAt: string;
}

export function SystemStatus({ health, checkedAt }: Props) {
  const operational = health.status === "healthy";
  const known = new Set(ROWS.map((row) => row.check));
  const extra = Object.keys(health.checks).filter((key) => !known.has(key));
  return (
    <section
      className="card glass command-section status-panel"
      aria-labelledby="sys-status-h"
    >
      <h2 id="sys-status-h">System Status</h2>
      <p>
        <span className={`badge ${operational ? "ok" : "bad"}`}>
          {health.status}
        </span>{" "}
        {operational && (
          <span className="muted">All systems operational</span>
        )}
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
              <span>{row.label}</span>
              <span className="muted">
                {state.text}
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
              <span>{key}</span>
              <span className="muted">
                {state.text}
                {state.detail !== "" ? `: ${state.detail}` : ""}
              </span>
            </li>
          );
        })}
      </ul>
      <p className="muted">
        Scenario {health.scenario_id} · Run <code>{health.run_id}</code>
      </p>
      <p className="muted">Checked {checkedAt}</p>
    </section>
  );
}
