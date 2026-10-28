"""JSON file store with atomic writes and deterministic reset."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app import evidence as evidence_mod
from app import rules as rules_mod
from app import seed as seed_mod
from app.config import STATE_PATH
from app.events import validate_and_normalize
from app.models import RuleResult


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class Store:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else STATE_PATH
        self.state: dict = {}
        if self.path.exists():
            self.state = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self.reset("scn_primary")

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    # -- reset / seed -----------------------------------------------------
    def reset(self, scenario_id: str) -> dict:
        if scenario_id == "scn_primary":
            scenario = seed_mod.build_primary()
        elif scenario_id == "scn_false_positive":
            scenario = seed_mod.build_false_positive()
        else:
            raise ValueError(f"UNKNOWN_SCENARIO: {scenario_id}")
        run_id = uuid.uuid4().hex
        primary = scenario["primary_transaction_id"]
        num = primary.split("_")[-1]
        trace_id = f"trace_run_{run_id[:12]}"
        rule_results = [r.model_dump() for r in rules_mod.evaluate(
            primary, scenario["transactions"], scenario["edges"], trace_id)]
        parsed = [RuleResult.model_validate(r) for r in rule_results]
        risk_txn = rules_mod.assess(primary, "transaction",
                                    scenario["transactions"], scenario["edges"],
                                    parsed, trace_id)
        risk_net = rules_mod.assess(primary, "network", scenario["transactions"],
                                    scenario["edges"], parsed, trace_id)
        events_by_id = {e["event_id"]: e for e in scenario["events"]}
        items = evidence_mod.build_items(
            next(t for t in scenario["transactions"]
                 if t["transaction_id"] == primary),
            parsed, scenario["edges"], events_by_id, trace_id)
        package = evidence_mod.build_package(
            scenario_id, seed_mod.SCENARIO_VERSION, trace_id, items)
        created = _now()
        alert_id, inv_id, case_id = f"alert_{num}", f"inv_{num}", f"case_{num}"
        self.state = {
            "scenario_id": scenario_id,
            "scenario_version": seed_mod.SCENARIO_VERSION,
            "run_id": run_id, "trace_id": trace_id,
            "seed_hash": seed_mod.seed_hash(scenario),
            "manifest": {
                "scenario_id": scenario_id,
                "scenario_version": seed_mod.SCENARIO_VERSION,
                "title": scenario["title"], "purpose": scenario["purpose"],
                "seed_hash": seed_mod.seed_hash(scenario),
                "synthetic_notice": "Synthetic demo data.",
                "event_sequence": [e["event_id"] for e in scenario["events"]],
                "expected_rule_results": {
                    r["rule_id"]: r["triggered"] for r in rule_results},
                "expected_graph_counts": self._counts(scenario),
                "expected_risk_band": {"transaction": risk_txn["band"],
                                       "network": risk_net["band"]},
                "expected_evidence_ids": [i.evidence_id for i in package.items],
            },
            "transactions": scenario["transactions"],
            "events": scenario["events"],
            "nodes": scenario["nodes"],
            "edges": scenario["edges"],
            "seen_event_ids": [e["event_id"] for e in scenario["events"]],
            "primary_transaction_id": primary,
            "rule_results": {primary: rule_results},
            "risk": {primary: {"transaction": risk_txn, "network": risk_net}},
            "alerts": [{"alert_id": alert_id, "transaction_id": primary,
                        "title": f"{risk_net['band']} network risk: transaction #{num}",
                        "status": "OPEN",
                        "risk_assessment_id": risk_net["risk_assessment_id"],
                        "created_at": created, "trace_id": trace_id}],
            "investigations": [{"investigation_id": inv_id, "alert_id": alert_id,
                                "transaction_id": primary, "status": "OPEN",
                                "created_at": created, "trace_id": trace_id}],
            "evidence_packages": {inv_id: package.model_dump()},
            "cases": [{"case_id": case_id, "investigation_id": inv_id,
                       "status": "NEW", "created_at": created,
                       "updated_at": created, "trace_id": trace_id}],
            "decisions": [], "audits": [], "ai_runs": [], "simulations": [],
            "audit_counter": 0, "replay": {"cursor": 0}, "created_at": created,
        }
        self.append_audit("system", "demo-reset", "scenario.reset", "scenario",
                          scenario_id, "", run_id,
                          f"Reset to {scenario_id} v{seed_mod.SCENARIO_VERSION}",
                          trace_id, trace_id)
        self.append_audit("system", "demo-reset", "case.opened", "case", case_id,
                          "", "NEW", "Case opened for primary investigation",
                          trace_id, trace_id)
        self._save()
        return {"scenario_id": scenario_id, "run_id": run_id,
                "trace_id": trace_id, "seed_hash": self.state["seed_hash"],
                "manifest": self.state["manifest"]}

    @staticmethod
    def _counts(scenario: dict) -> dict[str, int]:
        by_type: dict[str, int] = {}
        for node in scenario["nodes"]:
            by_type[node["node_type"]] = by_type.get(node["node_type"], 0) + 1
        return {"nodes": len(scenario["nodes"]), "edges": len(scenario["edges"]),
                "accounts": by_type.get("account", 0),
                "devices": by_type.get("device", 0),
                "phones": by_type.get("phone", 0),
                "merchants": by_type.get("merchant", 0),
                "beneficiaries": by_type.get("beneficiary", 0),
                "transactions": len(scenario["transactions"]),
                "events": len(scenario["events"])}

    # -- lookups ----------------------------------------------------------
    def get_case(self, case_id: str) -> dict | None:
        return next((c for c in self.state["cases"] if c["case_id"] == case_id),
                    None)

    def get_investigation(self, inv_id: str) -> dict | None:
        return next((i for i in self.state["investigations"]
                     if i["investigation_id"] == inv_id), None)

    def get_transaction(self, txn_id: str) -> dict | None:
        return next((t for t in self.state["transactions"]
                     if t["transaction_id"] == txn_id), None)

    # -- mutations --------------------------------------------------------
    def append_audit(self, actor_type: str, actor_id: str, action: str,
                     target_type: str, target_id: str, previous: str, new: str,
                     reason: str, trace_id: str, request_id: str) -> dict:
        self.state["audit_counter"] += 1
        entry = {
            "audit_event_id": f"audit_{self.state['audit_counter']:04d}",
            "actor_type": actor_type, "actor_id": actor_id, "action": action,
            "target_type": target_type, "target_id": target_id,
            "previous_state_reference": previous, "new_state_reference": new,
            "reason": reason, "timestamp": _now(), "trace_id": trace_id,
            "request_id": request_id,
        }
        self.state["audits"].append(entry)
        self._save()
        return entry

    def ingest_event(self, raw: dict) -> tuple[str, dict, list[str]]:
        event, warnings = validate_and_normalize(raw)
        dumped = event.model_dump()
        if dumped["event_id"] in self.state["seen_event_ids"]:
            return "duplicate", dumped, warnings
        self.state["events"].append(dumped)
        self.state["transactions"].append(dumped["transaction"])
        self.state["seen_event_ids"].append(dumped["event_id"])
        self._save()
        return "accepted", dumped, warnings

    def save_ai_run(self, run: dict) -> None:
        self.state["ai_runs"].append(run)
        self._save()

    def save_simulation(self, sim: dict) -> None:
        self.state["simulations"].append(sim)
        self._save()
