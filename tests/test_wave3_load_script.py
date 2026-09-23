"""Unit coverage for the Wave 3 burst helper (no live server)."""
from scripts.load_test_wave3 import percentile, run_burst


def test_percentile_interpolates():
    assert percentile([10, 20, 30, 40], 95) == 38.5


def test_run_burst_collects_status_and_latency():
    def call():
        return 200, 12.5

    summary = run_burst(call, total=8, concurrency=4)
    assert summary["total"] == 8
    assert summary["rate_limited"] == 0
    assert summary["p95_ms"] == 12.5
    assert summary["statuses"] == [200] * 8
