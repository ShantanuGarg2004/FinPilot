# Remediation 4 — health notices a dead application database

**Date:** 2026-09-26
**Plan:** `docs/ARCHITECTURE_REMEDIATION_PLAN.md` issue 4
**Verdict:** `GET /api/health` runs `SELECT 1` on the application database. If that ping fails, the probe is `degraded` and returns **503**, even when the rate-limit store is up.

The route stays public. The body does not include the database URL, credentials, or row counts.

---

## 1. What shipped

`ping_database()` borrows a connection with `get_connection()`, sets a 2-second `statement_timeout` for that transaction only (`SET LOCAL`), and runs `SELECT 1`. The connection is closed in a `finally` block. It is not stored on `g.db_conn`, so the request teardown does not share it with profile queries.

`status` is `ok` only when the limiter ping is not `False` and `database_ok` is true. Otherwise `status` is `degraded` and the HTTP status is 503.

`database_backend` is `postgresql` when the ping succeeded and `unavailable` when it did not. `sqlite_busy_timeout_ms` is gone from this JSON. The config constant remains until issue 7.

A failed ping is logged as “Application database health ping failed” without the exception text, so a connection error cannot write the database URL into the log.

## 2. Tests

`python -m pytest -q` — **111 passed** (108 before this issue).

| Case | Result |
| --- | --- |
| Health against the test database | 200, `database_ok: true`, `database_backend: postgresql` |
| `ping_database` forced to fail | 503, `status: degraded`, `database_ok: false`, `database_backend: unavailable` |
| Body | no `sqlite_busy_timeout_ms`, no `database_url` |
| Ping inside a request | `g.db_conn` stays unset |

## 3. Left for later

- No credentials table and no scopes. That is issue 5.
- Health does not check Groq or the report worker.
- `SQLITE_BUSY_TIMEOUT_MS` is still a config constant. Issue 7 deletes it once nothing reads it.
- Restart Flask so the process that is already listening returns this probe.
