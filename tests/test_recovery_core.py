"""Recovery OS core: rules, eligibility, lifecycle, capabilities."""
from __future__ import annotations

import pytest

import app.main as main  # noqa: F401  (store fixture binding)
from app import recovery, recovery_caps, recovery_rules


def _txn(**kw):
    base = {"transaction_id": "t1", "channel": "NIP",
            "amount_minor": 1000, "currency": "NGN",
            "sender_account_id": "a1", "receiver_account_id": "a2",
            "occurred_at": "2026-11-07T08:00:00Z"}
    base.update(kw)
    return base


# -- rules registry -------------------------------------------------------
def test_seed_rules_honest():
    rules = recovery_rules.seed_rules()
    assert len(rules) == 10
    statuses = {r["verification_status"] for r in rules}
    assert statuses == {"VERIFIED", "NOT_VERIFIED"}
    structural = [r for r in rules
                  if r["rule_id"].startswith("STRUCT-")]
    assert all(r["verification_status"] == "VERIFIED"
               for r in structural)
    templates = [r for r in rules
                 if r["rule_id"].startswith("TMPL-")]
    assert all(r["window_days"] is None for r in templates)
    assert all(r["verification_status"] == "NOT_VERIFIED"
               for r in templates)


def test_register_validates(tmp_store):
    base = {f: None for f in recovery_rules.FIELDS}
    base.update({"rule_id": "CUSTOM-001", "version": "1.0",
                 "scheme": "s", "transaction_type": "bank_transfer",
                 "reason": "fraud", "verification_status": "VERIFIED",
                 "rule_source": "counsel memo",
                 "effective_at": "2026-01-01", "window_days": 30})
    out = recovery_rules.register(tmp_store, base)
    assert out["rule_id"] == "CUSTOM-001"
    with pytest.raises(ValueError):
        recovery_rules.register(tmp_store, {"rule_id": "x"})
    seed = dict(recovery_rules.seed_rules()[0])
    with pytest.raises(ValueError):
        recovery_rules.register(tmp_store, seed)
    bad = dict(base, rule_id="CUSTOM-002", rule_source="")
    with pytest.raises(ValueError):
        recovery_rules.register(tmp_store, bad)


# -- eligibility ------------------------------------------------------------
def test_crypto_structural_not_eligible(tmp_store):
    out = recovery.assess(tmp_store, _txn(payment_method="crypto_onchain"),
                          "fraud")
    assert out["status"] == "NOT_ELIGIBLE"
    assert out["rule_id"] == "STRUCT-CRYPTO-001"
    assert "law-enforcement-referral" in out["alternatives"]


def test_unverified_template_blocks(tmp_store):
    out = recovery.assess(tmp_store, _txn(), "erroneous")
    assert out["status"] == "RULES_NOT_VERIFIED"
    assert out["rule_id"] == "TMPL-BANK-002"


def test_unknown_method_unsupported(tmp_store):
    out = recovery.assess(tmp_store, {"transaction_id": "x"}, "fraud")
    assert out["status"] == "UNSUPPORTED_PAYMENT_RAIL"


def test_verified_rule_full_ladder(tmp_store):
    base = {f: None for f in recovery_rules.FIELDS}
    base.update({"rule_id": "BANK-NG-001", "version": "2.0",
                 "scheme": "bank-rail", "transaction_type":
                 "nip_instant", "reason": "erroneous",
                 "verification_status": "VERIFIED",
                 "rule_source": "counsel memo 2026-11",
                 "effective_at": "2026-01-01", "window_days": 30,
                 "evidence_required": ["transaction-record"]})
    recovery_rules.register(tmp_store, base)
    aged = _txn(occurred_at="2020-01-01T00:00:00Z")
    assert recovery.assess(tmp_store, aged, "erroneous")[
        "status"] == "OUT_OF_SCHEME_WINDOW"
    need_ev = recovery.assess(tmp_store, _txn(), "erroneous")
    assert need_ev["status"] == "EVIDENCE_REQUIRED"
    ev = [{"kind": "transaction-record", "reference": "t1"}]
    need_prov = recovery.assess(tmp_store, _txn(), "erroneous",
                                evidence=ev)
    assert need_prov["status"] == "PROVIDER_CONFIRMATION_REQUIRED"
    need_funds = recovery.assess(tmp_store, _txn(), "erroneous",
                                 evidence=ev, provider_available=True)
    assert need_funds["status"] == "FUNDS_AVAILABILITY_UNKNOWN"
    poor = recovery.assess(tmp_store, _txn(), "erroneous", evidence=ev,
                           provider_available=True,
                           funds_record={"available": False})
    assert poor["status"] == "POTENTIALLY_ELIGIBLE"
    rich = recovery.assess(tmp_store, _txn(), "erroneous", evidence=ev,
                           provider_available=True,
                           funds_record={"available": True})
    assert rich["status"] == "ELIGIBLE_CONFIRMED"
    assert rich["rule_id"] == "BANK-NG-001"


def test_coded_reason_gate(tmp_store):
    out = recovery.assess(tmp_store, _txn(), "vibes")
    assert out["status"] == "LEGAL_REVIEW_REQUIRED"


# -- lifecycle ------------------------------------------------------------------
def test_case_idempotent_and_transitions(tmp_store):
    first = recovery.open_case(tmp_store, "t1", "fraud",
                               "org_primary", "judge")
    assert first["status"] == "opened"
    dup = recovery.open_case(tmp_store, "t1", "fraud", "org_primary",
                             "judge")
    assert dup["status"] == "duplicate"
    rid = first["case"]["recovery_id"]
    for state in ("TRANSACTION_VERIFIED", "ELIGIBILITY_ASSESSED",
                  "EVIDENCE_VALIDATED", "REQUEST_PREPARED",
                  "APPROVAL_PENDING", "APPROVED", "UNDER_REVIEW",
                  "FULL_RECOVERY", "CLOSED"):
        row = recovery.transition(tmp_store, rid, state, "judge")
        assert row["state"] == state
    with pytest.raises(ValueError):
        recovery.transition(tmp_store, rid, "APPROVED", "judge")
    with pytest.raises(ValueError):
        recovery.transition(tmp_store, rid, "NOPE", "judge")
    with pytest.raises(ValueError):
        recovery.transition(tmp_store, "recv_nope", "CLOSED", "judge")


def test_metrics_from_rows(tmp_store):
    recovery.open_case(tmp_store, "t1", "fraud", "org_primary",
                       "judge")
    metrics = recovery.metrics(tmp_store, "org_primary")
    assert metrics["total"] == 1
    assert metrics["by_reason"] == {"fraud": 1}
    assert recovery.metrics(tmp_store, "org_other")["total"] == 0


# -- capabilities ------------------------------------------------------------------
def test_matrix_defaults_unsupported(tmp_store):
    rows = recovery_caps.matrix(tmp_store)
    assert len(rows) == 33
    assert all(cap["status"] == "UNSUPPORTED"
               for row in rows for cap in row["capabilities"].values())


def test_declare_requires_evidence(tmp_store):
    with pytest.raises(ValueError):
        recovery_caps.declare(tmp_store, "nip-transfer", "recall",
                              "", "boss")
    with pytest.raises(ValueError):
        recovery_caps.declare(tmp_store, "nip-transfer", "teleport",
                              "doc", "boss")
    with pytest.raises(ValueError):
        recovery_caps.declare(tmp_store, "nope", "recall", "doc",
                              "boss")
    entry = recovery_caps.declare(tmp_store, "nip-transfer", "recall",
                                  "provider doc v3 section 4", "boss")
    assert entry["capabilities"]["recall"]["status"] == "VERIFIED"
    assert recovery_caps.verified(tmp_store, "nip-transfer",
                                  "recall") is True
    assert recovery_caps.verified(tmp_store, "nip-transfer",
                                  "reversal") is False
