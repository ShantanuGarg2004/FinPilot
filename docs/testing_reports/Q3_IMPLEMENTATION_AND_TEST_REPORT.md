# Q3 Implementation & Testing Report

**Date:** 2026-09-25  
**Scope:** `docs/PLATFORM_QUALITY_WAVES.md` — Q3 (data access fit for contention)  
**New dependencies installed:** none. `marshmallow` and `pytest` were already installed and are now listed in `requirements.txt` so CI can install them.

---

## 1. Summary

Handlers no longer run SQL. A request uses one SQLite connection. New PDFs are files on disk, and an existing blob is copied out once.

| Gate | Result |
|---|---|
| Pytest, excluding the optional Postgres ping | **80 passed**, 1 deselected |
| Browser click-through | **not run** |

---

## 2. What shipped

| Task | Change |
|---|---|
| Q3.1 | `database/repository.py` owns profile, report, and chat SQL. Routes call those functions. |
| Q3.2 | `database.db.connection()` reuses one connection for the request and closes it in teardown. `busy_timeout` is unchanged. |
| Q3.3 | PDFs go to `data/pdfs` (override with `PDF_STORAGE_DIR`). The row stores `pdf_path`. `pdf_blob` stays for old rows until startup copies the bytes out and clears them. Download reads the file, or the old blob, or rebuilds once and writes the file. |
| Q3.4 | Profile, report, and chat saves catch `sqlite3.Error` and return `code: server_error` when the save itself failed. A PDF file that cannot be cached still returns the download. |
| Q3.5 | `UserProfile` is removed. Profiles on the request path are dicts. `profiling_service` returns that same dict. |
| Q3.6 | `.github/workflows/pytest.yml` runs pytest on every push to `main` and on pull requests, without Postgres. |
| Q3.7 | `tests/test_q3_data.py` covers health-score bands and goal feasibility without Groq. |

Backup taken before this change: `backups/finance-pre-q3.db` (same size as `finance.db`, 217088 bytes). That folder is gitignored. The blob copy runs the next time the app starts.

---

## 3. How to reproduce

```bash
python -m pytest tests/ -q --tb=line --deselect tests/test_wave1_integration.py::test_sql_backend_ping_when_configured
```
