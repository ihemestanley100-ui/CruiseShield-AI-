"use client";

import { useEffect, useRef, useState } from "react";
import {
  ApiError,
  postAiAnalysis,
  postAiFollowup,
  type AgentRun,
} from "../lib/api";
import { useTranslation } from "../lib/i18n/context";
import { useCan } from "../lib/session";

const CLIENT_TIMEOUT_MS = 35000;

type AiState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ready"; run: AgentRun }
  | { kind: "error"; message: string };

interface Followup {
  question: string;
  run: AgentRun;
}

function RunResult({ run }: { run: AgentRun }) {
  const { t } = useTranslation("ai");
  return (
    <>
      <p>{run.result.summary}</p>
      <ul className="stack">
        {(run.result.key_findings ?? []).map((finding, index) => (
          <li key={index} className="finding">
            <div>{finding.finding}</div>
            <p className="muted">
              {t("confidencePre")}
              {finding.confidence_label} ·{" "}
              {(finding.evidence_ids ?? []).join(", ")}
            </p>
            <p className="muted">{finding.caveat}</p>
          </li>
        ))}
      </ul>
      {(run.result.missing_information ?? []).length > 0 && (
        <>
          <p className="muted">{t("missingTitle")}</p>
          <ul className="stack">
            {(run.result.missing_information ?? []).map((item, index) => (
              <li key={index} className="muted">
                {item}
              </li>
            ))}
          </ul>
        </>
      )}
      {(run.result.alternative_explanations ?? []).length > 0 && (
        <>
          <p className="muted">{t("altTitle")}</p>
          <ul className="stack">
            {(run.result.alternative_explanations ?? []).map((item, index) => (
              <li key={index} className="muted">
                {item}
              </li>
            ))}
          </ul>
        </>
      )}
      <p className="muted">{t("conclusionLine", { c: run.result.conclusion })}</p>
      <p className="muted">{run.result.disclaimer}</p>
      <p className="muted">
        {t("metaPre", {
          model: run.model_id,
          ms: run.latency_ms,
          s: run.schema_validation_status,
          r: run.evidence_reference_validation_status,
        })}
        <code>{run.agent_run_id}</code>
      </p>
    </>
  );
}

export function AiPanel({ invId }: { invId: string }) {
  // J4: roles without ai_run see analysis disabled (backend enforces).
  const runnable = useCan("ai_run");
  const { t } = useTranslation("ai");
  const { t: tCommon } = useTranslation("common");
  const [state, setState] = useState<AiState>({ kind: "idle" });
  const [followups, setFollowups] = useState<Followup[]>([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState("");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const controller = useRef<AbortController | null>(null);
  // J3-P4: follow-ups get their own timeout/abort pair so a hung
  // follow-up can never outlive the panel or clash with analysis.
  const askTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const askController = useRef<AbortController | null>(null);

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
      controller.current?.abort();
      if (askTimer.current) clearTimeout(askTimer.current);
      askController.current?.abort();
    },
    []
  );

  const run = () => {
    controller.current?.abort();
    const next = new AbortController();
    controller.current = next;
    setState({ kind: "loading" });
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => next.abort(), CLIENT_TIMEOUT_MS);
    postAiAnalysis(invId, next.signal)
      .then((runResult) => {
        if (timer.current) clearTimeout(timer.current);
        setState({ kind: "ready", run: runResult });
      })
      .catch((err: unknown) => {
        if (timer.current) clearTimeout(timer.current);
        if (next.signal.aborted) {
          setState({
            kind: "error",
            message: t("timedOut"),
          });
          return;
        }
        setState({
          kind: "error",
          message:
            err instanceof ApiError
              ? `${err.code}: ${err.message}`
              : err instanceof Error
                ? err.message
                : tCommon("requestFailed"),
        });
      });
  };

  return (
    <section className="card" aria-labelledby="ai-h" aria-live="polite">
      <h2 id="ai-h">{t("panelTitle")}</h2>
      <p className="muted">{t("panelBlurb")}</p>
      {!runnable && (
        <p className="muted" role="note">
          {t("cannotRun")}
        </p>
      )}
      {state.kind === "idle" && (
        <p>
          <button type="button" onClick={run} disabled={!runnable}>
            {t("runAnalysis")}
          </button>
        </p>
      )}
      {state.kind === "loading" && <p className="muted">{t("calling")}</p>}
      {state.kind === "error" && (
        <>
          <div className="alert error" role="alert">
            {state.message}
          </div>
          <p>
            <button type="button" onClick={run} disabled={!runnable}>
              {tCommon("retry")}
            </button>
          </p>
        </>
      )}
      {state.kind === "ready" && (
        <>
          <RunResult run={state.run} />
          <div data-testid="followups">
            {followups.map((f) => (
              <div key={f.run.agent_run_id} className="finding">
                <p>
                  <strong>{t("qLine", { q: f.question })}</strong>
                </p>
                <RunResult run={f.run} />
              </div>
            ))}
          </div>
          <form
            onSubmit={(ev) => {
              ev.preventDefault();
              const q = question.trim();
              if (q === "" || asking) return;
              setAsking(true);
              setAskError("");
              askController.current?.abort();
              const next = new AbortController();
              askController.current = next;
              if (askTimer.current) clearTimeout(askTimer.current);
              askTimer.current = setTimeout(
                () => next.abort(),
                CLIENT_TIMEOUT_MS
              );
              postAiFollowup(invId, q, next.signal)
                .then((runResult) => {
                  if (askTimer.current) clearTimeout(askTimer.current);
                  setFollowups((prev) => [
                    ...prev,
                    { question: q, run: runResult },
                  ]);
                  setQuestion("");
                })
                .catch((err: unknown) => {
                  if (askTimer.current) clearTimeout(askTimer.current);
                  setAskError(
                    next.signal.aborted
                      ? t("timedOut")
                      : err instanceof ApiError
                        ? `${err.code}: ${err.message}`
                        : err instanceof Error
                          ? err.message
                          : tCommon("requestFailed")
                  );
                })
                .finally(() => setAsking(false));
            }}
          >
            <p>
              <label htmlFor="ai-followup">
                {t("askLabel")}
              </label>
              <br />
              <input
                id="ai-followup"
                type="text"
                value={question}
                onChange={(ev) => setQuestion(ev.target.value)}
                placeholder={t("askPh")}
                className="text-input"
              />
            </p>
            {askError !== "" && (
              <div className="alert error" role="alert">
                {askError}
              </div>
            )}
            <p>
              <button
                type="submit"
                disabled={asking || question.trim() === "" || !runnable}
              >
                {asking ? t("asking") : t("askBtn")}
              </button>
            </p>
          </form>
        </>
      )}
    </section>
  );
}
