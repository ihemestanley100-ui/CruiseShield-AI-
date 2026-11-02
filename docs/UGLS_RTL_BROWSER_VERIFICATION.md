# UGLS-02 Task 3 — RTL Browser Verification

Date: 2026-11-02. Method: real Microsoft Edge (headless=new), isolated
fresh profiles, production `next start` build + local backend in
open-demo mode (`{"auth_enabled":false}`, GET-only traffic).
Evidence: `rtl-evidence-ugls02/` (20 screenshots + 8 dumped DOMs:
14 matrix shots from `rtl-matrix-ugls02.ps1` + 6 ad-hoc: case-ar-bdi,
case-ar-bdi2, demo-ar-bdi2, demo-en-mob, inv-en-mob, demo-en-true).
Reproduce: `rtl-qa-ugls02.ps1` (servers) + `rtl-matrix-ugls02.ps1`
(matrix) + `rtl-dom-ugls02.ps1` (UTF-8 DOM) — all require an
unsandboxed shell (node + browser + sockets).

## DOM assertions (all PASS)

| Page (?locale=) | lang | dir | native script | `[key]` markers | IDs verbatim |
| --------------- | ---- | --- | ------------- | --------------- | ------------ |
| demo (ar) | ar | rtl | yes | 0 | yes |
| investigations/inv_84721 (ar) | ar | rtl | yes | 0 | yes |
| network/txn_84721 (ar) | ar | rtl | yes | 0 | yes |
| cases/case_84721 (ar) | ar | rtl | yes | 0 | yes |
| cases/case_84721/audit (ar) | ar | rtl | yes | 0 | yes |
| replay/scn_primary (ar) | ar | rtl | yes | 0 | yes |
| demo (ha-Arab) | ha-Arab | rtl | yes (Ajami name + Hausa/English mix) | 0 | yes |
| demo (fr) | fr | ltr | n/a (Latin) | 0 | yes |

Authoritative risk values verified verbatim in-DOM (aria-labels, immune
to count-up animation): `المخاطر 84 من 100، HIGH` on investigation and
case pages; `35/100 MODERATE` transaction scope; 39/39 evidence items
with verbatim IDs; audit table with verbatim event IDs, actor
`system/demo-reset`, and ISO `datetime` attributes.

## Visual verification (all reviewed, PASS)

- Landing (ar, 1440/768/390): hero, journey strip in RTL reading
  order, capability cards, region panel, CTA, audio controls,
  reduced-motion/mute controls, globe + orbital canvas. No overflow.
- Demo (ar, 1440/390): shell chrome, sidebar (right side), system
  status, exec KPIs, AI brief, network preview. Data loads.
- Investigation (ar, 1440/390): breadcrumbs, tabs, amount `₦480,000`,
  risk badge, 8 triggered rules with verbatim evidence refs.
- Network (ar): orbital graph (22 nodes / 30 edges), filters, legend,
  view controls. Canvas coordinates unaffected by RTL (correct).
- Case (ar): tabs, AI assessment, decision form (Arabic labels,
  verbatim English option values = server data), audit section.
- Audit (ar): table with RTL-first column order, plural
  `حدث تدقيق واحد.`, verbatim row data.
- Replay (ar): reset card, deterministic controls, simulation baseline
  `HIGH 84/100`, edge checkboxes.
- ha-Arab: RTL layout + Hausa draft chrome + English fallback, no
  markers, no breakage — partial-locale mixing proven visually.
- fr desktop: full French demo, no overflow, no markers.

## Findings fixed in-programme

1. **Open-demo CORS rejected every browser fetch (FAIL → PASS).**
   `credentials:"include"` (needed for armed cookie auth) + backend
   `allow_credentials=False` in open mode = browser blocks all
   responses (`BACKEND_UNREACHABLE` on every data section). Fix:
   `app/config.py` sets `allow_credentials=True` in both modes
   (explicit origin allowlist unchanged — no wildcard). Regression
   tests in `tests/test_cors.py` (incl. socket-free ACA-C header
   assertion). Verified: live `access-control-allow-credentials: true`
   + data rendering in all screenshots.
2. **ISO timestamps scrambled in RTL sentences (FAIL → PASS).**
   `2026-10-28T20:32:15.829Z` rendered as `29T20:32:15.82528OZ-10-2026`
   in Arabic prose (bidi runs over T/Z/milllis). Fix: six templates
   split so ISO values render inside `<bdi>` (case updated/decidedBy,
   investigation overview, intel observed ×2, graph valid ×2, system
   checked) + `<bdi>` wraps on timeline/notification/activity
   timestamps. English textContent byte-identical (existing pins hold).
   Regression test: case page pins BDI parent + exact sentence.
   Rebuilt + re-screenshotted: timestamp intact.
3. **Screenshot-number artifacts (explained, not defects).**
   Animated counters (`useCountUp`) freeze mid-flight under
   virtual-time screenshots (66/70/80, 25/26/29). Authoritative values
   confirmed via aria-labels/DOM + unchanged `data/state.json`
   (BA1D4DB4…3790FE, 101417 B before/after).
4. **`?locale=` persistence + override proven by accident (PASS).**
   Sequential runs shared one profile: `?locale=fr` overrode stored
   `ha-Arab` (explicit param wins); the param-less final run rendered
   stored `fr` (preference survives navigation). Unit tests cover the
   storage/browser-detect/reset paths.

## Known limitations (not fixed — out of scope, pre-existing)

- **390px app-shell horizontal clip (PARTIAL, pre-existing).**
  English mobile controls (`demo-en-mob`, `inv-en-mob`) clip
  identically to Arabic: header row + content overflow at 390px in
  BOTH directions. Not RTL-introduced; responsive-layout ownership
  (Phase 7 area). Documented, not modified.
- **`storage_backend` mid-word wrap** in the narrow status column
  (all locales, cosmetic, pre-existing).
- Console-error and network-failure capture: headless CLI runs
  surface renderer errors only via stderr (only benign Edge
  task-manager noise observed); no in-page JS errors occurred (all
  pages rendered data). Full DevTools-protocol console/network
  capture was unavailable (no automation library) — marked PARTIAL
  in the zero-gap matrix.
- Authenticated-session locale check NOT performed (QA ran in
  open-demo mode; locale persists in localStorage independent of the
  session cookie by construction — unit-tested).
