# UGLS Authenticated-Session Audit (Section B)

Date: 2026-11-02 (resume of the UGLS final browser-acceptance run).
Backend: armed QA on `127.0.0.1:8010` (`SESSION_SECRET` set, `DATA_DIR`
pointing at `qa-scratch/data`, a byte copy of production state).
Frontend: production build targeting `:8010`, served on `:3000`.
Users: disposable `qa_es` (investigator) + `qa_ar` (auditor); credentials
lived only in a local temp env file, never in the repo or logs.
Method: genuine Edge (CDP) captures with planted session cookies,
persistent profiles for navigation/refresh, plus direct API checks.
Evidence: `auth-evidence/` (14 captures × png/dom/doc/console/net/
phases).

## Results

| # | Requirement | Status | Evidence |
| - | ----------- | ------ | -------- |
| B1 | Language selection before login (en/fr/ar gate) | PASS | `b1-gate-en/fr/ar`: login card renders, `lang`/`dir` correct (ar RTL), zero user data, zero CORS errors |
| B2 | Language selection after login | PASS | `b2-a-demo-es`, `b2-b-demo-ar`: correct user per session (`qa_es`/`qa_ar`), no gate, 0 console errors |
| B3 | Refresh and navigation persistence | PASS | `b3-*` (persistent profiles): es/ar survive route change + param-less reload; 0 console errors after hydration fix |
| B4 | Session renewal | PASS | Fresh login → `/me` 200; renewed cookie renders authed (`b4-a-renew`, es, 0 errors); pre-renewal session stays valid (stateless by design, verified `/me` 200) |
| B5 | Logout then login | PASS | `logout` → old session 401, other user unaffected (200); `b5-a-gate` re-shows gate in stored locale (es); re-login restores (`b5-a-back`, 0 errors) |
| B6 | Preference consistency | PASS | All A captures es, all B captures ar — including across the B5 logout boundary (logout does not clear the stored locale) |
| B7 | Multiple users, different preferences | PASS | Concurrent es (investigator) + ar (auditor) sessions, independent profiles/locales |
| B8 | No cross-user preference leak | PASS | 0 `qa_ar` mentions in A DOMs, 0 `qa_es` mentions in B DOMs; locales never cross (matrix below) |

Capture matrix (`lang`, gate?, user hits, console/net counts):

| capture | lang/dir | gate | A | B | cerr | net |
| - | - | - | - | - | - | - |
| b1-gate-en/fr/ar | en/fr/ar, ar RTL | 1 | 0 | 0 | 8–10 | 8–15 |
| b2-a-demo-es | es/ltr | 0 | 1 | 0 | 0 | 5 |
| b2-b-demo-ar | ar/rtl | 0 | 0 | 1 | 0 | 0 |
| b3-a-* (3) | es/ltr | 0 | 1 | 0 | 0 | 0–4 |
| b3-b-* (3) | ar/rtl | 0 | 0 | 1 | 0 | 0–1 |
| b4-a-renew | es/ltr | 0 | 1 | 0 | 0 | 1 |
| b5-a-gate | es/ltr | 1 | 0 | 0 | 12 | 13 |
| b5-a-back | es/ltr | 0 | 1 | 0 | 0 | 4 |

Logged-out `cerr`/`net` are one-time 401s per data endpoint plus the
browser's own "failed to load resource" lines — the honest logged-out
state. Authed `net` entries are all `ERR_ABORTED` (Next.js RSC
prefetch + React refetch aborts), never 4xx/5xx.

## Blocking defects found and fixed (armed mode was unusable)

1. **CORS middleware inside-out** (`app/main.py`): `CORSMiddleware`
   was registered first (= innermost), so `session_guard` 401/403s
   and all preflights bypassed it — the browser hid every 401 as a
   network failure, the login card never appeared, and no authed
   browser POST could preflight. Fix: register CORS last
   (= outermost). Regression tests:
   `tests/test_cors.py::test_armed_guard_401_carries_cors_headers`,
   `test_armed_preflight_answered_before_guard` (fail pre-fix).
2. **`/me` recheck storm** (`frontend/lib/api.ts`): `getAuthMe` 401s
   dispatched `UNAUTHORIZED_EVENT`, re-triggering `recheck()` forever
   (586 `/auth/me` calls in one page load, tripping the rate
   limiter). Fix: exclude the `/api/v1/auth/*` namespace from the
   expiry signal (the gate consumes auth outcomes directly).
   Regression: extended `lib/api.test.ts` expiry-signal test
   (fail pre-fix).
3. **Locale hydration mismatch** (`frontend/lib/i18n/context.tsx`):
   provider initialised state from `localStorage`, mismatching SSR
   English on every returning visit (React #418). Fix: fallback
   first render, stored/override/detected locale in the mount
   effect. Regression: `context.test.tsx` first-render test
   (fail pre-fix). Tradeoff: returning visitors may see one
   fallback frame.

## Verdict

**B1–B8 PASS.** Authenticated sessions preserve per-user language
preferences with no leakage. The three blocking defects are fixed,
regression-tested, and re-verified in the browser.
