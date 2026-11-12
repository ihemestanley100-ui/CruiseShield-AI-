# Stage 2 Master Architecture (preparation only — no implementation)

Status: DRAFT for owner Stage-2-commencement decision. $0 policy
carries over; every workstream lists free-tier options first.

## S2-01 production-grade data infrastructure

Scope: replace ephemeral JSON with durable Postgres (Supabase
Free reserved path) using the existing loader/parity tooling.
Deps: D-018 + PKG-07 live. Components: pooled adapter, tenant
RLS-equivalent guards, migrations, retention jobs. Tests: parity
+ drill suites. $0: Supabase Free within quotas; else stay JSON.

## S2-02 advanced financial-crime detection

Scope: structuring, insider-abuse, decline-driven, identity-fraud
detectors; ML_ANOMALY only with a real model + eval harness.
Deps: S2-05 event ingestion. Controls: thresholds versioned,
explainability mandatory, false-positive budgets per typology.

## S2-03 graph intelligence

Scope: entity resolution, multi-hop tracing at scale, network
discovery, risk propagation. Builds on tracing engine + R-006/007.

## S2-04 AI investigation intelligence

Scope: case summarization, evidence correlation, explainable
recommendations — human approval mandatory (DI-08 precedent).
Deps: provider governance + cost caps; advisory-only preserved.

## S2-05 real-time intelligence integrations

Scope: event ingestion, provider governance, provenance, failure
handling. Turns typology-only mappings (T-19 etc.) into live lanes.

## S2-06 enterprise identity

Scope: federation (OIDC/SAML), MFA enforcement, privileged
access, tenant administration. Builds on AUTH-01..09 when the
owner lifts deferral; preserves current UX/flows.

## S2-07 operational resilience

Scope: free-tier monitoring (health/ready + host meters),
incident response drills (CS-OPS-003), DR via PKG-07, perf
budgets, single→pooled scaling criteria.

## S2-08 advanced assurance

Scope: independent pentest completion, O-05 verdict
disposition, compliance mapping, evidence retention policy.

## Readiness

Stage 2 entry requires: Stage 1 acceptance signed; O-05 + CI
green; D-018/PKG-07 live; F-CSG signed. Until then this document
is architecture only — no Stage 2 code authorized.
