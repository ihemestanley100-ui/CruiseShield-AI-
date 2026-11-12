"""JSON file store with atomic writes and deterministic reset."""
from __future__ import annotations

import json
import threading
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path

from app import audit_chain as chain_mod
from app import evidence as evidence_mod
from app import rules as rules_mod
from app import seed as seed_mod
from app.config import STATE_PATH, validate_backend
from app.events import validate_and_normalize
from app.models import RuleResult


def storage_backend() -> str:
    """Validated SELECTED storage backend (default "json").

    Reads the live config value so tests can monkeypatch it. JSON remains
    the active backend in Phase 5.1; "pg" only enables the scratch
    migration-verification path (no cutover).
    """
    from app import config as config_mod

    return validate_backend(config_mod.STORE_BACKEND)


def open_store(backend: str | None = None, path=None):
    """Open the requested backend: Store (json) or PgStore (pg)."""
    selected = validate_backend(backend) if backend is not None \
        else storage_backend()
    if selected == "json":
        return Store(path)
    from app.db import PgStore

    return PgStore()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class Store:
    backend = "json"

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else STATE_PATH
        # Phase 11 (PERF-001): serialize _save() — concurrent writers shared
        # one fixed tmp path and collided (WinError 32 → HTTP 500).
        self._save_lock = threading.Lock()
        self.state: dict = {}
        # GAP-002 chain wiring: None = legacy plaintext entries
        # (production until D-018 records the key ceremony).
        self.audit_chain_key: bytes | None = None
        self.audit_chain_key_id = "k1"
        self._audit_head: str | None = None
        # D-1: arm BEFORE load/seed so a fresh armed boot seals from
        # genesis. Present-but-invalid key config fails closed (loud
        # ValueError, no key material) instead of booting unsealed.
        from app import config as config_mod  # lazy: file convention
        if config_mod.audit_chain_misconfigured():
            raise ValueError(
                "AUDIT_CHAIN_MISCONFIGURED: audit key invalid; fix "
                "AUDIT_CHAIN_KEY* or unset to stay legacy")
        if config_mod.audit_chain_armed():
            self.audit_chain_key = config_mod.audit_chain_key_bytes()
            self.audit_chain_key_id = config_mod.AUDIT_CHAIN_KEY_ID
        if self.path.exists():
            self.state = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            # Phase 10 (SEC-002): a missing state file silently reseeds a
            # fresh seed. Warn loudly so data loss is never mistaken for
            # a healthy start (surfaces on uvicorn stderr).
            warnings.warn(
                f"state file {self.path} missing; seeding fresh state",
                RuntimeWarning, stacklevel=2)
            from app import config as config_mod  # lazy: cycle-safe

            if config_mod.is_production():
                raise RuntimeError(
                    "CS_ENV=production refuses synthetic seed: "
                    "provision a persistent DATA_DIR or database")
            self.reset("scn_primary")

    def _save(self) -> None:
        with self._save_lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
            tmp.replace(self.path)

    # -- reset / seed -----------------------------------------------------
    def reset(self, scenario_id: str) -> dict:
        # Production guard (§4): synthetic scenarios must never enter
        # production data. Lazy import mirrors storage_backend().
        from app import config as config_mod

        if config_mod.is_production():
            raise ValueError(
                "PRODUCTION_REFUSED: scenario reset refused when "
                "CS_ENV=production")
        if scenario_id == "scn_primary":
            scenario = seed_mod.build_primary()
        elif scenario_id == "scn_false_positive":
            scenario = seed_mod.build_false_positive()
        elif scenario_id == "scn_ambiguous":
            scenario = seed_mod.build_ambiguous()
        else:
            raise ValueError(f"UNKNOWN_SCENARIO: {scenario_id}")
        # J4: a scenario reset must not log anyone out: login state
        # survives reseeds (first seed has no prior state to keep).
        prior = getattr(self, "state", {}) or {}
        keep_revoked = prior.get("revoked_sessions", [])
        keep_epochs = prior.get("user_epochs", {})
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
                "synthetic_notice": "Synthetic data.",
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
            "revoked_sessions": keep_revoked, "user_epochs": keep_epochs,
        }
        self.append_audit("system", "platform-reset", "scenario.reset", "scenario",
                          scenario_id, "", run_id,
                          f"Reset to {scenario_id} v{seed_mod.SCENARIO_VERSION}",
                          trace_id, trace_id)
        self.append_audit("system", "platform-reset", "case.opened", "case", case_id,
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
        if self.audit_chain_key is not None:
            sealed = [a for a in self.state["audits"]
                      if "audit_digest" in a]
            prev = (sealed[-1]["audit_digest"] if sealed
                    else chain_mod.GENESIS_HASH)
            entry = chain_mod.seal(entry, prev, self.audit_chain_key_id,
                                   self.audit_chain_key, len(sealed))
            self._audit_head = entry["audit_digest"]
        self.state["audits"].append(entry)
        self._save()
        return entry

    def verify_audit_chain(self, keyring: dict[str, bytes]) -> dict:
        """Verify sealed audit entries; legacy entries are skipped.

        Raises ValueError on any tamper/link/signature failure.
        Returns {"events": n, "head": digest}.
        """
        sealed = [a for a in self.state["audits"] if "audit_digest" in a]
        return chain_mod.verify_chain(sealed, keyring)

    def arm_audit_chain(self, key: bytes, key_id: str) -> None:
        """D-1: arm sealing explicitly (tests/tools/rotation).

        History stays legacy and is counted, never retro-sealed:
        sealed sequence numbers start at the count of already-sealed
        entries (see append_audit).
        """
        from app import config as config_mod  # lazy: file convention
        if (not key or len(key) < config_mod.MIN_AUDIT_CHAIN_KEY_BYTES
                or not config_mod.audit_key_id_valid(key_id)):
            raise ValueError(
                "AUDIT_CHAIN_MISCONFIGURED: explicit key needs "
                "32+ bytes and a valid key id")
        self.audit_chain_key = bytes(key)
        self.audit_chain_key_id = key_id

    def audit_verification_report(self) -> dict:
        """D-1: sealed-chain verification + legacy count.

        Verifies against the config keyring plus this store's live
        sealing key (covers direct/test assignment). Never leaks key
        material: counts, key ids, digests, and codes only.
        """
        sealed = [a for a in self.state["audits"]
                  if "audit_digest" in a]
        legacy = len(self.state["audits"]) - len(sealed)
        from app import config as config_mod  # lazy: file convention
        ring = config_mod.audit_chain_keyring()
        if self.audit_chain_key is not None:
            ring[self.audit_chain_key_id] = self.audit_chain_key
        return chain_mod.verification_report(sealed, ring, legacy)

    def ingest_event(self, raw: dict) -> tuple[str, dict, list[str]]:
        event, warnings = validate_and_normalize(raw)
        dumped = event.model_dump()
        if dumped["event_id"] in self.state["seen_event_ids"]:
            return "duplicate", dumped, warnings
        self.state["events"].append(dumped)
        # Phase 5.3 L2 canonical rule: one row per transaction_id,
        # first-wins. Matches PostgreSQL ON CONFLICT DO NOTHING. Existing
        # records are untouched (all live transaction IDs are unique).
        known = {t["transaction_id"] for t in self.state["transactions"]}
        if dumped["transaction"]["transaction_id"] not in known:
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

    # -- detection outcomes + signal<->investigation links -----------------
    def set_signal_outcome(self, signal_id: str, outcome: str,
                           actor: str, note: str = "") -> dict:
        """Record a reviewer outcome; history preserved per signal."""
        outcomes = self.state.setdefault("signal_outcomes", {})
        record = outcomes.setdefault(signal_id, {"history": []})
        entry = {"outcome": outcome, "actor": actor, "note": note,
                 "recorded_at": _now()}
        record["history"].append(entry)
        record["current"] = outcome
        self._save()
        return entry

    def signal_outcome(self, signal_id: str) -> dict | None:
        return self.state.get("signal_outcomes", {}).get(signal_id)

    def link_signal(self, signal_id: str, investigation_id: str,
                    actor: str) -> dict:
        """Link a signal to an investigation (idempotent)."""
        links = self.state.setdefault("signal_links", {})
        record = links.setdefault(signal_id, {"history": []})
        entry = {"investigation_id": investigation_id, "actor": actor,
                 "linked_at": _now()}
        if investigation_id not in [h["investigation_id"]
                                    for h in record["history"]]:
            record["history"].append(entry)
        self._save()
        return entry

    def signal_link(self, signal_id: str) -> dict | None:
        return self.state.get("signal_links", {}).get(signal_id)


    # -- notification read state (per-caller identity, bounded) ------
    def mark_notifications_read(self, identity: str,
                                notification_ids: list[str]) -> list[str]:
        """Record read timestamps for known ids; prune stale (bounded)."""
        from datetime import datetime, timezone

        known = {a.get("alert_id") for a in self.state.get("alerts", [])}
        if identity.startswith("user:"):
            who = identity[len("user:"):]
            known |= {e.get("notification_id")
                      for e in self.state.get("user_notifications", [])
                      if e.get("user") == who}
        reads = self.state.setdefault("notification_reads", {})
        mine = reads.setdefault(identity, {})
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        marked = []
        for nid in notification_ids:
            if nid in known:
                mine[nid] = now
                marked.append(nid)
        for stale in [k for k in mine if k not in known]:
            del mine[stale]
        self._save()
        return marked

    def notification_reads_for(self, identity: str) -> dict[str, str]:
        return dict(self.state.get("notification_reads", {}).get(identity, {}))

    # -- connector connections (persisted; v14.0 S04) --

    def connection_get(self, conn_id: str) -> dict | None:
        """One stored connection record or None."""
        return self.state.get("connections", {}).get(conn_id)

    def connection_save(self, record: dict) -> None:
        """Upsert a connection record (refs + params only)."""
        self.state.setdefault("connections", {})[record["id"]] = \
            record
        self._save()

    def connection_list(self) -> list:
        """All stored connection records (insertion order)."""
        return list(self.state.get("connections", {}).values())

    # -- telecom verifications + consents (persisted evidence) --
    def telecom_next_seq(self) -> int:
        self.state["telecom_seq"] = int(
            self.state.get("telecom_seq", 0)) + 1
        self._save()
        return self.state["telecom_seq"]

    def telecom_save(self, record: dict) -> None:
        """Upsert an evidence record (masked subject + hash only)."""
        self.state.setdefault(
            "telecom_verifications", {})[record["verification_id"]] = record
        self._save()

    def telecom_get(self, verification_id: str) -> dict | None:
        found = self.state.get("telecom_verifications", {}).get(
            verification_id)
        return found if isinstance(found, dict) else None

    def telecom_for_subject(self, subject_hash: str) -> list:
        return [r for r in
                self.state.get("telecom_verifications", {}).values()
                if isinstance(r, dict)
                and r.get("subject_hash") == subject_hash]

    def telecom_consent_save(self, record: dict) -> None:
        self.state.setdefault("telecom_consents", {})[record["consent_id"]] = (
            record)
        self._save()

    def telecom_consent_for(self, subject_hash: str,
                            purpose: str) -> dict | None:
        for record in self.state.get("telecom_consents", {}).values():
            if not isinstance(record, dict):
                continue
            if record.get("subject_hash") != subject_hash:
                continue
            if record.get("purpose") != purpose:
                continue
            if record.get("revoked"):
                continue
            return record
        return None

    def intel_purge_expired(self, collection: str,
                            older_than_ts: float) -> int:
        """Delete aged intel records (identity/address/location/netgeo).

        Cutoff compares expires_at; records without a numeric
        expiry are kept (fail-safe: never purge what we cannot
        date).
        """
        kept = {}
        dropped = 0
        for key, record in self.state.get(collection, {}).items():
            moment = None
            if isinstance(record, dict):
                value = record.get("expires_at")
                if isinstance(value, (int, float)):
                    moment = float(value)
            if moment is not None and moment < older_than_ts:
                dropped += 1
            else:
                kept[key] = record
        if dropped:
            self.state[collection] = kept
            self._save()
        return dropped

    def telecom_purge_expired(self, older_than_ts: float) -> int:
        """Delete verifications verified before the cutoff. No oracle."""
        kept = {}
        dropped = 0
        for vid, record in self.state.get("telecom_verifications",
                                          {}).items():
            moment = record.get("verified_ts", 0.0) if isinstance(
                record, dict) else 0.0
            if isinstance(moment, (int, float)) and moment < older_than_ts:
                dropped += 1
            else:
                kept[vid] = record
        if dropped:
            self.state["telecom_verifications"] = kept
            self._save()
        return dropped
    # -- agent plans + runs (persisted; master S11) --

    def agent_plan_save(self, plan: dict) -> None:
        """Upsert an agent plan by plan_id."""
        self.state.setdefault("agent_plans", {})[plan["plan_id"]] = \
            plan
        self._save()

    def agent_plan_get(self, plan_id: str) -> dict | None:
        """One stored agent plan or None."""
        return self.state.get("agent_plans", {}).get(plan_id)

    def agent_run_save(self, run: dict) -> None:
        """Append an agent run record."""
        self.state.setdefault("agent_runs", []).append(run)
        self._save()

    def agent_run_list(self) -> list:
        """All stored agent runs (oldest first)."""
        return list(self.state.get("agent_runs", []))
    # -- governance records: SAR / DSR / holds (master S13) --

    def sar_save(self, sar: dict) -> None:
        """Upsert a SAR draft by sar_id."""
        self.state.setdefault("sars", {})[sar["sar_id"]] = sar
        self._save()

    def sar_get(self, sar_id: str) -> dict | None:
        """One stored SAR draft or None."""
        return self.state.get("sars", {}).get(sar_id)

    def sar_list(self) -> list:
        """All stored SAR drafts."""
        return list(self.state.get("sars", {}).values())

    def dsr_save(self, dsr: dict) -> None:
        """Upsert a data-subject request by dsr_id."""
        self.state.setdefault("dsrs", {})[dsr["dsr_id"]] = dsr
        self._save()

    def dsr_get(self, dsr_id: str) -> dict | None:
        """One stored DSR or None."""
        return self.state.get("dsrs", {}).get(dsr_id)

    def dsr_list(self) -> list:
        """All stored data-subject requests."""
        return list(self.state.get("dsrs", {}).values())

    def hold_save(self, hold: dict) -> None:
        """Upsert a legal hold by hold_id."""
        self.state.setdefault("holds", {})[hold["hold_id"]] = hold
        self._save()

    def hold_get(self, hold_id: str) -> dict | None:
        """One stored legal hold or None."""
        return self.state.get("holds", {}).get(hold_id)

    def hold_list(self) -> list:
        """All stored legal holds."""
        h = self.state.get("holds", {})
        return list(h.values()) if isinstance(h, dict) else h
    # -- MFA state (persisted per user; D-022) --

    def mfa_state(self, username: str) -> dict:
        """Per-user MFA record (defaults for unknown users)."""
        from app import mfa as mfa_mod
        return mfa_mod.normalize_state(
            self.state.setdefault("mfa", {}).get(username))

    def save_mfa_state(self, username: str, record: dict) -> None:
        """Persist one user MFA record (hashes/counters only)."""
        self.state.setdefault("mfa", {})[username] = record
        self._save()

    def spend_mfa_ticket(self, nonce: str, exp: float) -> bool:
        """Single-use ticket guard: False if nonce already spent.

        Expired nonces are pruned on access so the set cannot
        grow without bound."""
        import time as _time
        moment = _time.time()
        spent = self.state.setdefault("mfa_tickets", {})
        for old in [k for k, v in spent.items()
                    if float(v) < moment]:
            del spent[old]
        if not nonce or nonce in spent:
            self._save()
            return False
        spent[nonce] = exp
        self._save()
        return True
    # -- J4 session revocation / epochs ---------------------------------
    def revoke_session(self, nonce: str, exp: int,
                       now: float | None = None) -> None:
        """Record a logout; prune entries expired before now (bounded)."""
        import time

        moment = time.time() if now is None else now
        live = [r for r in self.state.get("revoked_sessions", [])
                if int(r.get("exp", 0)) >= int(moment)
                and r.get("nonce") != nonce]
        live.append({"nonce": nonce, "exp": int(exp)})
        self.state["revoked_sessions"] = live
        self._save()

    def is_revoked(self, nonce: str, now: float | None = None) -> bool:
        import time

        moment = time.time() if now is None else now
        return any(r.get("nonce") == nonce
                   and int(r.get("exp", 0)) >= int(moment)
                   for r in self.state.get("revoked_sessions", []))

    def bump_epoch(self, username: str,
                   now: float | None = None) -> int:
        """Logout-all: tokens minted before now die for the user."""
        import time

        moment = int(time.time() if now is None else now)
        epochs = self.state.setdefault("user_epochs", {})
        epochs[username] = max(int(epochs.get(username, 0)), moment)
        self._save()
        return epochs[username]

    def epoch_of(self, username: str) -> int:
        return int(self.state.get("user_epochs", {}).get(username, 0))

    # -- login-risk baselines (per user; D-028) --

    def login_risk_for(self, username: str) -> dict:
        """Per-user login-risk baseline ({} for unknown)."""
        stored = self.state.setdefault("login_risk", {})
        record = stored.get(username)
        return record if isinstance(record, dict) else {}

    def save_login_risk(self, username: str,
                        record: dict) -> None:
        """Persist one baseline (digests/hour buckets only)."""
        self.state.setdefault("login_risk", {})[username] = \
            record
        self._save()

    # -- per-user security notifications (in-app leg; D-029) --

    def notify_user(self, username: str, kind: str, title: str,
                    detail: str, level: str = "info") -> dict:
        """Append one security notice (bounded per user)."""
        from datetime import datetime, timezone

        items = self.state.setdefault("user_notifications", [])
        self.state["notif_counter"] = int(
            self.state.get("notif_counter", 0)) + 1
        now = datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z")
        entry = {"notification_id": "sec_%04d" %
                 self.state["notif_counter"],
                 "user": username, "kind": kind, "title": title,
                 "detail": detail, "level": level,
                 "created_at": now}
        items.append(entry)
        mine = [e for e in items if e.get("user") == username]
        if len(mine) > 50:
            drop = {id(e) for e in mine[:-50]}
            items[:] = [e for e in items if id(e) not in drop]
        self._save()
        return entry

    def user_notifications_for(self, username: str) -> list:
        """Security notices for one user (oldest first)."""
        return [e for e in self.state.get("user_notifications", [])
                if e.get("user") == username]

    # -- Phase 5 account/commercial state (D-037/D-040) --
    def upsert_registered_user(self, record: dict) -> dict:
        """Insert or replace one runtime user (overlay wins)."""
        users = self.state.setdefault("registered_users", [])
        users[:] = [u for u in users
                    if not isinstance(u, dict)
                    or u.get("username") != record.get("username")]
        users.append(record)
        self._save()
        return record

    def registered_user(self, username: str) -> dict | None:
        """Runtime user record or None."""
        return next((u for u in self.state.get("registered_users", [])
                     if isinstance(u, dict)
                     and u.get("username") == username), None)

    def trial_for(self, username: str) -> dict | None:
        """Trial record or None (use billing.ensure_trial to create)."""
        rec = self.state.get("trials", {}).get(username)
        return rec if isinstance(rec, dict) else None

    def save_trial(self, username: str, record: dict) -> None:
        """Persist one trial record."""
        self.state.setdefault("trials", {})[username] = record
        self._save()

    def subscription_for(self, username: str) -> dict | None:
        """Subscription record or None."""
        rec = self.state.get("subscriptions", {}).get(username)
        return rec if isinstance(rec, dict) else None

    def save_subscription(self, username: str, record: dict) -> None:
        """Persist one subscription record."""
        self.state.setdefault("subscriptions", {})[username] = record
        self._save()

    def founder_record(self) -> dict | None:
        """Founder entitlement record or None."""
        rec = self.state.get("founder")
        return rec if isinstance(rec, dict) else None

    def save_founder(self, record: dict) -> None:
        """Persist the founder entitlement record."""
        self.state["founder"] = record
        self._save()

    def save_payment(self, record: dict) -> dict:
        """Append one payment record (bounded at 5000, oldest dropped)."""
        items = self.state.setdefault("payments", [])
        items.append(record)
        del items[:-5000]
        self._save()
        return record

    def payment(self, payment_id: str) -> dict | None:
        """Payment record or None."""
        return next((p for p in self.state.get("payments", [])
                     if isinstance(p, dict)
                     and p.get("payment_id") == payment_id), None)

    def payments_for(self, username: str) -> list:
        """Payment records for one user (oldest first)."""
        return [p for p in self.state.get("payments", [])
                if isinstance(p, dict) and p.get("user") == username]

    def register_session(self, nonce: str, username: str, exp: int,
                         ua_class: str = "", net_digest: str = "") -> None:
        """Track one live session (digests only; bounded 50/user)."""
        items = self.state.setdefault("sessions_live", [])
        mine = [s for s in items
                if isinstance(s, dict) and s.get("user") == username]
        if len(mine) >= 50:
            drop = {id(s) for s in mine[:len(mine) - 49]}
            items[:] = [s for s in items if id(s) not in drop]
        items.append({"nonce": nonce, "user": username,
                      "exp": int(exp), "ua_class": ua_class,
                      "net_digest": net_digest})
        self._save()

    def sessions_for(self, username: str) -> list:
        """Live (unexpired) session entries for one user."""
        import time as _time
        moment = int(_time.time())
        return [s for s in self.state.get("sessions_live", [])
                if isinstance(s, dict) and s.get("user") == username
                and int(s.get("exp", 0)) >= moment]

    def drop_session(self, nonce: str) -> bool:
        """Forget one tracked session; True when one was dropped."""
        items = self.state.get("sessions_live", [])
        kept = [s for s in items
                if not (isinstance(s, dict) and s.get("nonce") == nonce)]
        if len(kept) == len(items):
            return False
        self.state["sessions_live"] = kept
        self._save()
        return True

    def notif_prefs_for(self, username: str) -> dict:
        """Notification preferences with safe defaults merged."""
        prefs = {"security": True, "product": True, "marketing": False}
        saved = self.state.get("notif_prefs", {}).get(username)
        if isinstance(saved, dict):
            for key in ("product", "marketing"):
                if key in saved:
                    prefs[key] = bool(saved[key])
        return prefs

    def save_notif_prefs(self, username: str, prefs: dict) -> dict:
        """Persist preferences (security notices stay always-on)."""
        merged = {"product": bool(prefs.get("product", True)),
                  "marketing": bool(prefs.get("marketing", False))}
        self.state.setdefault("notif_prefs", {})[username] = merged
        self._save()
        return self.notif_prefs_for(username)

    # -- Phase 5F/J org, invitations, outbox, passkeys (D-042/D-043/D-045) --
    def org_profile(self) -> dict:
        """Org profile with defaults."""
        saved = self.state.get("org_profile")
        if isinstance(saved, dict):
            return {"name": saved.get("name", ""),
                    "contact_email": saved.get("contact_email", ""),
                    "updated_at": saved.get("updated_at", "")}
        return {"name": "", "contact_email": "", "updated_at": ""}

    def save_org_profile(self, name: str, contact_email: str) -> dict:
        """Persist the org profile."""
        self.state["org_profile"] = {
            "name": name, "contact_email": contact_email,
            "updated_at": _now()}
        self._save()
        return self.org_profile()

    def save_invitation(self, record: dict) -> dict:
        """Insert or replace one invitation by nonce."""
        invs = self.state.setdefault("invitations", [])
        invs[:] = [i for i in invs
                   if not isinstance(i, dict)
                   or i.get("nonce") != record.get("nonce")]
        invs.append(record)
        self._save()
        return record

    def invitation(self, nonce: str) -> dict | None:
        """Invitation record or None."""
        return next((i for i in self.state.get("invitations", [])
                     if isinstance(i, dict)
                     and i.get("nonce") == nonce), None)

    def save_outbox(self, entry: dict) -> dict:
        """Append one delivery record (bounded at 200, oldest dropped)."""
        items = self.state.setdefault("outbox", [])
        items.append(entry)
        del items[:-200]
        self._save()
        return entry

    def outbox(self) -> list:
        """Delivery records (oldest first)."""
        return [e for e in self.state.get("outbox", [])
                if isinstance(e, dict)]

    def save_passkey_credential(self, record: dict) -> dict:
        """Insert or replace one passkey credential by id."""
        creds = self.state.setdefault("passkey_credentials", [])
        creds[:] = [c for c in creds
                    if not isinstance(c, dict)
                    or c.get("credential_id") != record.get("credential_id")]
        creds.append(record)
        self._save()
        return record

    def cred_save(self, record: dict) -> dict:
        """Insert or replace one API credential by client id."""
        rows = self.state.setdefault("api_credentials", [])
        rows[:] = [r for r in rows
                   if not isinstance(r, dict)
                   or r.get("client_id") != record.get("client_id")]
        rows.append(record)
        self._save()
        return record

    def api_credentials(self) -> list:
        """API credential records (hashes included; redact for output)."""
        return [r for r in self.state.get("api_credentials", [])
                if isinstance(r, dict)]

    def cred_get(self, client_id: str) -> dict | None:
        """One credential by client id."""
        return next((r for r in self.api_credentials()
                     if r.get("client_id") == client_id), None)

    def device_save(self, record: dict) -> dict:
        """Insert or replace one trusted-device record by device key."""
        rows = self.state.setdefault("trusted_devices", [])
        rows[:] = [r for r in rows
                   if not isinstance(r, dict)
                   or r.get("device_key") != record.get("device_key")]
        rows.append(record)
        self._save()
        return record

    def device_get(self, device_key: str) -> dict | None:
        """One device by key."""
        return next((r for r in self.state.get("trusted_devices", [])
                     if isinstance(r, dict)
                     and r.get("device_key") == device_key), None)

    def user_devices(self, username: str) -> list:
        """Devices registered to one user."""
        return [r for r in self.state.get("trusted_devices", [])
                if isinstance(r, dict) and r.get("user") == username]

    def agent_exec_save(self, record: dict) -> dict:
        """Insert or replace one orchestrator execution (bounded 200)."""
        rows = self.state.setdefault("agent_executions", [])
        rows[:] = [r for r in rows
                   if not isinstance(r, dict)
                   or r.get("execution_id") != record.get("execution_id")]
        rows.append(record)
        del rows[:-200]
        self._save()
        return record

    def agent_exec_get(self, execution_id: str) -> dict | None:
        """One orchestrator execution by id."""
        return next((r for r in self.state.get("agent_executions", [])
                     if isinstance(r, dict)
                     and r.get("execution_id") == execution_id), None)

    def agent_executions(self) -> list:
        """Orchestrator executions (oldest first)."""
        return [r for r in self.state.get("agent_executions", [])
                if isinstance(r, dict)]

    def conversation_save(self, record: dict) -> dict:
        """Insert or replace one conversation by id (bounded 200)."""
        rows = self.state.setdefault("conversations", [])
        rows[:] = [r for r in rows
                   if not isinstance(r, dict)
                   or r.get("conversation_id") != record.get(
                       "conversation_id")]
        rows.append(record)
        del rows[:-200]
        self._save()
        return record

    def conversation_get(self, conversation_id: str) -> dict | None:
        """One conversation by id."""
        return next((r for r in self.state.get("conversations", [])
                     if isinstance(r, dict)
                     and r.get("conversation_id") == conversation_id), None)

    def conversations_for(self, tenant_id: str,
                          username: str | None = None) -> list:
        """Tenant conversations, optionally one user's."""
        rows = [r for r in self.state.get("conversations", [])
                if isinstance(r, dict) and r.get("tenant_id") == tenant_id]
        if username is not None:
            rows = [r for r in rows if r.get("owner") == username]
        return rows

    def recovery_case_save(self, record: dict) -> dict:
        """Insert or replace one recovery case (bounded 500)."""
        rows = self.state.setdefault("recovery_cases", [])
        rows[:] = [r for r in rows
                   if not isinstance(r, dict)
                   or r.get("recovery_id") != record.get("recovery_id")]
        rows.append(record)
        del rows[:-500]
        self._save()
        return record

    def recovery_cases(self) -> list:
        """Recovery cases (oldest first)."""
        return [r for r in self.state.get("recovery_cases", [])
                if isinstance(r, dict)]

    def passkeys_for(self, username: str) -> list:
        """Passkey credentials for one user."""
        return [c for c in self.state.get("passkey_credentials", [])
                if isinstance(c, dict) and c.get("user") == username]

    def fraud_alert_save(self, record: dict) -> dict:
        """Insert or replace one fraud alert by alert id (bounded 500)."""
        rows = self.state.setdefault("fraud_alerts", [])
        rows[:] = [r for r in rows
                   if not isinstance(r, dict)
                   or r.get("id") != record.get("id")]
        rows.append(record)
        del rows[:-500]
        self._save()
        return record

    def fraud_alerts(self) -> list:
        """Fraud alert lifecycle rows (oldest first)."""
        return [r for r in self.state.get("fraud_alerts", [])
                if isinstance(r, dict)]

    def trace_save(self, record: dict) -> dict:
        """Insert or replace one fund-movement trace by trace id."""
        rows = self.state.setdefault("traces", [])
        rows[:] = [r for r in rows
                   if not isinstance(r, dict)
                   or r.get("trace_id") != record.get("trace_id")]
        rows.append(record)
        del rows[:-200]
        self._save()
        return record

    def traces(self) -> list:
        """Stored fund-movement traces (oldest first)."""
        return [r for r in self.state.get("traces", [])
                if isinstance(r, dict)]

    def passkey_credential(self, credential_id: str) -> dict | None:
        """Passkey credential or None."""
        return next((c for c in self.state.get("passkey_credentials", [])
                     if isinstance(c, dict)
                     and c.get("credential_id") == credential_id), None)

    def save_passkey_challenge(self, cid: str, record: dict) -> None:
        """Stage one single-use ceremony challenge."""
        self.state.setdefault("passkey_challenges", {})[cid] = record
        self._save()

    def take_passkey_challenge(self, cid: str) -> dict | None:
        """Pop one staged challenge (single-use even when expired)."""
        table = self.state.get("passkey_challenges", {})
        rec = table.pop(cid, None)
        if rec is not None:
            self._save()
        return rec if isinstance(rec, dict) else None

    def delete_passkey_credential(self, credential_id: str,
                                    username: str) -> bool:
        """Delete one owned credential; False when absent/foreign."""
        creds = self.state.get("passkey_credentials", [])
        kept = [c for c in creds
                if not (isinstance(c, dict)
                        and c.get("credential_id") == credential_id
                        and c.get("user") == username)]
        if len(kept) == len(creds):
            return False
        self.state["passkey_credentials"] = kept
        self._save()
        return True
