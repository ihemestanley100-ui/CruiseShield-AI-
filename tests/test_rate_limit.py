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
