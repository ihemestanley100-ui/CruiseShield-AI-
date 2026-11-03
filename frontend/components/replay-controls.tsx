"use client";

/* Batch 4: deterministic replay controls. Each step fetches the exact
 * server state for that cursor; nothing is computed client-side. */

import { useEffect, useRef, useState } from "react";
import {
  getReplay,
  userErrorMessage,
  type ReplayState,
} from "../lib/api";
import { formatKobo } from "../lib/format";
import { useTranslation } from "../lib/i18n/context";
import { formatDate } from "../lib/i18n/format";

interface Props {
  scenarioId: string;
}

const PLAY_INTERVAL_MS = 1500;

export function ReplayControls({ scenarioId }: Props) {
  const { t, locale } = useTranslation("replay");
  const { t: tCommon } = useTranslation("common");
  const [cursor, setCursor] = useState(0);
  const [nonce, setNonce] = useState(0);
  const [state, setState] = useState<ReplayState | null>(null);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const reducedMotion = useRef(
    typeof window !== "undefined" &&
      typeof window.matchMedia === "function" &&
      (window.matchMedia("(prefers-reduced-motion: reduce)")?.matches ??
        false)
  );

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    getReplay(scenarioId, cursor, controller.signal)
      .then((s) => {
        setState(s);
        setLoading(false);
        if (s.cursor >= s.total) setPlaying(false);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setLoading(false);
        setPlaying(false);
        setError(userErrorMessage(err, tCommon));
      });
    return () => controller.abort();
  }, [scenarioId, cursor, nonce]);

  useEffect(() => {
    if (!playing || state === null) return;
    if (cursor >= state.total) {
      setPlaying(false);
      return;
    }
    const timer = window.setInterval(
      () => setCursor((c) => c + 1),
      PLAY_INTERVAL_MS
    );
    return () => window.clearInterval(timer);
  }, [playing, cursor, state]);

  const evt = state?.current_event ?? null;

  return (
    <section className="card" aria-label={t("controlsLabel")}>
      <h2>{t("controlsTitle")}</h2>
      <p className="muted" data-testid="replay-position" aria-live="polite">
        {state === null
          ? tCommon("loading")
          : t("positionLine", {
              c: state.cursor,
              t: state.total,
              e: state.counts.events,
              x: state.counts.transactions,
              g: state.counts.edges,
            })}
      </p>
      <div className="chip-row" role="group" aria-label={t("stepControls")}>
        <button
          type="button"
          className="chip"
          disabled={loading || cursor <= 0}
          onClick={() => setCursor((c) => Math.max(0, c - 1))}
        >
          {t("stepBack")}
        </button>
        <button
          type="button"
          className="chip"
          disabled={loading || (state !== null && cursor >= state.total)}
          onClick={() => setCursor((c) => c + 1)}
        >
          {t("stepFwd")}
        </button>
        <button
          type="button"
          className="chip"
          disabled={
            loading ||
            reducedMotion.current ||
            (state !== null && cursor >= state.total)
          }
          onClick={() => setPlaying((p) => !p)}
          title={reducedMotion.current ? t("reducedMotionPlay") : undefined}
        >
          {playing ? t("pause") : t("play")}
        </button>
        <button
          type="button"
          className="chip"
          disabled={loading || cursor === 0}
          onClick={() => {
            setPlaying(false);
            setCursor(0);
          }}
        >
          {t("restart")}
        </button>
      </div>
      {error !== "" && (
        <div className="alert error" role="alert">
          {error}{" "}
          <button
            type="button"
            className="chip"
            onClick={() => setNonce((n) => n + 1)}
          >
            {tCommon("retry")}
          </button>
        </div>
      )}
      {evt !== null && (
        <div className="alert ok" data-testid="replay-current">
          <strong>{evt.event_id}</strong> · {evt.event_type} ·{" "}
          <bdi>
            {formatDate(locale, evt.occurred_at, {
              dateStyle: "medium",
              timeStyle: "short",
            })}
          </bdi>
          <br />
          {t("currentTxnPre")}
          <code>{evt.transaction.transaction_id}</code> ·{" "}
          {formatKobo(
            evt.transaction.amount_minor,
            evt.transaction.currency,
            locale
          )}{" "}
          · {evt.transaction.sender_account_id} →{" "}
          {evt.transaction.receiver_account_id}
        </div>
      )}
      {state !== null && state.cursor === 0 && (
        <p className="muted">{t("startHint")}</p>
      )}
    </section>
  );
}
