# Remediation 1 — report jobs

**Date:** 2026-09-26
**Plan:** `docs/ARCHITECTURE_REMEDIATION_PLAN.md` issue 1
**Verdict:** The generate request no longer calls Groq. A separate process does.

Chat is unchanged. Issue 2 has not been started.

---

## 1. What shipped

`POST /api/generate-report` validates the profile, inserts one `jobs` row, and returns **202** `{ "job_id", "status" }`. A second click while that job is `queued` or `running` returns the same job. It does not start a second Groq call.

`python -m services.jobs.worker` claims one queued row with `FOR UPDATE SKIP LOCKED`, scores the profile, calls Groq, saves the advisory text, then builds the PDF. A PDF failure still marks the job `succeeded`. The previous report stays in place when generation fails. A `running` row older than `WORKER_TIMEOUT_SECONDS` is marked `failed` with `worker_lost` and is not sent to Groq again.

The worker checks `users.account_id` against the account stored on the job. It does not use the request actor. `NULL` matches `NULL`, which is how an API-key-created profile is stored today.

`GET /api/report/<user_id>` still returns the saved report. It adds `job` while the newest job is `queued`, `running`, or `failed`. A succeeded job is omitted. The Dashboard and Advisory screens poll that GET about every 2 seconds and keep Generate disabled until the job settles or 120 seconds pass.

## 2. Tests

`python -m pytest -q` — **100 passed** in 16 seconds.

New cases in `tests/test_remediation_1_jobs.py`:

| Case | Result |
| --- | --- |
| POST does not call Groq; a second POST reuses `job_id` | Pass |
| Another signed-in account cannot enqueue that profile | Pass |
| A failed regenerate leaves the previous advisory text | Pass |
| A stale `running` row becomes `worker_lost` with no Groq call | Pass |
| A job whose account does not own the profile is `not_found` | Pass |

Existing generate tests now accept 202 and call `process_once()` when they need the finished report.

## 3. Process check

Enqueue on PostgreSQL took **17 ms**. That request did not call Groq.

| Run | Result |
| --- | --- |
| Child process, `GROQ_STUB=true`, `process_once()` | `succeeded` |
| Child process, live Groq, one profile on a temporary schema | `succeeded` in about 11 seconds. Advisory text was 4698 characters. PDF was stored. |
| `python -m services.jobs.worker` from the repo root | Logged `Report worker watching the jobs table`, then the process was stopped |

The live call used a temporary schema (`DB_NAME` pointed at a temp path). It did not write a report onto the profiles in the `public` schema.

The Flask process already listening on port 5000 is still the previous code. Restart it, then start the worker, before trying Generate in the browser. Vite on port 5173 has compiled the new poll hook.

## 4. How to run the worker

From the repository root, with Postgres up and the same `.env` the API uses:

```bash
python -m services.jobs.worker
```

Leave that process running next to Flask. One worker is enough for this issue.

## 5. Left for later

- Chat still calls Groq inside the request. Issue 6 decides whether that joins this queue.
- The API key can still read every account. That is issue 2.
- Docker Compose does not start the worker.
- The browser flow was not clicked through, because the running API process does not include this change yet.
