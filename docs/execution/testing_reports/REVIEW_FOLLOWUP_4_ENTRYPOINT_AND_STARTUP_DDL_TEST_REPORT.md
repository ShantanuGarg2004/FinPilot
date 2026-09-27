# Review follow-up 4 — local debugger and startup DDL

**Date:** 2026-09-27
**Plan:** `docs/planning/ARCHITECTURE_REVIEW_FOLLOWUP_PLAN.md` issue 4
**Verdict:** `python app.py` listens only in a local environment. A jobs kind check that already allows report and chat is not dropped on the next startup.

---

## 1. What shipped

`serve()` is what `python app.py` calls. When `FLASK_ENV` is not `development`, `dev`, or `local`, it logs that this entrypoint is the local debugger and exits with status 1 before `create_app` and before `app.run`. Local environments still call `app.run(debug=True)`. Waitress was not added.

`_allow_chat_jobs` reads the check text. A check whose definition already contains `report` and `chat` is left in place, including its oid. A report-only check is dropped and replaced once with `kind IN ('report', 'chat')`.

## 2. Tests

`python -m pytest -q` — **131 passed** (128 before this issue, plus 3).

| Case | Result |
| --- | --- |
| `serve()` when `FLASK_ENV` is production | `SystemExit` 1, `create_app` not called |
| `serve()` when `FLASK_ENV` is development | `run(debug=True)` |
| Report-only kind check, then startup | Definition includes `report` and `chat` |
| Startup again | Same constraint oid and the same definition |
