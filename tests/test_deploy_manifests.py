"""GAP-016: pin deploy-manifest security properties in tests.

Dockerfile and render.yaml ship the production attack surface (base
image, install integrity, user, healthcheck, secret handling), but no
test asserted their content. These are text pins over the committed
files — no Docker daemon, no network, no YAML library needed.
"""
from pathlib import Path

import app.config as config_mod

ROOT = Path(__file__).resolve().parent.parent


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_dockerfile_pins_base_and_hashed_install():
    text = _read("Dockerfile")
    assert "FROM python:3.13-slim" in text
    assert "--require-hashes -r requirements.lock" in text
    assert "requirements.txt requirements.lock" in text


def test_dockerfile_runs_unprivileged_with_healthcheck():
    text = _read("Dockerfile")
    assert "useradd" in text and "USER appuser" in text
    assert "HEALTHCHECK" in text
    assert "/api/v1/health" in text
    assert "DATA_DIR=/srv/data" in text
    assert "uvicorn app.main:app" in text
    assert "${PORT:-8000}" in text


def test_render_backend_pins_service_and_secrets():
    text = _read("render.yaml")
    assert "name: cruiseshield-ai" in text
    assert "runtime: docker" in text
    assert "dockerfilePath: ./Dockerfile" in text
    assert "healthCheckPath: /api/v1/health" in text
    for secret in ("MODEL_API_KEY", "DEMO_WRITE_TOKEN", "SESSION_SECRET",
                   "DEMO_USERS"):
        assert "- key: %s\n        sync: false" % secret in text


def test_render_backend_defaults_match_code():
    text = _read("render.yaml")
    assert config_mod.META_MODEL_ID == "muse-spark-1.3"
    assert "value: muse-spark-1.3" in text
    assert "value: https://api.meta.ai/v1" in text
    assert config_mod.AI_DAILY_CALL_LIMIT == 100
    assert config_mod.AI_TIMEOUT_SECONDS == 30
    assert config_mod.AI_MAX_OUTPUT_TOKENS == 4096
    assert "AI_DAILY_CALL_LIMIT\n        value: 100" in text
    assert "AI_TIMEOUT_SECONDS\n        value: 30" in text
    assert "AI_MAX_OUTPUT_TOKENS\n        value: 4096" in text
    assert "STORE_BACKEND\n        value: json" in text


def test_render_frontend_pins_node_service_and_empty_token_rule():
    text = _read("render.yaml")
    assert "name: cruiseshield-ai-frontend" in text
    assert "runtime: node" in text
    assert "rootDir: frontend" in text
    assert "buildCommand: npm ci && npm run build" in text
    assert "startCommand: npm start -- --port $PORT" in text
    assert "healthCheckPath: /" in text
    assert "NEXT_PUBLIC_API_BASE_URL" in text
    # R6 (owner-approved): the public token stays empty; any value here
    # bakes PUBLIC into browser JS.
    assert "LEAVE EMPTY for public deploys" in text
    assert "- key: NEXT_PUBLIC_DEMO_WRITE_TOKEN\n        sync: false" in text
