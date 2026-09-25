# Q1 Implementation & Testing Report

**Date:** 2026-09-25  
**Scope:** `docs/PLATFORM_QUALITY_WAVES.md` — Q1 (one enforcement path)  
**New dependencies installed:** none (`limits` is already installed via Flask-Limiter)

---

## 1. Summary

The custom gateway is the only live limiter. Route `@limiter.limit` decorators are removed. Quota strings in config are parsed by the `limits` package. An `/api` route with no policy is denied. PDF rebuild uses its own bucket, separate from `GET /report`.

| Gate | Result |
|---|---|
| Pytest, excluding the optional Postgres ping | **68 passed**, 1 deselected |
| Optional `test_sql_backend_ping_when_configured` | **not run** in this pass (connects to local Postgres) |
| New libraries | **none** |

---

## 2. What shipped

| Task | Change |
|---|---|
| Q1.1 | Removed `@limiter.limit` from user, report, chat, and goal routes. Flask-Limiter stays imported for its old unit tests; it no longer decorates routes. |
| Q1.2 | `PolicyRegistry` builds rules with `limits.parse` from `Config.RATELIMIT_*` (`5 per minute`, `10 per hour`). |
| Q1.3 | Unmapped `/api/*` returns HTTP 429, `code: rate_policy_missing`. Health and `OPTIONS` stay exempt. |
| Q1.4 | `GET /download-report/<id>` counts as `read_download`. Rebuilding a missing PDF also consumes `pdf_rebuild` (default `5 per minute`). |
| Q1.5 | `tests/test_q1_enforcement.py` |

---

## 3. Q1 tests

| Test | Result |
|---|---|
| `test_registry_reads_quota_from_config` | passed — `2 per minute` and `9 per hour` land on the registry |
| `test_download_is_not_read_report` | passed |
| `test_unmapped_api_route_is_denied` | passed — `rate_policy_missing` |
| `test_download_rebuild_does_not_use_read_report_bucket` | passed — exhausted `read_report` still allows one rebuild; the next rebuild is `pdf_rebuild` |

---

## 4. How to reproduce

```bash
python -m pytest tests/ -q --tb=line --deselect tests/test_wave1_integration.py::test_sql_backend_ping_when_configured
```

With Postgres up, drop the `--deselect` to include the store ping.
