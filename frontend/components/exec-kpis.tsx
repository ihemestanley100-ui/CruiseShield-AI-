/* Executive KPI row. Every card renders resolved backend values from
 * props; unavailable metrics show "Not available" or "None yet" — never
 * invented counts. Built on the shared Stat primitive. */

import type { AiAssessment } from "../lib/api";
import { Stat } from "./stat";

interface Props {
  invId: string;
  invStatus: string;
  networkBand: string;
  evidenceCount: number;
  latestRun: AiAssessment | null;
  decisionsCount: number;
  caseId: string;
  caseStatus: string;
  txnCount: number | null;
  txnPending: boolean;
}

export function ExecKpis(props: Props) {
  const {
    invId,
    invStatus,
    networkBand,
    evidenceCount,
    latestRun,
    decisionsCount,
    caseId,
    caseStatus,
    txnCount,
    txnPending,
  } = props;
  const highRisk =
    networkBand === "HIGH" || networkBand === "CRITICAL" ? 1 : 0;
  return (
    <section aria-labelledby="exec-h" className="command-section">
      <h2 id="exec-h">Executive overview</h2>
      <div className="exec-grid">
        <article className="card kpi-card" aria-label="Active investigations">
          <Stat
            label="Active investigations"
            value={1}
            caption={`${invId} · ${invStatus}`}
          />
        </article>
        <article className="card kpi-card" aria-label="Transactions monitored">
          <Stat
            label="Transactions monitored"
            value={txnCount ?? (txnPending ? "Loading…" : "Not available")}
            caption="Synthetic demo data"
          />
        </article>
        <article className="card kpi-card" aria-label="High-risk investigations">
          <Stat
            label="High-risk investigations"
            value={highRisk}
            caption={`Network band ${networkBand}`}
          />
        </article>
        <article className="card kpi-card" aria-label="Evidence records">
          <Stat
            label="Evidence records"
            value={evidenceCount}
            caption={`Linked to ${invId}`}
          />
        </article>
        <article className="card kpi-card" aria-label="AI analysis runs">
          <Stat
            label="AI analysis runs"
            value={latestRun ? latestRun.agent_run_id : "None yet"}
            caption={
              latestRun
                ? `${latestRun.model_id} · ${latestRun.status}`
                : "No runs recorded"
            }
          />
        </article>
        <article className="card kpi-card" aria-label="Human decisions">
          <Stat
            label="Human decisions"
            value={decisionsCount}
            caption={
              decisionsCount === 0
                ? `${caseId} · ${caseStatus} — requires analyst action`
                : `${caseId} · ${caseStatus}`
            }
          />
        </article>
      </div>
    </section>
  );
}
