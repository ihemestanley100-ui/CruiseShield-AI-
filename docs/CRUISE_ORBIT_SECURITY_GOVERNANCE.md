# CRUISE ORBIT — Security and Governance Matrix

Date: 2026-11-03 · Design (not implemented).

| Control | Design | Status |
|---|---|---|
| Permissions | New `orbit_read` (all authed roles) + `orbit_manage` (admin: provider config, alert rules); enforced in `session_guard` + per-route | MISSING |
| Credentials | `ORBIT_*` env names only; server-side; never logged/persisted/returned (mirror `MODEL_API_KEY` handling + secret-scan gate) | MISSING |
| Rate limits | Provider quotas enforced pre-call + global 600/min/IP; `Retry-After` + audited rejections | MISSING |
| Timeouts/retries | Mirror `ai_adapter`: 30 s cap, 3 attempts on transient, fail-closed codes | MISSING |
| Input validation | Bbox/coords via `validate_coordinates`; id allowlists; 1 MB bodies | MISSING |
| Score immutability | HARD INVARIANT: no orbit code path may write risk/score/decision fields — enforced by architecture (one-way links) + regression test | MISSING (gate) |
| No individual inference | UI copy + validator reject person-targeting queries; audit any attempt | MISSING |
| AI boundary | AI may summarize VERIFIED observations only; observation invention rejected by extended output validator | MISSING |
| Synthetic separation | Namespace flag on every read/write; mixed queries require explicit flag + banner | MISSING |
| Audit | Provider config changes, links, alert acks, quota rejections — all audited | MISSING |
