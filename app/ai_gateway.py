"""Provider-neutral AI gateway (Phase 6, AI-02 / D-047).

Routes model tasks across registered providers with
registration, task-fit, and per-provider quota checks, fallback
across lanes, usage accounting, and prompt-version governance.
The Meta lane (app/ai_adapter.py) is registered as the first
provider; further providers join the registry without gateway
changes. Credential state is reported per candidate and orders
configured lanes first, but the lane itself is authoritative:
attempting a lane without a credential fails closed with
MODEL_NOT_CONFIGURED and falls through to the next lane, so a
missing primary credential never masks a healthy secondary.

Honest scope: routing, registry, accounting, and stats are real
and socket-free tested. A live model call still needs a
configured provider credential plus owner approval (D-016 /
PKG-04); with no credential anywhere every route fails closed
with MODEL_NOT_CONFIGURED. Usage reports tokens from stored run
records only — never currency (no prices are invented), and
empty histories report None rates rather than zeros dressed
as measurements.
"""
from __future__ import annotations

import hashlib
from typing import Any

from app import ai_adapter
from app import config as config_mod

TASKS = ("analysis", "followup")

#: Task -> provider names in preference order. Deterministic:
#: auditability beats cleverness for model routing.
ROUTES: dict[str, list[str]] = {
    "analysis": ["meta"],
    "followup": ["meta"],
}

#: Provider failures worth trying the next candidate for. Auth
#: failure and missing credentials are included (a second lane
#: carries different credentials); validation and refusal fail
#: fast — the same prompt would fail on every lane.
FALLBACK_CODES = frozenset({
    "MODEL_TIMEOUT", "MODEL_PROVIDER_UNAVAILABLE",
    "MODEL_RATE_LIMITED", "MODEL_PROVIDER_ERROR",
    "MODEL_AUTH_FAILED", "MODEL_NOT_CONFIGURED",
})


class BaseProvider:
    """Interface every lane implements (duck-typed)."""

    name = "base"

    def models(self) -> list[str]:
        raise NotImplementedError

    def tasks(self) -> tuple[str, ...]:
        return TASKS

    def configured(self) -> bool:
        raise NotImplementedError

    async def analyze(self, package: Any, summary: str,
                      trace_id: str, run_id: str,
                      timeout: int = 30,
                      transport: Any = None,
                      question: str = "",
                      prior_context: str = "") -> dict[str, Any]:
        raise NotImplementedError


class MetaProvider(BaseProvider):
    """The Meta Model API lane (delegates; no logic duplicated)."""

    name = "meta"

    def models(self) -> list[str]:
        return [config_mod.META_MODEL_ID]

    def configured(self) -> bool:
        return ai_adapter.configured()

    async def analyze(self, package: Any, summary: str,
                      trace_id: str, run_id: str,
                      timeout: int = 30,
                      transport: Any = None,
                      question: str = "",
                      prior_context: str = "") -> dict[str, Any]:
        return await ai_adapter.analyze(
            package, summary, trace_id, run_id, timeout=timeout,
            transport=transport, question=question,
            prior_context=prior_context)


_REGISTRY: dict[str, BaseProvider] = {}


def register(provider: BaseProvider) -> BaseProvider:
    """Add a provider lane. Duplicate names are rejected."""
    name = provider.name
    if not name or name in _REGISTRY:
        raise ValueError("provider name %r unavailable" % (name,))
    _REGISTRY[name] = provider
    return provider


def unregister(name: str) -> bool:
    """Remove a provider lane (tests / decommission)."""
    return _REGISTRY.pop(name, None) is not None


def providers() -> list[BaseProvider]:
    return list(_REGISTRY.values())


def get_provider(name: str) -> BaseProvider | None:
    return _REGISTRY.get(name)


register(MetaProvider())


def model_registry() -> list[dict[str, Any]]:
    """Live model catalogue: provider, model, tasks, status.

    Status is observed (credential presence), never claimed
    connectivity: "ready" or "blocked-no-credential".
    """
    entries = []
    for provider in providers():
        status = "ready" if provider.configured() \
            else "blocked-no-credential"
        for model_id in provider.models():
            entries.append({
                "provider": provider.name, "model_id": model_id,
                "tasks": list(provider.tasks()),
                "cost_tier": "metered",
                "status": status})
    return entries


def provider_calls_today(runs: list[dict[str, Any]] | None,
                         provider: str,
                         today: str | None = None) -> int:
    """Count today's run attempts for one provider (UTC)."""
    mine = [r for r in (runs or [])
            if isinstance(r, dict) and r.get("provider") == provider]
    return ai_adapter.attempts_today(mine, today)


def quota_ok(provider: str, runs: list[dict[str, Any]] | None,
             today: str | None = None) -> bool:
    """Per-provider daily quota headroom.

    AI_PROVIDER_DAILY_LIMIT 0 disables the per-provider check;
    the global AI_DAILY_CALL_LIMIT still governs every call.
    """
    limit = config_mod.AI_PROVIDER_DAILY_LIMIT
    if limit <= 0:
        return True
    return provider_calls_today(runs, provider, today) < limit


def route(task: str, runs: list[dict[str, Any]] | None,
          today: str | None = None) -> dict[str, Any]:
    """Routing decision: candidates with reasons + try order.

    Never raises: unknown tasks and empty routes select
    nothing, and run() maps that to an honest AIError. The
    "order" list is the try sequence: eligible lanes with a
    credential first (stable, so route-table preference holds
    within each group).
    """
    decision: dict[str, Any] = {
        "task": task, "candidates": [], "order": [],
        "selected": None}
    if task not in TASKS:
        decision["reason"] = "unknown-task"
        return decision
    for name in ROUTES.get(task, []):
        provider = get_provider(name)
        if provider is None:
            decision["candidates"].append(
                {"provider": name, "model": "",
                 "ok": False, "reason": "not-registered",
                 "credential": False})
            continue
        models = provider.models()
        model = models[0] if models else ""
        if task not in provider.tasks():
            decision["candidates"].append(
                {"provider": name, "model": model,
                 "ok": False, "reason": "task-unsupported",
                 "credential": provider.configured()})
        elif not quota_ok(name, runs, today):
            decision["candidates"].append(
                {"provider": name, "model": model,
                 "ok": False, "reason": "quota-exhausted",
                 "credential": provider.configured()})
        else:
            decision["candidates"].append(
                {"provider": name, "model": model,
                 "ok": True, "reason": "eligible",
                 "credential": provider.configured()})
    order = sorted(
        (c for c in decision["candidates"] if c["ok"]),
        key=lambda c: not c["credential"])
    decision["order"] = [{"provider": c["provider"],
                          "model": c["model"]} for c in order]
    if order:
        decision["selected"] = dict(decision["order"][0])
    return decision


async def run(task: str, package: Any, summary: str,
              trace_id: str, run_id: str,
              runs: list[dict[str, Any]] | None,
              timeout: int | None = None,
              transport: Any = None,
              question: str = "",
              prior_context: str = "",
              today: str | None = None) -> dict[str, Any]:
    """Route one model call with fallback; stamp the receipt.

    Tries the decision order (configured lanes first, then
    route-table preference). Fallback-code failures fall
    through to the next lane; anything else raises
    immediately. The winning run carries a "gateway" receipt
    (task/provider/model/attempts) for the audit trail.
    """
    decision = route(task, runs, today)
    if task not in TASKS:
        raise ai_adapter.AIError(
            "AI_ROUTE_UNKNOWN", "unknown model task %r" % (task,),
            detail={"route": decision})
    if not decision["order"]:
        reasons = {c["reason"] for c in decision["candidates"]}
        if reasons and reasons <= {"quota-exhausted"}:
            raise ai_adapter.AIError(
                "AI_PROVIDER_QUOTA_EXHAUSTED",
                "every provider for %r is over quota" % (task,),
                detail={"route": decision})
        raise ai_adapter.AIError(
            "AI_ROUTE_UNAVAILABLE",
            "no lane available for %r" % (task,),
            detail={"route": decision})
    seconds = config_mod.AI_TIMEOUT_SECONDS if timeout is None \
        else timeout
    attempts: list[dict[str, Any]] = []
    last: ai_adapter.AIError | None = None
    for cand in decision["order"]:
        provider = get_provider(cand["provider"])
        assert provider is not None  # ordered implies registered
        try:
            result = await provider.analyze(
                package, summary, trace_id, run_id,
                timeout=seconds, transport=transport,
                question=question, prior_context=prior_context)
        except ai_adapter.AIError as exc:
            attempts.append({"provider": cand["provider"],
                             "model": cand["model"],
                             "error": exc.code})
            last = exc
            exc.detail.setdefault("route", decision)
            if exc.code in FALLBACK_CODES:
                continue
            exc.detail.setdefault("gateway_attempts", attempts)
            raise
        attempts.append({"provider": cand["provider"],
                         "model": cand["model"], "error": ""})
        if isinstance(result, dict):
            result["gateway"] = {
                "task": task, "provider": cand["provider"],
                "model": cand["model"], "attempts": attempts}
        return result
    assert last is not None
    last.detail.setdefault("route", decision)
    last.detail.setdefault("gateway_attempts", attempts)
    raise last


def _tokens_of(run: dict[str, Any]) -> dict[str, int]:
    usage = run.get("usage")
    if not isinstance(usage, dict):
        return {"prompt_tokens": 0, "completion_tokens": 0,
                "total_tokens": 0}
    out = {}
    for key in ("prompt_tokens", "completion_tokens",
                "total_tokens"):
        value = usage.get(key, 0)
        out[key] = value if isinstance(value, int) and value >= 0 \
            else 0
    return out


def usage_totals(runs: list[dict[str, Any]] | None,
                 provider: str | None = None,
                 today: str | None = None) -> dict[str, int]:
    """Token accounting from stored runs (cost governance input).

    Malformed entries contribute zero. Currency is never
    derived here — no price table exists to derive it from.
    """
    totals = {"calls": 0, "prompt_tokens": 0,
              "completion_tokens": 0, "total_tokens": 0}
    for run in runs or []:
        if not isinstance(run, dict):
            continue
        if provider is not None and run.get("provider") != provider:
            continue
        if today is not None and \
                str(run.get("started_at", ""))[:10] != today:
            continue
        totals["calls"] += 1
        for key, value in _tokens_of(run).items():
            totals[key] += value
    return totals


def provider_stats(runs: list[dict[str, Any]] | None,
                   provider: str,
                   today: str | None = None) -> dict[str, Any]:
    """Observed-only per-provider health (empty stays empty).

    Rates are None — not 0% — when no calls exist, so an
    uncontacted provider can never read as measured-unhealthy.
    """
    mine = []
    for run in runs or []:
        if not isinstance(run, dict):
            continue
        if run.get("provider") != provider:
            continue
        if today is not None and \
                str(run.get("started_at", ""))[:10] != today:
            continue
        mine.append(run)
    latencies = [r["latency_ms"] for r in mine
                 if isinstance(r.get("latency_ms"), int)
                 and r["latency_ms"] >= 0]
    errors: dict[str, int] = {}
    succeeded = 0
    for run in mine:
        if run.get("status") == "SUCCEEDED":
            succeeded += 1
        code = run.get("error_code", "")
        if code:
            errors[str(code)] = errors.get(str(code), 0) + 1
    calls = len(mine)
    return {
        "provider": provider, "calls": calls,
        "succeeded": succeeded, "failed": calls - succeeded,
        "success_rate": (succeeded / calls) if calls else None,
        "avg_latency_ms": (sum(latencies) / len(latencies))
        if latencies else None,
        "error_codes": errors,
        "tokens": usage_totals(mine, provider)}


def prompt_registry() -> dict[str, dict[str, str]]:
    """Prompt-version governance: version -> instruction digest.

    Digests pin the exact instruction text each recorded
    prompt_version maps to; reviewers verify runs against this.
    """
    return {
        ai_adapter.PROMPT_VERSION: {
            "instruction_sha256": hashlib.sha256(
                ai_adapter.SYSTEM_INSTRUCTION.encode()).hexdigest(),
            "applies_to": "analysis"},
        ai_adapter.FOLLOWUP_PROMPT_VERSION: {
            "instruction_sha256": hashlib.sha256(
                ai_adapter.FOLLOWUP_INSTRUCTION.encode()).hexdigest(),
            "applies_to": "followup"},
    }
