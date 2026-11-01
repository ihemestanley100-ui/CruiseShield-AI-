"use client";

/* Phase 5: protected-demo login gate. Open demo (backend auth disabled)
 * renders children exactly as before. When the backend arms login
 * (SESSION_SECRET set), logged-out visitors get a login card instead of
 * the demo routes; the landing page stays public branding and is never
 * gated here. Fail-open is UI-only: data protection is enforced by the
 * backend session guard, so an unreachable backend just shows the
 * pages' existing backend-error states. */

import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  getAuthMe,
  getAuthMode,
  postLogin,
  postLogout,
  type AuthSession,
} from "../lib/api";

export type GateState =
  | { status: "open" }
  | { status: "authed"; session: AuthSession }
  | { status: "login" };

export function useDemoSession() {
  // Optimistic open: open-demo first paint is unchanged, and every
  // existing shell render (including tests without a backend) behaves
  // exactly as before until the mode check resolves.
  const [gate, setGate] = useState<GateState>({ status: "open" });

  useEffect(() => {
    const controller = new AbortController();
    let live = true;
    (async () => {
      try {
        const mode = await getAuthMode(controller.signal);
        if (!live || !mode.auth_enabled) return;
        try {
          const session = await getAuthMe(controller.signal);
          if (live) setGate({ status: "authed", session });
        } catch (err: unknown) {
          if (live && err instanceof ApiError && err.status === 401) {
            setGate({ status: "login" });
          }
          // Other /me failures fail open: pages surface their own errors.
        }
      } catch {
        // Unreachable backend: fail open, existing behavior preserved.
      }
    })();
    return () => {
      live = false;
      controller.abort();
    };
  }, []);

  const login = useCallback(
    async (username: string, password: string): Promise<string | null> => {
      try {
        const session = await postLogin(username, password);
        setGate({ status: "authed", session });
        return null;
      } catch (err: unknown) {
        if (err instanceof ApiError && err.status === 429) {
          return "Too many login attempts. Wait a minute and try again.";
        }
        if (err instanceof ApiError && err.code === "BACKEND_UNREACHABLE") {
          return "Backend unreachable. Check the demo server and retry.";
        }
        return "Invalid username or password.";
      }
    },
    []
  );

  const logout = useCallback(async () => {
    try {
      await postLogout();
    } catch {
      // Cookie may already be gone; the gate is what matters.
    }
    setGate({ status: "login" });
  }, []);

  return { gate, login, logout };
}

export function LoginCard({
  onLogin,
}: {
  onLogin: (username: string, password: string) => Promise<string | null>;
}) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(ev: React.FormEvent) {
    ev.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    const failure = await onLogin(username.trim(), password);
    setBusy(false);
    if (failure !== null) setError(failure);
  }

  return (
    <div className="login-wrap">
      <section className="card login-card" aria-labelledby="login-h">
        <h2 id="login-h">Demo sign in</h2>
        <p className="muted">
          This hosted demo is protected. Sign in with the investigator
          credentials supplied for this evaluation. Synthetic data only.
        </p>
        <form onSubmit={submit}>
          <label>
            Username
            <input
              className="text-input"
              type="text"
              name="username"
              autoComplete="username"
              value={username}
              onChange={(ev) => setUsername(ev.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              className="text-input"
              type="password"
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(ev) => setPassword(ev.target.value)}
              required
            />
          </label>
          {error !== null && (
            <p className="alert error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" disabled={busy} className="btn-commit">
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </section>
    </div>
  );
}
