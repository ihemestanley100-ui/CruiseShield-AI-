"""Versioned deterministic rules and risk scoring.

Score function risk-score-v1: score = min(100, BASE + sum(weights of
triggered rules in scope)). Transaction scope uses R-001/R-002 only;
network scope uses all rules.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.graph import features_for_transaction
from app.models import RuleDefinition, RuleResult

SCORE_VERSION = "risk-score-v1"
BASE_SCORE = 12

RULES: list[RuleDefinition] = [
    RuleDefinition(rule_id="R-001", rule_version="1.0",
                   description="Single transfer at or above NGN 400,000.",
                   threshold="amount_minor >= 40000000", severity="high", weight=15),
    RuleDefinition(rule_id="R-002", rule_version="1.0",
                   description="Sender issued 2+ transfers within a 120-minute window.",
                   threshold="sender_outgoing_120m >= 2", severity="medium", weight=8),
    RuleDefinition(rule_id="R-003", rule_version="1.0",
                   description="One device shared by 2+ accounts.",
                   threshold="device_sharing_max >= 2", severity="high", weight=12),
    RuleDefinition(rule_id="R-004", rule_version="1.0",
                   description="One phone shared by 2+ accounts.",
                   threshold="phone_sharing_max >= 2", severity="medium", weight=10),
    RuleDefinition(rule_id="R-005", rule_version="1.0",
                   description="One beneficiary linked to 2+ accounts.",
                   threshold="beneficiary_links_max >= 2", severity="medium", weight=8),
    RuleDefinition(rule_id="R-006", rule_version="1.0",
                   description="Receiver has 3+ distinct incoming senders (fan-in).",
                   threshold="fan_in_distinct_senders >= 3", severity="medium", weight=8),
    RuleDefinition(rule_id="R-007", rule_version="1.0",
                   description="Sender pays 2+ distinct receivers (fan-out).",
                   threshold="fan_out_distinct_receivers >= 2", severity="low", weight=6),
    RuleDefinition(rule_id="R-008", rule_version="1.0",
                   description="One merchant paid by 2+ distinct accounts.",
                   threshold="merchant_sharing_max >= 2", severity="low", weight=5),
]

TRANSACTION_RULES = {"R-001", "R-002"}
NETWORK_RULES = {rule.rule_id for rule in RULES}

BANDS = [(29, "LOW"), (59, "MODERATE"), (84, "HIGH"), (100, "CRITICAL")]

LIMITATIONS = ("Deterministic demo risk score from versioned rules over "
               "synthetic data. A risk signal is not proof of criminal intent.")


def band_for(score: int) -> str:
    for ceiling, band in BANDS:
        if score <= ceiling:
            return band
    return "CRITICAL"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def evaluate(txn_id: str, transactions: list[dict], edges: list[dict],
             trace_id: str) -> list[RuleResult]:
    txn = next(t for t in transactions if t["transaction_id"] == txn_id)
    num = txn_id.split("_")[-1]
    feats = features_for_transaction(txn, transactions, edges)
    checks = {
        "R-001": (feats["amount_minor"] >= 40000000,
                  {"amount_minor": feats["amount_minor"]},
                  f"Observed {feats['amount_minor']} kobo vs threshold 40000000 kobo."),
        "R-002": (feats["sender_outgoing_120m"] >= 2,
                  {"sender_outgoing_120m": feats["sender_outgoing_120m"]},
                  f"Sender {txn['sender_account_id']} issued "
                  f"{feats['sender_outgoing_120m']} transfers within 120 minutes "
                  f"(threshold 2)."),
        "R-003": (feats["device_sharing_max"] >= 2,
                  {"device_sharing_max": feats["device_sharing_max"],
                   "device_sharing": feats["device_sharing"]},
                  f"Max device sharing is {feats['device_sharing_max']} accounts "
                  f"(threshold 2)."),
        "R-004": (feats["phone_sharing_max"] >= 2,
                  {"phone_sharing_max": feats["phone_sharing_max"],
                   "phone_sharing": feats["phone_sharing"]},
                  f"Max phone sharing is {feats['phone_sharing_max']} accounts "
                  f"(threshold 2)."),
        "R-005": (feats["beneficiary_links_max"] >= 2,
                  {"beneficiary_links_max": feats["beneficiary_links_max"],
                   "beneficiary_links": feats["beneficiary_links"]},
                  f"Max beneficiary linkage is {feats['beneficiary_links_max']} "
                  f"accounts (threshold 2)."),
        "R-006": (feats["fan_in_distinct_senders"] >= 3,
                  {"fan_in_distinct_senders": feats["fan_in_distinct_senders"],
                   "fan_in_senders": feats["fan_in_senders"]},
                  f"Receiver {txn['receiver_account_id']} has "
                  f"{feats['fan_in_distinct_senders']} distinct senders (threshold 3)."),
        "R-007": (feats["fan_out_distinct_receivers"] >= 2,
                  {"fan_out_distinct_receivers": feats["fan_out_distinct_receivers"],
                   "fan_out_receivers": feats["fan_out_receivers"]},
                  f"Sender {txn['sender_account_id']} pays "
                  f"{feats['fan_out_distinct_receivers']} distinct receivers "
                  f"(threshold 2)."),
        "R-008": (feats["merchant_sharing_max"] >= 2,
                  {"merchant_sharing_max": feats["merchant_sharing_max"],
                   "merchant_sharing": feats["merchant_sharing"]},
                  f"Max merchant sharing is {feats['merchant_sharing_max']} accounts "
                  f"(threshold 2)."),
    }
    results: list[RuleResult] = []
    for rule in RULES:
        triggered, observed, explanation = checks[rule.rule_id]
        results.append(RuleResult(
            rule_result_id=f"rr_{rule.rule_id}_{num}", rule_id=rule.rule_id,
            rule_version=rule.rule_version, triggered=triggered,
            observed_values=observed, threshold=rule.threshold,
            explanation=explanation,
            source_record_ids=[txn_id],
            evidence_ids=[f"evidence_rr_{rule.rule_id}_{num}"],
            trace_id=trace_id,
        ))
    return results


def assess(txn_id: str, scope: str, transactions: list[dict],
           edges: list[dict], rule_results: list[RuleResult],
           trace_id: str) -> dict:
    if scope == "transaction":
        wanted = TRANSACTION_RULES
    elif scope == "network":
        wanted = NETWORK_RULES
    else:
        raise ValueError(f"UNKNOWN_SCOPE: {scope}")
    by_id = {rule.rule_id: rule for rule in RULES}
    score = BASE_SCORE
    contributions, result_ids, evidence_ids = [], [], []
    for result in rule_results:
        if result.rule_id not in wanted:
            continue
        weight = by_id[result.rule_id].weight
        contributions.append({"rule_id": result.rule_id, "weight": weight,
                              "triggered": result.triggered})
        result_ids.append(result.rule_result_id)
        evidence_ids.extend(result.evidence_ids)
        if result.triggered:
            score += weight
    score = min(100, score)
    num = txn_id.split("_")[-1]
    return {
        "risk_assessment_id": f"risk_{scope}_{num}", "target_id": txn_id,
        "target_type": "transaction" if scope == "transaction" else "network",
        "score": score, "band": band_for(score), "score_version": SCORE_VERSION,
        "contributions": contributions, "rule_results": result_ids,
        "evidence_ids": sorted(set(evidence_ids)), "computed_at": _now(),
        "trace_id": trace_id, "limitations": LIMITATIONS,
    }
