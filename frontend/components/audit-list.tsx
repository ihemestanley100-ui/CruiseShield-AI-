"use client";

/* Batch 4: audit trail list. Renders exactly the entries returned by
 * GET /api/v1/cases/{id}/audit, newest last (server order preserved). */

import type { AuditEntry } from "../lib/api";
import { useTranslation } from "../lib/i18n/context";

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
  const { t, tp } = useTranslation("audit");
  return (
    <section className="card" aria-label={t("auditLabel")}>
      <h2 id="audit-h">{t("auditTitle")}</h2>
      <p className="muted" data-testid="audit-counts">
        {tp("events", audits.length)}
      </p>
      {audits.length === 0 ? (
        <p className="muted">{t("auditEmpty")}</p>
      ) : (
        <div className="table-scroll">
          <table>
            <caption className="muted">{t("caption")}</caption>
            <thead>
              <tr>
                <th scope="col">{t("thEvent")}</th>
                <th scope="col">{t("thTime")}</th>
                <th scope="col">{t("thActor")}</th>
                <th scope="col">{t("thAction")}</th>
                <th scope="col">{t("thState")}</th>
                <th scope="col">{t("thReason")}</th>
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
