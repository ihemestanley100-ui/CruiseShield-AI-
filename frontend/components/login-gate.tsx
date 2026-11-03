"use client";

/* Phase 5: protected-demo login gate. Open demo (backend auth disabled)
 * renders children exactly as before. When the backend arms login
 * (SESSION_SECRET set), logged-out visitors get a login card instead of
 * the demo routes; the landing page stays public branding and is never
 * gated here. Fail-open is UI-only: data protection is enforced by the
 * backend session guard, so an unreachable backend just shows the
 * pages' existing backend-error states. */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ApiError,
  UNAUTHORIZED_EVENT,
  getAuthMe,
  getAuthMode,
  postLogin,
  postLogout,
  postLogoutAll,
  type AuthSession,
} from "../lib/api";
import { useTranslation } from "../lib/i18n/context";
import { publishSession } from "../lib/session";

export type GateState =
  | { status: "checking" }
  | { status: "open" }
  | { status: "authed"; session: AuthSession }
  | { status: "login" };

export function useDemoSession() {
  // Checking first: the shell withholds children until the mode check
  // resolves, so logged-out armed visitors never see data sections
  // flash (and fire doomed fetches) before the login card. One tiny
  // GET delays open-demo first paint by milliseconds.
  const [gate, setGate] = useState<GateState>({ status: "checking" });

  // J3-P6: session-expiry re-gating. Any 401/403 from a data call
  // re-runs the check: a live session keeps the app open, an expired
  // one flips the whole shell back to sign-in (the re-login affordance).
  const armed = useRef(false);
  const recheck = useCallback(async () => {
    if (!armed.current) return;
    try {
      const session = await getAuthMe();
      setGate({ status: "authed", session });
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 401) {
        setGate({ status: "login" });
      }
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    let live = true;
    (async () => {
      try {
        const mode = await getAuthMode(controller.signal);
        if (!live) return;
        if (!mode.auth_enabled) {
          setGate({ status: "open" });
          return;
        }
        armed.current = true;
        await recheck();
        // Other /me failures fail open: pages surface their own errors.
        if (live)
          setGate((g) =>
            g.status === "checking" ? { status: "open" } : g
          );
      } catch {
        // Unreachable backend: fail open, existing behavior preserved.
        if (live) setGate({ status: "open" });
      }
    })();
    const onUnauthorized = () => void recheck();
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => {
      live = false;
      controller.abort();
      window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    };
  }, [recheck]);

  const { t: tAuth } = useTranslation("auth");
  const login = useCallback(
    async (username: string, password: string): Promise<string | null> => {
      try {
        const session = await postLogin(username, password);
        setGate({ status: "authed", session });
        return null;
      } catch (err: unknown) {
        if (err instanceof ApiError && err.status === 429) {
          return tAuth("rateLimited");
        }
        if (err instanceof ApiError && err.code === "BACKEND_UNREACHABLE") {
          return tAuth("unreachable");
        }
        return tAuth("invalid");
      }
    },
    [tAuth]
  );

  const logout = useCallback(async () => {
    try {
      await postLogout();
    } catch {
      // Cookie may already be gone; the gate is what matters.
    }
    setGate({ status: "login" });
  }, []);

  const logoutAll = useCallback(async () => {
    try {
      await postLogoutAll();
    } catch {
      // Same fail-safe as logout.
    }
    setGate({ status: "login" });
  }, []);

  // J4: publish for role-aware controls (decision/AI/simulation gates).
  useEffect(() => {
    publishSession(
      gate.status === "authed"
        ? { mode: "authed", session: gate.session }
        : gate.status === "login"
          ? { mode: "login" }
          : { mode: "open" }
    );
  }, [gate]);

  return { gate, login, logout, logoutAll };
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
  const { t } = useTranslation("auth");

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
        <h2 id="login-h">{t("title")}</h2>
        <p className="muted">{t("blurb")}</p>
        <form onSubmit={submit}>
          <label>
            {t("username")}
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
            {t("password")}
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
            {busy ? t("signingIn") : t("signIn")}
          </button>
        </form>
      </section>
    </div>
  );
}
