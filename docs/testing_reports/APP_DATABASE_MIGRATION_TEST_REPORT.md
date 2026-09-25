# Application database migration — test report

**Date:** 2026-09-25  
**Question:** Did the move from `finance.db` to PostgreSQL database `finpilot` succeed?  
**Verdict:** **Yes.** Row counts and ids match. One profile that had no account in SQLite is now owned by the bootstrap account. That is the existing startup rule, not a dropped row.

---

## 1. Data comparison

Compared `finance.db` (217088 bytes) with PostgreSQL database `finpilot` on `127.0.0.1:5432` after `create_tables()` imported the file.

| Table | SQLite rows | PostgreSQL rows | Ids match |
|---|---:|---:|---|
| `accounts` | 2 | 2 | Yes |
| `users` | 6 | 6 | Yes |
| `reports` | 5 | 5 | Yes |
| `chat_history` | 56 | 56 | Yes |

Field checks on the copied rows:

| Check | Result |
|---|---|
| Account id and email | Match |
| Report `user_id`, advisory text length, `pdf_path` | Match |
| Chat id, `user_id`, role, message length | Match |
| User id, age, income, expenses, savings, risk, goals | Match, except `users.id` **16** |

`users.id` 16 had `account_id` NULL in SQLite and `account_id` 1 in PostgreSQL. Account 1 is `bootstrap@finpilot.local`. No profile remains without an account. Reports and chats for that profile were not moved to another id.

The limiter database `finpilot_ratelimit` was not part of this copy.

## 2. Automated tests

```text
python -m pytest tests/ -q --tb=line --deselect tests/test_wave1_integration.py::test_sql_backend_ping_when_configured
```

**94 passed**, 1 deselected, in 13.33s.

The deselected test is the optional limiter Postgres ping. App tests used database `finpilot_test`, each case in its own schema, so they did not write into `finpilot`.

Covered by that run: schema creation, nullable `pdf_blob`, one connection per request, signup and profile ownership, bootstrap attach, and a plain `SELECT 1` on a pooled connection.

## 3. What this run does not claim

- No new load test was run after the copy. The Q6 numbers were measured on SQLite.
- The browser was not clicked through against the PostgreSQL data.
- `finance.db` is still on disk. The app reads PostgreSQL when `APP_DATABASE_URL` is set and the process is restarted.

## 4. How to repeat the comparison

With Postgres up and `APP_DATABASE_URL` pointing at `finpilot`:

```bash
python -c "from database.models import create_tables; from database.db import get_connection; create_tables(); c=get_connection(); print(dict(c.execute('SELECT (SELECT COUNT(*) FROM accounts) AS accounts, (SELECT COUNT(*) FROM users) AS users, (SELECT COUNT(*) FROM reports) AS reports, (SELECT COUNT(*) FROM chat_history) AS chats').fetchone())); c.close()"
```

A second run must not insert another copy. `users` is already non-empty, so the importer returns immediately.
