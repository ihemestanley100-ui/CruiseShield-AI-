"""J7 performance smoke: local-only timings (not thresholds).

Targets (declared before measuring; demo-scale, single worker):
- reads p50 < 50 ms, writes p50 < 100 ms (local, warm)
- import + seed startup < 2 s
Prints observed means; deviations explained in docs/J7_VALIDATION.md.
Socket-free: direct handler calls on a tmp store.
"""
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.main as main
from app.store import Store


def _timed(fn, runs=20):
    samples = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples.sort()
    return samples[len(samples) // 2], sum(samples) / len(samples)


def main_() -> int:
    import shutil
    import tempfile

    tmpdir = Path(tempfile.mkdtemp(prefix="perf-smoke-"))
    t0 = time.perf_counter()
    store = Store(tmpdir / "state.json")
    seed_ms = (time.perf_counter() - t0) * 1000.0
    main.store = store

    print(f"seed: {seed_ms:.1f} ms")
    for name, fn in [
        ("health", main.health),
        ("ready", lambda: main.ready()),
        ("risk", lambda: main.get_risk("txn_84721", "network")),
        ("graph", lambda: main.get_graph("txn_84721")),
        ("case", lambda: main.get_case("case_84721")),
        ("alerts", main.list_alerts),
    ]:
        p50, mean = _timed(fn)
        print(f"{name}: p50 {p50:.2f} ms, mean {mean:.2f} ms")

    def _write():
        store.append_audit("service", "j7-perf", "perf.probe", "case",
                           "case_84721", "", "", "timing",
                           store.state["trace_id"], "trace_perf")

    p50, mean = _timed(_write)
    print(f"audit-append: p50 {p50:.2f} ms, mean {mean:.2f} ms")
    print("rss_mb: not measured (stdlib-only env, no psutil)")
    shutil.rmtree(tmpdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main_())
