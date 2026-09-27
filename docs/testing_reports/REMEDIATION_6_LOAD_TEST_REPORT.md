# Remediation 6 — capacity measurement

**Date:** 2026-09-27
**Plan:** `docs/ARCHITECTURE_REMEDIATION_PLAN.md` issue 6
**Verdict:** This host does not meet the written pass lines for 100 concurrent health checks or 100 concurrent profile lists. Report enqueue does. Eighty lists while 10 report jobs were running, and the chat gate after chat was queued, are both still over 300 ms. It is not fair to say that about 100 people can load the app and list their profiles at once, or that a report no longer freezes those reads.

The five live Groq jobs were not run. That row costs money and was not accepted.

---

## 1. Host

Waitress, 6 threads, `channel-timeout` 120, on `http://127.0.0.1:5001`. Port 5000 was already `python app.py`, so it was not the host and it was not stopped.

`GROQ_STUB=true` on that Waitress process. `FLASK_ENV=development`, so the light-read quota is 600 per minute. The limiter store is PostgreSQL. Health before the runs: `database_ok` true, `ratelimit_store_ok` true.

The client logged in as the bootstrap account and sent the session cookie. It did not send `X-API-Key`. Quotas were not changed. Profiles created for the runs were deleted afterward.

```text
cmd /c "set GROQ_STUB=true&& python -m waitress --host=127.0.0.1 --port=5001 --threads=6 --channel-timeout=120 --call app:create_app"
python scripts/load_test_issue6.py
```

## 2. Pass lines

| Run | Result | Pass line |
| --- | --- | --- |
| 100 concurrent `GET /api/health` | p95 **367.78 ms**, 100×200, no 5xx | p95 under 200 ms. **Fail** |
| 100 concurrent `GET /api/users` | p95 **421.33 ms**, 100×200, no 5xx, no 401 | p95 under 300 ms. **Fail** |
| 20 concurrent `POST /api/generate-report` | p95 **114.82 ms**, **5×202**, **15×429** | p95 under 300 ms. **Pass**, with the quota below |
| 80 lists while 10 report jobs are `running` | p95 **334.79 ms**, 80×200, 10 jobs still `running` after the burst | p95 under 300 ms. **Fail** |
| Chat gate, before chat was queued | read p95 **526.63 ms**, 80×200. Chats **15×200**, **5×429**. Replies were the stub | p95 under 300 ms. **Fail** |
| Chat gate, after chat was queued | read p95 **356.86 ms**, 80×200. Chats **15×202**, **5×429** | p95 under 300 ms. **Fail** |
| 5 live report jobs | Not run | — |

Every list and health response was 200. The misses are queue time on 6 threads, not 429s and not 5xx.

The generate quota is **5 per minute** for the account and **10 per hour** for each profile. Twenty concurrent enqueues on twenty profiles accepted 5 jobs and rate-limited 15. That is the quota, not a dropped request.

The 10 running jobs used a 12-second stub hold inside the worker (`GROQ_STUB_HOLD_SECONDS=12`) so the rows stayed `running` for the whole read burst. Ten claim threads shared one process and one connection pool. An earlier attempt started 10 separate worker processes; that read p95 was 1168.82 ms and is not the result, because each process opens its own pool.

```text
cmd /c "set GROQ_STUB=true&& set GROQ_STUB_HOLD_SECONDS=12&& python scripts/load_test_issue6.py --row reads"
python scripts/load_test_issue6.py --row chat
```

## 3. What changed because the chat gate failed

The first chat gate failed, so chat left the web request. `POST /api/chat` now returns **202** and a job id. The same worker that runs reports calls Groq and then stores the turn. A failed chat is still not stored. The screen polls history for up to 120 seconds.

`python -m pytest -q` — **117 passed**.

The rerun is the second chat row above. It is faster than the synchronous stub and still over 300 ms. No further capacity claim is made from it.

The Flask process on port 5000 is still the old debug server. Restart it to serve the chat queue. The measurement Waitress on 5001 was stopped.

## 4. Left for later

- The live sample of 5 report jobs, after the cost is accepted.
- Issue 7. This was not a second pass at the SQL.
