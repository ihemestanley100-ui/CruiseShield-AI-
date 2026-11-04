"use client";

/* Notification bell + panel over GET /api/v1/notifications. The badge
 * counts the backend's unread_count (OPEN + unread by this caller).
 * Per-item and mark-all-read POST to /api/v1/notifications/read and
 * persist server-side per caller identity. Investigation links derive
 * from the backend invariant that alert/investigation IDs share one
 * numeric suffix; anything not matching that shape gets no
 * investigation link, never a guessed one. */

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  listNotifications,
  markNotificationsRead,
  userErrorMessage,
  type NotificationItem,
} from "../lib/api";
import { useTranslation } from "../lib/i18n/context";
import { formatDate } from "../lib/i18n/format";

type State =
  | { kind: "loading" }
  | { kind: "ready"; items: NotificationItem[]; unread: number }
  | { kind: "error"; message: string };

function investigationIdFor(item: NotificationItem): string | null {
  const match = /^alert_(.+)$/.exec(item.notification_id);
  return match ? `inv_${match[1]}` : null;
}

export function Notifications() {
  const { t, locale } = useTranslation("notify");
  const { t: tCommon } = useTranslation("common");
  const [state, setState] = useState<State>({ kind: "loading" });
  const [open, setOpen] = useState(false);
  const [acting, setActing] = useState(false);
  const bell = useRef<HTMLButtonElement | null>(null);
  const heading = useRef<HTMLHeadingElement | null>(null);
  const wasOpen = useRef(false);

  const refresh = useCallback(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    listNotifications(controller.signal).then(
      (res) =>
        setState({
          kind: "ready",
          items: res.notifications,
          unread: res.unread_count,
        }),
      (err: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          kind: "error",
          message: userErrorMessage(err, tCommon),
        });
      }
    );
    return () => controller.abort();
  }, [tCommon]);

  useEffect(() => refresh(), [refresh]);

  useEffect(() => {
    if (open) {
      wasOpen.current = true;
      heading.current?.focus();
    } else if (wasOpen.current) {
      wasOpen.current = false;
      bell.current?.focus();
    }
  }, [open ]);

  useEffect(() => {
    if (!open) return;
    function onKey(ev: KeyboardEvent) {
      if (ev.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open ]);

  async function mark(
    body: { notification_ids?: string[]; all?: boolean },
    apply: (items: NotificationItem[], marked: string[]) => NotificationItem[]
  ) {
    if (state.kind !== "ready" || acting) return;
    setActing(true);
    try {
      const res = await markNotificationsRead(body);
      setState({
        kind: "ready",
        items: apply(state.items, res.marked),
        unread: res.unread_count,
      });
    } catch (err: unknown) {
      setState({ kind: "error", message: userErrorMessage(err, tCommon) });
    } finally {
      setActing(false);
    }
  }

  const markOne = (id: string) =>
    mark({ notification_ids: [id] }, (items, marked) =>
      items.map((n) =>
        marked.includes(n.notification_id) ? { ...n, read: true } : n
      )
    );
  const markAll = () =>
    mark({ all: true }, (items, marked) =>
      items.map((n) =>
        marked.includes(n.notification_id) ? { ...n, read: true } : n
      )
    );

  const unread = state.kind === "ready" ? state.unread : 0;

  return (
    <div className="notif-wrap">
      <button
        ref={bell}
        type="button"
        className="btn-secondary btn-icon notif-btn"
        aria-expanded={open}
        aria-controls="notif-panel"
        aria-label={
          state.kind === "loading"
            ? t("bellLoading")
            : t("bellOpen", { n: unread })
        }
        onClick={() => setOpen(!open)}
      >
        <svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true">
          <path
            d="M10 2a6 6 0 0 0-6 6v4l-2 3h16l-2-3V8a6 6 0 0 0-6-6zM8 18a2 2 0 0 0 4 0"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
          />
        </svg>
        {unread > 0 && (
          <span className="notif-badge" aria-hidden="true">
            {unread}
          </span>
        )}
      </button>
      {open && (
        <>
          <button
            type="button"
            className="popover-overlay"
            aria-label={t("closeNotif")}
            onClick={() => setOpen(false)}
          />
          <div
            id="notif-panel"
            role="dialog"
            aria-label={t("panelLabel")}
            className="notif-panel"
          >
            <h2 ref={heading} tabIndex={-1}>
              {t("panelTitle")}
            </h2>
            <p className="notif-actions">
              <button
                type="button"
                className="btn-secondary"
                disabled={acting || state.kind !== "ready" || unread === 0}
                onClick={() => void markAll()}
              >
                {t("markAllRead")}
              </button>{" "}
              <button
                type="button"
                className="btn-secondary"
                disabled={acting || state.kind === "loading"}
                onClick={() => refresh()}
              >
                {tCommon("retry")}
              </button>
            </p>
            {state.kind === "loading" && (
              <p className="muted" aria-live="polite">
                {t("loadingAlerts")}
              </p>
            )}
            {state.kind === "error" && (
              <div className="alert error" role="alert">
                {state.message}
              </div>
            )}
            {state.kind === "ready" &&
              (state.items.length === 0 ? (
                <p className="muted">{t("noAlerts")}</p>
              ) : (
                <ul className="stack">
                  {state.items.map((item) => {
                    const invId = investigationIdFor(item);
                    return (
                      <li key={item.notification_id} className="rule-row">
                        <div>
                          <strong>{item.title}</strong>{" "}
                          <span className="badge">{item.status}</span>
                          {!item.read && (
                            <span className="badge badge-unread">•</span>
                          )}
                        </div>
                        <p className="muted">
                          <code>{item.notification_id}</code> ·{" "}
                          <bdi>
                            {formatDate(locale, item.created_at, {
                              dateStyle: "medium",
                              timeStyle: "short",
                            })}
                          </bdi>
                        </p>
                        <p>
                          {invId !== null && (
                            <>
                              <Link
                                href={`/investigations/${invId}`}
                                onClick={() => setOpen(false)}
                              >
                                {t("openInv")}
                              </Link>{" "}
                            </>
                          )}
                          {item.transaction_id !== null && (
                            <>
                              <Link
                                href={`/network/${item.transaction_id}`}
                                onClick={() => setOpen(false)}
                              >
                                {t("networkLink")}
                              </Link>{" "}
                            </>
                          )}
                          {!item.read && (
                            <button
                              type="button"
                              className="btn-link"
                              disabled={acting}
                              onClick={() => void markOne(item.notification_id)}
                            >
                              {t("markRead")}
                            </button>
                          )}
                        </p>
                      </li>
                    );
                  })}
                </ul>
              ))}
          </div>
        </>
      )}
    </div>
  );
}
