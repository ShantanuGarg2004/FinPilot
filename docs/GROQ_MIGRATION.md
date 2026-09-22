# Backend Migration Guide — OpenAI → Groq

> **Status:** Planning document. **No code has been changed.** This lists *every* change
> required to make the FinPilot backend run against the **Groq API** using `GROQ_API_KEY`
> instead of OpenAI.

Groq exposes an **OpenAI-compatible** Chat Completions endpoint, so the migration is small:
the request/response shapes (`client.chat.completions.create(...)`, `messages`, `temperature`,
`max_tokens`, `response.choices[0].message.content`) are identical. Only the **client
initialisation**, the **model name**, and the **config/validation** need to change.

Two implementation paths are described:

- **Path A (recommended, minimal churn):** keep the existing `openai` SDK and point it at
  Groq's base URL. No new dependency.
- **Path B (official SDK):** use the `groq` Python package.

Pick **one** path. Path A touches the fewest files.

---

## Summary of Files to Change

| # | File | Change | Required? |
|---|---|---|---|
| 1 | `.env` | `GROQ_API_KEY` replaces `OPENAI_API_KEY` | ✅ Done already |
| 2 | `config.py` | Load & validate `GROQ_API_KEY`; add model/base-URL config | ✅ Required |
| 3 | `services/ai_service.py` | Point client at Groq; change model name | ✅ Required |
| 4 | `requirements.txt` | Path A: no change · Path B: add `groq` | ⬜ Path B only |
| 5 | `README.md` / `docs/ARCHITECTURE.md` | Update "OpenAI / gpt-4o-mini" references | ⬜ Optional (docs accuracy) |

There are **no other code references** to OpenAI in the project (verified across all
`*.py` files — only `config.py` and `services/ai_service.py` mention it).

---

## 1. `.env` (already updated)

```env
GROQ_API_KEY=gsk_...your-key...
API_SECRET_KEY=c0af8656...
RATELIMIT_STORAGE_URI='memory://'
```

`OPENAI_API_KEY` is intentionally removed. (Optional but recommended: add
`GROQ_MODEL` and `GROQ_BASE_URL` so the model can be swapped without code edits — see below.)

Optional additions:

```env
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

---

## 2. `config.py`

The current `Config` class loads and **requires** `OPENAI_API_KEY`, which will crash startup
now that only `GROQ_API_KEY` exists (`Config.validate()` raises `EnvironmentError`).

**Current (`config.py`):**

```python
class Config:
    OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
    API_SECRET_KEY   = os.getenv("API_SECRET_KEY")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")

    @classmethod
    def validate(cls):
        missing = [k for k in ("OPENAI_API_KEY", "API_SECRET_KEY") if not getattr(cls, k)]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Add them to your .env file."
            )
```

**Proposed:**

```python
class Config:
    GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
    # Groq's OpenAI-compatible endpoint + a default supported model.
    GROQ_BASE_URL    = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    GROQ_MODEL       = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    API_SECRET_KEY   = os.getenv("API_SECRET_KEY")
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

Key points:
- `OPENAI_API_KEY` removed.
- `GROQ_API_KEY` added and now the required key in `validate()`.
- `GROQ_MODEL` and `GROQ_BASE_URL` added so the model/endpoint are configurable.

---

## 3. `services/ai_service.py`

Only the **client construction** (lines ~1–7) and the **model string** (line ~42) change.
The prompt-building and `(success, payload)` return contract stay exactly the same.

### Path A — reuse the `openai` SDK (recommended)

**Current:**

```python
from openai import OpenAI
from config import Config

# Initialize OpenAI client
client = OpenAI(
    api_key=Config.OPENAI_API_KEY
)
```

**Proposed:**

```python
from openai import OpenAI
from config import Config

# Groq is OpenAI-compatible — just point the same SDK at Groq's base URL.
client = OpenAI(
    api_key=Config.GROQ_API_KEY,
    base_url=Config.GROQ_BASE_URL,
)
```

### Path B — use the official `groq` SDK (alternative)

**Proposed:**

```python
from groq import Groq
from config import Config

client = Groq(api_key=Config.GROQ_API_KEY)
```

> Under both paths the call site is unchanged, because `groq.Groq` mirrors the OpenAI
> client interface (`client.chat.completions.create(...)`).

### Model name (both paths)

Groq does **not** serve `gpt-4o-mini`. Change the model in `ask_gpt(...)`:

**Current:**

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=1000,
    messages=[...],
)
```

**Proposed:**

```python
response = client.chat.completions.create(
    model=Config.GROQ_MODEL,   # e.g. "llama-3.3-70b-versatile"
    temperature=0.7,
    max_tokens=1000,
    messages=[...],
)
```

`temperature`, `max_tokens`, `messages`, and `response.choices[0].message.content` all work
identically on Groq — no further changes to the function body.

#### Suggested Groq models

| Model | Notes |
|---|---|
| `llama-3.3-70b-versatile` | Strong general reasoning — good default for advisory reports |
| `llama-3.1-8b-instant` | Fastest / cheapest — good for chat |
| `openai/gpt-oss-20b` | Open-weight GPT-OSS, balanced |

(Verify the exact model IDs against the current Groq model catalogue at deploy time, as
availability changes.)

---

## 4. `requirements.txt`

**Path A (recommended):** no change — the `openai` package is already listed and is reused
against Groq's base URL.

**Path B (official SDK):** add `groq`:

```diff
 flask
 flask-cors
 flask-limiter
 python-dotenv
 openai
+groq
 requests
 reportlab
 flasgger
```

(You may keep `openai` for Path B or remove it if nothing else uses it — currently nothing
else does.)

---

## 5. Documentation references (optional, for accuracy)

These are non-functional but keep docs truthful:

- `README.md` — "AI / LLM: OpenAI API (`gpt-4o-mini`)" → "Groq API (`llama-3.3-70b-versatile`)",
  and the architecture diagram's `OpenAI API` node → `Groq API`.
- `docs/ARCHITECTURE.md` — same substitutions in the overview, diagrams, and service section.

---

## Verification Checklist (after implementing)

1. `.env` contains `GROQ_API_KEY` and `API_SECRET_KEY`; `OPENAI_API_KEY` is gone.
2. `python app.py` starts without an `EnvironmentError` (proves `config.validate()` was updated).
3. `POST /api/generate-report` returns a report (proves the Groq client + model work).
4. `POST /api/chat` returns a response.
5. No traceback mentioning `gpt-4o-mini` or an OpenAI auth error appears in logs.

---

## Notes / Caveats

- **Rate limits & token limits differ** on Groq vs OpenAI. `max_tokens=1000` is safe on the
  suggested models, but confirm against the chosen model's context window.
- **`prompt_builder.py` / `profiling_service.py`** remain unused (see `ARCHITECTURE.md`) — this
  migration does not touch them.
- The **known chat-context bug** (`content` vs `message` key) is unrelated to the provider and
  is **not** fixed by this migration; track it separately.
- No change is needed in routes, schemas, database, or the frontend for the provider swap —
  the API contract is unchanged.
