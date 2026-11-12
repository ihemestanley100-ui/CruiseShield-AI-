# CRUISE ORBIT — Evidence Provenance Specification

Date: 2026-11-03 · Design (not implemented).

Every intelligence item carries (required fields, validated):

- `source`: provider name + dataset/collection.
- `observed_at`: provider's observation time (UTC).
- `retrieved_at`: our fetch time (UTC).
- `location`: lat/lon + validity + accuracy radius where known.
- `confidence`: high/medium/low/none/unknown (provider +
  system assessment, both shown when they differ).
- `freshness`: fresh/stale/expired per ORBIT-15 windows.
- `license`: license id + attribution text + link-out.
- `limitations`: free-text (cloud cover, coastal-only AIS,
  TLE age, resolution) — MANDATORY, never empty.
- `synthetic`: boolean + namespace.

Chain: provider payload hash → observation record → case link
→ audit entry (append-only). Package export reuses the
evidence-package hash chain. Missing/stale feeds render as
such with last-good timestamps — never as live, never hidden.
