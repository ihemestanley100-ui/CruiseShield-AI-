"""Payment scheme rules registry (recovery directive section 4).

Versioned, per-scheme rules with explicit verification status. Two
seed classes:

- STRUCTURAL rules (VERIFIED): architectural facts already
  established by the platform taxonomy (on-chain irreversibility,
  cash-leg breaks). Sourced to the taxonomy, not to scheme law.
- SCHEME templates (NOT_VERIFIED): field-complete rule shells for
  bank/card/mobile-money/wallet/remittance/gift rails whose windows,
  deadlines, and sources REQUIRE legal verification (D-058) before
  any eligibility decision may rely on them.

No generic global deadline exists anywhere in this module. Admins
register verified rules (with source + dates) through the API; the
seed templates can never silently become verified.
"""
from __future__ import annotations

from typing import Any

STATUSES = ("VERIFIED", "NOT_VERIFIED", "EXPIRED", "SUPERSEDED")

FIELDS = (
    "rule_id", "version", "scheme", "country", "jurisdiction",
    "provider", "transaction_type", "reason", "conditions",
    "window_days", "evidence_required", "requester_role",
    "receiver_role", "actions", "response_deadline_days",
    "rule_source", "published_at", "effective_at", "expires_at",
    "superseded_by", "verification_status",
)


def _rule(rule_id: str, scheme: str, transaction_type: str,
          reason: str, verification_status: str,
          conditions: tuple[str, ...] = (),
          window_days: int | None = None,
          evidence_required: tuple[str, ...] = (),
          actions: tuple[str, ...] = (),
          response_deadline_days: int | None = None,
          rule_source: str = "", country: str = "",
          jurisdiction: str = "", provider: str = "",
          version: str = "1.0") -> dict[str, Any]:
    return {
        "rule_id": rule_id, "version": version, "scheme": scheme,
        "country": country, "jurisdiction": jurisdiction,
        "provider": provider, "transaction_type": transaction_type,
        "reason": reason, "conditions": list(conditions),
        "window_days": window_days,
        "evidence_required": list(evidence_required),
        "requester_role": "originating-institution",
        "receiver_role": "receiving-institution",
        "actions": list(actions),
        "response_deadline_days": response_deadline_days,
        "rule_source": rule_source, "published_at": None,
        "effective_at": None, "expires_at": None,
        "superseded_by": None,
        "verification_status": verification_status,
    }


SEED: tuple[dict[str, Any], ...] = (
    _rule("STRUCT-CRYPTO-001", "on-chain-crypto", "crypto_onchain",
          "any", "VERIFIED",
          conditions=("transfer is confirmed on-chain",),
          actions=("trace-only",),
          rule_source="platform-taxonomy: crypto legs irreversible"),
    _rule("STRUCT-CASH-001", "physical-cash", "cash",
          "any", "VERIFIED",
          conditions=("value moved as physical cash",),
          actions=("investigate-only",),
          rule_source="platform-taxonomy: cash breaks tracing"),
    _rule("TMPL-BANK-001", "bank-rail", "bank_transfer",
          "unauthorized", "NOT_VERIFIED",
          conditions=("rule text verified by counsel",),
          evidence_required=("transaction-record", "fraud-report"),
          actions=("recall-request",)),
    _rule("TMPL-BANK-002", "bank-rail", "nip_instant",
          "erroneous", "NOT_VERIFIED",
          conditions=("rule text verified by counsel",),
          evidence_required=("transaction-record",
                              "beneficiary-details"),
          actions=("recall-request",)),
    _rule("TMPL-CARD-001", "card-scheme", "card_present",
          "unauthorized", "NOT_VERIFIED",
          conditions=("rule text verified by counsel",),
          evidence_required=("transaction-record",
                              "cardholder-statement"),
          actions=("dispute",)),
    _rule("TMPL-CARD-002", "card-scheme", "card_not_present",
          "unauthorized", "NOT_VERIFIED",
          conditions=("rule text verified by counsel",),
          evidence_required=("transaction-record",
                              "cardholder-statement"),
          actions=("dispute",)),
    _rule("TMPL-MM-001", "mobile-money", "mobile_money",
          "erroneous", "NOT_VERIFIED",
          conditions=("rule text verified by counsel",),
          evidence_required=("transaction-record",),
          actions=("reversal-request",)),
    _rule("TMPL-WALLET-001", "digital-wallet", "mobile_wallet",
          "unauthorized", "NOT_VERIFIED",
          conditions=("rule text verified by counsel",),
          evidence_required=("transaction-record",),
          actions=("dispute",)),
    _rule("TMPL-REMIT-001", "remittance", "remittance",
          "erroneous", "NOT_VERIFIED",
          conditions=("rule text verified by counsel",
                      "payout not completed"),
          evidence_required=("transaction-record",
                              "transfer-reference"),
          actions=("cancellation",)),
    _rule("TMPL-GIFT-001", "gift-card", "gift_card",
          "unauthorized", "NOT_VERIFIED",
          conditions=("rule text verified by counsel",),
          evidence_required=("transaction-record",
                              "issuer-reference"),
          actions=("issuer-request",)),
)


def seed_rules() -> list[dict[str, Any]]:
    return [dict(r) for r in SEED]


def all_rules(store: Any) -> list[dict[str, Any]]:
    """Seed + admin-registered rules (registered override by id)."""
    rules = {r["rule_id"]: dict(r) for r in SEED}
    for record in store.state.get("recovery_rules", []):
        if isinstance(record, dict) and record.get("rule_id"):
            rules[record["rule_id"]] = dict(record)
    return list(rules.values())


def get_rule(store: Any, rule_id: str) -> dict[str, Any] | None:
    for rule in all_rules(store):
        if rule["rule_id"] == rule_id:
            return rule
    return None


def register(store: Any, rule: dict[str, Any]) -> dict[str, Any]:
    """Register an admin-supplied rule. Templates can never flip to
    VERIFIED by edit: verification requires source + dates + version
    bump, and seed ids are immutable."""
    missing = [f for f in FIELDS if f not in rule]
    if missing:
        raise ValueError("RULE_FIELDS_MISSING: %s" % ",".join(missing))
    if rule.get("rule_id") in {r["rule_id"] for r in SEED}:
        raise ValueError("RULE_SEED_IMMUTABLE")
    if rule.get("verification_status") == "VERIFIED":
        if not rule.get("rule_source") or not rule.get(
                "effective_at") or rule.get("window_days") is None:
            raise ValueError("RULE_VERIFY_NEEDS_SOURCE_WINDOW_DATES")
    if rule.get("verification_status") not in STATUSES:
        raise ValueError("RULE_STATUS_UNKNOWN")
    rows = store.state.setdefault("recovery_rules", [])
    rows[:] = [r for r in rows
               if not isinstance(r, dict)
               or r.get("rule_id") != rule["rule_id"]]
    rows.append(dict(rule))
    store._save()
    return dict(rule)


def match(store: Any, method_id: str,
          reason: str) -> list[dict[str, Any]]:
    """Candidate rules for a method + reason (any status)."""
    return [r for r in all_rules(store)
            if r["transaction_type"] == method_id
            and r["reason"] in (reason, "any")]
