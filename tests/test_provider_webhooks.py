"""D-044 provider interface + webhook verification. Socket-free."""
import base64
import hashlib
import hmac

from app import payments as payments_mod

SECRET = "whsec-test-only-not-a-credential"
BODY = b'{"id":"evt_1","type":"payment.succeeded"}'


def _sig(secret, body, ts):
    return base64.b64encode(
        hmac.new(secret.encode(), b"%d." % ts + body,
                 hashlib.sha256).digest()).decode()


def test_interface_version_and_stub_conformance():
    assert payments_mod.PROVIDER_INTERFACE_VERSION == 1
    assert payments_mod.provider_conformance("stub-manual") == []
    assert payments_mod.provider_conformance("nope") == [
        "PROVIDER_UNKNOWN: nope"]


def test_webhook_verify_accepts_fresh():
    ts = 1_700_000_000
    assert payments_mod.webhook_verify(
        SECRET, BODY, _sig(SECRET, BODY, ts), ts, now=float(ts)) is True


def test_webhook_verify_rejects():
    ts = 1_700_000_000
    good = _sig(SECRET, BODY, ts)
    assert payments_mod.webhook_verify(
        SECRET, b"tampered", good, ts, now=float(ts)) is False
    assert payments_mod.webhook_verify(
        SECRET, BODY, good[:-2] + "xx", ts, now=float(ts)) is False
    assert payments_mod.webhook_verify(
        "wrong", BODY, good, ts, now=float(ts)) is False
    assert payments_mod.webhook_verify(
        "", BODY, good, ts, now=float(ts)) is False
    assert payments_mod.webhook_verify(
        SECRET, BODY, "!!!not-base64!!!", ts, now=float(ts)) is False


def test_webhook_verify_window():
    ts = 1_700_000_000
    good = _sig(SECRET, BODY, ts)
    assert payments_mod.webhook_verify(
        SECRET, BODY, good, ts, now=float(ts + 301)) is False
    assert payments_mod.webhook_verify(
        SECRET, BODY, good, ts, now=float(ts - 301)) is False
    assert payments_mod.webhook_verify(
        SECRET, BODY, good, ts, now=float(ts + 300)) is True


def test_find_intent_by_reference(tmp_store):
    rec = payments_mod.create_intent(tmp_store, "judge", 100, "USD",
                                     "stub-manual", "order-9")
    assert payments_mod.find_intent_by_reference(
        tmp_store, "order-9")["payment_id"] == rec["payment_id"]
    assert payments_mod.find_intent_by_reference(
        tmp_store, "missing") is None
    assert payments_mod.find_intent_by_reference(tmp_store, "") is None
