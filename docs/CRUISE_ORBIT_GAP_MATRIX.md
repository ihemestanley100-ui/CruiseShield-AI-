# CRUISE ORBIT — Implementation Gap Matrix

Date: 2026-11-03 · Verdict: GREENFIELD — 16/18 modules MISSING,
2 PARTIAL foundations. No code exists to preserve-or-remove;
all work is additive.

| Requirement | Status | Gap → action |
|---|---|---|
| ORBIT-01/02 core + gateway | MISSING | New `app/orbit/` package (protocols, null provider, config) |
| ORBIT-03 tracking | MISSING | `sgp4` dep + CelesTrak client + pass math + tests |
| ORBIT-04/09/10 EO + imagery explorer | MISSING | CDSE STAC/OData client (metadata-first) + USGS depth |
| ORBIT-05/16 monitoring + alerts | MISSING | Rules + alert store + ack flow + notifications hookup |
| ORBIT-06 cross-border | PARTIAL | Join layer over `geo_intel` + new observations |
| ORBIT-07 AIS | MISSING | AISStream client (free key TBD) + snapshot cache |
| ORBIT-08 ports | MISSING | Open dataset import (license-verify each) |
| ORBIT-11 geo-risk | PARTIAL | Advisory overlay + score-immutability gate |
| ORBIT-12 correlation | MISSING | Evidence-ID join + validator extension |
| ORBIT-13/14/16 links/provenance/alerts | MISSING | Extend evidence/audit/alerts (no forks) |
| ORBIT-15 freshness | MISSING | Policy engine + read-time verification |
| ORBIT-17/18 perms/observability | MISSING | 2 RBAC perms + health/quota surfacing |
| Frontend `/orbit` (7 screens) | MISSING | Route + components + i18n + tests |
| Live provider accounts | BLOCKED | CDSE + USGS + AISStream accounts are owner actions |
| Paid data (dense AIS/VHR) | BLOCKED | Out of $0 scope by design |

Phasing: P1 gateway+core+freshness+1 provider (CelesTrak, no
key) + overview UI → P2 CDSE imagery metadata + AIS →
P3 links/alerts/correlation → P4 hardening + live verification.
Each phase independently testable and shippable.
