# WORLD ATLAS — INTERACTION DESIGN

Date: 2026-11-03 · Spec only · Matches existing a11y/i18n bars.

## 1. Camera controls (OrbitControls profile)

Drag rotate (360° azimuth, free) · polar clamp 15°–165°
(no pole flip) · wheel zoom 2.2–12 units · pinch zoom +
two-finger drag (touch) · double-click: raycast → tween
target to point · auto-rotate 0.6×/s default ON with
visible toggle + pause/resume · reset button restores
default view · any user drag pauses auto-rotate until
resumed (user override wins).

## 2. 2D/3D switch

Segmented control "Globe | Map". Map = equirectangular
plane, same boundary data, same markers projected;
camera state (center/zoom) translated, not reset.
Preference persists per-session only.

## 3. Search + selection

Search box: country/region name → ranked matches (local
index, keyboard navigable, Enter selects, Esc clears).
Click/Enter on globe: raycast pick → info panel (name,
ISO, continent, hub status, linked overlay counts).
Non-pickable areas yield an honest "open ocean — no
boundary data" note, never a guess.

## 4. Layers + filters

Checkbox list from `GET /layers`; each row shows state
pill (LIVE green / STALE amber / PLACEHOLDER grey with
reason tooltip). Filters: date window, risk band,
kind. Marker overflow: "+N more — refine filters".
PLACEHOLDER layers are toggleable (shows the honest
empty state) — toggling never invents content.

## 5. Info panel content rules

Only: boundary identity, counts, timestamps,
provenance, licence. No invented GDP/population/stats.
Every number links to its source endpoint or is
labelled "illustrative demo".

## 6. Accessibility + responsive

Full keyboard map (arrows rotate, +/− zoom, 0 reset,
F fullscreen, ? help) · visible focus · `role`
application with describedby help · reduced-motion:
static frame + instant (non-tweened) moves ·
touch targets ≥44px · layouts 390/768/1440 verified ·
12-locale strings via existing registry (no hard-coded
English in new UI).

## 7. Honest-state language (mandatory copy)

- No data: "No observations in view — adjust filters."
- Stale: "Last updated {ts} — showing cached data."
- Placeholder: "Awaiting authorized provider — no live
  data." Demo: "Synthetic demo overlay — not real."
