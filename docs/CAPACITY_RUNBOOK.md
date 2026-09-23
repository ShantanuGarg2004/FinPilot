# Capacity runbook (Wave 3)

FinPilot keeps report generation synchronous. Capacity comes from worker count, timeouts, and SQLite waiting on the writer instead of failing immediately.

The report job queue and the app-database move to PostgreSQL stay deferred until a load test shows hardened SQLite or sync Groq calls failing.

## Worker formula

```
workers = max(2, peak_concurrent_llm + headroom)
```

Defaults: `PEAK_CONCURRENT_LLM=4`, `WORKER_HEADROOM=2` → **6 workers**.

That covers the early-production band (about 4–8). Reads stay cheap; the limit is how many Groq calls can be in flight. The rate limiter still caps `llm_report` (5/min) and `llm_chat` (15/min).

`GET /api/health` returns `recommended_workers`.

## Timeouts

| Setting | Default | Role |
|---|---|---|
| `GROQ_TIMEOUT_SECONDS` | 90 | Groq HTTP client timeout |
| `WORKER_TIMEOUT_SECONDS` | 120 | WSGI worker / proxy timeout |

`WORKER_TIMEOUT_SECONDS` must be greater than `GROQ_TIMEOUT_SECONDS`. A slow Groq call then returns HTTP **504** with `code: upstream_timeout` instead of the worker being killed.

`SQLITE_BUSY_TIMEOUT_MS` (default 5000) is applied on every SQLite connection via `PRAGMA busy_timeout`.

## How to run

Local development stays `python app.py` (one process).

Windows (Waitress):

```bash
pip install waitress
waitress-serve --listen=127.0.0.1:5000 --channel-timeout=120 --threads=6 --call app:create_app
```

Linux (Gunicorn):

```bash
pip install gunicorn
gunicorn --workers 6 --timeout 120 --bind 0.0.0.0:5000 "app:create_app()"
```

Match `--timeout` / `--channel-timeout` to `WORKER_TIMEOUT_SECONDS`. Match worker or thread count to `recommended_workers`.

## Load check

With the API already running:

```bash
python scripts/load_test_wave3.py --base-url http://127.0.0.1:5000 --api-key YOUR_KEY --path /api/health --total 80 --concurrency 20
```

Pass: p95 under 200 ms and zero HTTP 429s on that read path. This script does not call Groq.

## Chaos

Kill one worker while a generate is in flight. Other workers should keep serving `GET /api/health`. Rate-limit counters stay in PostgreSQL when `RATELIMIT_STORAGE_BACKEND=sql`, so a restart does not reset quotas.

## Deferred

| Item | Why it waits |
|---|---|
| Report job queue | Advisory text is already saved before PDF |
| App SQLite → PostgreSQL | Only if this load check or real traffic shows write contention |
| App-DB connection pool | Follows the PostgreSQL move |
