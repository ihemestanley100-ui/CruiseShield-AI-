"use client";

import { useEffect, useRef, useState } from "react";
import {
  ApiError,
  postAiAnalysis,
  postAiFollowup,
  type AgentRun,
} from "../lib/api";

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
  return (
    <>
      <p>{run.result.summary}</p>
      <ul className="stack">
        {(run.result.key_findings ?? []).map((finding, index) => (
          <li key={index} className="finding">
            <div>{finding.finding}</div>
            <p className="muted">
              Confidence: {finding.confidence_label} ·{" "}
              {(finding.evidence_ids ?? []).join(", ")}
            </p>
            <p className="muted">{finding.caveat}</p>
          </li>
        ))}
      </ul>
      {(run.result.missing_information ?? []).length > 0 && (
        <>
          <p className="muted">Missing information:</p>
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
          <p className="muted">Alternative explanations:</p>
          <ul className="stack">
            {(run.result.alternative_explanations ?? []).map((item, index) => (
              <li key={index} className="muted">
                {item}
              </li>
            ))}
          </ul>
        </>
      )}
      <p className="muted">Conclusion: {run.result.conclusion}</p>
      <p className="muted">{run.result.disclaimer}</p>
      <p className="muted">
        {run.model_id} · {run.latency_ms} ms · schema{" "}
        {run.schema_validation_status} · refs{" "}
        {run.evidence_reference_validation_status} · run{" "}
        <code>{run.agent_run_id}</code>
      </p>
    </>
  );
}

export function AiPanel({ invId }: { invId: string }) {
  const [state, setState] = useState<AiState>({ kind: "idle" });
  const [followups, setFollowups] = useState<Followup[]>([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState("");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const controller = useRef<AbortController | null>(null);

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
      controller.current?.abort();
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
            message: "Request timed out or was cancelled.",
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
                : "request failed",
        });
      });
  };

  return (
    <section className="card" aria-labelledby="ai-h" aria-live="polite">
      <h2 id="ai-h">Analyze with Muse Spark</h2>
      <p className="muted">
        Read-only explanation of the evidence package. The model cannot change
        risk scores or authorize actions.
      </p>
      {state.kind === "idle" && (
        <p>
          <button type="button" onClick={run}>
            Run AI analysis
          </button>
        </p>
      )}
      {state.kind === "loading" && <p className="muted">Calling model…</p>}
      {state.kind === "error" && (
        <>
          <div className="alert error" role="alert">
            {state.message}
          </div>
          <p>
            <button type="button" onClick={run}>
              Retry
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
                  <strong>Q: {f.question}</strong>
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
              postAiFollowup(invId, q)
                .then((runResult) => {
                  setFollowups((prev) => [
                    ...prev,
                    { question: q, run: runResult },
                  ]);
                  setQuestion("");
                })
                .catch((err: unknown) => {
                  setAskError(
                    err instanceof ApiError
                      ? `${err.code}: ${err.message}`
                      : err instanceof Error
                        ? err.message
                        : "request failed"
                  );
                })
                .finally(() => setAsking(false));
            }}
          >
            <p>
              <label htmlFor="ai-followup">
                Ask a follow-up about this evidence
              </label>
              <br />
              <input
                id="ai-followup"
                type="text"
                value={question}
                onChange={(ev) => setQuestion(ev.target.value)}
                placeholder="e.g. Why is dev_04 shared across accounts?"
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
                disabled={asking || question.trim() === ""}
              >
                {asking ? "Asking…" : "Ask follow-up"}
              </button>
            </p>
          </form>
        </>
      )}
    </section>
  );
}
