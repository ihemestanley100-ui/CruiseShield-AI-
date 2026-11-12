# CruiseShield AI Agent OS™ — Implementation Record

**Status:** Deterministic orchestration slice implemented in worktree
(uncommitted). Backend verified; frontend written, execution pending
hosted CI (sandbox node EPERM). No model provider configured —
degraded mode is explicit, never fabricated.

## 1. Reuse (no duplication)

| Directive asks | Canonical reuse |
|---|---|
| Agent runtime | `app/agents.py` kernel (propose/approve/execute, ABAC, audit) |
| Intel tools | `app/intel_tools.py` extended (+2 = 13 tools) |
| Model gateway | `app/ai_gateway.py` + `app/ai_adapter.py` untouched |
| Cases/evidence | `app/cases.py`, evidence packages, reports |
| Tenancy/audit | `app/tenancy.py`, `append_audit`, hash chain |
| Industries | registry + profiles + `industry_adapters.py` |
| Detection/graph | `detection.py`, `graph.py`, `monitoring.py` |

## 2. New modules

- `app/orchestration.py` — lifecycle RECEIVED→…→COMPLETED/PARTIAL/
  FAILED/APPROVAL_REQUIRED; rule-based intent classification (8
  intents); manifest pipelines (depth ≤ 2); budgets (8 tool calls);
  persisted execution traces; resume-after-approval.
- `app/nl_search.py` — deterministic NL→structured transaction
  search (amounts/currency/dates/channels/refs); clarification on
  ambiguity; validated explanation; no generated SQL.
- `app/agent_retrieval.py` — tenant-isolated hybrid retrieval with
  attribution + freshness; embedding adapter UNCONFIGURED (honest).
- `app/conversations.py` — org/user-scoped threads, redaction,
  90-day retention + purge.
- Store: `agent_exec_*`, `conversation_*`. Routes: 11
  (`/api/v1/agent-os/*`, `/api/v1/conversations*`,
  `/api/v1/industries/{id}/agent-config`).
- UI: `AssistantShell` (one reusable shell, context props) on the
  investigation page + 3 vitest cases (TESTING).

## 3. A01–A20 registry mapping (shared runtime, no 20 apps)

A01→case-assistant, A02→txn-intel, A03→fraud-detection,
A04→graph-investigator+trace.read, A05→txn-intel+parties,
A06→report.build+identity sections, A07→intel-panels+device tools,
A08→telecom-section+summary, A09→geointel-map+map payloads,
A10→graph-investigator, A11→AssistantShell+case-assistant,
A12→evidence-analyst, A13→report.build agents, A14→industry-intel,
A15→compliance-research, A16→data-quality/ops-reliability,
A17→org admin routes (no agent writes), A18→security-monitor,
A19→why-risk + typology matches, A20→orchestrator VALIDATING +
contract tests. Roles are configuration over 12 runtime manifests;
no role claims a live model.

## 4. Approvals + writes

Only two write tools exist (`case.create` + kernel-executed plans),
granted solely to requires_approval manifests; every write executes
via the human approve flow (admin/manage). Reads never mutate.
Approval binds exact plan + args; expiry forces re-proposal.

## 5. Threat model (AI-specific)

- Prompt injection: NL parser is rule-based (no instruction-following
  model in-tree); retrieved content quoted as data, never executed.
- Cross-tenant leakage: every tool + retrieval + conversation path
  enforces tenant scope; tests prove cross-tenant denial.
- Tool misuse: kernel allowlists per manifest; schemas validated;
  unknown args rejected; write tools approval-gated.
- Autonomy: budgets (calls/depth), no self-modification, no direct
  DB access, middleware + ABAC on every route.
- Secrets: conversations redacted; runs store outputs of read tools
  only (masked accounts); no keys in code/logs.
- Model compromise: N/A in-tree (no provider configured); gateway
  treats responses as untrusted when a provider lands (UFI-AIMODEL).

## 6. Degraded mode

No embedding provider, no model provider: retrieval serves
keyword/structured with UNAVAILABLE vector state; orchestrator is
fully deterministic; NL search never claims model understanding.
Model-backed generation stays NOT_STARTED (UFI-AIMODEL, D-054).

## 7. Verification

- `tests/test_agent_os.py` (18) + `tests/test_agent_os_routes.py`
  (9): lifecycle, intents, budgets, NL parse/execute, retrieval
  isolation, conversation redaction/scope/purge, configs, tools.
- Contract parity extended (assistant shell imports + paths).
- Registry count updated 11→13 tools (deliberate extension).
- Full suite + matrix check before close.
