"use client";

/* Batch 4: audit trail list. Renders exactly the entries returned by
 * GET /api/v1/cases/{id}/audit, newest last (server order preserved). */

import type { AuditEntry } from "../lib/api";

/* Display trims fractional seconds ("2026-10-29 20:32:15 UTC"); the
 * full precision stays in dateTime/title. Shapes this cannot parse
 * render verbatim — never guessed, never relabelled. */
function shortTime(iso: string): string {
  const m = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})(?:\.\d+)?(Z)?$/.exec(
    iso
  );
  if (!m) return iso;
  return `${m[1]} ${m[2]}${m[3] === "Z" ? " UTC" : ""}`;
}

interface Props {
  audits: AuditEntry[];
}

export function AuditList({ audits }: Props) {
  return (
    <section className="card" aria-label="Audit trail">
      <h2 id="audit-h">Audit trail</h2>
      <p className="muted" data-testid="audit-counts">
        {audits.length} audit event{audits.length === 1 ? "" : "s"}.
      </p>
      {audits.length === 0 ? (
        <p className="muted">No audit events recorded for this case.</p>
      ) : (
        <div className="table-scroll">
          <table>
            <caption className="muted">
              Every recorded action with actor, state change, and reason.
            </caption>
            <thead>
              <tr>
                <th scope="col">Event</th>
                <th scope="col">Time</th>
                <th scope="col">Actor</th>
                <th scope="col">Action</th>
                <th scope="col">State change</th>
                <th scope="col">Reason</th>
              </tr>
            </thead>
            <tbody>
              {audits.map((a) => (
                <tr key={a.audit_event_id} data-audit-row={a.audit_event_id}>
                  <td className="nowrap">
                    <code>{a.audit_event_id}</code>
                  </td>
                  <td className="nowrap">
                    <time dateTime={a.timestamp} title={a.timestamp}>
                      {shortTime(a.timestamp)}
                    </time>
                  </td>
                  <td className="nowrap">
                    {a.actor_type}/{a.actor_id}
                  </td>
                  <td className="nowrap">
                    <code>{a.action}</code>
                  </td>
                  <td>
                    <code>{a.previous_state_reference || "—"}</code> →{" "}
                    <code>{a.new_state_reference || "—"}</code>
                  </td>
                  <td>{a.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
