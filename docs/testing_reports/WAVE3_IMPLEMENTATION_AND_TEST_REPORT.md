# Wave 3 Implementation & Testing Report

**Date:** 2026-09-23  
**Scope:** Hardening slice of Wave 3 (workers, timeouts, SQLite busy timeout)  
**New dependencies installed:** none (Waitress/Gunicorn are documented, not added to `requirements.txt`)

---

## 1. Summary

Wave 3 sizing and failure behavior are in the app. SQLite waits on the writer, Groq calls time out into a structured 504, and health reports the worker formula. The job queue and the move of app data to PostgreSQL stay deferred.

| Gate | Result |
|---|---|
| Full pytest suite | **65 passed** |
| Live 80/20 load + chaos kill | **not run here** — script is `scripts/load_test_wave3.py` against a running API |

---

## 2. What shipped

| Task | Change |
|---|---|
| 3.1 Worker formula | `recommended_worker_count()` = max(2, peak LLM + headroom). Defaults 4 + 2 = 6. Exposed on `GET /api/health` |
| 3.2 Timeouts | Groq client timeout 90s. Worker timeout must be greater (default 120s). `APITimeoutError` → `code: upstream_timeout`, HTTP 504 |
| 3.4 Busy timeout | `PRAGMA busy_timeout` from `SQLITE_BUSY_TIMEOUT_MS` (default 5000) on every connection |
| Load script | `scripts/load_test_wave3.py` — concurrent GETs, p95 and 429 check, no Groq |

### Deferred

| Task | Reason |
|---|---|
| 3.3 Job queue | Advisory text is already persisted before PDF (Wave 2) |
| 3.5 App DB → PostgreSQL | Plan allows SQLite until write contention shows up |
| 3.6 App connection pool | Follows 3.5 |

---

## 3. Files

| Area | Files |
|---|---|
| Config / DB | `config.py`, `database/db.py`, `conftest.py`, `.env.example` |
| API | `services/ai_service.py`, `routes/report_routes.py`, `routes/chat_routes.py`, `app.py` |
| Frontend | `frontend/src/lib/apiErrors.js` |
| Ops | `docs/CAPACITY_RUNBOOK.md`, `scripts/load_test_wave3.py`, README serve note |
| Tests | `tests/test_wave3_capacity.py`, `tests/test_wave3_load_script.py` |

---

## 4. How to verify

```bash
python -m pytest tests/test_wave3_capacity.py tests/test_wave3_load_script.py -v
python scripts/load_test_wave3.py --api-key YOUR_KEY
```
