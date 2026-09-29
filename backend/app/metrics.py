"""Latency metrics for itinerary generation (monotonic clock)."""

from __future__ import annotations

import statistics
import threading
import time

_lock = threading.Lock()
_samples: list[float] = []  # seconds
_errors: int = 0
_total: int = 0


def now() -> float:
    """Monotonic timestamp (seconds) — perf_counter is monotonic with best resolution."""
    return time.perf_counter()


def elapsed_seconds(start: float, end: float) -> float:
    return max(0.0, end - start)


def record_latency(seconds: float, *, ok: bool = True) -> None:
    with _lock:
        _samples.append(float(seconds))
        global _errors, _total
        _total += 1
        if not ok:
            _errors += 1


def clear() -> None:
    with _lock:
        _samples.clear()
        global _errors, _total
        _errors = 0
        _total = 0


def _percentile(data: list[float], pct: float) -> float:
    if not data:
        return 0.0
    ordered = sorted(data)
    k = (len(ordered) - 1) * (pct / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(ordered) - 1)
    frac = k - lo
    return ordered[lo] + (ordered[hi] - ordered[lo]) * frac


def summary() -> dict:
    with _lock:
        data = list(_samples)
        total = _total
        errors = _errors
    if not data:
        return {"count": total, "median_ms": 0.0, "p95_ms": 0.0, "error_rate": 0.0}
    median_ms = statistics.median(data) * 1000.0
    p95_ms = _percentile(data, 95) * 1000.0
    error_rate = (errors / total) if total else 0.0
    return {"count": total, "median_ms": round(median_ms, 2), "p95_ms": round(p95_ms, 2), "error_rate": round(error_rate, 4)}
