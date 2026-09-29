"""Repeatable itinerary-generation benchmark (mock integrations by default).

Measures time from accepted request to completed itinerary response using a
monotonic clock. Email sending time is NOT included.

Usage:
    MOCK_AGENT=true python benchmark.py --requests 20
    MOCK_AGENT=true python backend/benchmark.py --requests 20 --out benchmark-results.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("MOCK_AGENT", "true")
os.environ.setdefault("MOCK_EMAIL", "true")

from backend.app import metrics
from backend.app.agent_adapter import generate_itinerary
from backend.app.validation import TripRequest


def representative_requests() -> list[TripRequest]:
    base = dt.date.today() + dt.timedelta(days=30)
    dests = ["Paris", "Tokyo", "New York", "Amsterdam", "Barcelona"]
    reqs = []
    for i, d in enumerate(dests):
        reqs.append(TripRequest(
            origin="Madrid", destination=d,
            outbound_date=base + dt.timedelta(days=i),
            return_date=base + dt.timedelta(days=i + 6),
            adults=2 if i % 2 == 0 else 1, children=0,
            hotel_class=4, rooms=1,
            user_prompt=f"Benchmark trip {i}: prefer central locations and direct flights.",
        ))
    return reqs


def percentile(data: list[float], pct: float) -> float:
    if not data:
        return 0.0
    ordered = sorted(data)
    k = (len(ordered) - 1) * (pct / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--out", type=str, default="benchmark-results.json")
    args = parser.parse_args()

    pool = representative_requests()
    latencies: list[float] = []
    errors = 0
    metrics.clear()
    for i in range(args.requests):
        req = pool[i % len(pool)]
        start = time.perf_counter()
        try:
            generate_itinerary(req)
            latencies.append((time.perf_counter() - start) * 1000.0)
            metrics.record_latency(latencies[-1] / 1000.0, ok=True)
        except Exception:
            errors += 1
            metrics.record_latency(time.perf_counter() - start, ok=False)

    result = {
        "label": "LOCAL TEST RESULTS — not production latency",
        "config": {
            "mock_agent": os.environ.get("MOCK_AGENT"),
            "mock_email": os.environ.get("MOCK_EMAIL"),
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "sample_count": len(latencies),
        "errors": errors,
        "error_rate": round(errors / args.requests, 4) if args.requests else 0.0,
        "median_latency_ms": round(statistics.median(latencies), 2) if latencies else 0.0,
        "p95_latency_ms": round(percentile(latencies, 95), 2) if latencies else 0.0,
        "min_latency_ms": round(min(latencies), 2) if latencies else 0.0,
        "max_latency_ms": round(max(latencies), 2) if latencies else 0.0,
    }
    print(json.dumps(result, indent=2))
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
