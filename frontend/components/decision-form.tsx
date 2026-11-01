"use client";

/* Batch 4: human decision form. The server validates the decision label,
 * requires a non-empty reason, and enforces allowed transitions
 * (app/cases.py); this form only collects the input honestly. Submit is
 * disabled while a request is in flight so one click cannot create
 * duplicate decisions. */

import { useState } from "react";
import {
  ApiError,
  postDecision,
  type DecisionResponse,
} from "../lib/api";

/* Exact copy of DECISION_LABELS in app/cases.py; the server rejects any
 * other value, so drift here can only narrow choices, never widen them. */
export const DECISION_LABELS = [
  "Close Case",
  "Escalate",
  "Mark False Positive",
  "Monitor",
  "Request Verification",
];

interface Props {
  caseId: string;
  allowedTransitions: string[];
  onDecided: (response: DecisionResponse) => void;
}

export function DecisionForm({ caseId, allowedTransitions, onDecided }: Props) {
  // No preselected decision: the analyst must choose explicitly (F1).
  const [decision, setDecision] = useState("");
  const [target, setTarget] = useState(allowedTransitions[0] ?? "");
  const [reason, setReason] = useState("");
  const [actor, setActor] = useState("investigator");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    if (!DECISION_LABELS.includes(decision)) {
      setError("Select a decision before recording.");
      return;
    }
    if (reason.trim() === "") {
      setError("A reason is required before recording a decision.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const response = await postDecision(caseId, {
        decision,
        target_status: target,
        reason: reason.trim(),
        actor_id: actor.trim() === "" ? "investigator" : actor.trim(),
        evidence_viewed: [],
        recommendation: "",
      });
      setReason("");
      onDecided(response);
    } catch (err: unknown) {
      setError(
        err instanceof ApiError
          ? `${err.code}: ${err.message}`
          : err instanceof Error
            ? err.message
            : "request failed"
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (allowedTransitions.length === 0) {
    return (
      <section className="card" aria-label="Human decision">
        <h2 id="human-decision-h">Human decision</h2>
        <p className="muted">
          This case is in a terminal state; no further transitions are
          allowed.
        </p>
      </section>
    );
  }

  return (
    <section className="card" aria-label="Human decision">
      <h2 id="human-decision-h">Human decision</h2>
      <form onSubmit={onSubmit}>
        <p>
          <label htmlFor="decision-label">Decision</label>
          <br />
          <select
            id="decision-label"
            value={decision}
            onChange={(ev) => setDecision(ev.target.value)}
            required
          >
            <option value="">Select a decision…</option>
            {DECISION_LABELS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </p>
        <p>
          <label htmlFor="decision-target">Move case to</label>
          <br />
          <select
            id="decision-target"
            value={target}
            onChange={(ev) => setTarget(ev.target.value)}
          >
            {allowedTransitions.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </p>
        <p>
          <label htmlFor="decision-reason">Reason (required)</label>
          <br />
          <textarea
            id="decision-reason"
            value={reason}
            onChange={(ev) => setReason(ev.target.value)}
            rows={3}
            className="text-input"
          />
        </p>
        <p>
          <label htmlFor="decision-actor">Analyst ID</label>
          <br />
          <input
            id="decision-actor"
            type="text"
            value={actor}
            onChange={(ev) => setActor(ev.target.value)}
            className="text-input"
          />
        </p>
        {error !== "" && (
          <div className="alert error" role="alert">
            {error}
          </div>
        )}
        <p>
          <button
            type="submit"
            className="btn-commit"
            disabled={submitting}
          >
            {submitting ? "Recording…" : "Record decision"}
          </button>
        </p>
      </form>
    </section>
  );
}
