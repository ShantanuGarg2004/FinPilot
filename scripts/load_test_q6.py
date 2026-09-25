"""Q6 mixed load: 80 cheap reads and 20 stubbed chats.

Pass line for reads is p95 under 200 ms. Chat 429s are recorded, not failed,
because the chat quota is tighter than 20 calls in one minute.
"""
from __future__ import annotations

import argparse
import json
import os
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


def _request(method: str, url: str, api_key: str, body: dict | None = None, headers: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    hdrs = {"X-API-Key": api_key}
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return resp.status, (time.perf_counter() - t0) * 1000, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, (time.perf_counter() - t0) * 1000, raw


def _summarize(name: str, rows: list[tuple[int, float, bytes]]) -> dict:
    latencies = [row[1] for row in rows]
    statuses: dict[str, int] = {}
    locked = 0
    for status, _elapsed, raw in rows:
        statuses[str(status)] = statuses.get(str(status), 0) + 1
        if b"database is locked" in raw.lower():
            locked += 1
    return {
        "name": name,
        "total": len(rows),
        "p95_ms": None if not latencies else round(percentile(latencies, 95), 2),
        "statuses": statuses,
        "sqlite_locked": locked,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FinPilot Q6 mixed load")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--api-key", default=os.getenv("API_SECRET_KEY", ""))
    parser.add_argument("--reads", type=int, default=80)
    parser.add_argument("--chats", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--max-p95-ms", type=float, default=200)
    args = parser.parse_args(argv)
    if not args.api_key:
        print("Set API_SECRET_KEY or pass --api-key")
        return 2
    base = args.base_url.rstrip("/")

    created = _request(
        "POST",
        base + "/api/profile",
        args.api_key,
        {
            "age": 30,
            "income": 100000,
            "expenses": 40000,
            "savings": 20000,
            "risk_appetite": "medium",
            "financial_goals": "q6 load",
        },
    )
    if created[0] != 201:
        print("could not create profile", created[0], created[2][:200])
        return 2
    user_id = json.loads(created[2])["user_id"]

    def read_call():
        return _request("GET", base + "/api/users", args.api_key)

    def chat_call():
        return _request(
            "POST",
            base + "/api/chat",
            args.api_key,
            {"user_id": user_id, "query": "Where should I keep an emergency fund?"},
        )

    rows_reads = []
    rows_chats = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = {pool.submit(read_call): "read" for _ in range(args.reads)}
        futures.update({pool.submit(chat_call): "chat" for _ in range(args.chats)})
        for fut in as_completed(futures):
            kind = futures[fut]
            if kind == "read":
                rows_reads.append(fut.result())
            else:
                rows_chats.append(fut.result())

    read_summary = _summarize("reads", rows_reads)
    chat_summary = _summarize("chats", rows_chats)
    print(json.dumps({"reads": read_summary, "chats": chat_summary}, indent=2))

    # One slow stubbed chat must not stop health.
    health_codes = []

    def slow_chat():
        return _request(
            "POST",
            base + "/api/chat",
            args.api_key,
            {"user_id": user_id, "query": "slow"},
            headers={"X-FinPilot-Stub-Delay-Ms": "1500"},
        )

    with ThreadPoolExecutor(max_workers=6) as pool:
        slow = pool.submit(slow_chat)
        time.sleep(0.2)
        for _ in range(5):
            health_codes.append(_request("GET", base + "/api/health", args.api_key)[0])
        slow.result()
    print(json.dumps({"health_during_slow_chat": health_codes}))

    if read_summary["p95_ms"] is None or read_summary["p95_ms"] > args.max_p95_ms:
        return 1
    if read_summary["sqlite_locked"] or chat_summary["sqlite_locked"]:
        return 1
    if any(code != 200 for code in health_codes):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
