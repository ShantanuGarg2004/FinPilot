# Application database on PostgreSQL

**Date:** 2026-09-25

Profiles, reports, and chat now live in PostgreSQL. The rate limiter keeps its own database on the same server. PDF files stay on disk.

This follows the Q6 decision to move app data when SQLite’s single writer would limit concurrent use. The load measurement itself is still in `docs/testing_reports/Q6_IMPLEMENTATION_AND_TEST_REPORT.md`. Whether this copy succeeded is in `docs/testing_reports/APP_DATABASE_MIGRATION_TEST_REPORT.md`.

## What changed

| Piece | Before | After |
|---|---|---|
| Profiles, accounts, reports, chat | SQLite file `finance.db` | PostgreSQL database `finpilot` |
| Rate-limit counters | PostgreSQL database `finpilot_ratelimit` | Unchanged |
| PDF bytes | Files under `data/pdfs` | Unchanged. The row stores `pdf_path`. |
| Driver | `sqlite3` | SQLAlchemy with `psycopg`, already used by the limiter |
| Pool | A new SQLite connection per request | 10 pooled connections, plus up to 10 extra |

`APP_DATABASE_URL` points at `finpilot`. `RATELIMIT_DATABASE_URL` still points at `finpilot_ratelimit`. The two stores do not share tables.

Local PostgreSQL is the Compose service in `docker-compose.yml` (Postgres 16, user `finpilot`, port 5432). If `finpilot` does not exist yet, startup creates it. A fresh volume still creates `finpilot_ratelimit` for the limiter.

## How a request uses the database

`database/db.py` opens one pooled connection for the request and returns it when the request ends. SQL still uses `?` placeholders. The wrapper binds them for PostgreSQL and turns each row into a mapping, so `row["column"]` still works.

Startup in `database/models.py` creates `accounts`, `users`, `reports`, and `chat_history` if they are missing, then the indexes used by report lookup, chat history, and account ownership.

## Copy from SQLite

`database/sqlite_import.py` runs only when all of these are true:

1. The connection is using the `public` schema (the real app database, not a test schema).
2. `users` in PostgreSQL is empty.
3. A file named `finance.db` is in the working directory.

It copies `accounts`, `users`, `reports`, and `chat_history`, keeping each `id`. Identity sequences are moved past the highest copied id so the next insert does not collide. If PostgreSQL already has profiles, the file is left unread.

After the copy, startup still attaches any profile with no `account_id` to the bootstrap account from `BOOTSTRAP_ACCOUNT_EMAIL` and `BOOTSTRAP_ACCOUNT_PASSWORD`. That rule already existed for SQLite. Reports and chats stay on `users.id`.

`finance.db` is not deleted. It is the source copy. The running app does not read it again once `finpilot` has profiles.

## Tests

Pytest does not use `finpilot`. `conftest.py` sets `APP_DATABASE_URL` to database `finpilot_test`. Each test that used to point at its own SQLite file now gets its own PostgreSQL schema on that database, so cases do not see each other’s rows. GitHub Actions starts Postgres 16 and sets the same test URL.

## Run it

Postgres must be up (`docker compose up -d`). Root `.env` needs:

```
APP_DATABASE_URL=postgresql+psycopg://finpilot:finpilot_dev_password@127.0.0.1:5432/finpilot
```

Restart `python app.py` after that line is present. A process started before the change is still on SQLite.
