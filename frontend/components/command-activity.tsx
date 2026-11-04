"use client";

/* Command Center recent activity. Compact view of the latest case
 * audit entries exactly as returned by GET case audit — server order
 * preserved, truncation labelled. */

import Link from "next/link";
import type { AuditEntry } from "../lib/api";
import { useTranslation } from "../lib/i18n/context";

const RECENT_LIMIT = 5;

interface Props {
  audits: AuditEntry[];
  caseId: string;
}

export function CommandActivity({ audits, caseId }: Props) {
  const { t, tp } = useTranslation("command");
  const shown = audits.slice(-RECENT_LIMIT);
  return (
    <section className="card command-section" aria-labelledby="activity-h">
      <h2 id="activity-h">{t("activityTitle")}</h2>
      <p className="muted" data-testid="command-activity-counts">
        {tp("activityEvents", audits.length)}
        {audits.length > shown.length &&
          t("activityMore", { n: shown.length })}
        .
      </p>
      {shown.length === 0 ? (
        <p className="muted">{t("activityEmpty")}</p>
      ) : (
        <ul className="stack">
          {shown.map((a) => (
            <li key={a.audit_event_id} className="rule-row">
              <div>
                <code>{a.audit_event_id}</code>{" "}
                <span className="muted">
                  <bdi>{a.timestamp}</bdi>
                </span>
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
        <Link href={`/cases/${caseId}/audit`}>{t("openCaseAudit")}</Link>
      </p>
    </section>
  );
}
