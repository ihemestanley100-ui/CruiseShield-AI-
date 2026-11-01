"use client";

/* Notification bell + panel. Lists exactly the alerts returned by
 * GET /api/v1/alerts; the badge counts alerts whose backend status is
 * OPEN. Investigation links derive from the backend invariant that
 * alert/investigation/case IDs share one numeric suffix (see
 * store.reset, the single alert creation site); alerts not matching
 * that shape get no investigation link, never a guessed one. Read-only:
 * nothing here marks alerts read or mutates the backend. */

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  ApiError,
  listAlerts,
  type AlertItem,
} from "../lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ready"; alerts: AlertItem[] }
  | { kind: "error"; message: string };

function investigationIdFor(alert: AlertItem): string | null {
  const match = /^alert_(.+)$/.exec(alert.alert_id);
  return match ? `inv_${match[1]}` : null;
}

export function Notifications() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [open, setOpen] = useState(false);
  const bell = useRef<HTMLButtonElement | null>(null);
  const heading = useRef<HTMLHeadingElement | null>(null);
  const wasOpen = useRef(false);

  useEffect(() => {
    const controller = new AbortController();
    listAlerts(controller.signal).then(
      (res) => setState({ kind: "ready", alerts: res.alerts }),
      (err: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          kind: "error",
          message:
            err instanceof ApiError
              ? `${err.code}: ${err.message}`
              : err instanceof Error
                ? err.message
                : "request failed",
        });
      }
    );
    return () => controller.abort();
  }, []);

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

  const openCount =
    state.kind === "ready"
      ? state.alerts.filter((a) => a.status === "OPEN").length
      : 0;

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
            ? "Notifications, loading"
            : `Notifications, ${openCount} open`
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
        {openCount > 0 && (
          <span className="notif-badge" aria-hidden="true">
            {openCount}
          </span>
        )}
      </button>
      {open && (
        <>
          <button
            type="button"
            className="popover-overlay"
            aria-label="Close notifications"
            onClick={() => setOpen(false)}
          />
          <div
            id="notif-panel"
            role="dialog"
            aria-label="Notifications"
            className="notif-panel"
          >
            <h2 ref={heading} tabIndex={-1}>
              Notifications
            </h2>
            {state.kind === "loading" && (
              <p className="muted" aria-live="polite">
                Loading alerts…
              </p>
            )}
            {state.kind === "error" && (
              <div className="alert error" role="alert">
                {state.message}
              </div>
            )}
            {state.kind === "ready" &&
              (state.alerts.length === 0 ? (
                <p className="muted">No alerts.</p>
              ) : (
                <ul className="stack">
                  {state.alerts.map((alert) => {
                    const invId = investigationIdFor(alert);
                    return (
                      <li key={alert.alert_id} className="rule-row">
                        <div>
                          <strong>{alert.title}</strong>{" "}
                          <span className="badge">{alert.status}</span>
                        </div>
                        <p className="muted">
                          <code>{alert.alert_id}</code> · {alert.created_at}
                        </p>
                        <p>
                          {invId !== null && (
                            <>
                              <Link
                                href={`/investigations/${invId}`}
                                onClick={() => setOpen(false)}
                              >
                                Open investigation
                              </Link>{" "}
                            </>
                          )}
                          <Link
                            href={`/network/${alert.transaction_id}`}
                            onClick={() => setOpen(false)}
                          >
                            Network
                          </Link>
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
