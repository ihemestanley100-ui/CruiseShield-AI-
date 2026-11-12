"""Evidence-based fund-movement tracing (UFI section 10).

Links are built from exact shared references in transaction records plus
the investigation graph's provenanced edges. Strength ladder:

- CONFIRMED_LINK: same exact provider/supplied reference on both legs.
- PROVIDER_REPORTED_LINK: a graph edge whose provenance passes
  app/graph.validate_provenance.
- STRONGLY_SUPPORTED_LINK: exact account/wallet continuity in the same
  currency with matching direction (receiver -> sender).
- POSSIBLE_LINK: exact shared reference but currency unknown/mismatched.
- UNVERIFIED_LINK: shared weak signal (device/phone/merchant) only.
- NO_MATCH / PROVIDER_UNAVAILABLE / ACCESS_RESTRICTED as labelled.

Cash legs end deterministic tracing. The engine never freezes, reverses,
or recovers funds; it only reports evidenced movements and limitations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app import graph as _graph

STATUSES = (
    "CONFIRMED_LINK", "PROVIDER_REPORTED_LINK", "STRONGLY_SUPPORTED_LINK",
    "POSSIBLE_LINK", "UNVERIFIED_LINK", "NO_MATCH",
    "PROVIDER_UNAVAILABLE", "ACCESS_RESTRICTED",
)

_WEAK = ("device_id", "phone_id", "merchant_id", "ip_id")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def related_investigations(trace: dict[str, Any],
                           investigations: list[dict[str, Any]]
                           ) -> list[str]:
    """Investigation ids whose transaction the trace visited (derived)."""
    visited = set(trace.get("visited_transactions", []) or [])
    return sorted(i.get("investigation_id") for i in investigations
                  if isinstance(i, dict)
                  and i.get("transaction_id") in visited
                  and i.get("investigation_id"))


def _ref(txn: dict[str, Any]) -> str | None:
    for field in ("provider_reference", "external_reference",
                  "transaction_reference", "tx_hash"):
        value = txn.get(field)
        if isinstance(value, str) and value:
            return value
    return None


def link_strength(leg_a: dict[str, Any],
                  leg_b: dict[str, Any]) -> dict[str, Any]:
    """Classify the evidence linking two transaction legs."""
    ref_a, ref_b = _ref(leg_a), _ref(leg_b)
    if ref_a and ref_a == ref_b:
        return {"status": "CONFIRMED_LINK",
                "evidence": "identical supplied reference %s" % ref_a}
    recv = leg_a.get("receiver_account_id") or leg_a.get("wallet_address")
    send = leg_b.get("sender_account_id") or leg_b.get("wallet_address")
    if recv and send and recv == send:
        cur_a, cur_b = leg_a.get("currency"), leg_b.get("currency")
        if cur_a and cur_b and cur_a == cur_b:
            return {"status": "STRONGLY_SUPPORTED_LINK",
                    "evidence": "receiver->sender continuity in %s"
                                % cur_a}
        return {"status": "POSSIBLE_LINK",
                "evidence": "receiver->sender continuity, currency "
                            "unconfirmed (%s/%s)" % (cur_a, cur_b)}
    shared = [f for f in _WEAK
              if leg_a.get(f) and leg_a.get(f) == leg_b.get(f)]
    if shared:
        return {"status": "UNVERIFIED_LINK",
                "evidence": "shared weak signals: %s" % ",".join(shared)}
    return {"status": "NO_MATCH", "evidence": "no shared references"}


def build_trace(transactions: list[dict[str, Any]],
                edges: list[dict[str, Any]],
                origin_id: str, max_hops: int = 4) -> dict[str, Any]:
    """Breadth-first trace from an origin transaction over evidenced links."""
    by_id = {t.get("transaction_id"): t for t in transactions
             if isinstance(t, dict)}
    origin = by_id.get(origin_id)
    if origin is None:
        raise ValueError("TRACE_ORIGIN_UNKNOWN: %s" % origin_id)
    provenance_errors = _graph.validate_provenance(edges)
    provenanced: set | None = None
    account_links: set = set()
    if not provenance_errors:
        provenanced = set()
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            provenanced.add((str(edge.get("source")),
                             str(edge.get("target"))))
            src = edge.get("source_node_id")
            tgt = edge.get("target_node_id")
            if src and tgt:
                account_links.add((str(src), str(tgt)))
    movements: list[dict[str, Any]] = []
    visited = {origin_id}
    frontier = [(origin_id, 0)]
    unknown_downstream = False
    while frontier:
        current_id, hop = frontier.pop(0)
        if hop >= max_hops:
            unknown_downstream = True
            continue
        current = by_id[current_id]
        for cand_id, cand in by_id.items():
            if cand_id in visited:
                continue
            link = link_strength(current, cand)
            if (provenanced is not None
                    and (current_id, cand_id) in provenanced
                    and link["status"] in ("STRONGLY_SUPPORTED_LINK",
                                           "POSSIBLE_LINK",
                                           "UNVERIFIED_LINK")):
                link = {"status": "PROVIDER_REPORTED_LINK",
                        "evidence": "provenanced graph edge %s->%s"
                                    % (current_id, cand_id)}
            elif (link["status"] == "STRONGLY_SUPPORTED_LINK"
                    and account_links):
                recv = (current.get("receiver_account_id")
                        or current.get("wallet_address"))
                send = (cand.get("sender_account_id")
                        or cand.get("wallet_address"))
                if recv and send and (recv, send) in account_links:
                    link = {"status": "PROVIDER_REPORTED_LINK",
                            "evidence": "provenanced account edge "
                                        "%s->%s" % (recv, send)}
            if link["status"] == "NO_MATCH":
                continue
            visited.add(cand_id)
            frontier.append((cand_id, hop + 1))
            movements.append({
                "from_transaction": current_id,
                "to_transaction": cand_id,
                "hop": hop + 1,
                "status": link["status"],
                "evidence": link["evidence"],
                "amount_minor": cand.get("amount_minor"),
                "currency": cand.get("currency"),
            })
    cash_break = any(m.get("currency") is None for m in movements)
    limitations = []
    if provenance_errors:
        limitations.append("Graph edges failed provenance validation; "
                           "edge-reported links withheld.")
    if unknown_downstream:
        limitations.append("Hop limit reached; downstream movement unknown.")
    if cash_break or not movements:
        limitations.append("No confirmed downstream record; cash or "
                           "off-ledger legs cannot be traced.")
    return {
        "trace_id": "trace_%s" % origin_id,
        "origin_transaction": origin_id,
        "movements": movements,
        "visited_transactions": sorted(visited),
        "limitations": limitations,
        "built_at": _now(),
    }
