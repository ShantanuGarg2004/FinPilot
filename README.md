<div align="center">

# FinPilot AI

### AI-Powered Personal Financial Advisor

A production-oriented **Flask + React** application that pairs deterministic financial-scoring
engines with an LLM advisory layer (**Groq**) to deliver personalised financial
health assessments, AI-generated advisory reports, conversational guidance, and
goal-feasibility simulations for Indian retail investors.

<br/>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-Frontend-646CFF?logo=vite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM-F55036?logo=groq&logoColor=white)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Request Lifecycle](#request-lifecycle)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Financial Health Scoring Model](#financial-health-scoring-model)
- [Goal Feasibility Simulator](#goal-feasibility-simulator)
- [Database Schema](#database-schema)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)
- [Author](#author)

---

## Overview

FinPilot AI ingests a user's financial profile — age, income, expenses, savings, risk
appetite, goals, and an optional EMI figure — and layers three independent engines on top of it:

1. **Deterministic financial-health scorer** — a 7-pillar, rule-based engine that produces a
   0–100 score with no AI involvement, so results are reproducible and explainable.
2. **LLM advisory layer** — turns the scored profile into a structured, SEBI-advisor-style
   report and a conversational chat assistant, grounded in the user's actual numbers. Powered
   by **Groq** with per-service model routing (a high-capability model for the in-depth report,
   a low-latency model for live chat).
3. **Goal-feasibility simulator** — SIP (Systematic Investment Plan) annuity-due mathematics
   that projects Conservative / Balanced / Aggressive investment scenarios.

Reports are rendered to branded PDF documents on disk. Profiles, reports, and chat live in
PostgreSQL. The browser signs in with an email and password and keeps an HttpOnly session
cookie. Scripts and Swagger still send `X-API-Key`. A rate-limit gateway sits in front of
the API, with its own PostgreSQL database. Swagger is on only when `FLASK_ENV` is local.

---

## Key Features

- **Financial Health Score** — 7-pillar rule-based engine (savings rate, expense control,
  emergency fund, debt-to-income, retirement adequacy, tax efficiency, surplus buffer).
- **AI-Generated Advisory Reports** — structured, section-based reports grounded in the
  user's real figures, produced via Groq (`openai/gpt-oss-120b` by default).
- **Conversational Advisor Chat** — per-profile chat with history stored in PostgreSQL.
- **Goal Feasibility Simulator** — SIP PMT–based required-contribution calculator with three
  CAGR scenarios, feasibility scoring, and a recommended timeline.
- **PDF Report Generation** — branded, multi-section advisory PDFs via ReportLab (cover page,
  snapshot, insights, warnings, AI recommendations, action checklist, disclaimer).
- **Persistent storage** — PostgreSQL database `finpilot` for accounts, profiles, reports, and
  chat. PDF files live under `data/pdfs`. The limiter uses a separate database,
  `finpilot_ratelimit`.
- **Sign-in** — email and a Werkzeug password hash. The browser session is an HttpOnly cookie,
  `finpilot_session`. A signed-in person only sees their own profiles.
- **API key** — `X-API-Key` remains for Swagger and local scripts. It can read every profile.
  The React app does not send it.
- **Rate limiting** — one gateway. Quotas come from config. Unknown `/api` routes are denied.
- **Swagger / OpenAPI** — `http://127.0.0.1:5000/apidocs/` when `FLASK_ENV` is `development`,
  `dev`, or `local`. Password is `API_SECRET_KEY` (any username).
- **Strict Request Validation** — Marshmallow schemas on every mutating endpoint.
- **React + Vite Frontend** — a polished single-page client (`frontend/`) that consumes the API.

---

## Architecture

```mermaid
flowchart LR
    subgraph CLIENT["Frontend — React + Vite"]
        UI["FinancialAdvisor UI<br/>Profile · Report · Chat · Simulator"]
    end

    subgraph API["Flask API — app.py (create_app)"]
        MW["Actor<br/>session cookie or X-API-Key"]
        RL["Rate-limit gateway"]
        SW["Swagger UI<br/>/apidocs"]
        UB["user_routes<br/>/api/profile · /api/users"]
        RB["report_routes<br/>/api/generate-report · /api/download-report"]
        CB["chat_routes<br/>/api/chat · /api/chat/history"]
        GB["goal_routes<br/>/api/goal-plan"]
    end

    subgraph SERVICES["Service Layer"]
        HS["health_service<br/>7-pillar scorer"]
        GS["goal_service<br/>SIP PMT engine"]
        AS["ai_service<br/>Groq wrapper"]
        PS["pdf_service<br/>ReportLab builder"]
    end

    subgraph EXTERNAL["External"]
        OAI["Groq API<br/>report + chat models"]
    end

    subgraph DATA["PostgreSQL"]
        DB[("finpilot<br/>accounts · users · reports · chat")]
        RLDB[("finpilot_ratelimit<br/>rate-limit buckets")]
    end

    UI -- "HTTP + session cookie" --> MW
    MW --> RL
    RL --> UB & RB & CB & GB

    RL --> RLDB
    UB --> DB
    RB --> HS & AS & PS & DB
    CB --> AS & DB
    GB --> GS & DB
    AS --> OAI
```

**Layer summary**

1. Every `/api/*` request (except `OPTIONS`, health, sign-in, sign-up, and sign-out) needs a
   session cookie or a valid `X-API-Key`, then the rate-limit gateway, before a blueprint runs.
2. Route handlers validate incoming JSON against Marshmallow schemas, then delegate to the
   service layer.
3. `health_service` computes a deterministic 0–100 score, `goal_service` runs SIP
   projections, `ai_service` calls Groq, and `pdf_service` renders the final PDF.
4. Accounts, profiles, reports, and chat live in PostgreSQL (`finpilot`) through a connection
   pool. Advisory PDFs are files on disk. Rate-limit counters live in `finpilot_ratelimit`.

> A deeper engineering write-up — including the data model, per-service diagrams, and a full
> production-readiness assessment — lives in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Request Lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant API as Flask API
    participant SC as Marshmallow
    participant S as Service Layer
    participant DB as PostgreSQL

    C->>API: HTTP request + session cookie or X-API-Key
    API->>API: Actor check + rate-limit gateway
    API->>SC: schema.load(json)
    alt invalid
        SC-->>C: 400 + field errors
    else valid
        API->>S: delegate to service
        S->>DB: read / write
        DB-->>S: rows
        S-->>API: result
        API-->>C: 200 JSON
    end
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Flask, Flask-CORS, rate-limit gateway |
| API documentation | Flasgger (Swagger UI) |
| Validation | Marshmallow |
| Database | PostgreSQL 16 (`finpilot` for app data, `finpilot_ratelimit` for quotas) |
| AI / LLM | Groq (`openai/gpt-oss-120b` report · `openai/gpt-oss-20b` chat) |
| PDF generation | ReportLab |
| Frontend | React 19, Vite, Tailwind, ESLint |
| Config | python-dotenv |

---

## Project Structure

```
FinPilot/
├── app.py                     # App factory: CORS, auth middleware, rate limiter, Swagger, blueprints
├── config.py                  # Environment variable loading and validation
├── extensions.py              # Shared Flask-Limiter instance
├── schemas.py                 # Marshmallow request schemas (Profile, Report, Chat, GoalPlan)
├── requirements.txt           # Python dependencies
├── database/
│   ├── db.py                  # PostgreSQL pool (one connection per request)
│   ├── models.py              # Table creation for accounts, users, reports, chat
│   ├── repository.py          # Profile, report, chat, and account SQL
│   └── sqlite_import.py       # One-time copy from finance.db when finpilot is empty
├── routes/
│   ├── auth_routes.py         # Sign-up, sign-in, sign-out, current account
│   ├── user_routes.py         # Profile CRUD (/api/profile, /api/users)
│   ├── report_routes.py       # Report generation, retrieval, PDF download
│   ├── chat_routes.py         # Chat + chat-history retrieval/deletion
│   └── goal_routes.py         # Goal feasibility simulation endpoint
├── services/
│   ├── health_service.py      # 7-pillar financial-health scoring engine
│   ├── goal_service.py        # SIP PMT math, scenario simulation, feasibility scoring
│   ├── ai_service.py          # Groq client wrapper, report + chat generation
│   ├── pdf_service.py         # ReportLab PDF report builder
│   └── profiling_service.py   # Standalone profile validation/normalization helpers
├── utils/
│   └── prompt_builder.py      # Deterministic, grounded prompt construction for the LLM
├── frontend/
│   └── src/                   # Sign-in gate, profile, dashboard, chat, goals
├── tests/                     # Pytest. Groq is mocked. App DB is finpilot_test.
├── conftest.py                # Pytest bootstrap (sys.path + deterministic test env)
└── docs/
    └── ARCHITECTURE.md        # Detailed architecture & production-readiness reference
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Docker (local PostgreSQL 16)
- A Groq API key
- Node.js 18+ (for the frontend)

### 1. Clone the repository

```bash
git clone https://github.com/ShantanuGarg2004/FinPilot.git
cd FinPilot
```

### 2. Backend setup

```bash
# (recommended) create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your-groq-api-key
API_SECRET_KEY=your-chosen-api-secret
FLASK_ENV=development
RATELIMIT_STORAGE_BACKEND=sql
RATELIMIT_DATABASE_URL=postgresql+psycopg://finpilot:finpilot_dev_password@127.0.0.1:5432/finpilot_ratelimit
APP_DATABASE_URL=postgresql+psycopg://finpilot:finpilot_dev_password@127.0.0.1:5432/finpilot

# Optional — per-service model overrides (defaults shown)
GROQ_REPORT_MODEL=openai/gpt-oss-120b
GROQ_CHAT_MODEL=openai/gpt-oss-20b
```

> `GROQ_API_KEY` and `API_SECRET_KEY` are **required**. `FLASK_ENV=development` turns Swagger on.
> `APP_DATABASE_URL` is the application database. `RATELIMIT_DATABASE_URL` is only the limiter.
> See `.env.example`.

**Local PostgreSQL:**

```bash
docker compose up -d
```

The limiter schema is applied from `database/sql/rate_limit_schema.sql` on a new volume. The `finpilot` database is created when the API starts. If a `finance.db` file is present and `finpilot` has no profiles, those rows are copied once. Set `BOOTSTRAP_ACCOUNT_EMAIL` and `BOOTSTRAP_ACCOUNT_PASSWORD` when copied profiles have no account.

Run the server:

```bash
python app.py
```

Production uses several workers so one slow Groq call does not block every reader. See `docs/CAPACITY_RUNBOOK.md`. On Windows, Waitress; on Linux, Gunicorn. Install those only on the host that serves traffic (`pip install waitress` or `pip install gunicorn`). Defaults are 6 workers, a 90s Groq timeout, and a 120s worker timeout.

- API base: `http://127.0.0.1:5000`
- Interactive docs: `http://127.0.0.1:5000/apidocs/` (local `FLASK_ENV` only)

Sign in from the React app, or send `X-API-Key: your-chosen-api-secret` from curl and Swagger. Swagger first asks for HTTP Basic auth. The password is the same `API_SECRET_KEY`. Any username works.

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The dev server runs at `http://localhost:5173` and proxies `/api` to Flask, so the session cookie stays on one origin. `frontend/.env`:

```env
VITE_API_URL=/api
```

Do not put the API key in the frontend. Details are in [`frontend/README.md`](frontend/README.md).

### 4. Running tests

Groq calls are mocked. Tests use PostgreSQL database `finpilot_test` (Docker must be up locally; GitHub Actions starts its own Postgres):

```bash
python -m pytest tests/ -q --tb=line --deselect tests/test_wave1_integration.py::test_sql_backend_ping_when_configured
```

---

## API Reference

Health, sign-up, sign-in, and sign-out are public. `/api/auth/me` needs the session cookie. Other `/api/*` routes accept that cookie or `X-API-Key`. A cookie actor only sees their own profiles. The API key sees every profile.

| Endpoint | Method | Who | Description |
|---|---|---|---|
| `/api/health` | GET | public | Liveness |
| `/apidocs/` | GET | local env + Basic password `API_SECRET_KEY` | Swagger UI |
| `/api/auth/signup` | POST | public | Create an account and set the session cookie |
| `/api/auth/login` | POST | public | Sign in and set the session cookie |
| `/api/auth/logout` | POST | public | Clear the session cookie |
| `/api/auth/me` | GET | session cookie | Current account |
| `/api/users` | GET | cookie or API key | List profiles for that actor |
| `/api/profile` | POST | cookie or API key | Create a profile |
| `/api/profile/<user_id>` | DELETE | cookie or API key | Delete a profile, its report, and its chat |
| `/api/generate-report` | POST | cookie or API key | Generate an AI report, then a PDF |
| `/api/report/<user_id>` | GET | cookie or API key | Fetch a stored report |
| `/api/download-report/<user_id>` | GET | cookie or API key | Download the PDF |
| `/api/chat` | POST | cookie or API key | Send a message to the advisor |
| `/api/chat/history/<user_id>` | GET, DELETE | cookie or API key | Read or clear chat history |
| `/api/goal-plan` | POST | cookie or API key | Run the goal feasibility simulation |

Quotas are per route class in config (for example chat 15 per minute, report generation 5 per minute). The gateway is the only limiter. Unknown `/api` paths return 429 `rate_policy_missing`.

<details>
<summary>Example: create a profile</summary>

```bash
curl -X POST http://127.0.0.1:5000/api/profile \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-chosen-api-secret" \
  -d '{
    "age": 28,
    "income": 90000,
    "expenses": 50000,
    "savings": 25000,
    "risk_appetite": "medium",
    "financial_goals": "Buy a house in 7 years",
    "debt_emi": 8000
  }'
```
</details>

---

## Financial Health Scoring Model

The health score is computed across seven weighted pillars, totalling 100 points:

| Pillar | Max points | Full-marks threshold |
|---|---|---|
| Savings rate | 25 | 30% of income or higher |
| Expense control | 20 | Expenses ≤ 50% of income |
| Emergency fund | 20 | 6+ months of expenses covered |
| Debt-to-income ratio | 15 | ≤ 20% DTI (partial credit if EMI not provided) |
| Retirement adequacy | 10 | Age-adjusted corpus projection vs. a 25× annual-expense target |
| Tax efficiency | 5 | Estimated Section 80C utilisation |
| Surplus buffer | 5 | Any positive monthly surplus |

Each pillar independently returns point contributions, human-readable insights, and warnings,
which are aggregated into the final score and passed to the AI report generator for grounded advice.

---

## Goal Feasibility Simulator

The simulator uses the standard SIP PMT (annuity-due) formula to compute the monthly
contribution required to reach a target amount within a given horizon:

```
P = FV × r / [ ((1 + r)^n − 1) × (1 + r) ]
```

Where `P` is the required monthly SIP, `FV` is the target amount, `r` is the monthly rate, and
`n` is the number of months. The engine:

- Selects instrument recommendations and CAGR assumptions from risk appetite and horizon
  (Low / Medium / High tiers).
- Produces Conservative, Balanced, and Aggressive scenario projections.
- Computes a rule-based feasibility score (0–100) from savings coverage, horizon bonus, and
  risk-alignment bonus.
- Binary-searches the achievable timeline at the current savings rate.

---

## Database Schema

Database `finpilot` on PostgreSQL:

| Table | Purpose | Key constraints |
|---|---|---|
| `accounts` | Email and password hash | Unique email |
| `users` | Financial profiles owned by an account | `account_id` references `accounts` |
| `reports` | Advisory text and the PDF file name | `user_id` unique, cascade delete. `pdf_blob` is nullable leftover storage |
| `chat_history` | Per-profile chat messages | Cascade delete, `role ∈ {user, ai}` |

Indexes cover `reports(user_id)`, `chat_history(user_id, id DESC)`, and `users(account_id)`. PDF bytes are files named `profile_<user_id>.pdf` under `data/pdfs`.

Rate-limit counters stay in database `finpilot_ratelimit`, not in these tables.

---

## Roadmap

- Move report generation off the request thread if live Groq calls saturate the workers.
- Confirm capacity with about 100 concurrent people. The Q6 check measured a smaller read burst. See `docs/testing_reports/Q6_IMPLEMENTATION_AND_TEST_REPORT.md`.
- Support live market data for CAGR assumptions instead of static tiers.

---

## Disclaimer

This system provides AI-assisted **educational** financial guidance and does **not** constitute
regulated investment advice. Independent professional consultation is recommended before making
investment decisions.

---

## Author

**Shantanu Garg**
B.Tech CSE-AI, Graphic Era (Deemed to be University), Dehradun
