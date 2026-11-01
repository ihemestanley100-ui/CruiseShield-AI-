"""Per-IP fixed-window rate limiting (in-memory, single-instance).

Render staging (D-001): closes the no-throttling gap for the demo/hosting
scale this product actually serves. Honest limits, stated up front:
- In-memory: correct for ONE instance (the supported staging topology);
  multi-instance needs a shared store (documented, not built).
- Client key: first X-Forwarded-For entry when present (Render terminates
  TLS at its proxy), else the direct peer. XFF is spoofable; spoofing only
  rotates the attacker's own bucket, but a fixed proxy-trust list is the
  production answer (documented, not built).
- Health/ready endpoints are EXEMPT (orchestrator checks must never 429).
"""
from __future__ import annotations

import time

# Generous for demos (matrix + assets burst well under this), tight enough
# to blunt floods: 600 req/min/IP ≈ 10 rps sustained per client.
LIMIT_PER_MINUTE = 600
WINDOW_SECONDS = 60


class _Bucket:
    __slots__ = ("window_start", "count")

    def __init__(self, now: float) -> None:
        self.window_start = now
        self.count = 0


_buckets: dict[str, _Bucket] = {}


def _now() -> float:
    return time.monotonic()


def client_key(x_forwarded_for: str | None, peer: str | None) -> str:
    if x_forwarded_for:
        first = x_forwarded_for.split(",")[0].strip()
        if first:
            return "xff:" + first
    return "peer:" + (peer or "unknown")


def check_and_consume(key: str, now: float | None = None,
                      limit: int = LIMIT_PER_MINUTE,
                      window: int = WINDOW_SECONDS) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds). Records the attempt."""
    moment = _now() if now is None else now
    bucket = _buckets.get(key)
    if bucket is None or moment - bucket.window_start >= window:
        bucket = _Bucket(moment)
        _buckets[key] = bucket
    bucket.count += 1
    if bucket.count > limit:
        retry = int(bucket.window_start + window - moment) + 1
        return False, max(retry, 1)
    return True, 0


def reset() -> None:
    """Test/demo helper: clear all buckets."""
    _buckets.clear()
