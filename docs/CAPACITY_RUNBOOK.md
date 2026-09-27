# Capacity runbook

The web process serves HTTP. Groq runs in a second process: `python -m services.jobs.worker`. Application data is PostgreSQL database `finpilot`. Rate-limit counters are `finpilot_ratelimit`. The measured result is `docs/testing_reports/REMEDIATION_6_LOAD_TEST_REPORT.md`.

## Worker formula

The number below is Waitress threads or Gunicorn workers for the **web** process, not the Groq worker.

```
threads or workers = max(2, peak_concurrent_llm + headroom)
```

Defaults: `PEAK_CONCURRENT_LLM=4`, `WORKER_HEADROOM=2` → **6**.

`GET /api/health` returns `recommended_workers`. The limiter still caps `llm_report` (5 per minute) and `llm_chat` (15 per minute) on the enqueue request.

## Timeouts

| Setting | Default | Role |
|---|---|---|
| `GROQ_TIMEOUT_SECONDS` | 90 | Groq HTTP client timeout inside the job worker |
| `WORKER_TIMEOUT_SECONDS` | 120 | A `running` job older than this is failed as `worker_lost`. Match the web server channel timeout to this value. |

`WORKER_TIMEOUT_SECONDS` must be greater than `GROQ_TIMEOUT_SECONDS`.

## How to run

Local development is two processes:

```bash
python app.py
python -m services.jobs.worker
```

Windows (Waitress) replaces `python app.py` only. Keep the job worker running beside it:

```bash
pip install waitress
python -m waitress --host=127.0.0.1 --port=5000 --threads=6 --channel-timeout=120 --call app:create_app
```

Linux (Gunicorn), same split:

```bash
pip install gunicorn
gunicorn --workers 6 --timeout 120 --bind 0.0.0.0:5000 "app:create_app()"
```

Match `--timeout` / `--channel-timeout` to `WORKER_TIMEOUT_SECONDS`. Match the web thread or worker count to `recommended_workers`.

## Load check

The issue 6 script signs in with `BOOTSTRAP_ACCOUNT_EMAIL` and `BOOTSTRAP_ACCOUNT_PASSWORD`. It does not take an API key.

```bash
python scripts/load_test_issue6.py
```

Start the web process and do not treat a pass line in an older script as the current result. The written result is the issue 6 report.

## Chaos

Stop the job worker while a report is `running`. The next time a worker claims work, a `running` job older than `WORKER_TIMEOUT_SECONDS` is marked `failed` with `worker_lost`. The web process should keep serving `GET /api/health`. Rate-limit counters stay in PostgreSQL when `RATELIMIT_STORAGE_BACKEND=sql`.
