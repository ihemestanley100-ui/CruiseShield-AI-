"""Per-IP fixed-window rate limiting (in-memory, single-instance).

Render staging (D-001): closes the no-throttling gap for staging/hosting
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

# Generous for clients (matrix + assets burst well under this), tight enough
# to blunt floods: 600 req/min/IP ≈ 10 rps sustained per client.
LIMIT_PER_MINUTE = 600
WINDOW_SECONDS = 60
# R09-F1: bound the bucket store. Forged X-Forwarded-For values must not
# grow memory without limit: at capacity, expired buckets are swept
# first, then the single oldest bucket is evicted for the new key.
MAX_BUCKETS = 10_000


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


def _make_room(moment: float, window: int) -> None:
    """Evict buckets so one new key fits (R09-F1 bounded store)."""
    if len(_buckets) < MAX_BUCKETS:
        return
    for victim in [k for k, b in _buckets.items()
                   if moment - b.window_start >= window]:
        del _buckets[victim]
    if len(_buckets) < MAX_BUCKETS:
        return
    oldest = min(_buckets, key=lambda k: _buckets[k].window_start)
    del _buckets[oldest]


def check_and_consume(key: str, now: float | None = None,
                      limit: int = LIMIT_PER_MINUTE,
                      window: int = WINDOW_SECONDS) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds). Records the attempt."""
    moment = _now() if now is None else now
    bucket = _buckets.get(key)
    if bucket is None:
        _make_room(moment, window)
        bucket = _Bucket(moment)
        _buckets[key] = bucket
    elif moment - bucket.window_start >= window:
        bucket = _Bucket(moment)
        _buckets[key] = bucket
    bucket.count += 1
    if bucket.count > limit:
        retry = int(bucket.window_start + window - moment) + 1
        return False, max(retry, 1)
    return True, 0


def reset() -> None:
    """Test helper: clear all buckets."""
    _buckets.clear()
