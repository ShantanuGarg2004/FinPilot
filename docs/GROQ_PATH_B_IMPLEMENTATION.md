# Groq Migration — Path B Implementation Steps (Official `groq` SDK)

> **Companion to** [`GROQ_MIGRATION.md`](GROQ_MIGRATION.md). That document explains *what*
> changes and *why*; this one is the **hands-on, step-by-step recipe for Path B** — using the
> official `groq` Python SDK — including a **per-service model assignment**.
>
> **No code has been changed yet.** These are the exact steps to implement.

Path B installs the official `groq` package and initialises a `Groq()` client. Because the
`groq` SDK mirrors the OpenAI interface (`client.chat.completions.create(...)`), the call site
barely changes. On top of the base Path B, these steps also add **per-service model
selection**, so the in-depth report and the live chat can each use the model best suited to
their job.

---

## 1. Model Assignment per Service (user-perspective rationale)

Only two services actually call the LLM. The rest are deterministic (no model needed). The
picks below come **only** from the models available on your Groq key.

| Service | Uses LLM? | Assigned model | Why (from the user's point of view) |
|---|:---:|---|---|
| **AI Advisory Report** (`generate_financial_report`) | ✅ | **`openai/gpt-oss-120b`** | This is the flagship deliverable the user reads and downloads as a PDF. It's a long, structured, multi-section financial analysis where **depth, accuracy, and coherent reasoning matter most**. It's generated once and the user is willing to wait a few seconds, so the largest, most capable model is the right trade-off. |
| **Conversational Advisor Chat** (`chat_with_advisor`) | ✅ | **`llama-3.1-8b-instant`** | Chat is a live back-and-forth. Users expect **near-instant, snappy replies**. The "instant" 8B model minimises latency while still giving concise, personalised answers — the responsiveness makes the assistant feel real-time. |
| Financial Health Scoring (`health_service`) | ❌ | — | Pure deterministic math; no model involved. |
| Goal Feasibility Simulator (`goal_service`) | ❌ | — | Pure SIP/PMT math; no model involved. |
| PDF Report Builder (`pdf_service`) | ❌ | — | Formatting/rendering only. |
| User Profile CRUD (`user_routes`) | ❌ | — | Database operations only. |

### Alternative profiles (pick per taste)

If you prefer a different balance, swap the two model values (all from your available list):

| Priority | Report model | Chat model |
|---|---|---|
| **Quality-first** (default above) | `openai/gpt-oss-120b` | `llama-3.1-8b-instant` |
| **Balanced** | `llama-3.3-70b-versatile` | `llama-3.3-70b-versatile` |
| **Speed / cost-first** | `openai/gpt-oss-20b` | `llama-3.1-8b-instant` |
| **Deeper chat quality** | `openai/gpt-oss-120b` | `llama-3.3-70b-versatile` |

> **Models on your key that we intentionally do NOT use** (wrong modality for a text advisor):
> `whisper-large-v3`, `whisper-large-v3-turbo` (speech-to-text), `canopylabs/orpheus-*`
> (text-to-speech), `meta-llama/llama-prompt-guard-2-*` and `openai/gpt-oss-safeguard-20b`
> (input-moderation classifiers), `allam-2-7b` (Arabic-focused), `qwen/qwen3.6-27b` and
> `groq/compound(-mini)` (viable chat/agentic options, but not needed for this scope).
> See the optional enhancement at the end for where a guard model *could* fit later.

---

## 2. Step-by-Step Implementation

### Step 1 — Install the Groq SDK

```bash
pip install groq
```

### Step 2 — Add `groq` to `requirements.txt`

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

> You may leave `openai` in place (harmless) or remove it, since nothing else in the codebase
> imports it after this migration.

### Step 3 — Update `.env`

Your `.env` already has `GROQ_API_KEY`. Add the two per-service model variables so models can
be changed without touching code:

```env
GROQ_API_KEY=gsk_...your-key...
GROQ_REPORT_MODEL=openai/gpt-oss-120b
GROQ_CHAT_MODEL=llama-3.1-8b-instant
API_SECRET_KEY=c0af8656...
RATELIMIT_STORAGE_URI='memory://'
```

### Step 4 — Update `config.py`

Replace the OpenAI key with the Groq key and register the two model settings.

**Current:**

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
    GROQ_API_KEY      = os.getenv("GROQ_API_KEY")
    # Per-service model selection (overridable via .env)
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

### Step 5 — Update `services/ai_service.py`

Three edits: (a) swap the client, (b) let `ask_gpt` accept a model, (c) pass each service's
model at its call site.

**(a) Client construction — current (lines ~1–7):**

```python
from openai import OpenAI
from config import Config

# Initialize OpenAI client
client = OpenAI(
    api_key=Config.OPENAI_API_KEY
)
```

**→ Proposed:**

```python
from groq import Groq
from config import Config

# Initialize Groq client (OpenAI-compatible interface)
client = Groq(
    api_key=Config.GROQ_API_KEY
)
```

**(b) `ask_gpt` — accept a `model` argument. Current:**

```python
def ask_gpt(prompt):

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ]
        )
        return True, response.choices[0].message.content.strip()
    except Exception as e:
        return False, str(e)
```

**→ Proposed:**

```python
def ask_gpt(prompt, model=None):

    try:
        response = client.chat.completions.create(
            model=model or Config.GROQ_CHAT_MODEL,   # default to fast chat model
            temperature=0.7,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ]
        )
        return True, response.choices[0].message.content.strip()
    except Exception as e:
        return False, str(e)
```

**(c) Pass the right model at each call site.**

In `generate_financial_report(...)`, the final line:

```python
    return ask_gpt(prompt)
```

**→ becomes:**

```python
    return ask_gpt(prompt, model=Config.GROQ_REPORT_MODEL)
```

In `chat_with_advisor(...)`, the final line:

```python
    return ask_gpt(prompt)
```

**→ becomes (explicit for clarity; default already resolves to the chat model):**

```python
    return ask_gpt(prompt, model=Config.GROQ_CHAT_MODEL)
```

That is the complete set of code edits. Nothing in `routes/`, `schemas.py`, `database/`, or
the frontend needs to change — the request/response contract is unchanged.

---

## 3. Verification Checklist

1. `pip show groq` confirms the SDK is installed; `groq` appears in `requirements.txt`.
2. `.env` has `GROQ_API_KEY`, `GROQ_REPORT_MODEL`, `GROQ_CHAT_MODEL`, `API_SECRET_KEY`; no `OPENAI_API_KEY`.
3. `python app.py` starts with **no** `EnvironmentError` (confirms `config.validate()` was updated).
4. `POST /api/generate-report {user_id}` returns a full report → confirms the **`openai/gpt-oss-120b`** report path works.
5. `POST /api/chat {user_id, query}` returns a quick reply → confirms the **`llama-3.1-8b-instant`** chat path works.
6. Logs show no reference to `gpt-4o-mini` and no OpenAI auth error.
7. (Optional) Temporarily set `GROQ_CHAT_MODEL` to a bad value and confirm the endpoint returns a clean `500` with the Groq error message — proves the model is read from config.

---

## 4. Optional Future Enhancement — input moderation

Your key also includes guard/safeguard classifiers (`meta-llama/llama-prompt-guard-2-86m`,
`meta-llama/llama-prompt-guard-2-22m`, `openai/gpt-oss-safeguard-20b`). These are **not**
required for the migration, but later you could add a lightweight pre-check in
`chat_with_advisor` that runs the incoming `query` through `llama-prompt-guard-2-22m`
(smallest/fastest) to flag prompt-injection or unsafe input before spending tokens on the main
model. This is a separate feature, not part of the provider swap.

---

## 5. Notes / Caveats

- **Token/context limits differ per model.** `max_tokens=1000` is safe for both assigned
  models; if you switch the report model, confirm the output isn't being truncated.
- The **known chat-context bug** (`content` vs `message` key in `chat_with_advisor`, described
  in `ARCHITECTURE.md`) is unrelated to the provider and is **not** fixed here — track it
  separately.
- Model IDs occasionally get deprecated on Groq; if a model 404s at runtime, update the
  corresponding `.env` value — no code change needed thanks to the config indirection.
