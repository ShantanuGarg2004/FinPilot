# Review follow-up 3 — health body and the local database default

**Date:** 2026-09-27
**Plan:** `docs/planning/ARCHITECTURE_REVIEW_FOLLOWUP_PLAN.md` issue 3
**Verdict:** Public health returns status and the two probe flags. A production-shaped process refuses the local `finpilot` database when that URL still has the dev password.

---

## 1. What shipped

`GET /api/health` still takes no cookie and still pings the application database and the rate-limit store. The body is `status`, `database_ok`, and `ratelimit_store_ok`. Timeouts, the recommended worker count, and backend names are no longer in that body. A failed ping is still HTTP 503. The ping still does not log the exception text.

`Config.validate` refuses to start when `FLASK_ENV` is outside `development`, `dev`, and `local` and `APP_DATABASE_URL` is the local Compose database: the database name is `finpilot` and the URL still contains the dev password. The error says the URL is still the local default. It does not include the password or the host. `development` still accepts that URL, and Compose is unchanged.

The test database is named `finpilot_test` on the same local server. That name is not the local default, so the suite can keep starting in a production-shaped environment. A production URL that points at the database named `finpilot` with the dev password does not start.

## 2. Tests

`python -m pytest -q` — **128 passed** (126 before this issue, plus 2).

| Case | Result |
| --- | --- |
| Health when the database answers | 200, `status` ok, `database_ok` true, `ratelimit_store_ok` true |
| Health when the database ping fails | 503, `status` degraded, `database_ok` false |
| Removed fields | `database_backend`, timeouts, `recommended_workers`, `ratelimit_backend`, `ratelimit_enabled` are absent |
| Production and the local `finpilot` URL | `Config.validate` raises, and the message has neither the password nor the host |
| Development and that same URL | `Config.validate` returns |
