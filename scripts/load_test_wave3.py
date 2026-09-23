"""Wave 3 read-burst helper.

Exercises cheap GET traffic against a running API. It does not call Groq.
Pass criteria from the plan: p95 under 200 ms and almost no read 429s.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = (pct / 100) * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    weight = rank - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def run_burst(request_fn, total: int, concurrency: int) -> dict:
    latencies: list[float] = []
    statuses: list[int] = []
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        futures = [pool.submit(request_fn) for _ in range(total)]
        for fut in as_completed(futures):
            status, elapsed_ms = fut.result()
            statuses.append(int(status))
            latencies.append(float(elapsed_ms))
    elapsed = time.perf_counter() - started
    limited = sum(1 for code in statuses if code == 429)
    return {
        "total": total,
        "concurrency": concurrency,
        "elapsed_s": round(elapsed, 3),
        "p95_ms": None if not latencies else round(percentile(latencies, 95), 2),
        "rate_limited": limited,
        "statuses": statuses,
    }


def _http_get(url: str, api_key: str):
    req = urllib.request.Request(url, headers={"X-API-Key": api_key})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
            return resp.status, (time.perf_counter() - t0) * 1000
    except urllib.error.HTTPError as exc:
        return exc.code, (time.perf_counter() - t0) * 1000


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FinPilot Wave 3 read burst")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--api-key", default="dev-key")
    parser.add_argument("--path", default="/api/health")
    parser.add_argument("--total", type=int, default=80)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--max-p95-ms", type=float, default=200)
    args = parser.parse_args(argv)

    url = args.base_url.rstrip("/") + args.path

    def call():
        return _http_get(url, args.api_key)

    try:
        probe_status, _ = call()
    except urllib.error.URLError as exc:
        print(f"API unreachable at {url}: {exc}")
        return 2

    if probe_status >= 500:
        print(f"API unhealthy ({probe_status}) at {url}")
        return 2

    summary = run_burst(call, args.total, args.concurrency)
    printable = {k: v for k, v in summary.items() if k != "statuses"}
    print(json.dumps(printable, indent=2))
    if summary["rate_limited"]:
        print(f"FAIL: {summary['rate_limited']} read requests returned 429")
        return 1
    if summary["p95_ms"] is not None and summary["p95_ms"] > args.max_p95_ms:
        print(f"FAIL: p95 {summary['p95_ms']} ms exceeds {args.max_p95_ms} ms")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
