# Remediation 9 — dead code and comments

**Date:** 2026-09-27
**Plan:** `docs/planning/ARCHITECTURE_REMEDIATION_PLAN.md` issue 9
**Verdict:** Three unused symbols are gone. `database/sqlite_import.py` stays, because startup still calls it when `SQLITE_IMPORT` is on. Pytest stayed green. Behavior of the running routes did not change.

---

## 1. What was removed

A repo search of `*.py` found no import and no call of these, including tests:

| Symbol | Search result |
| --- | --- |
| `services/profiling_service.py` | No importer. Profile checks on the live path are Marshmallow schemas. |
| `utils/prompt_builder.py` | No importer. Prompts on the live path are built in `services/ai_service.py`. |
| `get_latest_user()` in `database/repository.py` | Defined only. Profiles are loaded with `get_user_by_id` and `get_all_users`, which apply the account filter. |

Those three were deleted. Historical testing reports that still name them were left as records of the day they were written. `docs/architecture/ARCHITECTURE.md` no longer points at the deleted files.

## 2. What was kept

`database/sqlite_import.py` is still imported by `database/models.py`. `create_tables` calls `import_sqlite_if_empty` when `SQLITE_IMPORT` is true and the schema is `public`. The issue 7 report says the flag defaults off. It does not say the old `finance.db` copy already happened and that the flag is unused. Removing the file would drop that startup path, so it stays.

`services/actor.py` already describes the shipped rule: cookie first, then a scoped credential, and `API_SECRET_KEY` is not a data actor. That docstring was left as it is.

## 3. Comments on live functions

- `app.py` `require_api_key`: cookie first, then a scoped credential. The docs password opens local Swagger only.
- `app.py` `enforce_rate_limit`: the gateway is the live limiter. Health is exempt.
- `database/models.py` `create_tables`: tables are created on startup. SQLite opens only when `SQLITE_IMPORT` is on.

The log line that still says “Wave 1” was not changed. Tests do not assert it, and it is a log string, not the rule on the request.

## 4. Tests

```text
python -m pytest -q
118 passed
```

Same count as after issue 7. No test imported the deleted modules.
