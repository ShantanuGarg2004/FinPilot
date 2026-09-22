# Groq Migration — Path B Implementation Report

> Post-implementation record of the OpenAI → Groq (Path B, official `groq` SDK) migration.
> Compares what was **planned** in [`GROQ_PATH_B_IMPLEMENTATION.md`](GROQ_PATH_B_IMPLEMENTATION.md)
> against what was **actually applied**, documents the unit-test suite, and records results.

- **Date:** 2026-08-02
- **Scope:** Backend provider swap (OpenAI → Groq) + per-service model routing + unit tests
- **Status:** ✅ Implemented, unit-tested (17/17 passing). Integrated testing pending (owner: user).
- **Committed:** No — changes staged in working tree for review.

---

## 1. Summary

The backend now uses the official **`groq` SDK** instead of OpenAI. Model selection is
per-service and configurable via environment variables, defaulting to a high-capability model
for the advisory report and a low-latency model for chat. A new offline unit-test suite covers
the configuration and AI-service behaviour with all Groq network calls mocked.

---

## 2. Planned vs. Applied — Step-by-Step Comparison

| Planned step (from implementation doc) | Applied? | Notes / deviations |
|---|:---:|---|
| **Step 1** — `pip install groq` | ✅ | Installed `groq 1.6.0`. Also installed `pytest 9.0.3` for the test suite. |
| **Step 2** — Add `groq` to `requirements.txt` | ✅ | Added `groq` after `openai`. `openai` left in place (harmless; nothing imports it now). |
| **Step 3** — Update `.env` (`GROQ_API_KEY` + model vars) | ✅ | Added `GROQ_REPORT_MODEL=openai/gpt-oss-120b` and `GROQ_CHAT_MODEL=llama-3.1-8b-instant`. |
| **Step 4** — Update `config.py` | ✅ | Exactly as planned (details §3.2). |
| **Step 5(a)** — Swap client to `Groq(...)` | ✅ | As planned. |
| **Step 5(b)** — `ask_gpt(prompt, model=None)` | ✅ + enhancement | Added a docstring **and production logging** (`logger.exception`) on failure — see §4. |
| **Step 5(c)** — Pass per-service model at call sites | ✅ | Report → `GROQ_REPORT_MODEL`, chat → `GROQ_CHAT_MODEL`. |
| Model assignment (report vs chat) | ✅ | `openai/gpt-oss-120b` (report) / `llama-3.1-8b-instant` (chat), as recommended. |

### Additions beyond the plan (production-readiness)

1. **Structured logging** in `ask_gpt` — failures are now logged with `logger.exception`
   (model included) instead of being silently returned. Consistent with the rest of the codebase.
2. **Unit-test suite** — `conftest.py` + `tests/` (not in the original step list; requested here).
3. **Comment cleanup** — the stale `# OPENAI CALL WRAPPER` header is now `# GROQ CALL WRAPPER`.

Nothing planned was skipped.

---

## 3. Detailed Change Log (by file)

### 3.1 `requirements.txt`

```diff
 openai
+groq
 requests
```

### 3.2 `config.py`

- Removed `OPENAI_API_KEY`.
- Added `GROQ_API_KEY`, `GROQ_REPORT_MODEL` (default `openai/gpt-oss-120b`),
  `GROQ_CHAT_MODEL` (default `llama-3.1-8b-instant`).
- `validate()` now checks `("GROQ_API_KEY", "API_SECRET_KEY")`.

```python
class Config:
    GROQ_API_KEY      = os.getenv("GROQ_API_KEY")
    GROQ_REPORT_MODEL = os.getenv("GROQ_REPORT_MODEL", "openai/gpt-oss-120b")
    GROQ_CHAT_MODEL   = os.getenv("GROQ_CHAT_MODEL", "llama-3.1-8b-instant")
    API_SECRET_KEY    = os.getenv("API_SECRET_KEY")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")

    @classmethod
    def validate(cls):
        missing = [k for k in ("GROQ_API_KEY", "API_SECRET_KEY") if not getattr(cls, k)]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Add them to your .env file."
            )
```

### 3.3 `services/ai_service.py`

- Import + client: `from openai import OpenAI` → `from groq import Groq`;
  `client = Groq(api_key=Config.GROQ_API_KEY)`. Added a module `logger`.
- `ask_gpt(prompt, model=None)`: resolves `model or Config.GROQ_CHAT_MODEL`, logs on failure.
- `generate_financial_report(...)` → `return ask_gpt(prompt, model=Config.GROQ_REPORT_MODEL)`.
- `chat_with_advisor(...)` → `return ask_gpt(prompt, model=Config.GROQ_CHAT_MODEL)`.

```python
import logging
from groq import Groq
from config import Config

logger = logging.getLogger(__name__)
client = Groq(api_key=Config.GROQ_API_KEY)

def ask_gpt(prompt, model=None):
    selected_model = model or Config.GROQ_CHAT_MODEL
    try:
        response = client.chat.completions.create(
            model=selected_model,
            temperature=0.7,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
        )
        return True, response.choices[0].message.content.strip()
    except Exception as exc:
        logger.exception("ask_gpt: Groq completion failed (model=%s)", selected_model)
        return False, str(exc)
```

### 3.4 `.env`

```diff
 GROQ_API_KEY=gsk_...
+GROQ_REPORT_MODEL=openai/gpt-oss-120b
+GROQ_CHAT_MODEL=llama-3.1-8b-instant
 API_SECRET_KEY=c0af8656...
 RATELIMIT_STORAGE_URI='memory://'
```

### 3.5 New files (tests)

- `conftest.py` (project root) — adds root to `sys.path`; sets a deterministic, offline env
  (`GROQ_API_KEY`, `API_SECRET_KEY`, model vars, `RATELIMIT_STORAGE_URI`) via `setdefault`
  **before** `config`/`ai_service` import, so no real key is needed and no network is touched.
- `tests/test_config.py` — 7 tests.
- `tests/test_ai_service.py` — 10 tests.

### Files intentionally NOT changed

`routes/*`, `schemas.py`, `database/*`, `models/*`, `services/{health,goal,pdf,profiling}_service.py`,
`utils/prompt_builder.py`, and the frontend — the API contract is unchanged, so none needed edits.

---

## 4. Unit-Test Suite

All tests are **fully offline**: the Groq `client.chat.completions.create` method is replaced
with a recorder stub, so no API key is used and no request leaves the machine.

### 4.1 Test infrastructure

- **`conftest.py`** guarantees imports resolve and the environment is deterministic.
- A `_Recorder` stub captures the exact kwargs passed to `create(...)` and can simulate both
  success (returns a Groq-shaped response object) and failure (raises).

### 4.2 `tests/test_config.py`

| Test | What it verifies |
|---|---|
| `test_required_keys_present_by_default` | `GROQ_API_KEY` and `API_SECRET_KEY` are populated. |
| `test_validate_passes_when_keys_present` | `validate()` returns `None` (no raise) when keys exist. |
| `test_validate_raises_when_groq_key_missing` | Missing `GROQ_API_KEY` → `EnvironmentError` naming it. |
| `test_validate_raises_when_api_secret_missing` | Missing `API_SECRET_KEY` → `EnvironmentError` naming it. |
| `test_validate_no_longer_requires_openai_key` | `Config` has no `OPENAI_API_KEY`; validation is independent of it. |
| `test_per_service_models_configured` | Report/chat models equal the expected IDs. |
| `test_model_defaults_fall_back_when_env_absent` | With model env vars removed and `.env` neutralised, code defaults apply (via `importlib.reload`). |

### 4.3 `tests/test_ai_service.py`

| Test | What it verifies |
|---|---|
| `test_ask_gpt_success_returns_stripped_content` | Success returns `(True, content)` with whitespace stripped. |
| `test_ask_gpt_defaults_to_chat_model` | No model arg → uses `GROQ_CHAT_MODEL`. |
| `test_ask_gpt_uses_explicit_model` | Explicit `model=` is honoured. |
| `test_ask_gpt_sends_system_and_user_messages` | Correct message roles/content, `temperature=0.7`, `max_tokens=1000`. |
| `test_ask_gpt_returns_false_on_exception` | Exceptions are caught → `(False, error_message)`, no propagation. |
| `test_generate_financial_report_uses_report_model` | Report path uses `GROQ_REPORT_MODEL`. |
| `test_generate_financial_report_prompt_contains_profile` | Prompt embeds profile goal and health score. |
| `test_chat_with_advisor_uses_chat_model` | Chat path uses `GROQ_CHAT_MODEL`. |
| `test_chat_with_advisor_includes_query_in_prompt` | User query is embedded in the prompt. |
| `test_report_and_chat_use_distinct_models` | Report and chat models are actually different. |

### 4.4 Coverage rationale

The suite targets exactly the surface area changed by the migration: config loading/validation,
client wiring, the model-selection contract (default vs explicit vs per-service), the request
payload shape, and error handling. Deterministic engines (`health_service`, `goal_service`) were
out of scope for this change and are not covered here.

---

## 5. Test Results

Command:

```bash
python -m pytest tests/ -v
```

Result:

```
platform win32 -- Python 3.14.2, pytest-9.0.3, pluggy-1.6.0
collected 17 items

tests/test_ai_service.py ..........  (10 passed)
tests/test_config.py     .......     (7 passed)

============================= 17 passed in 1.18s ==============================
```

**17 / 17 passed.** No linter errors in the changed files.

---

## 6. Verification Checklist Status

| Checklist item (from implementation doc) | Status |
|---|:---:|
| `groq` installed and in `requirements.txt` | ✅ |
| `.env` has Groq key + model vars; no `OPENAI_API_KEY` | ✅ |
| `config.validate()` updated (unit-verified) | ✅ |
| Report path resolves to `openai/gpt-oss-120b` (unit-verified) | ✅ |
| Chat path resolves to `llama-3.1-8b-instant` (unit-verified) | ✅ |
| No `gpt-4o-mini` / OpenAI references remain in code | ✅ |
| Live `python app.py` + real Groq calls | ⏳ Pending (integrated testing by user) |

---

## 7. Known Items / Out of Scope

- **Chat-context bug** (`content` vs `message` key in `chat_with_advisor`) is unrelated to the
  provider swap and was intentionally left unchanged. Track separately.
- **Live integration** (real Groq API, end-to-end report/chat) is the user's next step.
- **Model IDs** may be deprecated by Groq over time; because selection is env-driven, a swap is a
  `.env` change with no code edit.
