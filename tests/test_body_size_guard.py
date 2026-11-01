"""SEC-009: transport body cap rejects giant Content-Length with 413.

Socket-free: drives the middleware function directly with minimal scopes.
"""
import json

from starlette.requests import Request

import app.main as main


def _drive(coro):
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise AssertionError("coroutine suspended on real I/O")


async def _downstream_ok(request):
    from starlette.responses import JSONResponse
    return JSONResponse({"ok": True})


def _run(content_length=None):
    headers = []
    if content_length is not None:
        headers.append((b"content-length", str(content_length).encode()))
    scope = {"type": "http", "method": "POST", "path": "/api/v1/events",
             "headers": headers}
    return _drive(main.body_size_guard(Request(scope), _downstream_ok))


def test_oversized_body_rejected_413():
    resp = _run(main.MAX_BODY_BYTES + 1)
    assert resp.status_code == 413
    payload = json.loads(bytes(resp.body).decode())
    assert payload["error"]["code"] == "BODY_TOO_LARGE"
    assert payload["error"]["trace_id"]


def test_boundary_body_passes_through():
    resp = _run(main.MAX_BODY_BYTES)
    assert resp.status_code == 200


def test_small_body_passes_through():
    resp = _run(1024)
    assert resp.status_code == 200


def test_missing_length_passes_through():
    # Chunked/unknown-length bodies: proxy limits apply (documented limit).
    resp = _run(None)
    assert resp.status_code == 200


def test_malformed_length_passes_through():
    resp = _run("not-a-number")
    assert resp.status_code == 200


def test_secure_headers_stamped():
    resp = _run(1024)
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert resp.headers["referrer-policy"] == \
        "strict-origin-when-cross-origin"
    assert resp.headers["permissions-policy"] == \
        "camera=(), microphone=(), geolocation=()"
