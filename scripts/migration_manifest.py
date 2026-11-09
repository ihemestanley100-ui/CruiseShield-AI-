"""J5: migration manifest generator. READ-ONLY.

Reads a COPY of state.json (refuses the live file, like the loader)
and emits a markdown inventory: counts, identifier samples, content
hashes, and referential-integrity spot checks. Used to reconcile a
PostgreSQL rehearsal load against its source.

Usage:
    python scripts/migration_manifest.py <copy-of-state.json>
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIVE = (ROOT / "data" / "state.json").resolve()


def _sha(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]


def build_manifest(source: Path) -> str:
    if source.resolve() == LIVE:
        raise SystemExit("refusing live state file; migrate a copy")
    raw = source.read_bytes()
    state = json.loads(raw.decode("utf-8"))
    digest = hashlib.sha256(raw).hexdigest()
    lines = [
        "# J5 — MIGRATION MANIFEST (generated, read-only)",
        "",
        f"source bytes: {len(raw)}",
        f"source sha256: {digest}",
        f"scenario: {state.get('scenario_id')} "
        f"v{state.get('scenario_version')}",
        "",
        "## Collection counts",
        "",
    ]
    for key in sorted(state):
        value = state[key]
        if isinstance(value, list):
            lines.append(f"- {key}: {len(value)} rows")
        elif isinstance(value, dict):
            lines.append(f"- {key}: {len(value)} keys")
        else:
            lines.append(f"- {key}: scalar")
    lines += ["", "## Identifier inventory", ""]
    txns = state.get("transactions", [])
    lines.append(f"- transactions: {len(txns)} "
                 f"({', '.join(t['transaction_id'] for t in txns[:3])})")
    nodes = {n["node_id"] for n in state.get("nodes", [])}
    edges = state.get("edges", [])
    lines.append(f"- nodes: {len(nodes)}; edges: {len(edges)}")
    events = {e["event_id"] for e in state.get("events", [])}
    lines.append(f"- events: {len(events)}")
    rules = state.get("rule_results", {})
    n_rules = sum(len(v) for v in rules.values())
    lines.append(f"- rule_results: {n_rules}")
    pkgs = state.get("evidence_packages", {})
    n_items = sum(len(p.get("items", [])) for p in pkgs.values())
    lines.append(f"- evidence_packages: {len(pkgs)} ({n_items} items)")
    lines.append(f"- investigations: {len(state.get('investigations', []))}")
    lines.append(f"- cases: {len(state.get('cases', []))}")
    lines.append(f"- decisions: {len(state.get('decisions', []))}")
    lines.append(f"- audits: {len(state.get('audits', []))}")
    lines.append(f"- ai_runs: {len(state.get('ai_runs', []))}")
    lines.append(f"- simulations: {len(state.get('simulations', []))}")
    lines += ["", "## Content hashes (canonical subsets)", ""]
    lines.append(f"- transactions: {_sha(txns)}")
    lines.append(f"- edges: {_sha(edges)}")
    lines.append(f"- risk: {_sha(state.get('risk', {}))}")
    lines.append(f"- audits: {_sha(state.get('audits', []))}")
    lines += ["", "## Referential checks", ""]
    checks = []
    bad_edge = [e["edge_id"] for e in edges
                if e.get("source_node_id") not in nodes
                or e.get("target_node_id") not in nodes]
    checks.append(("edges reference known nodes", not bad_edge, bad_edge[:3]))
    rule_ids = {r["rule_result_id"]
                for rs in rules.values() for r in rs}
    edge_ids = {e["edge_id"] for e in edges}
    bad_ev = []
    for pkg in pkgs.values():
        for item in pkg.get("items", []):
            if (set(item.get("event_ids", [])) - events
                    or set(item.get("graph_edge_ids", [])) - edge_ids
                    or set(item.get("graph_node_ids", [])) - nodes
                    or set(item.get("rule_result_ids", [])) - rule_ids):
                bad_ev.append(item["evidence_id"])
    checks.append(("evidence items resolve", not bad_ev, bad_ev[:3]))
    case_ids = {c["case_id"] for c in state.get("cases", [])}
    bad_dec = [d.get("decision_id") for d in state.get("decisions", [])
               if d.get("case_id") not in case_ids]
    checks.append(("decisions reference cases", not bad_dec, bad_dec[:3]))
    got_ids = [a.get("audit_event_id") for a in state.get("audits", [])]
    want_ids = ["audit_%04d" % (i + 1) for i in range(len(got_ids))]
    checks.append(("audit chain audit_0001..N in order",
                   got_ids == want_ids, got_ids[:5]))
    for name, ok, sample in checks:
        lines.append(f"- {name}: {'OK' if ok else 'FAIL ' + str(sample)}")
    risk = state.get("risk", {}).get("txn_84721", {})
    txn = risk.get("transaction", {})
    net = risk.get("network", {})
    lines += ["", "## Risk pins",
              f"- txn-only: {txn.get('score')}/{txn.get('band')}",
              f"- network: {net.get('score')}/{net.get('band')}",
              ""]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    if not argv or len(argv) != 1:
        print("usage: python scripts/migration_manifest.py <state-copy>",
              file=sys.stderr)
        return 2
    print(build_manifest(Path(argv[0])), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
