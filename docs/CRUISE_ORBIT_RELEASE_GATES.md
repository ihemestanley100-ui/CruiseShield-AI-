# CRUISE ORBIT — Release Gate Register

Date: 2026-11-03 · All gates CLOSED. Each needs explicit owner
approval with the named scope; opening one never opens another.

| Gate | Scope | Prerequisites | Status |
|---|---|---|---|
| O-DESIGN | This 12-doc architecture | Audit complete | READY FOR REVIEW (this pack) |
| O-ACCOUNT | Provider accounts/keys (CDSE/USGS/AISStream) | Owner creates; quotas recorded | BLOCKED (owner action) |
| O-BUILD-P1 | Gateway+core+freshness+CelesTrak+overview UI | O-DESIGN approved; tests green; secret-scan clean | BLOCKED |
| O-BUILD-P2 | CDSE/USGS imagery metadata + AIS | P1 green + O-ACCOUNT for those providers | BLOCKED |
| O-BUILD-P3 | Links/alerts/correlation + full UI | P2 green | BLOCKED |
| O-LIVE | Live verification per provider (7-step plan) | Relevant build green + quota math | BLOCKED |
| O-SPEND | Any paid data (if ever) | Separate budget approval naming amount | BLOCKED (forbidden under $0) |
| O-RELEASE | Public orbit claims + demo | O-LIVE evidence for every claimed feed; score-immutability test green; 84-feature regression green | BLOCKED |

Standing rules: additive-only (84 features preserved); risk
scores immutable (release-blocking test); synthetic/real
separation enforced; no live claim without captured evidence;
no new map CDN without CSP+privacy review.
