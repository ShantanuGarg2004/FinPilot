# Review follow-up 8 — column types

**Date:** 2026-09-27
**Plan:** `docs/planning/ARCHITECTURE_REVIEW_FOLLOWUP_PLAN.md` issue 8
**Verdict:** Health scores are `jsonb`. Account, profile, report, and chat timestamps are `timestamptz`. The advisory text stays `text`. No Alembic migration was added.

---

## 1. What shipped

`database/sql/issue8_column_types.sql` is the one-time script. It alters a column only when that column is still `text`, so running it again does nothing. `CREATE TABLE` in `database/models.py` now creates empty databases with the same types.

`ai_report` stays `text`. It is the advisory prose, not JSON.

`load_report` accepts a health value that is already a dict, which is what PostgreSQL returns for `jsonb`, or a string. Profile lists can include a timestamp, and the API encodes that as an ISO string.

## 2. Live data

The script was applied to a copy of the `public` schema first. Every cast succeeded, and the copy had the same row counts as `public`. The copy was dropped. The same script was then committed on `public`.

| Table | Rows before and after |
| --- | --- |
| accounts | 2 |
| users | 6 |
| reports | 6 |
| chat_history | 26 |

| Column | Type after the script |
| --- | --- |
| accounts.created_at | timestamptz |
| users.created_at | timestamptz |
| reports.generated_at | timestamptz |
| reports.health_json | jsonb |
| reports.ai_report | text |
| chat_history.created_at | timestamptz |

## 3. Tests

`python -m pytest -q` — **136 passed** (134 before this issue, plus 2).

| Case | Result |
| --- | --- |
| New schema from `create_tables` | The six columns above have those types |
| Script on a schema whose columns were altered back to text | Columns convert, a second run leaves `jsonb` in place, and the health score round-trips |
