# Remediation 8 — docs that match this process

**Date:** 2026-09-27
**Plan:** `docs/planning/ARCHITECTURE_REMEDIATION_PLAN.md` issue 8
**Verdict:** A new reader can start the API, sign in, and find `python -m services.jobs.worker` from the README and `docs/architecture/ARCHITECTURE.md`. This was a checklist against the code, not a pytest run.

---

## 1. Files opened

Code, to check the sentences:

- `app.py` (`require_api_key`, `_required_scope`, `health`)
- `services/actor.py`
- `services/sessions.py`
- `services/jobs/worker.py`
- `routes/report_routes.py`
- `routes/chat_routes.py`
- `routes/auth_routes.py` (logout bumps `session_version`)
- `database/db.py` (`schema_name`)
- `database/repository.py` (`latest_report_job`, `latest_chat_job`)
- `.env.example`
- `scripts/load_test_issue6.py` (cookie login, no `--api-key`)

Docs written or edited:

- `docs/architecture/ARCHITECTURE.md` (rewritten as the as-built description)
- `README.md` (diagram, request lifecycle, start commands, API table, schema, roadmap)
- `docs/planning/PLATFORM_QUALITY_WAVES.md` (status block only; the wave tables stay)
- `docs/architecture/AUTH_ARCHITECTURE.md` (cookie, scoped key, docs password are one story)
- `docs/architecture/CAPACITY_RUNBOOK.md` (the README points here; it still said SQLite and a synchronous report)

## 2. Checklist

| Check | Result |
| --- | --- |
| Request path is cookie, else scoped credential, else docs password, then the gateway, then the blueprint | Matches `app.py` and `services/actor.py` |
| A bad cookie does not fall through to a key | Matches `resolve_actor` |
| `POST /api/generate-report` returns 202; the worker calls Groq | Matches `report_routes.py` and `services/jobs/worker.py` |
| `GET /api/report/<id>` adds `job` for queued, running, or failed, and omits succeeded | Matches `latest_report_job` |
| Chat is queued the same way | Matches `chat_routes.py`. The issue 6 gate is why it is queued. |
| App database `finpilot`, limiter database `finpilot_ratelimit`, PDFs in `data/pdfs` | Matches config comments and `database/pdf_files.py` |
| `public` is production; a test schema is isolation | Matches `schema_name()` |
| No Redis, no OAuth | Stated as absent. Not added. |
| Worker command is in the README and in `docs/architecture/ARCHITECTURE.md` | `python -m services.jobs.worker` |
| Sign-in path is in Getting Started | Vite on port 5173, cookie, no API key in the browser |
| Capacity sentence | Copied from the issue 6 report into `docs/architecture/ARCHITECTURE.md` and the README roadmap. No new pass line. |
| Wave tables | Still in `docs/planning/PLATFORM_QUALITY_WAVES.md`. The top no longer says there is no login. |
| Secrets | Placeholders only. `.env` was not edited. |

## 3. Left for later

Issue 9 still owns `services/profiling_service.py`, `utils/prompt_builder.py`, and `get_latest_user()`. They are named as off the request path. They were not deleted here. Historical testing reports were not rewritten.
