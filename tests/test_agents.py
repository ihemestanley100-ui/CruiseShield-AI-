"""Master S11: governed agent kernel, tools, approval. Socket-free."""
import json

import pytest
from starlette.requests import Request

import app.main as main
from app import agents as agents_mod
from app import auth as auth_mod
from app import config as config_mod

SECRET = "test-secret-not-a-real-credential"
RECORD = auth_mod.hash_password("demo-pass-1")


def _users(monkeypatch, token=""):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", token)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s,431.0.0:auditor:%s"
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


def test_registry_manifests_and_tool_catalogue():
    body = main.agents_registry()
    assert len(body["agents"]) == 13
    assert len(body["tools"]) == 16
    by_id = {m["id"]: m for m in body["agents"]}
    assert by_id["fraud-detection"]["requires_approval"] is True
    assert by_id["aml-intel"]["requires_approval"] is True
    assert by_id["security-monitor"]["requires_approval"] is True
    assert by_id["txn-intel"]["requires_approval"] is False
    for manifest in body["agents"]:
        assert manifest["tools"]
        for tool in manifest["tools"]:
            assert tool in body["tools"], (manifest["id"], tool)
        assert manifest["model_tier"] == "deterministic"


def test_auto_run_flow_records_and_audits(monkeypatch, tmp_store):
    _users(monkeypatch)
    req = Request(_scope("/api/v1/agents/txn-intel/propose",
                         method="POST", cookie=_inv(), xrw=True))
    body = json.loads(main.agent_propose(
        "txn-intel", {"tool": "signal.search", "args": {"limit": 5}},
        req).body.decode())
    assert body["plan"]["status"] == "EXECUTED"
    assert body["run"]["status"] == "OK"
    assert body["run"]["tool"] == "signal.search"
    assert body["run"]["output"]["count"] <= 5
    assert body["run"]["actor"] == "judge"
    assert body["run"]["auto"] is True
    runs = tmp_store.agent_run_list()
    assert len(runs) == 1 and runs[0]["run_id"] == body["run"]["run_id"]
    actions = [e.get("action")
               for e in tmp_store.state.get("audits", [])]
    assert "agent.propose" in actions and "agent.run" in actions


def test_approval_flow_admin_only(monkeypatch, tmp_store):
    _users(monkeypatch)
    case_id = tmp_store.state["cases"][0]["case_id"]
    ireq = Request(_scope("/x", method="POST", cookie=_inv(), xrw=True))
    body = json.loads(main.agent_propose(
        "fraud-detection",
        {"tool": "case.read", "args": {"case_id": case_id}},
        ireq).body.decode())
    assert body["plan"]["status"] == "PENDING"
    assert body["run"] is None
    plan_id = body["plan"]["plan_id"]
    with pytest.raises(main.AppError) as exc:
        main.agent_approve(plan_id, ireq)
    assert exc.value.code == "AGENT_FORBIDDEN"
    areq = Request(_scope("/x", method="POST", cookie=_adm(), xrw=True))
    done = json.loads(main.agent_approve(plan_id, areq).body.decode())
    assert done["run"]["status"] == "OK"
    assert done["run"]["output"]["found"] is True
    assert done["run"]["auto"] is False
    with pytest.raises(main.AppError) as exc:
        main.agent_approve(plan_id, areq)
    assert exc.value.code == "AGENT_PLAN_STATE"
    assert exc.value.status == 409


def test_propose_rejects_unknowns_and_bad_args(monkeypatch, tmp_store):
    _users(monkeypatch)
    req = Request(_scope("/x", method="POST", cookie=_inv(), xrw=True))
    with pytest.raises(main.AppError) as exc:
        main.agent_propose("no-agent", {"tool": "case.read",
                                        "args": {}}, req)
    assert exc.value.code == "AGENT_UNKNOWN"
    assert exc.value.status == 404
    with pytest.raises(main.AppError) as exc:
        main.agent_propose("txn-intel", {"tool": "no.tool",
                                         "args": {}}, req)
    assert exc.value.code == "AGENT_TOOL_UNKNOWN"
    with pytest.raises(main.AppError) as exc:
        main.agent_propose("txn-intel", {"tool": "case.read",
                                         "args": {"case_id": "x"}},
                           req)
    assert exc.value.code == "AGENT_TOOL_DENIED"
    assert exc.value.status == 403
    with pytest.raises(main.AppError) as exc:
        main.agent_propose("case-assistant", {"tool": "case.read",
                                              "args": {}}, req)
    assert exc.value.code == "AGENT_ARGS"
    with pytest.raises(main.AppError) as exc:
        main.agent_propose(
            "case-assistant",
            {"tool": "case.read",
             "args": {"case_id": "x", "smuggled": 1}}, req)
    assert exc.value.code == "AGENT_ARGS"


def test_token_and_anonymous_denied(monkeypatch, tmp_store):
    _users(monkeypatch, token="tok-1")
    treq = Request(_scope("/x", method="POST", token="tok-1"))
    with pytest.raises(main.AppError) as exc:
        main.agent_propose("txn-intel", {"tool": "signal.search",
                                         "args": {}}, treq)
    # Armed + no session: the established R3 AI gate fires first.
    assert exc.value.code == "AI_LOGIN_REQUIRED"
    assert exc.value.status == 403
    monkeypatch.setattr(config_mod, "SESSION_SECRET", "")
    with pytest.raises(main.AppError) as exc:
        main.agent_propose("txn-intel", {"tool": "signal.search",
                                         "args": {}},
                           Request(_scope("/x", method="POST")))
    assert exc.value.code == "AGENT_SESSION_REQUIRED"


def test_auditor_lacks_ai_run(monkeypatch, tmp_store):
    _users(monkeypatch)
    cookie = _sess("431.0.0", "auditor")
    req = Request(_scope("/x", method="POST", cookie=cookie, xrw=True))
    with pytest.raises(main.AppError) as exc:
        main.agent_propose("txn-intel", {"tool": "signal.search",
                                         "args": {}}, req)
    assert exc.value.code == "AGENT_FORBIDDEN"


def test_plan_expiry(monkeypatch, tmp_store):
    _users(monkeypatch)
    ireq = Request(_scope("/x", method="POST", cookie=_inv(), xrw=True))
    body = json.loads(main.agent_propose(
        "aml-intel", {"tool": "signal.search", "args": {}}, ireq
    ).body.decode())
    plan_id = body["plan"]["plan_id"]
    plan = tmp_store.agent_plan_get(plan_id)
    plan["expires_at"] = 1.0
    tmp_store.agent_plan_save(plan)
    areq = Request(_scope("/x", method="POST", cookie=_adm(), xrw=True))
    with pytest.raises(main.AppError) as exc:
        main.agent_approve(plan_id, areq)
    assert exc.value.code == "AGENT_PLAN_EXPIRED"


def test_runs_list_and_limit(monkeypatch, tmp_store):
    _users(monkeypatch)
    req = Request(_scope("/x", method="POST", cookie=_inv(), xrw=True))
    main.agent_propose("txn-intel", {"tool": "signal.search",
                                     "args": {}}, req)
    body = main.agent_runs(Request(_scope("/x", cookie=_inv())))
    assert body["count"] == 1 and len(body["runs"]) == 1
    with pytest.raises(main.AppError) as exc:
        main.agent_runs(Request(_scope("/x", cookie=_inv())), limit=0)
    assert exc.value.code == "FILTER_INVALID"


def test_every_tool_binds_to_real_data(monkeypatch, tmp_store):
    _users(monkeypatch)
    req = Request(_scope("/x", method="POST", cookie=_inv(), xrw=True))
    case_id = tmp_store.state["cases"][0]["case_id"]
    node_id = tmp_store.state["nodes"][0]["node_id"]
    inv_id = next(iter(tmp_store.state["evidence_packages"]))
    calls = [
        ("case-assistant", "case.read", {"case_id": case_id}),
        ("case-assistant", "case.read", {"case_id": "case_nope"}),
        ("graph-investigator", "graph.neighbors", {"node_id": node_id}),
        ("evidence-analyst", "evidence.read", {"package_id": inv_id}),
        ("industry-intel", "industry.readiness",
         {"module_id": "banking"}),
        ("data-quality", "connector.read",
         {"connection_id": "conn_nope"}),
    ]
    for agent_id, tool, args in calls:
        body = json.loads(main.agent_propose(
            agent_id, {"tool": tool, "args": args}, req).body.decode())
        assert body["run"]["status"] == "OK", (agent_id, tool)
    missing = json.loads(main.agent_propose(
        "case-assistant", {"tool": "case.read",
                           "args": {"case_id": "case_nope"}},
        req).body.decode())
    assert missing["run"]["output"] == {"found": False,
                                        "case_id": "case_nope"}
