"""Agent OS routes: run/resume, search, retrieve, conversations,
industry agent config. Socket-free direct handlers."""
from __future__ import annotations

import pytest
from starlette.requests import Request

import app.main as main
from app import auth as auth_mod
from app import config as config_mod

SECRET = "test-secret-not-a-real-credential"
RECORD = auth_mod.hash_password("demo-pass-1")


def _users(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))


def _req(cookie=None):
    headers = [(b"host", b"t")]
    if cookie is not None:
        headers.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    return Request({"type": "http", "method": "POST", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"", "headers": headers})


def _inv():
    return auth_mod.create_session("judge", "investigator", SECRET)


def test_run_and_resume_flow(tmp_store, monkeypatch):
    _users(monkeypatch)
    out = main.agent_os_run({"text": "monitoring queue status"},
                            _req(_inv()))
    assert out["state"] == "COMPLETED"
    assert out["execution_id"]
    with pytest.raises(main.AppError):
        main.agent_os_resume(out["execution_id"], _req(_inv()))
    with pytest.raises(main.AppError):
        main.agent_os_run({"text": ""}, _req(_inv()))
    with pytest.raises(main.AppError):
        main.agent_os_run({"text": "hi"}, _req())


def test_executions_and_metrics(tmp_store, monkeypatch):
    _users(monkeypatch)
    main.agent_os_run({"text": "monitoring status"}, _req(_inv()))
    listed = main.agent_os_executions(_req(_inv()))
    assert listed["executions"]
    assert listed["tenant_scope"] == "org_primary"
    metrics = main.agent_os_metrics(_req(_inv()))
    assert metrics["total"] >= 1


def test_search_route(tmp_store, monkeypatch):
    _users(monkeypatch)
    out = main.agent_os_search({"text": "show NIP transfers"},
                               _req(_inv()))
    assert out["results"]["count"] >= 0
    assert "NIP" in out["results"]["explanation"]
    vague = main.agent_os_search({"text": "hello"}, _req(_inv()))
    assert vague["results"] is None
    assert vague["query"]["needs_clarification"]


def test_retrieve_route(tmp_store, monkeypatch):
    _users(monkeypatch)
    out = main.agent_os_retrieve({"query": "banking"}, _req(_inv()))
    assert out["hits"]
    assert out["tenant_scope"] == "org_primary"


def test_conversation_flow(tmp_store, monkeypatch):
    _users(monkeypatch)
    conv = main.create_conversation({"context": {"investigation_id":
                                                 "inv_1"}},
                                    _req(_inv()))
    assert conv["conversation_id"]
    turn = main.post_conversation_message(
        conv["conversation_id"], {"text": "monitoring status"},
        _req(_inv()))
    assert turn["user_message"]["role"] == "user"
    assert "COMPLETED" in turn["assistant_message"]["text"]
    assert turn["execution"]["execution_id"]
    fetched = main.get_conversation(conv["conversation_id"],
                                    _req(_inv()))
    assert len(fetched["messages"]) == 2
    listed = main.list_conversations(_req(_inv()))
    assert any(c["conversation_id"] == conv["conversation_id"]
               for c in listed["conversations"])
    assert all("messages" not in c for c in listed["conversations"])
    with pytest.raises(main.AppError):
        main.get_conversation("conv_nope", _req(_inv()))
    adm = auth_mod.create_session("boss", "admin", SECRET)
    with pytest.raises(main.AppError):
        main.get_conversation(conv["conversation_id"], _req(adm))


def test_industry_agent_config_route(tmp_store):
    out = main.industry_agent_config("banking")
    assert out["operational"] is True
    assert "txn.search" in out["tools"]
    with pytest.raises(main.AppError):
        main.industry_agent_config("nope")
