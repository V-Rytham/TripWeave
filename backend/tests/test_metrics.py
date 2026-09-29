import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.app import metrics


def test_record_and_summary():
    metrics.clear()
    metrics.record_latency(0.1, ok=True)
    metrics.record_latency(0.2, ok=True)
    metrics.record_latency(0.3, ok=True)
    s = metrics.summary()
    assert s["count"] == 3
    assert 100 <= s["median_ms"] <= 300
    assert s["p95_ms"] >= s["median_ms"]
    assert s["error_rate"] == 0.0


def test_error_rate():
    metrics.clear()
    metrics.record_latency(0.1, ok=True)
    metrics.record_latency(0.1, ok=False)
    s = metrics.summary()
    assert s["count"] == 2
    assert s["error_rate"] == 0.5


def test_monotonic_clock():
    t1 = metrics.now()
    t2 = metrics.now()
    assert t2 >= t1
    assert metrics.elapsed_seconds(t1, t2) >= 0.0
