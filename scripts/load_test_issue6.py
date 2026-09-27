"""Issue 6 capacity rows. Uses the existing session-cookie helper.

The host is started separately: Waitress, 6 threads, channel-timeout 120, GROQ_STUB=true.
This script does not change quotas. It does not call live Groq.

Rows, in order: health, list profiles, enqueue burst, reads while report jobs
are running, then the chat gate. Profiles created here are deleted at the end.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.http_session import data_headers, login_cookie
from scripts.load_test_wave3 import percentile

PROFILE = {
    "age": 30,
    "income": 100000,
    "expenses": 40000,
    "savings": 20000,
    "risk_appetite": "medium",
}


def _request(method: str, url: str, cookie: str, body: dict | None = None, timeout: float = 30):
    data = None if body is None else json.dumps(body).encode()
    headers = data_headers(cookie)
    if body is None:
        headers.pop("Content-Type", None)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, (time.perf_counter() - started) * 1000, raw
    except urllib.error.HTTPError as exc:
        return exc.code, (time.perf_counter() - started) * 1000, exc.read()
    except urllib.error.URLError as exc:
        return 0, (time.perf_counter() - started) * 1000, str(exc.reason).encode()


def _burst(calls: list) -> list[tuple[int, float, bytes]]:
    rows = []
    with ThreadPoolExecutor(max_workers=max(1, len(calls))) as pool:
        futures = [pool.submit(call) for call in calls]
        for fut in futures:
            rows.append(fut.result())
    return rows


def _summary(rows: list[tuple[int, float, bytes]]) -> dict:
    latencies = [row[1] for row in rows if row[0] != 0]
    statuses: dict[str, int] = {}
    for status, _elapsed, _raw in rows:
        statuses[str(status)] = statuses.get(str(status), 0) + 1
    return {
        "total": len(rows),
        "p95_ms": None if not latencies else round(percentile(latencies, 95), 2),
        "statuses": statuses,
        "server_errors": sum(1 for status, _e, _r in rows if status >= 500),
        "unauthorized": sum(1 for status, _e, _r in rows if status == 401),
        "transport_errors": sum(1 for status, _e, _r in rows if status == 0),
    }


def _profile(label: str) -> dict:
    body = dict(PROFILE)
    body["financial_goals"] = label
    return body


def _create_profile(base: str, cookie: str, label: str) -> int:
    status, _ms, raw = _request("POST", base + "/api/profile", cookie, _profile(label))
    if status != 201:
        raise RuntimeError(f"create profile failed: {status} {raw[:180]!r}")
    return int(json.loads(raw)["user_id"])


def _named_ids(user_ids: list[int]) -> tuple[str, dict]:
    params = {f"id{index}": user_id for index, user_id in enumerate(user_ids)}
    marks = ", ".join(f":id{index}" for index in range(len(user_ids)))
    return marks, params


def _job_counts(user_ids: list[int]) -> dict[str, int]:
    from database.db import get_connection

    if not user_ids:
        return {}
    marks, params = _named_ids(user_ids)
    conn = get_connection()
    try:
        rows = conn.execute(
            f"""
            SELECT status, COUNT(*) AS n
            FROM jobs
            WHERE kind = 'report' AND user_id IN ({marks})
            GROUP BY status
            """,
            params,
        ).fetchall()
    finally:
        conn.close()
    return {row["status"]: int(row["n"]) for row in rows}


def _enqueue(base: str, cookie: str, user_id: int):
    return _request(
        "POST",
        base + "/api/generate-report",
        cookie,
        {"user_id": user_id},
    )


def _start_claim_threads(count: int) -> list[threading.Thread]:
    """One process, many claims, one connection pool. Ten processes would open ten pools."""
    from services.jobs.worker import process_once

    threads = []
    for _ in range(count):
        thread = threading.Thread(target=process_once, daemon=True)
        thread.start()
        threads.append(thread)
    return threads


def _join_threads(threads: list[threading.Thread]) -> None:
    for thread in threads:
        thread.join(timeout=40)


def _top_up(base: str, cookie: str, user_ids: list[int], target: int) -> dict:
    """Enqueue until `target` jobs are queued or running, without raising quotas."""
    notes = []
    for attempt in range(4):
        counts = _job_counts(user_ids)
        active = counts.get("queued", 0) + counts.get("running", 0)
        if active >= target:
            notes.append({"attempt": attempt, "active": active, "statuses": counts})
            return {"active": active, "notes": notes}
        need = target - active
        idle = []
        # A profile with a queued or running job must not be asked again.
        from database.db import get_connection
        marks, params = _named_ids(user_ids)
        conn = get_connection()
        try:
            rows = conn.execute(
                f"""
                SELECT user_id FROM jobs
                WHERE kind = 'report' AND status IN ('queued', 'running')
                  AND user_id IN ({marks})
                """,
                params,
            ).fetchall()
        finally:
            conn.close()
        busy = {int(row["user_id"]) for row in rows}
        idle = [user_id for user_id in user_ids if user_id not in busy][:need]
        results = _burst([lambda uid=uid: _enqueue(base, cookie, uid) for uid in idle])
        accepted = sum(1 for status, _ms, _raw in results if status == 202)
        limited = sum(1 for status, _ms, _raw in results if status == 429)
        notes.append({
            "attempt": attempt,
            "asked": len(idle),
            "accepted": accepted,
            "limited": limited,
            "statuses": _summary(results)["statuses"],
        })
        if accepted == 0 and limited:
            time.sleep(70)
            continue
        if accepted == 0:
            break
    counts = _job_counts(user_ids)
    return {
        "active": counts.get("queued", 0) + counts.get("running", 0),
        "notes": notes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Issue 6 capacity rows")
    parser.add_argument("--row", choices=("all", "reads", "chat"), default="all")
    args = parser.parse_args(argv)

    import config
    from database.models import create_tables

    base = os.environ.get("ISSUE6_BASE_URL", "http://127.0.0.1:5001").rstrip("/")
    email = os.environ.get("BOOTSTRAP_ACCOUNT_EMAIL", "") or (config.Config.BOOTSTRAP_ACCOUNT_EMAIL or "")
    password = os.environ.get("BOOTSTRAP_ACCOUNT_PASSWORD", "") or (config.Config.BOOTSTRAP_ACCOUNT_PASSWORD or "")
    if not email or not password:
        print("Set BOOTSTRAP_ACCOUNT_EMAIL and BOOTSTRAP_ACCOUNT_PASSWORD")
        return 2

    create_tables()
    cookie = login_cookie(base, email, password)
    health_status, _ms, health_raw = _request("GET", base + "/api/health", cookie, timeout=10)
    health_body = json.loads(health_raw)
    report: dict = {
        "row": args.row,
        "base_url": base,
        "flask_env": config.Config.FLASK_ENV,
        "groq_stub_in_this_process": bool(config.Config.GROQ_STUB),
        "stub_hold_seconds": os.environ.get("GROQ_STUB_HOLD_SECONDS", ""),
        "llm_report": config.Config.RATELIMIT_LLM_REPORT,
        "llm_report_user": config.Config.RATELIMIT_LLM_REPORT_USER,
        "llm_chat": config.Config.RATELIMIT_LLM_CHAT,
        "read_light": config.Config.RATELIMIT_READ_LIGHT,
        "health_probe": {
            "status_code": health_status,
            "status": health_body.get("status"),
            "database_ok": health_body.get("database_ok"),
            "ratelimit_store_ok": health_body.get("ratelimit_store_ok"),
        },
    }
    if health_status != 200 or health_body.get("database_ok") is not True:
        print(json.dumps(report, indent=2))
        return 2

    created_ids: list[int] = []
    threads: list[threading.Thread] = []
    try:
        if args.row == "all":
            report["health"] = _summary(_burst(
                [lambda: _request("GET", base + "/api/health", cookie) for _ in range(100)]
            ))
            report["users"] = _summary(_burst(
                [lambda: _request("GET", base + "/api/users", cookie) for _ in range(100)]
            ))
            for index in range(20):
                created_ids.append(_create_profile(base, cookie, f"issue6-generate-{index}"))
            generate_rows = _burst([
                lambda uid=uid: _enqueue(base, cookie, uid) for uid in created_ids
            ])
            report["generate"] = _summary(generate_rows)
            report["generate"]["jobs_accepted"] = sum(
                1 for status, _ms, _raw in generate_rows if status == 202
            )

        if args.row in ("all", "reads"):
            if args.row == "reads":
                for index in range(10):
                    created_ids.append(_create_profile(base, cookie, f"issue6-running-{index}"))
            topped = _top_up(base, cookie, created_ids, 10)
            report["enqueue_for_running"] = topped
            threads = _start_claim_threads(10)
            running_seen = 0
            deadline = time.perf_counter() + 20
            while time.perf_counter() < deadline:
                running_seen = _job_counts(created_ids).get("running", 0)
                if running_seen >= 10:
                    break
                time.sleep(0.2)
            report["running_when_reads_started"] = running_seen
            report["reads_during_jobs"] = _summary(_burst(
                [lambda: _request("GET", base + "/api/users", cookie) for _ in range(80)]
            ))
            report["jobs_after_reads"] = _job_counts(created_ids)
            _join_threads(threads)
            threads = []

        if args.row in ("all", "chat"):
            chat_profile = _create_profile(base, cookie, "issue6-chat")
            created_ids.append(chat_profile)

            def read_call():
                return _request("GET", base + "/api/users", cookie)

            def chat_call():
                return _request(
                    "POST",
                    base + "/api/chat",
                    cookie,
                    {"user_id": chat_profile, "query": "Where should I keep an emergency fund?"},
                )

            read_rows = []
            chat_rows = []
            with ThreadPoolExecutor(max_workers=100) as pool:
                futures = {pool.submit(read_call): "read" for _ in range(80)}
                futures.update({pool.submit(chat_call): "chat" for _ in range(20)})
                for fut in as_completed(futures):
                    if futures[fut] == "read":
                        read_rows.append(fut.result())
                    else:
                        chat_rows.append(fut.result())
            report["chat_gate_reads"] = _summary(read_rows)
            report["chat_gate_chats"] = _summary(chat_rows)
            report["chat_jobs_accepted"] = sum(
                1 for status, _elapsed, raw in chat_rows if status == 202 and b"job_id" in raw
            )
    finally:
        _join_threads(threads)
        for user_id in created_ids:
            _request("DELETE", base + f"/api/profile/{user_id}", cookie)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
