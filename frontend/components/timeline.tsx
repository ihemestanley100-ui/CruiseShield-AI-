/* Shared timeline (presentational): ordered events with timestamps.
 * Order and content come from props exactly as passed. */

"use client";

import { useTranslation } from "../lib/i18n/context";
import { formatDate } from "../lib/i18n/format";

export interface TimelineItem {
  id: string;
  time: string;
  title: string;
  detail?: string;
}

export function Timeline({ items }: { items: TimelineItem[] }) {
  const { t, locale } = useTranslation("common");
  if (items.length === 0) {
    return <p className="muted">{t("timelineEmpty")}</p>;
  }
  return (
    <ol className="timeline">
      {items.map((item) => (
        <li key={item.id} className="timeline-item">
          <div className="timeline-time muted">
            <bdi>
              {formatDate(locale, item.time, {
                dateStyle: "medium",
                timeStyle: "short",
              })}
            </bdi>
          </div>
          <div className="timeline-title">{item.title}</div>
          {item.detail !== undefined && item.detail !== "" && (
            <div className="timeline-detail muted">{item.detail}</div>
          )}
        </li>
      ))}
    </ol>
  );
}
