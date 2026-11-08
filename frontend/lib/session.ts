/* J4: shared platform-session snapshot for role-aware UI.
 *
 * The login gate publishes here; write controls (decision form, AI
 * panel, simulation panel) disable themselves for read-only roles.
 * This is UX only — the backend session guard enforces permissions.
 * Open mode (backend auth disabled) enables everything, exactly
 * as before.
 */
"use client";

import { useSyncExternalStore } from "react";
import type { AuthSession } from "./api";

export type SessionSnapshot =
  | { mode: "open" }
  | { mode: "authed"; session: AuthSession }
  | { mode: "login" };

let snapshot: SessionSnapshot = { mode: "open" };
const listeners = new Set<() => void>();

export function publishSession(next: SessionSnapshot): void {
  snapshot = next;
  listeners.forEach((notify) => notify());
}

function subscribe(notify: () => void): () => void {
  listeners.add(notify);
  return () => {
    listeners.delete(notify);
  };
}

function getSnapshot(): SessionSnapshot {
  return snapshot;
}

export function useSessionSnapshot(): SessionSnapshot {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

export function useCan(permission: string): boolean {
  const snap = useSessionSnapshot();
  if (snap.mode === "open") return true;
  if (snap.mode === "login") return false;
  return snap.session.permissions.includes(permission);
}
