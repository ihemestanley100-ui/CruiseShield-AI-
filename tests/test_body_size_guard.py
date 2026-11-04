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


def _run_scheme(scheme, x_forwarded_proto=None):
    headers = []
    if x_forwarded_proto is not None:
        headers.append((b"x-forwarded-proto",
                        x_forwarded_proto.encode()))
    scope = {"type": "http", "method": "GET", "scheme": scheme,
             "server": ("t", 443 if scheme == "https" else 80),
             "path": "/api/v1/health", "headers": headers}
    return _drive(main.body_size_guard(Request(scope), _downstream_ok))


def test_hsts_on_direct_https():
    """R09-F4: HSTS stamped over direct TLS."""
    resp = _run_scheme("https")
    assert resp.headers["strict-transport-security"] == "max-age=31536000"


def test_hsts_behind_tls_proxy():
    """R09-F4: first X-Forwarded-Proto hop drives HSTS (proxy TLS)."""
    resp = _run_scheme("http", "https")
    assert resp.headers["strict-transport-security"] == "max-age=31536000"
    resp = _run_scheme("http", "https, http")
    assert resp.headers["strict-transport-security"] == "max-age=31536000"


def test_no_hsts_on_plain_local_http():
    """R09-F4: local plain-HTTP dev gets no HSTS header."""
    resp = _run_scheme("http")
    assert "strict-transport-security" not in resp.headers
    resp = _run_scheme("http", "http")
    assert "strict-transport-security" not in resp.headers
