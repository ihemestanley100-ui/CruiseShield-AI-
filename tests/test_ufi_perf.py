"""UFI performance smoke: bounded wall-clock checks on synthetic
fixtures. Generous limits; a failure means real regression, not a
missed benchmark. Timings are environment-local, never production
claims."""
from __future__ import annotations

import time

import pytest

from app import detection as det_mod
from app import tracing as tracing_mod


def _txn(i, branches=4):
    return {"transaction_id": "p%d" % i, "channel": "TRANSFER",
            "amount_minor": 1000 + i, "currency": "NGN",
            "sender_account_id": "acct_%d" % (i % branches),
            "receiver_account_id": "acct_%d" % ((i + 1) % branches),
            "occurred_at": "2026-11-07T10:00:00Z",
            "device_id": "dev_%d" % (i % 7),
            "phone_id": "phn_%d" % (i % 5),
            "merchant_id": "mch_%d" % (i % 3)}


PERF_TXNS = 400
PERF_BUDGET_SECONDS = 60.0
TRACE_BUDGET_SECONDS = 10.0


def test_detection_smoke_bounded():
    txns = [_txn(i) for i in range(PERF_TXNS)]
    started = time.perf_counter()
    result = det_mod.evaluate_all(txns, [])
    elapsed = time.perf_counter() - started
    assert result["signals"] is not None
    assert elapsed < PERF_BUDGET_SECONDS, elapsed


def test_trace_build_smoke_bounded():
    txns = [_txn(i) for i in range(PERF_TXNS)]
    started = time.perf_counter()
    trace = tracing_mod.build_trace(txns, [], "p0", max_hops=3)
    elapsed = time.perf_counter() - started
    assert trace["visited_transactions"]
    assert elapsed < TRACE_BUDGET_SECONDS, elapsed


@pytest.mark.skip(reason="load profile needs hosted data volume; "
                        "not asserted in-tree")
def test_hosted_load_profile():
    raise AssertionError("unreachable")
