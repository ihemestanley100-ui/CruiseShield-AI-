"""SEC-011 (D-001): per-IP fixed-window throttle. Socket-free."""
import json

from starlette.requests import Request
from starlette.responses import JSONResponse

import app.main as main
from app import ratelimit as rl


def _drive(coro):
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise AssertionError("coroutine suspended on real I/O")


async def _downstream_ok(request):
    return JSONResponse({"ok": True})


def setup_function(_):
    rl.reset()


def test_allows_burst_then_throttles():
    for _ in range(rl.LIMIT_PER_MINUTE):
        allowed, _ = rl.check_and_consume("k1", now=1000.0)
        assert allowed
    allowed, retry = rl.check_and_consume("k1", now=1000.0)
    assert not allowed
    assert retry >= 1


def test_window_resets():
    rl.check_and_consume("k2", now=1000.0)
    allowed, _ = rl.check_and_consume(
        "k2", now=1000.0 + rl.WINDOW_SECONDS)
    assert allowed


def test_keys_are_independent():
    for _ in range(rl.LIMIT_PER_MINUTE):
        rl.check_and_consume("a", now=1000.0)
    allowed, _ = rl.check_and_consume("b", now=1000.0)
    assert allowed


def test_client_key_prefers_xff():
    assert rl.client_key("1.2.3.4, 5.6.7.8", "9.9.9.9") == "xff:1.2.3.4"
    assert rl.client_key(None, "9.9.9.9") == "peer:9.9.9.9"
    assert rl.client_key("", None) == "peer:unknown"


def _scope(path, xff=None):
    headers = [(b"host", b"t")]
    if xff is not None:
        headers.append((b"x-forwarded-for", xff.encode()))
    return {"type": "http", "method": "GET", "scheme": "http",
            "server": ("t", 80), "client": ("9.9.9.9", 1234),
            "path": path, "query_string": b"", "headers": headers}


def test_middleware_exempts_health():
    for _ in range(rl.LIMIT_PER_MINUTE + 5):
        resp = _drive(main.rate_limit_guard(
            Request(_scope("/api/v1/health")), _downstream_ok))
        assert resp.status_code == 200


def test_bucket_store_stays_bounded():
    """R09-F1: forged keys (unique XFFs) must not grow memory unbounded."""
    for i in range(rl.MAX_BUCKETS + 500):
        rl.check_and_consume(f"flood-{i}", now=1000.0)
    assert len(rl._buckets) <= rl.MAX_BUCKETS


def test_expired_buckets_swept_first():
    """R09-F1: at capacity, expired buckets are evicted before fresh ones."""
    for i in range(rl.MAX_BUCKETS):
        rl.check_and_consume(f"old-{i}", now=1000.0)
    allowed, _ = rl.check_and_consume(
        "new-key", now=1000.0 + rl.WINDOW_SECONDS + 1)
    assert allowed
    assert "new-key" in rl._buckets
    assert len(rl._buckets) <= rl.MAX_BUCKETS
    assert not any(k.startswith("old-") for k in rl._buckets)


def test_oldest_evicted_when_full_and_fresh():
    """R09-F1: at capacity with no expired buckets, oldest goes first."""
    for i in range(rl.MAX_BUCKETS):
        rl.check_and_consume(f"fresh-{i}", now=1000.0 + i * 0.001)
    allowed, _ = rl.check_and_consume("late-key", now=1000.0 + 5)
    assert allowed
    assert len(rl._buckets) == rl.MAX_BUCKETS
    assert "fresh-0" not in rl._buckets
    assert "late-key" in rl._buckets


def test_middleware_throttles_with_429_envelope():
    for _ in range(rl.LIMIT_PER_MINUTE):
        resp = _drive(main.rate_limit_guard(
            Request(_scope("/api/v1/risk/x", xff="10.0.0.7")),
            _downstream_ok))
        assert resp.status_code == 200
    resp = _drive(main.rate_limit_guard(
        Request(_scope("/api/v1/risk/x", xff="10.0.0.7")), _downstream_ok))
    assert resp.status_code == 429
    assert resp.headers["retry-after"]
    payload = json.loads(bytes(resp.body).decode())
    assert payload["error"]["code"] == "RATE_LIMITED"
    assert payload["error"]["trace_id"]
