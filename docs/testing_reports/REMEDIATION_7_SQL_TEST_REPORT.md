# Remediation 7 — PostgreSQL-shaped SQL

**Date:** 2026-09-27
**Plan:** `docs/ARCHITECTURE_REMEDIATION_PLAN.md` issue 7
**Verdict:** Repository SQL now uses named binds. `reports.pdf_blob` is gone. A normal start does not open SQLite. This was not a second load test, and issue 6 was not rerun.

---

## 1. What changed

- `AppConnection.execute` accepts a dict of names. A tuple or list raises `DatabaseError`. `_qmarks` is gone.
- Statements under `database/` use `:name` binds. `scripts/load_test_issue6.py` uses the same style for its `IN` lists.
- New schemas create `reports` without `pdf_blob`. Startup still runs `export_legacy_blobs` when the column exists, then drops it only when no row still has bytes and an empty path. PDF files on disk were not deleted.
- `SQLITE_BUSY_TIMEOUT_MS` is removed from `config.py`, `conftest.py`, and `.env.example`. Docs that still name it stay until issue 8.
- `SQLITE_IMPORT` defaults off. `import_sqlite_if_empty` runs only when that flag is on and the schema is `public`. `database/sqlite_import.py` is still in the tree.
- `schema_name()` is documented as test isolation. Production stays on `public`.

## 2. Blob check

Before the drop, public `reports` had 5 rows and 0 rows with PDF bytes and no path. After `create_tables()`, `pdf_blob` is absent. Those 5 reports and 26 chat rows are still there.

## 3. Tests

```text
python -m pytest -q
118 passed
```

The extra test is `tests/test_remediation_7_sql.py`: a positional tuple and a missing `:user_id` both raise `DatabaseError`. `tests/test_pdf_blob_nullable.py` now expects the column to be absent. `tests/test_q3_data.py` still checks that a leftover blob is written to disk before the column is dropped.

## 4. Query plans

Checked on public after the change. Counts: `users` 5, `reports` 5, `chat_history` 26.

| Query | Plan |
| ----- | ---- |
| `users` by id | Seq Scan, filter on `id` |
| `reports` by `user_id` | Bitmap Index Scan on `idx_reports_user_id` |
| `chat_history` by `user_id` | Seq Scan, then sort and limit |

A literal `id = 1` is also a sequential scan, at the same cost. These tables are one page. The predicates did not change; only the placeholder style did. This is not a new sequential scan the old SQL avoided, so issue 6 was not rerun.

## 5. Left for later

Issue 8 rewrites the docs. Issue 9 may delete the importer only after `SQLITE_IMPORT` has stayed off in real use. Pool size was not changed. Alembic was not added.
