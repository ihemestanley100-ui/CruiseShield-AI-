"""Master S13: SAR/DSR/hold workflows + case-close hold. Socket-free."""
import json

import pytest
from starlette.requests import Request

import app.main as main
from app import auth as auth_mod
from app import config as config_mod
from app import governance as gov_mod

SECRET = "test-secret-not-a-real-credential"
RECORD = auth_mod.hash_password("demo-pass-1")


def _users(monkeypatch, token=""):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", token)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s,deputy:admin:%s"
        % (RECORD, RECORD, RECORD))


def _scope(path, method="GET", cookie=None, token=None, xrw=False):
    headers = [(b"host", b"t")]
    if cookie is not None:
        headers.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    if token is not None:
        headers.append((b"authorization", ("Bearer %s" % token).encode()))
    if xrw:
        headers.append((b"x-requested-with", b"XMLHttpRequest"))
    return {"type": "http", "method": method, "scheme": "http",
            "server": ("t", 80), "client": ("9.9.9.9", 1234),
            "path": path, "query_string": b"", "headers": headers}


def _sess(user, role):
    return auth_mod.create_session(user, role, SECRET)


def _inv():
    return _sess("judge", "investigator")


def _adm():
    return _sess("boss", "admin")


def _body(resp):
    return json.loads(resp.body.decode())


def _ireq():
    return Request(_scope("/x", method="POST", cookie=_inv(), xrw=True))


def _areq():
    return Request(_scope("/x", method="POST", cookie=_adm(), xrw=True))


def test_sar_full_flow_with_separation(monkeypatch, tmp_store):
    _users(monkeypatch)
    case_id = tmp_store.state["cases"][0]["case_id"]
    sar = _body(main.sar_create(
        {"case_id": case_id, "summary": "Structuring pattern, 3 accts."},
        _ireq()))
    assert sar["status"] == "DRAFT"
    sid = sar["sar_id"]
    main.sar_transition(sid, {"to": "IN_REVIEW"}, _ireq())
    with pytest.raises(main.AppError) as exc:
        main.sar_transition(sid, {"to": "READY"}, _ireq())
    assert exc.value.code == "GOV_FORBIDDEN"  # investigator lacks manage
    ready = _body(main.sar_transition(sid, {"to": "READY"}, _areq()))
    assert ready["status"] == "READY"
    with pytest.raises(main.AppError) as exc:
        main.sar_transition(sid, {"to": "FILED"}, _areq())  # no handoff
    assert exc.value.code == "GOV_HANDOFF_REF"
    filed = _body(main.sar_transition(
        sid, {"to": "FILED", "note": "HANDOFF-2026-001 counsel"}, _areq()))
    assert filed["status"] == "FILED"
    acked = _body(main.sar_transition(
        sid, {"to": "ACKNOWLEDGED", "note": "ACK-7788"}, _areq()))
    assert acked["status"] == "ACKNOWLEDGED"
    assert len(acked["history"]) == 5
    actions = [e.get("action")
               for e in tmp_store.state.get("audits", [])]
    assert "gov.sar.create" in actions
    assert "gov.sar.transition" in actions


def test_sar_self_approval_denied_and_guards(monkeypatch, tmp_store):
    _users(monkeypatch)
    case_id = tmp_store.state["cases"][0]["case_id"]
    sar = _body(main.sar_create({"case_id": case_id, "summary": "x"},
                                _areq()))
    main.sar_transition(sar["sar_id"], {"to": "IN_REVIEW"}, _areq())
    with pytest.raises(main.AppError) as exc:
        main.sar_transition(sar["sar_id"], {"to": "READY"}, _areq())
    assert exc.value.code == "GOV_SEPARATION"
    deputy = Request(_scope("/x", method="POST",
                            cookie=_sess("deputy", "admin"), xrw=True))
    ready = _body(main.sar_transition(sar["sar_id"], {"to": "READY"},
                                      deputy))
    assert ready["status"] == "READY"
    with pytest.raises(main.AppError) as exc:
        main.sar_create({"case_id": "case_nope", "summary": "x"}, _ireq())
    assert exc.value.code == "CASE_NOT_FOUND"
    with pytest.raises(main.AppError) as exc:
        main.sar_create({"case_id": case_id, "summary": "  "}, _ireq())
    assert exc.value.code == "GOV_SUMMARY_REQUIRED"
    with pytest.raises(main.AppError) as exc:
        main.sar_transition("sar_nope", {"to": "READY"}, _areq())
    assert exc.value.code == "SAR_NOT_FOUND"


def test_dsr_flow_and_outcome_notes(monkeypatch, tmp_store):
    _users(monkeypatch)
    dsr = _body(main.dsr_create(
        {"subject_ref": "SUBJ-1", "kind": "erasure",
         "details": "Delete marketing copy."}, _ireq()))
    assert dsr["status"] == "RECEIVED"
    did = dsr["dsr_id"]
    main.dsr_transition(did, {"to": "VERIFYING"}, _ireq())
    main.dsr_transition(did, {"to": "IN_PROGRESS"}, _ireq())
    with pytest.raises(main.AppError) as exc:
        main.dsr_transition(did, {"to": "FULFILLED", "note": ""}, _areq())
    assert exc.value.code == "GOV_OUTCOME"
    done = _body(main.dsr_transition(
        did, {"to": "FULFILLED",
              "note": "3 records purged per retention schedule"}, _areq()))
    assert done["status"] == "FULFILLED"
    with pytest.raises(main.AppError) as exc:
        main.dsr_create({"subject_ref": "S", "kind": "forget-all",
                         "details": ""}, _ireq())
    assert exc.value.code == "GOV_KIND"
    with pytest.raises(main.AppError) as exc:
        main.dsr_transition(did, {"to": "RECEIVED"}, _areq())
    assert exc.value.code == "GOV_TRANSITION"
    assert exc.value.status == 409


def test_hold_lifecycle_and_case_close_block(monkeypatch, tmp_store):
    _users(monkeypatch)
    case_id = tmp_store.state["cases"][0]["case_id"]
    with pytest.raises(main.AppError) as exc:
        main.hold_place({"resource_kind": "case", "resource_id": case_id,
                         "reason": "x"}, _ireq())
    assert exc.value.code == "GOV_FORBIDDEN"
    hold = _body(main.hold_place(
        {"resource_kind": "case", "resource_id": case_id,
         "reason": "Litigation L-9"}, _areq()))
    assert hold["active"] is True
    assert gov_mod.is_held(tmp_store, "case", case_id) is True
    assert gov_mod.is_held(tmp_store, "case", "case_other") is False
    with pytest.raises(main.AppError) as exc:
        main.post_decision(case_id, {"decision": "Close Case",
                                     "target_status": "CLOSED",
                                     "reason": "x", "actor_id": "boss"},
                           _areq())
    assert exc.value.code == "CASE_ON_HOLD"
    assert exc.value.status == 409
    released = _body(main.hold_release(
        hold["hold_id"], {"reason": "Matter settled"}, _areq()))
    assert released["active"] is False
    with pytest.raises(main.AppError) as exc:
        main.post_decision(case_id, {"decision": "Close Case",
                                     "target_status": "CLOSED",
                                     "reason": "x", "actor_id": "boss"},
                           _areq())
    assert exc.value.code != "CASE_ON_HOLD"  # hold gone; other rules apply
    with pytest.raises(main.AppError) as exc:
        main.hold_release(hold["hold_id"], {"reason": "again"}, _areq())
    assert exc.value.code == "GOV_HOLD_STATE"


def test_sensitive_surface_denies_token_and_anonymous(monkeypatch,
                                                      tmp_store):
    _users(monkeypatch, token="tok-1")
    treq = Request(_scope("/x", method="POST", token="tok-1"))
    with pytest.raises(main.AppError) as exc:
        main.sar_list(treq)
    assert exc.value.code == "GOV_FORBIDDEN"
    with pytest.raises(main.AppError) as exc:
        main.dsr_list(Request(_scope("/x")))
    assert exc.value.code == "LOGIN_REQUIRED"


def test_list_shapes(monkeypatch, tmp_store):
    _users(monkeypatch)
    case_id = tmp_store.state["cases"][0]["case_id"]
    main.sar_create({"case_id": case_id, "summary": "x"}, _ireq())
    main.dsr_create({"subject_ref": "S", "kind": "access",
                     "details": ""}, _ireq())
    assert main.sar_list(_ireq())["count"] == 1
    assert main.dsr_list(_ireq())["count"] == 1
    assert main.hold_list(_ireq())["count"] == 0
