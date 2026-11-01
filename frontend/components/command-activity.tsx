/* Command Center recent activity. Compact view of the latest case
 * audit entries exactly as returned by GET case audit — server order
 * preserved, truncation labelled. */

import Link from "next/link";
import type { AuditEntry } from "../lib/api";

const RECENT_LIMIT = 5;

interface Props {
  audits: AuditEntry[];
  caseId: string;
}

export function CommandActivity({ audits, caseId }: Props) {
  const shown = audits.slice(-RECENT_LIMIT);
  return (
    <section className="card command-section" aria-labelledby="activity-h">
      <h2 id="activity-h">Recent activity</h2>
      <p className="muted" data-testid="command-activity-counts">
        {audits.length} audit event{audits.length === 1 ? "" : "s"}
        {audits.length > shown.length &&
          ` — showing latest ${shown.length}`}
        .
      </p>
      {shown.length === 0 ? (
        <p className="muted">No audit events recorded yet.</p>
      ) : (
        <ul className="stack">
          {shown.map((a) => (
            <li key={a.audit_event_id} className="rule-row">
              <div>
                <code>{a.audit_event_id}</code>{" "}
                <span className="muted">{a.timestamp}</span>
              </div>
              <p className="muted">
                {a.actor_type}/{a.actor_id} · <code>{a.action}</code> ·{" "}
                {a.target_type}/{a.target_id}
              </p>
              {a.reason !== "" && <p className="muted">{a.reason}</p>}
            </li>
          ))}
        </ul>
      )}
      <p>
        <Link href={`/cases/${caseId}/audit`}>Open case audit trail</Link>
      </p>
    </section>
  );
}
