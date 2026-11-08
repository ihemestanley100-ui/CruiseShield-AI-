"""D-040 trials/subs/founder: lifecycle + metering. Socket-free."""
from datetime import datetime, timedelta, timezone

import pytest
from starlette.requests import Request

import app.config as config_mod
import app.main as main
from app import auth as auth_mod
from app import billing as billing_mod
from app import ratelimit as rl

SECRET = "test-secret-billing-032-chars-ok"
RECORD = auth_mod.hash_password("demo-pass-1")
TOKEN = "test-platform-token-bill-not-secret"


@pytest.fixture(autouse=True)
def _buckets():
    rl.reset()
    yield
    rl.reset()


@pytest.fixture()
def armed(monkeypatch):
    monkeypatch.setattr(config_mod, "SESSION_SECRET", SECRET)
    monkeypatch.setattr(
        config_mod, "DEMO_USERS",
        "judge:investigator:%s,boss:admin:%s" % (RECORD, RECORD))
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", TOKEN)
    monkeypatch.setattr(config_mod, "TRIAL_ENFORCEMENT", "0")
    monkeypatch.setattr(config_mod, "FOUNDER_USER", "")
    return monkeypatch


def _req(cookie=None, headers=()):
    hdrs = [(b"host", b"t")] + list(headers)
    if cookie is not None:
        hdrs.append((b"cookie", ("csai_session=%s" % cookie).encode()))
    return Request({"type": "http", "method": "POST", "scheme": "http",
                    "server": ("t", 80), "client": ("9.9.9.9", 1234),
                    "path": "/x", "query_string": b"", "headers": hdrs})


def _login(user, password="demo-pass-1"):
    resp = main.auth_login({"username": user, "password": password},
                           _req())
    raw = resp.headers["set-cookie"]
    part = [p for p in raw.split(";") if "csai_session=" in p][0]
    return part.split("csai_session=", 1)[1]


def test_trial_lifecycle(tmp_store):
    first = billing_mod.ensure_trial(tmp_store, "amy")
    assert (first["credits"], first["status"]) == (2, "active")
    assert billing_mod.ensure_trial(tmp_store, "amy") is first
    billing_mod.consume_trial_credit(tmp_store, "amy")
    assert billing_mod.consume_trial_credit(
        tmp_store, "amy")["credits"] == 0
    with pytest.raises(ValueError, match="TRIAL_EXHAUSTED"):
        billing_mod.consume_trial_credit(tmp_store, "amy")
    assert billing_mod.trial_state(
        tmp_store.trial_for("amy")) == "exhausted"


def test_trial_expiry_and_bad_clock(tmp_store):
    trial = billing_mod.ensure_trial(tmp_store, "amy")
    trial["ends_at"] = "2020-01-01T00:00:00Z"
    tmp_store.save_trial("amy", trial)
    assert billing_mod.trial_state(trial) == "expired"
    with pytest.raises(ValueError, match="TRIAL_EXPIRED"):
        billing_mod.consume_trial_credit(tmp_store, "amy")
    assert billing_mod.trial_state({"ends_at": "junk"}) == "expired"


def test_metered_action_branches(tmp_store):
    assert billing_mod.metered_action(
        tmp_store, "amy", "", False) is None
    assert tmp_store.trial_for("amy") is None
    assert billing_mod.metered_action(
        tmp_store, "boss", "boss", True) is None
    billing_mod.start_subscription(tmp_store, "amy", "starter",
                                   "order-1")
    assert billing_mod.metered_action(
        tmp_store, "amy", "", True) is None
    trial = billing_mod.metered_action(tmp_store, "judge", "", True)
    assert trial["credits"] == 1


def test_subscription_lifecycle(tmp_store):
    rec = billing_mod.start_subscription(tmp_store, "amy", "starter",
                                         "order-1")
    assert (rec["plan"], rec["status"]) == ("starter", "active")
    assert rec["renews_at"] is None
    with pytest.raises(ValueError, match="PLAN_UNKNOWN"):
        billing_mod.start_subscription(tmp_store, "amy", "platinum",
                                       "order-2")
    with pytest.raises(ValueError, match="SUBSCRIPTION_EVIDENCE_REQUIRED"):
        billing_mod.start_subscription(tmp_store, "amy", "starter", " ")
    failed = billing_mod.record_payment_event(tmp_store, "amy",
                                              "recon-9", ok=False)
    assert failed["status"] == "past_due"
    healed = billing_mod.record_payment_event(tmp_store, "amy",
                                              "recon-10", ok=True)
    assert healed["status"] == "active"
    assert billing_mod.record_payment_event(tmp_store, "ghost",
                                            "x") is None
    cancelled = billing_mod.cancel_subscription(tmp_store, "amy")
    assert cancelled["status"] == "cancelled"
    with pytest.raises(ValueError, match="SUBSCRIPTION_NOT_FOUND"):
        billing_mod.cancel_subscription(tmp_store, "ghost")


def test_plans_carry_no_prices():
    assert [p["id"] for p in billing_mod.PLANS] == [
        "trial", "starter", "professional", "business",
        "enterprise", "government"]
    assert all(p["price"] is None and p["currency"] is None
               for p in billing_mod.PLANS)


def test_founder_recorded_once(tmp_store, armed):
    armed.setattr(config_mod, "FOUNDER_USER", "boss")
    _login("boss")
    rec = tmp_store.founder_record()
    assert rec["user"] == "boss"
    _login("boss")
    assert [a for a in tmp_store.state["audits"]
            if a["action"] == "founder.active"] != []
    assert len([a for a in tmp_store.state["audits"]
                if a["action"] == "founder.active"]) == 1
    _login("judge")
    assert tmp_store.founder_record()["user"] == "boss"


def test_founder_absent_when_unset(tmp_store, armed):
    _login("boss")
    assert tmp_store.founder_record() is None


def test_case_metering_armed(tmp_store, armed):
    armed.setattr(config_mod, "TRIAL_ENFORCEMENT", "1")
    cookie = _login("judge")
    main.post_case({"title": "one"}, _req(cookie))
    main.post_case({"title": "two"}, _req(cookie))
    assert tmp_store.trial_for("judge")["credits"] == 0
    with pytest.raises(main.AppError) as exc:
        main.post_case({"title": "three"}, _req(cookie))
    assert (exc.value.code, exc.value.status) == ("TRIAL_EXHAUSTED",
                                                  402)


def test_case_metering_bypass_and_off(tmp_store, armed):
    cookie = _login("judge")
    for i in range(4):
        main.post_case({"title": "open-%d" % i}, _req(cookie))
    assert tmp_store.trial_for("judge") is None
    armed.setattr(config_mod, "TRIAL_ENFORCEMENT", "1")
    armed.setattr(config_mod, "FOUNDER_USER", "boss")
    for i in range(3):
        main.post_case({"title": "founder-%d" % i},
                       _req(_login("boss")))
    assert tmp_store.trial_for("boss") is None
    authed = _req(headers=[(b"authorization",
                            b"Bearer " + TOKEN.encode())])
    main.post_case({"title": "token-call"}, authed)


def test_subscription_endpoints(tmp_store, armed):
    cookie = _login("boss")
    body = main.admin_start_subscription(
        {"username": "judge", "plan": "professional",
         "evidence": "order-7"}, _req(cookie))
    assert body["subscription"]["status"] == "active"
    assert any(a["action"] == "subscription.start"
               for a in tmp_store.state["audits"])
    cancelled = main.admin_cancel_subscription({"username": "judge"},
                                               _req(cookie))
    assert cancelled["subscription"]["status"] == "cancelled"
    with pytest.raises(main.AppError) as exc:
        main.admin_start_subscription(
            {"username": "judge", "plan": "nope",
             "evidence": "order-8"}, _req(cookie))
    assert exc.value.code == "PLAN_UNKNOWN"
    with pytest.raises(main.AppError) as exc:
        main.admin_start_subscription(
            {"username": "judge", "plan": "starter",
             "evidence": "order-9"}, _req())
    assert exc.value.code == "ADMIN_REQUIRED"
    with pytest.raises(main.AppError) as exc:
        main.admin_cancel_subscription({"username": "judge"}, _req())
    assert exc.value.code == "ADMIN_REQUIRED"


def test_entitlements_endpoint(tmp_store, armed):
    cookie = _login("judge")
    before = main.get_entitlements(_req(cookie))
    assert before["trial"] is None and before["founder"] is None
    assert before["enforcement"] is False
    billing_mod.ensure_trial(tmp_store, "judge")
    after = main.get_entitlements(_req(cookie))
    assert after["trial"]["credits"] == 2
    with pytest.raises(main.AppError):
        main.get_entitlements(_req())
