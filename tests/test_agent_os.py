"""Agent OS: orchestration, NL search, retrieval, conversations,
industry agent configs. Socket-free; tmp_store isolation."""
from __future__ import annotations

import pytest

import app.main as main  # noqa: F401  (store fixture binding)
from app import agent_retrieval as retrieval
from app import conversations as conv_mod
from app import industry_adapters as adapters
from app import nl_search
from app import orchestration as orch
from app import tenancy as tenancy_mod


def _subject():
    return {"kind": "session", "user": "judge",
            "role": "investigator", "tenant": "org_primary"}


def _ctx(tenant="org_primary"):
    return tenancy_mod.TenantContext(tenant_id=tenant, actor="judge")


# -- classification -------------------------------------------------------
def test_classify_intents():
    assert orch.classify("trace the funds")["intent"] == "TRACE"
    assert orch.classify("show suspicious transfers")["intent"] in (
        "FRAUD_EXPLAIN", "TRANSACTION_SEARCH")
    assert orch.classify("summarise case CS-1")["intent"] == "CASE_SUMMARY"
    assert orch.classify("banking industry status")["intent"] == \
        "INDUSTRY_INFO"
    assert orch.classify("blargle wump")["intent"] == "UNKNOWN"


def test_start_unknown_fails_clean(tmp_store):
    out = orch.start(tmp_store, "blargle wump", _subject())
    assert out["state"] == "FAILED"
    assert "INTENT_UNKNOWN" in out["error"]
    assert tmp_store.agent_exec_get(out["execution_id"]) is not None


def test_start_monitoring_completes(tmp_store):
    out = orch.start(tmp_store, "monitoring queue status", _subject())
    assert out["state"] == "COMPLETED"
    assert out["steps"] and out["steps"][0]["status"] == "OK"
    assert out["steps"][0]["output"]["mode"] == "on-demand-evaluation"


def test_start_transaction_search(tmp_store):
    out = orch.start(tmp_store, "show NIP transfers", _subject(),
                     args={"channel": "NIP"})
    assert out["state"] == "COMPLETED"
    assert "transactions" in out["steps"][0]["output"]


def test_start_denied_tool_partial(tmp_store, monkeypatch):
    monkeypatch.setattr(orch, "PIPELINES",
                        {"TRANSACTION_SEARCH": ("data-quality",
                                                ("trace.read",))})
    out = orch.start(tmp_store, "show transfers", _subject())
    assert out["state"] == "PARTIAL"
    assert out["steps"][0]["status"] == "DENIED"


def test_metrics_from_rows(tmp_store):
    orch.start(tmp_store, "monitoring status", _subject())
    metrics = orch.metrics(tmp_store)
    assert metrics["total"] >= 1
    assert metrics["tool_calls"] >= 1


# -- NL search --------------------------------------------------------------
def test_parse_amount_currency_dates():
    query = nl_search.parse("Show suspicious transactions above \u20a61 "
                            "million today.")
    filters = query["filters"]
    assert filters["min_amount_minor"] == 100_000_000
    assert filters["currency"] == "NGN"
    assert filters["start"]
    assert filters["flagged_only"] is True


def test_parse_channel_and_refs():
    query = nl_search.parse("Find POS transfers for case CS-1001 "
                            "linked to dev_04.")
    assert query["filters"]["channel"] == "POS"
    assert query["filters"]["case_ref"] == "CS-1001"
    assert query["filters"]["device_id"] == "dev_04"


def test_parse_ambiguous_asks():
    query = nl_search.parse("hello there")
    assert query.get("needs_clarification") is True
    assert query.get("question")


def test_execute_filters_rows(tmp_store):
    txns = tmp_store.state["transactions"]
    out = nl_search.execute(tmp_store, txns, [],
                            {"filters": {"channel": "NIP"}})
    assert out["count"] >= 0
    assert "explanation" in out
    assert "NIP" in out["explanation"]


# -- retrieval ---------------------------------------------------------------
def test_retrieval_tenant_isolated(tmp_store):
    hit = retrieval.search(tmp_store, _ctx(), "acct",
                           sources=["transactions"])
    assert hit["tenant_scope"] == "org_primary"
    assert isinstance(hit["hits"], list)
    other = retrieval.search(tmp_store, _ctx("org_other"), "acct")
    assert other["hits"] == []
    assert retrieval.embedding_status()["status"] == "UNAVAILABLE"
    empty = retrieval.search(tmp_store, _ctx(), "   ")
    assert empty["hits"] == []


def test_retrieval_attribution(tmp_store):
    out = retrieval.search(tmp_store, _ctx(), "banking",
                           sources=["industries"])
    assert out["hits"]
    assert all(set(h) >= {"kind", "reference", "observed_at",
                          "freshness", "label"} for h in out["hits"])


# -- conversations --------------------------------------------------------------
def test_conversation_lifecycle(tmp_store):
    conv = conv_mod.create(tmp_store, "org_primary", "judge",
                           {"investigation_id": "inv_1"})
    assert conv["expires_at"]
    msg = conv_mod.post_message(tmp_store, conv["conversation_id"],
                                "user", "trace csc_abc123 now",
                                "org_primary", "judge")
    assert "csc_abc123" not in msg["text"]
    assert "[REDACTED-CREDENTIAL]" in msg["text"]
    visible = conv_mod.get_visible(tmp_store, conv["conversation_id"],
                                   "org_primary", "judge")
    assert len(visible["messages"]) == 1
    assert conv_mod.get_visible(tmp_store, conv["conversation_id"],
                                "org_other", "judge") is None
    with pytest.raises(ValueError):
        conv_mod.post_message(tmp_store, conv["conversation_id"],
                              "user", "hi", "org_primary", "mallory")
    with pytest.raises(ValueError):
        conv_mod.post_message(tmp_store, conv["conversation_id"],
                              "hacker", "hi", "org_primary", "judge")


def test_conversation_purge(tmp_store):
    conv = conv_mod.create(tmp_store, "org_primary", "judge")
    conv["expires_at"] = "2000-01-01T00:00:00Z"
    tmp_store.conversation_save(conv)
    assert conv_mod.purge_expired(tmp_store) == 1
    assert conv_mod.purge_expired(tmp_store) == 0


# -- industry agent configs -------------------------------------------------------
def test_agent_config_banking():
    config = adapters.agent_config("banking")
    assert config["operational"] is True
    assert "txn.search" in config["tools"]
    assert config["permitted_roles"]
    assert len(config["report_templates"]) == 15
    assert config["terminology"] == {}


def test_agent_config_all_45():
    from app import industries as ind
    for entry in ind.registry():
        config = adapters.agent_config(entry["id"])
        assert config["industry_id"] == entry["id"]
        assert config["tools"]
    with pytest.raises(ValueError):
        adapters.agent_config("nope")


# -- new tools -----------------------------------------------------------------------
def test_txn_search_masked(tmp_store):
    from app import intel_tools as itools
    out = itools.txn_search(tmp_store, {}, _ctx())
    assert out["total"] >= 1
    first = out["transactions"][0]
    assert "sender_account_id" not in first
    assert first["sender_masked"] != ""
    other = itools.txn_search(tmp_store, {}, _ctx("org_other"))
    assert other["total"] == 0


def test_case_create_write(tmp_store):
    from app import intel_tools as itools
    out = itools.case_create(tmp_store, {"title": "agent-opened case"},
                             _ctx())
    assert out["case_id"]
    with pytest.raises(ValueError):
        itools.case_create(tmp_store, {"title": "  "}, _ctx())
