"""Evidence items and versioned evidence packages."""
from __future__ import annotations

import hashlib
import json

from app.models import EvidenceItem, EvidencePackage, RuleResult

EVIDENCE_VERSION = "1.0"
PACKAGE_ITEM_CAP = 100


def kobo_to_naira(amount_minor: int) -> str:
    return f"\u20a6{amount_minor / 100:,.0f}"


def build_items(txn: dict, rule_results: list[RuleResult],
                edges: list[dict], events_by_id: dict,
                trace_id: str) -> list[EvidenceItem]:
    num = txn["transaction_id"].split("_")[-1]
    items = [EvidenceItem(
        evidence_id=f"evidence_txn_{num}", evidence_type="transaction",
        title=f"Transaction #{num}: {kobo_to_naira(txn['amount_minor'])} "
              f"{txn['sender_account_id']} -> {txn['receiver_account_id']}",
        description=(f"Channel {txn['channel']} at {txn['occurred_at']}. "
                     f"Synthetic demo record."),
        source_record_ids=[txn["transaction_id"]],
        event_ids=[e for e in events_by_id
                   if events_by_id[e]["transaction"]["transaction_id"]
                   == txn["transaction_id"]],
        observed_at=txn["occurred_at"], trace_id=trace_id,
    )]
    for result in rule_results:
        items.append(EvidenceItem(
            evidence_id=result.evidence_ids[0], evidence_type="rule_result",
            title=f"Rule {result.rule_id} "
                  f"{'TRIGGERED' if result.triggered else 'not triggered'}",
            description=result.explanation,
            source_record_ids=list(result.source_record_ids),
            rule_result_ids=[result.rule_result_id],
            observed_at=txn["occurred_at"], trace_id=trace_id,
        ))
    for edge in sorted(edges, key=lambda e: e["edge_id"]):
        items.append(EvidenceItem(
            evidence_id=edge["evidence_ids"][0] if edge["evidence_ids"]
            else f"evidence_{edge['edge_id']}", evidence_type="graph_relationship",
            title=(f"{edge['source_node_id']} {edge['relationship_type']} "
                   f"{edge['target_node_id']}"),
            description=(f"Provenance: {', '.join(edge['source_event_ids'])}. "
                         f"Synthetic seeded relationship."),
            event_ids=list(edge["source_event_ids"]),
            graph_node_ids=[edge["source_node_id"], edge["target_node_id"]],
            graph_edge_ids=[edge["edge_id"]],
            observed_at=txn["occurred_at"], trace_id=trace_id,
        ))
    return items[:PACKAGE_ITEM_CAP]


def build_package(scenario_id: str, scenario_version: str, trace_id: str,
                  items: list[EvidenceItem]) -> EvidencePackage:
    ordered = sorted(items, key=lambda item: item.evidence_id)
    canonical = json.dumps([item.model_dump() for item in ordered],
                           sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return EvidencePackage(
        package_id=f"evidence_pkg_{scenario_id}_{scenario_version}",
        scenario_id=scenario_id, scenario_version=scenario_version,
        trace_id=trace_id, items=ordered, package_hash=digest,
    )


def find_unknown_ids(package: EvidencePackage, sent_ids: set[str]) -> list[str]:
    """IDs cited by a model response that were not in the submitted package."""
    return sorted({item for item in sent_ids
                   if item not in {i.evidence_id for i in package.items}})
