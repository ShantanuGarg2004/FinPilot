# Q6 Implementation & Testing Report

**Date:** 2026-09-25  
**Scope:** `docs/PLATFORM_QUALITY_WAVES.md` — Q6 (prove about 100 concurrent users)  
**Host:** Windows. Waitress 3.0.2 installed on the machine. It is not an application dependency in `requirements.txt`.  
**Server:** `python -m waitress --listen=127.0.0.1:5000 --channel-timeout=120 --threads=6 --call app:create_app`  
**Groq:** `GROQ_STUB=true`. `ask_gpt` returned fixed text and did not call the provider.

---

## 1. Summary

Cheap reads on 6 Waitress threads stayed under the 200 ms line. SQLite did not report `database is locked` during that measurement. App data was later moved to PostgreSQL. See `docs/APP_DATABASE_POSTGRES.md` and `docs/testing_reports/APP_DATABASE_MIGRATION_TEST_REPORT.md`. No report job queue was added.

| Check | Result |
|---|---|
| `GET /api/health`, 80 requests, concurrency 20 | **Pass.** p95 **67.24 ms**, 80×200, 0×429 |
| `GET /api/users`, 80 requests, concurrency 20 | **Pass.** p95 **176.46 ms**, 80×200, 0×429 |
| Mixed: 80 `GET /api/users` and 20 stubbed `POST /api/chat` together | Reads p95 **1261.27 ms** (all 200). Chats **15×200** and **5×429**. 0 SQLite lock errors |
| Health during one 1.5 s stubbed chat | **5×200** |
| Limiter rows after the Waitress process was stopped | **37 buckets, 251 hits**, same counts after the process exited |
| Move app data to PostgreSQL (Q6.4) | **Done.** Profiles, reports, and chat use database `finpilot` on the same PostgreSQL server as the limiter. `finpilot_ratelimit` is unchanged. A leftover `finance.db` is copied once when the new database has no profiles. |
| Report job queue (Q6.5) | **Not done.** The stub returns immediately, so workers were not stuck on Groq |

The mixed-run read p95 is queue time. Six threads were shared with the chat calls. It is not a SQLite lock and it is not a Groq stall. The pass line in `docs/CAPACITY_RUNBOOK.md` is the cheap GET measured on its own.

Chat 429s match the existing chat quota (15 per minute). The limiter allowed 15 and refused 5.

---

## 2. What shipped

| Task | Change |
|---|---|
| Q6.1 | The measurement used Waitress, not `python app.py`. |
| Q6.2 | `scripts/load_test_q6.py` runs 80 list reads and 20 chats. `GROQ_STUB=true` skips Groq. A delay header exists only while the stub is on, for the in-flight health check. |
| Q6.3 | Waitress is one process. A single thread cannot be killed while the others stay up. Health stayed 200 during a slow stubbed chat. Postgres still held the limiter counts after the process exited. |
| Q6.4 | App data moved to PostgreSQL database `finpilot`. Copy check: `docs/testing_reports/APP_DATABASE_MIGRATION_TEST_REPORT.md`. |
| Q6.5 | Not triggered. |
| Q6.6 | This report. |

---

## 3. Residual risk

A mixed burst of list reads and chats on 6 threads can push read latency above 200 ms even when Groq is instant. That measurement was on SQLite. The app database is now PostgreSQL. The thread-queue limit and the missing job queue are unchanged.

Waitress cannot show the “kill one worker, the others keep serving” check. That check still needs Gunicorn on Linux.

`GROQ_STUB` defaults to off. A normal `python app.py` start still calls Groq.

---

## 4. How to reproduce

```bash
pip install waitress
set GROQ_STUB=true
python -m waitress --listen=127.0.0.1:5000 --channel-timeout=120 --threads=6 --call app:create_app
```

In another shell, with `API_SECRET_KEY` set:

```bash
python scripts/load_test_q6.py
python scripts/load_test_wave3.py --path /api/health --total 80 --concurrency 20
python scripts/load_test_wave3.py --path /api/users --total 80 --concurrency 20
```
