"""Deterministic synthetic scenarios. No randomness; fixed IDs and timestamps.

Primary scenario: txn_84721 (NGN 480,000, acct_A -> acct_B) with a seeded
network of 12 accounts, 4 devices, 3 phones, 2 merchants, 1 beneficiary.
Every graph edge carries source-event provenance.
"""
from __future__ import annotations

import hashlib
import json

SCENARIO_VERSION = "1.0.0"
SEED_DATETIME = "2026-10-27T10:00:00Z"

# (txn_id, amount_minor_kobo, channel, sender, receiver, minute_offset, device, phone)
PRIMARY_TXNS: list[tuple] = [
    ("txn_84721", 48000000, "MOBILE_APP", "acct_A", "acct_B", 0, "dev_04", "phn_03"),
    ("txn_84722", 12000000, "TRANSFER_NIP", "acct_C", "acct_D", 6, None, None),
    ("txn_84723", 9500000, "USSD", "acct_D", "acct_E", 11, None, None),
    ("txn_84724", 22000000, "POS", "acct_G", "acct_H", 17, "dev_02", None),
    ("txn_84725", 7400000, "TRANSFER_NIP", "acct_J", "acct_K", 23, None, "phn_01"),
    ("txn_84726", 31000000, "MOBILE_APP", "acct_C", "acct_B", 29, None, None),
    ("txn_84727", 18500000, "ATM", "acct_D", "acct_B", 34, None, None),
    ("txn_84728", 26000000, "POS", "acct_A", "acct_C", 40, None, None),
    ("txn_84729", 15000000, "WEB", "acct_B", "acct_E", 47, "dev_04", "phn_03"),
    ("txn_84731", 8800000, "QR", "acct_F", "acct_I", 52, "dev_02", "phn_02"),
    ("txn_84732", 5400000, "AGENT_AGENCY", "acct_L", "acct_K", 58, "dev_03", None),
]

# (source, target, relationship, source_event_txn)
# Rule: SENT_TO edges use their own txn event; static edges use the first
# event involving either endpoint account (deterministic, documented).
PRIMARY_EDGES: list[tuple] = [
    ("acct_A", "acct_B", "SENT_TO", "txn_84721"),
    ("acct_B", "dev_04", "USES_DEVICE", "txn_84721"),
    ("acct_B", "phn_03", "USES_PHONE", "txn_84721"),
    ("acct_C", "dev_04", "USES_DEVICE", "txn_84722"),
    ("acct_D", "dev_04", "USES_DEVICE", "txn_84722"),
    ("acct_C", "acct_D", "SENT_TO", "txn_84722"),
    ("acct_D", "acct_E", "SENT_TO", "txn_84723"),
    ("acct_E", "phn_03", "USES_PHONE", "txn_84723"),
    ("acct_E", "merch_01", "PAID_MERCHANT", "txn_84723"),
    ("acct_F", "merch_01", "PAID_MERCHANT", "txn_84731"),
    ("acct_F", "dev_02", "USES_DEVICE", "txn_84731"),
    ("acct_G", "dev_02", "USES_DEVICE", "txn_84724"),
    ("acct_G", "acct_H", "SENT_TO", "txn_84724"),
    ("acct_H", "ben_01", "BENEFICIARY_OF", "txn_84724"),
    ("acct_I", "ben_01", "BENEFICIARY_OF", "txn_84731"),
    ("acct_I", "phn_01", "USES_PHONE", "txn_84731"),
    ("acct_J", "phn_01", "USES_PHONE", "txn_84725"),
    ("acct_J", "acct_K", "SENT_TO", "txn_84725"),
    ("acct_K", "merch_02", "PAID_MERCHANT", "txn_84725"),
    ("acct_L", "merch_02", "PAID_MERCHANT", "txn_84732"),
    ("acct_K", "dev_01", "USES_DEVICE", "txn_84725"),
    ("acct_L", "dev_03", "USES_DEVICE", "txn_84732"),
    ("acct_F", "phn_02", "USES_PHONE", "txn_84731"),
    ("acct_H", "phn_02", "USES_PHONE", "txn_84724"),
    ("acct_C", "acct_B", "SENT_TO", "txn_84726"),
    ("acct_D", "acct_B", "SENT_TO", "txn_84727"),
    ("acct_A", "acct_C", "SENT_TO", "txn_84728"),
    ("acct_B", "acct_E", "SENT_TO", "txn_84729"),
    ("acct_F", "acct_I", "SENT_TO", "txn_84731"),
    ("acct_L", "acct_K", "SENT_TO", "txn_84732"),
]


def _ts(minute_offset: int) -> str:
    return f"2026-10-27T10:{minute_offset:02d}:00Z"


def _node_type(node_id: str) -> str:
    if node_id.startswith("acct_"):
        return "account"
    if node_id.startswith("dev_"):
        return "device"
    if node_id.startswith("phn_"):
        return "phone"
    if node_id.startswith("merch_"):
        return "merchant"
    if node_id.startswith("ben_"):
        return "beneficiary"
    return "unknown"


def _label(node_id: str) -> str:
    prefix, _, suffix = node_id.partition("_")
    names = {"acct": "Account", "dev": "Device", "phn": "Phone",
             "merch": "Merchant", "ben": "Beneficiary", "fp": "FP Account"}
    return f"{names.get(prefix, prefix)} {suffix}"


def build_primary() -> dict:
    txns, events = [], []
    for txn_id, amount, channel, sender, receiver, mins, dev, phn in PRIMARY_TXNS:
        num = txn_id.split("_")[1]
        entities: dict[str, str | None] = {}
        if dev:
            entities["device_id"] = dev
        if phn:
            entities["phone_id"] = phn
        if txn_id == "txn_84721":
            entities["ip_id"] = "ip_02"
            entities["location_id"] = "loc_01"
        txns.append({
            "transaction_id": txn_id, "amount_minor": amount, "currency": "NGN",
            "channel": channel, "sender_account_id": sender,
            "receiver_account_id": receiver, "occurred_at": _ts(mins),
            "device_id": dev, "phone_id": phn,
            "ip_id": entities.get("ip_id"), "location_id": entities.get("location_id"),
            "merchant_id": None,
        })
        events.append({
            "event_id": f"evt_demo_{num}", "event_type": "financial.transaction.created",
            "schema_version": "1.0", "occurred_at": _ts(mins),
            "source": "synthetic_demo", "trace_id": f"trace_demo_{num}",
            "privacy_classification": "synthetic",
            "transaction": txns[-1], "entities": entities,
        })

    node_ids: list[str] = []
    for edge in PRIMARY_EDGES:
        for endpoint in (edge[0], edge[1]):
            if endpoint not in node_ids:
                node_ids.append(endpoint)
    node_ids.sort()
    nodes = [{
        "node_id": nid, "node_type": _node_type(nid), "display_label": _label(nid),
        "synthetic_flag": True, "source_record_ids": [f"seed:scn_primary:{nid}"],
    } for nid in node_ids]

    edges = []
    for i, (src, tgt, rel, txn) in enumerate(PRIMARY_EDGES, start=1):
        num = txn.split("_")[1]
        edges.append({
            "edge_id": f"edge_{i:04d}", "source_node_id": src,
            "target_node_id": tgt, "relationship_type": rel,
            "source_event_ids": [f"evt_demo_{num}"],
            "evidence_ids": [f"evidence_edge_{i:04d}"],
            "valid_from": SEED_DATETIME, "valid_to": None,
            "synthetic_flag": True, "trace_id": f"trace_demo_{num}",
        })

    return {
        "scenario_id": "scn_primary", "transactions": txns, "events": events,
        "nodes": nodes, "edges": edges,
        "primary_transaction_id": "txn_84721",
        "title": "Seeded suspicious network — Transaction #84721",
        "purpose": "Demonstrate network-level investigation of txn_84721.",
    }


def build_false_positive() -> dict:
    txn = {
        "transaction_id": "txn_84730", "amount_minor": 60000000, "currency": "NGN",
        "channel": "MOBILE_APP", "sender_account_id": "fp_acct_1",
        "receiver_account_id": "fp_acct_2", "occurred_at": _ts(5),
        "device_id": None, "phone_id": None, "ip_id": None,
        "location_id": None, "merchant_id": None,
    }
    event = {
        "event_id": "evt_demo_84730", "event_type": "financial.transaction.created",
        "schema_version": "1.0", "occurred_at": _ts(5),
        "source": "synthetic_demo", "trace_id": "trace_demo_84730",
        "privacy_classification": "synthetic", "transaction": txn, "entities": {},
    }
    nodes = [
        {"node_id": "fp_acct_1", "node_type": "account",
         "display_label": "FP Account 1", "synthetic_flag": True,
         "source_record_ids": ["seed:scn_false_positive:fp_acct_1"]},
        {"node_id": "fp_acct_2", "node_type": "account",
         "display_label": "FP Account 2", "synthetic_flag": True,
         "source_record_ids": ["seed:scn_false_positive:fp_acct_2"]},
    ]
    edges = [{
        "edge_id": "edge_fp_0001", "source_node_id": "fp_acct_1",
        "target_node_id": "fp_acct_2", "relationship_type": "SENT_TO",
        "source_event_ids": ["evt_demo_84730"],
        "evidence_ids": ["evidence_edge_fp_0001"],
        "valid_from": SEED_DATETIME, "valid_to": None,
        "synthetic_flag": True, "trace_id": "trace_demo_84730",
    }]
    return {
        "scenario_id": "scn_false_positive", "transactions": [txn],
        "events": [event], "nodes": nodes, "edges": edges,
        "primary_transaction_id": "txn_84730",
        "title": "False-positive check — large but unconnected transfer",
        "purpose": "Show an unusual transaction that lacks network evidence.",
    }


def seed_hash(scenario: dict) -> str:
    canonical = json.dumps(
        {k: scenario[k] for k in ("transactions", "events", "nodes", "edges")},
        sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def available_scenarios() -> list[dict[str, str]]:
    return [
        {"scenario_id": "scn_primary",
         "title": "Seeded suspicious network — Transaction #84721"},
        {"scenario_id": "scn_false_positive",
         "title": "False-positive check — large but unconnected transfer"},
    ]
