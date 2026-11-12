"""Universal fraud typology registry (UFI section 08).

40 detection hypotheses mapped to the real detector families
(app/detection.py FAMILIES) and versioned engine rules (R-001..R-008).
Typologies with no covering family/rule carry detection_gap=true: they are
documented hypotheses awaiting detector work, never silent claims.
Industry relevance reuses canonical industry ids plus existing PROFILE
risk_taxonomy codes where a pilot module defines them.
"""
from __future__ import annotations

from typing import Any

from app import detection as _detection

RULE_IDS = ("R-001", "R-002", "R-003", "R-004",
            "R-005", "R-006", "R-007", "R-008")


def _typo(ident: str, label: str, families: tuple[str, ...] = (),
          rules: tuple[str, ...] = (),
          industries: tuple[str, ...] = ("banking",),
          industry_codes: tuple[str, ...] = ()) -> dict[str, Any]:
    unknown_fam = [f for f in families if f not in _detection.FAMILIES]
    unknown_rules = [r for r in rules if r not in RULE_IDS]
    return {
        "typology_id": ident, "label": label,
        "detector_families": list(families), "engine_rules": list(rules),
        "industries": list(industries),
        "industry_taxonomy_codes": list(industry_codes),
        "detection_gap": not families and not rules,
        "mapping_errors": (
            ["unknown family %s" % f for f in unknown_fam]
            + ["unknown rule %s" % r for r in unknown_rules]
        ),
    }


TYPOLOGIES: tuple[dict[str, Any], ...] = (
    _typo("T-01", "Unusual transaction velocity", ("VELOCITY",), ("R-002",),
          ("banking", "fintech-payments"), ("BNK-VEL",)),
    _typo("T-02", "Transaction splitting", ("VELOCITY",), ("R-002",),
          ("banking", "fx-remittance"), ("FX-SPLIT",)),
    _typo("T-03", "Potential structuring", ("VELOCITY",), ("R-002",),
          ("banking", "government"), ("BNK-VEL",)),
    _typo("T-04", "Rapid movement of funds", ("VELOCITY",), ("R-007",),
          ("banking", "fintech-payments"), ("BNK-CASHOUT", "FX-CASCADE")),
    _typo("T-05", "Multiple-hop transfers", ("GRAPH_PATTERN",), ("R-007",)),
    _typo("T-06", "Circular transaction patterns", ("GRAPH_PATTERN",), (),
          ("banking", "capital-markets")),
    _typo("T-07", "Potential layering", ("GRAPH_PATTERN",), ("R-007",),
          ("banking",)),
    _typo("T-08", "Mule-account indicators", ("BENEFICIARY_CLUSTER",),
          ("R-006",), ("banking",), ("BNK-MULE",)),
    _typo("T-09", "Account takeover", ("DEVICE_REUSE", "GEOGRAPHIC_ANOMALY"),
          ("R-003",), ("banking", "fintech-payments", "telecom")),
    _typo("T-10", "New beneficiary anomalies", ("BENEFICIARY_CLUSTER",),
          ("R-005",), ("banking",)),
    _typo("T-11", "Dormant-account reactivation", (), (),
          ("banking", "insurance-pensions")),
    _typo("T-12", "Cross-border anomalies", ("GEOGRAPHIC_ANOMALY",), (),
          ("fx-remittance", "banking")),
    _typo("T-13", "Unusual geographic patterns", ("GEOGRAPHIC_ANOMALY",), (),
          ("banking", "ecommerce")),
    _typo("T-14", "Device-reuse anomalies", ("DEVICE_REUSE",), ("R-003",),
          ("banking", "fintech-payments"), ("BNK-RING", "FX-RING")),
    _typo("T-15", "Shared merchant patterns", ("SHARED_MERCHANT",), ("R-008",),
          ("ecommerce", "retail"), ("BNK-MERCH",)),
    _typo("T-16", "Unusual payment-channel switching",
          ("CROSS_CHANNEL_PATTERN",), (), ("banking", "fintech-payments")),
    _typo("T-17", "Refund abuse", ("RULE_MATCH",), (), ("ecommerce", "retail")),
    _typo("T-18", "Chargeback abuse", ("RULE_MATCH",), (), ("ecommerce",)),
    _typo("T-19", "Repeated declined transactions", ("RULE_MATCH",), (),
          ("banking", "ecommerce")),
    _typo("T-20", "Suspicious merchant concentration",
          ("SHARED_MERCHANT",), ("R-008",), ("ecommerce",)),
    _typo("T-21", "Beneficiary clustering", ("BENEFICIARY_CLUSTER",),
          ("R-005",), ("banking", "government"), ("BNK-MERCH",)),
    _typo("T-22", "Account-to-account relationship anomalies",
          ("GRAPH_PATTERN", "NETWORK_PROXIMITY"), ("R-006",), ("banking",)),
    _typo("T-23", "Payment splitting across instruments", ("VELOCITY",), (),
          ("fintech-payments",)),
    _typo("T-24", "Unusual cash-in/cash-out", ("RULE_MATCH",), ("R-007",),
          ("banking", "fintech-payments"), ("BNK-CASHOUT",)),
    _typo("T-25", "Suspicious gift-card redemption", (), (),
          ("retail", "ecommerce")),
    _typo("T-26", "Crypto-to-fiat conversion patterns", (), (),
          ("crypto-assets", "banking")),
    _typo("T-27", "Suspicious exchange withdrawal patterns", (), (),
          ("crypto-assets",)),
    _typo("T-28", "Unusual transaction timing", ("ML_ANOMALY",), (),
          ("banking",)),
    _typo("T-29", "Unusual account balance movements", ("ML_ANOMALY",), (),
          ("banking", "insurance-pensions")),
    _typo("T-30", "Synthetic identity indicators", (), (), ("fintech-payments",)),
    _typo("T-31", "Unusual identity changes", (), (), ("banking",)),
    _typo("T-32", "Unusual SIM-swap and device changes",
          ("DEVICE_REUSE", "PHONE_REUSE"), ("R-003", "R-004"),
          ("telecom", "banking")),
    _typo("T-33", "Transaction and login geography discrepancies",
          ("GEOGRAPHIC_ANOMALY",), (), ("banking", "fintech-payments")),
    _typo("T-34", "Suspicious intermediary patterns",
          ("NETWORK_PROXIMITY",), (), ("banking", "import-export")),
    _typo("T-35", "Suspicious merchant-agent relationships",
          ("SHARED_MERCHANT", "NETWORK_PROXIMITY"), (), ("retail",)),
    _typo("T-36", "Repeated transaction reference anomalies",
          ("RULE_MATCH",), (), ("banking",)),
    _typo("T-37", "Unauthorized payment indicators", ("RULE_MATCH",), (),
          ("banking", "fintech-payments")),
    _typo("T-38", "Unusual beneficiary changes",
          ("BENEFICIARY_CLUSTER",), ("R-005",), ("banking",)),
    _typo("T-39", "Cross-channel transaction anomalies",
          ("CROSS_CHANNEL_PATTERN",), (), ("banking", "fintech-payments")),
    _typo("T-40", "Industry-specific typologies", ("RULE_MATCH",), (),
          ("banking",)),
)

_BY_ID = {t["typology_id"]: t for t in TYPOLOGIES}


def list_typologies(industry: str | None = None) -> list[dict[str, Any]]:
    rows = [dict(t) for t in TYPOLOGIES]
    if industry:
        rows = [t for t in rows if industry in t["industries"]]
    return rows


def get_typology(typology_id: str) -> dict[str, Any] | None:
    found = _BY_ID.get(typology_id)
    return dict(found) if found else None


def signals_for_typology(typology_id: str,
                         signals: list[dict[str, Any]]) -> list[dict]:
    """Filter real signals to those evidencing a typology. Gap typologies
    (no family/rule mapping) honestly match nothing."""
    typo = _BY_ID.get(typology_id)
    if not typo or typo["detection_gap"]:
        return []
    families = set(typo["detector_families"])
    rules = set(typo["engine_rules"])
    matched = []
    for sig in signals:
        fam = sig.get("detector_family") or sig.get("family")
        detail = str(sig.get("detail", ""))
        if fam in families or any(r in detail for r in rules):
            matched.append(sig)
    return matched
