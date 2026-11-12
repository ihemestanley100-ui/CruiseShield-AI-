"""D-041 payments + Web3: intents, refunds, no live charge. Socket-free."""
import pytest
from starlette.requests import Request

import app.config as config_mod
import app.main as main
from app import auth as auth_mod
from app import payments as payments_mod
from app import ratelimit as rl
from app import web3 as web3_mod

SECRET = "test-secret-payments-032-chars!!"
RECORD = auth_mod.hash_password("demo-pass-1")
ADDR = "0x" + "ab" * 20
TXH = "0x" + "cd" * 32


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
    monkeypatch.setattr(config_mod, "DEMO_WRITE_TOKEN", "")


def _req(cookie=None):
    hdrs = [(b"host", b"t")]
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


def test_intent_lifecycle(tmp_store):
    rec = payments_mod.create_intent(tmp_store, "judge", 250000, "ngn",
                                     "stub-manual", "order-1")
    assert (rec["payment_id"], rec["currency"],
            rec["status"]) == ("pay_0001", "NGN", "pending")
    assert payments_mod.transition(
        tmp_store, "pay_0001", "succeeded")["status"] == "succeeded"
    assert payments_mod.transition(
        tmp_store, "pay_0001", "refunded")["status"] == "refunded"
    with pytest.raises(ValueError, match="PAYMENT_TRANSITION_ILLEGAL"):
        payments_mod.transition(tmp_store, "pay_0001", "pending")
    with pytest.raises(ValueError, match="PAYMENT_NOT_FOUND"):
        payments_mod.transition(tmp_store, "pay_9999", "pending")


def test_intent_validation(tmp_store):
    with pytest.raises(ValueError, match="PROVIDER_UNKNOWN"):
        payments_mod.create_intent(tmp_store, "judge", 100, "NGN",
                                   "stripe-live")
    for amount in (0, -5, "100", True, None):
        with pytest.raises(ValueError, match="AMOUNT_INVALID"):
            payments_mod.create_intent(tmp_store, "judge", amount,
                                       "NGN", "stub-manual")
    for currency in ("", "N", "USDD", "12", None):
        with pytest.raises(ValueError, match="CURRENCY_INVALID"):
            payments_mod.create_intent(tmp_store, "judge", 100,
                                       currency, "stub-manual")
    with pytest.raises(ValueError, match="REFERENCE_TOO_LONG"):
        payments_mod.create_intent(tmp_store, "judge", 100, "NGN",
                                   "stub-manual", "r" * 201)


def test_live_charge_impossible_and_stub_not_live():
    assert payments_mod.provider_ids() == ("stub-manual",)
    assert payments_mod.live_capable("stub-manual") is False
    with pytest.raises(ValueError, match="LIVE_CHARGING_DISABLED"):
        payments_mod.live_charge(amount=100)


def test_intent_endpoints(tmp_store, armed):
    cookie = _login("judge")
    body = main.create_intent(
        {"amount": 250000, "currency": "NGN",
         "provider": "stub-manual", "reference": "order-1"},
        _req(cookie))
    pid = body["payment"]["payment_id"]
    assert any(a["action"] == "billing.intent"
               for a in tmp_store.state["audits"])
    mine = main.list_intents(_req(cookie))["payments"]
    assert [p["payment_id"] for p in mine] == [pid]
    assert main.list_intents(_req(_login("boss")))["payments"] == []
    cancelled = main.cancel_intent(pid, _req(cookie))
    assert cancelled["payment"]["status"] == "cancelled"
    with pytest.raises(main.AppError) as exc:
        main.cancel_intent(pid, _req(cookie))
    assert exc.value.code == "PAYMENT_TRANSITION_ILLEGAL"
    with pytest.raises(main.AppError) as exc:
        main.create_intent({"amount": 1, "currency": "NGN",
                            "provider": "stub-manual"}, _req())
    assert exc.value.code == "LOGIN_REQUIRED"


def test_intent_foreign_is_404(tmp_store, armed):
    cookie = _login("judge")
    pid = main.create_intent(
        {"amount": 100, "currency": "USD", "provider": "stub-manual"},
        _req(cookie))["payment"]["payment_id"]
    with pytest.raises(main.AppError) as exc:
        main.cancel_intent(pid, _req(_login("boss")))
    assert (exc.value.code, exc.value.status) == ("PAYMENT_NOT_FOUND",
                                                  404)
    with pytest.raises(main.AppError) as exc:
        main.cancel_intent("pay_9999", _req(cookie))
    assert exc.value.code == "PAYMENT_NOT_FOUND"


def test_admin_refund(tmp_store, armed):
    cookie = _login("judge")
    pid = main.create_intent(
        {"amount": 100, "currency": "USD", "provider": "stub-manual"},
        _req(cookie))["payment"]["payment_id"]
    payments_mod.transition(tmp_store, pid, "succeeded")
    boss = _login("boss")
    body = main.admin_refund({"payment_id": pid, "evidence": "arf-1"},
                             _req(boss))
    assert body["payment"]["status"] == "refunded"
    with pytest.raises(main.AppError) as exc:
        main.admin_refund({"payment_id": pid, "evidence": "arf-2"},
                          _req(boss))
    assert exc.value.code == "PAYMENT_TRANSITION_ILLEGAL"
    with pytest.raises(main.AppError) as exc:
        main.admin_refund({"payment_id": pid, "evidence": " "},
                          _req(boss))
    assert exc.value.code == "REFUND_EVIDENCE_REQUIRED"
    with pytest.raises(main.AppError) as exc:
        main.admin_refund({"payment_id": pid, "evidence": "arf-3"},
                          _req(cookie))
    assert exc.value.code == "ADMIN_REQUIRED"


def test_web3_prepare_and_tx(tmp_store, armed):
    cookie = _login("judge")
    body = main.web3_prepare(
        {"asset": "USDC", "chain": "base", "amount": 50000,
         "address": ADDR}, _req(cookie))
    rec = body["payment"]
    assert (rec["payment_id"], rec["status"]) == ("w3_0001",
                                                  "awaiting_tx")
    assert rec["confirmations"] == 0
    claimed = " ".join(rec.keys())
    assert "private" not in claimed and "mnemonic" not in claimed \
        and "seed" not in claimed
    done = main.web3_record_tx({"payment_id": "w3_0001", "tx_hash": TXH},
                               _req(cookie))
    assert (done["payment"]["status"],
            done["payment"]["confirmations"]) == (
                "awaiting_confirmations", 0)
    with pytest.raises(main.AppError) as exc:
        main.web3_record_tx({"payment_id": "w3_0001", "tx_hash": TXH},
                            _req(cookie))
    assert exc.value.code == "WEB3_TX_LATE"


def test_web3_validation(tmp_store, armed):
    cookie = _login("judge")
    bad = [
        ({"asset": "BTC", "chain": "base", "amount": 1,
          "address": ADDR}, "WEB3_ASSET_UNSUPPORTED"),
        ({"asset": "USDC", "chain": "solana", "amount": 1,
          "address": ADDR}, "WEB3_CHAIN_UNSUPPORTED"),
        ({"asset": "USDC", "chain": "base", "amount": 1,
          "address": "0xshort"}, "WEB3_ADDRESS_INVALID"),
        ({"asset": "USDC", "chain": "base", "amount": 0,
          "address": ADDR}, "AMOUNT_INVALID"),
    ]
    for payload, code in bad:
        with pytest.raises(main.AppError) as exc:
            main.web3_prepare(payload, _req(cookie))
        assert exc.value.code == code, payload
    pid = main.web3_prepare(
        {"asset": "USDT", "chain": "polygon", "amount": 10,
         "address": ADDR}, _req(cookie))["payment"]["payment_id"]
    with pytest.raises(main.AppError) as exc:
        main.web3_record_tx({"payment_id": pid, "tx_hash": "0xzz"},
                            _req(cookie))
    assert exc.value.code == "WEB3_TX_INVALID"
    with pytest.raises(main.AppError) as exc:
        main.web3_record_tx({"payment_id": pid, "tx_hash": TXH},
                            _req(_login("boss")))
    assert exc.value.code == "PAYMENT_NOT_FOUND"


def test_web3_refund_policy():
    assert web3_mod.refund_policy() == {
        "refunds": "manual-operator-only",
        "custody": "none — platform never holds keys or funds"}
