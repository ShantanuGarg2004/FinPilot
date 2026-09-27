# Documents

Files under `docs/` are grouped by what they are for.

## architecture

How the running system works.

- `ARCHITECTURE.md` — request path, worker, and databases
- `AUTH_ARCHITECTURE.md` — cookie, scoped key, and the docs password
- `CAPACITY_RUNBOOK.md` — Waitress or Gunicorn, threads, and timeouts
- `APP_DATABASE_POSTGRES.md` — the application database
- `RATE_LIMITER_ARCHITECTURE.md` — limiter design
- `IDENTITY_SEAM.md` — who a request is
- `USER_EXPERIENCE.md` — what a person using the app sees
- `FRONTEND_ERROR_HANDLING.md` — toasts and error states

## planning

What was going to be built, and in what order.

- `PLATFORM_QUALITY_WAVES.md` — Q1 through Q6
- `IMPLEMENTATION_PLAN_RATE_LIMITER_AND_BOTTLENECKS.md` — Waves 0 through 3
- `ARCHITECTURE_REMEDIATION_PLAN.md` — issues 1 through 11
- `ARCHITECTURE_REVIEW_FOLLOWUP_PLAN.md` — the later review, issues 1 through 8
- `ISSUE_REMEDIATION_PLAN.md` — debt, chat memory, and prompts
- `GROQ_MIGRATION.md` — why the provider moved to Groq
- `GROQ_PATH_B_IMPLEMENTATION.md` — the steps for that move

## analysis

Reviews and measurements. These record what was found.

- `PLATFORM_ARCHITECTURE_BOTTLENECKS.md`
- `ARCHITECTURE_AND_ISSUE_6_ANALYSIS.md`

## execution

What was built, and the reports from running it.

- `GROQ_PATH_B_IMPLEMENTATION_REPORT.md` — what the Groq move changed
- `testing_reports/` — one report for each quality wave, remediation issue, the database move, and each review follow-up

`architecture/ARCHITECTURE.md` is the current system. `planning/` is the order the work was planned.
