"""Homepage routing contract: two-origin architecture, locked.

Primary user interface .... Next.js frontend (local: http://localhost:3000)
Backend API + legacy pages . FastAPI (local: http://127.0.0.1:8000)

The backend root (/) deliberately still serves the legacy Jinja2
Command Center (Render serves the backend only; its contract is
unchanged). These tests lock that split: the legacy homepage marker,
the health/readiness/auth endpoints the frontend depends on, and the
exact CORS allowlist the local frontend origin needs.
"""
import pytest
from env_probe import CAN_SOCKETS

needs_sockets = pytest.mark.skipif(
    not CAN_SOCKETS,
    reason="socket creation forbidden in this sandbox; runs in CI/user envs")


@needs_sockets
def test_backend_root_serves_legacy_command_center(client):
    """/ on :8000 is the deliberate legacy page, not the new frontend."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Command Center" in resp.text
    # The Atlas landing never renders from the backend.
    assert "Global Intelligence Core" not in resp.text


@needs_sockets
def test_frontend_dependency_endpoints_healthy(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "healthy"
    assert client.get("/api/v1/ready").status_code == 200
    mode = client.get("/api/v1/auth/mode").json()
    assert "auth_enabled" in mode


@needs_sockets
def test_local_frontend_origin_preflight_accepted(client):
    """:3000 dev origin passes CORS preflight with credentials."""
    resp = client.options(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000",
                 "Access-Control-Request-Method": "GET"})
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == \
        "http://localhost:3000"


@needs_sockets
def test_unknown_origin_rejected(client):
    resp = client.options(
        "/api/v1/health",
        headers={"Origin": "http://evil.example",
                 "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in resp.headers
