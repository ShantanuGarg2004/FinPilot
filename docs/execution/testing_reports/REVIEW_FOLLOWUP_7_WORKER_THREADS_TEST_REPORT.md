# Review follow-up 7 — worker claim threads

**Date:** 2026-09-27
**Plan:** `docs/planning/ARCHITECTURE_REVIEW_FOLLOWUP_PLAN.md` issue 7
**Verdict:** The worker can run more than one claim loop inside the one process. The default is 1, so throughput and the Groq bill are unchanged. Pool size is still 10.

---

## 1. What shipped

`WORKER_CLAIM_THREADS` defaults to 1 in `config.py` and in `.env.example`. `claim_thread_count()` never returns less than 1. With 1, `main` runs the same loop as before: claim one job, and sleep 0.5 seconds when the queue is empty. A higher value starts that many threads in the same process, sharing one engine. Extra operating-system processes were not added. `pool_size` and `max_overflow` were not changed. The default was not raised.

## 2. Tests

`python -m pytest -q` — **134 passed** (131 before this issue, plus 3).

| Case | Result |
| --- | --- |
| Count 1, 0, and 3 | 1, 1, and 3 |
| One claim thread and an empty queue | `process_once` runs, then sleep of 0.5 seconds |
| Two queued report jobs | Two `process_once` calls succeed on the same engine, pool max size 10 |
