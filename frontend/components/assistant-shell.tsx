"use client";

/* Reusable assistant shell. One component serves every surface via
 * props: it opens a tenant-scoped conversation with the given
 * context, sends turns through the orchestrator, and renders the
 * execution state, tool steps, approval plans and errors verbatim.
 * Closed by default; no invented findings. */

import type { Conversation, OrchestratedTurn } from "../lib/api";
import {
  getConversation,
  postConversation,
  postConversationMessage,
  userErrorMessage,
} from "../lib/api";
import { useState } from "react";

type ShellState =
  | { kind: "closed" }
  | { kind: "opening" }
  | { kind: "ready"; conversation: Conversation; busy: boolean }
  | { kind: "error"; message: string };

export function AssistantShell({
  context,
  title,
}: {
  context: Record<string, string>;
  title: string;
}) {
  const [shell, setShell] = useState<ShellState>({ kind: "closed" });
  const [draft, setDraft] = useState("");

  function open() {
    if (shell.kind !== "closed") {
      setShell({ kind: "closed" });
      return;
    }
    setShell({ kind: "opening" });
    postConversation(context)
      .then((conversation) =>
        setShell({ kind: "ready", conversation, busy: false })
      )
      .catch((err: unknown) =>
        setShell({ kind: "error", message: userErrorMessage(err) })
      );
  }

  function send() {
    if (shell.kind !== "ready" || shell.busy || draft.trim() === "") return;
    const conversation = shell.conversation;
    setShell({ kind: "ready", conversation, busy: true });
    postConversationMessage(conversation.conversation_id, draft)
      .then((_turn: OrchestratedTurn) =>
        getConversation(conversation.conversation_id)
      )
      .then((updated) => {
        setShell({ kind: "ready", conversation: updated, busy: false });
        setDraft("");
      })
      .catch((err: unknown) =>
        setShell({ kind: "error", message: userErrorMessage(err) })
      );
  }

  return (
    <div>
      <h3>{title}</h3>
      <button
        type="button"
        aria-expanded={shell.kind !== "closed"}
        onClick={open}
      >
        {shell.kind === "closed" ? "Open assistant" : "Close assistant"}
      </button>
      {shell.kind === "opening" && <p role="status">Opening assistant…</p>}
      {shell.kind === "error" && <p role="alert">{shell.message}</p>}
      {shell.kind === "ready" && (
        <div>
          <ol>
            {shell.conversation.messages.map((m, index) => (
              <li key={`${m.at}-${index}`}>
                <strong>{m.role}:</strong>{" "}
                <span style={{ whiteSpace: "pre-wrap" }}>{m.text}</span>
              </li>
            ))}
          </ol>
          <label>
            Ask about this {title.toLowerCase()}
            <input
              type="text"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="e.g. monitoring queue status"
            />
          </label>{" "}
          <button
            type="button"
            onClick={send}
            disabled={shell.busy || draft.trim() === ""}
          >
            {shell.busy ? "Working…" : "Send"}
          </button>
        </div>
      )}
    </div>
  );
}
