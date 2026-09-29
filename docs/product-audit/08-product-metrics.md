# FinPilot AI — product metrics

**Date:** 2026-09-29  
**Method:** Routes, tables, and log lines were read. No analytics SDK was found in the frontend (`gtag`, PostHog, Mixpanel, Segment, Amplitude, Plausible: none).  
**Rule for this document:** A metric is “measurable today” only when a durable row or a structured log can answer it without guessing. Server logs are not that system. Several log lines include a goal amount or sit next to profile data. They are operational traces, not a warehouse.

Application code was not changed. Counts of real users are `UNKNOWN`. Nothing in the repository is a usage report.

---

## What can be counted today

| Store | What a query can see | What it cannot see |
| --- | --- | --- |
| `accounts` | Signup time (`created_at`). Email exists. `session_version` increases on logout | Login time, failed login, landing visit, device, return visit |
| `users` | Profile created (`created_at`), and that the required fields were present at insert | Abandoned forms, field edits, time on the form. There is no `updated_at` because there is no update route |
| `reports` | Whether a profile has an essay and a score payload. `generated_at` is the **latest** write. `pdf_path` empty or set | How many times they generated. The upsert overwrites the row. Download clicks. Whether they read it |
| `jobs` | Each report or chat attempt: `queued` / `running` / `succeeded` / `failed`, `error_code`, `created_at`, `started_at`, `finished_at` | Whether the person was still on the page when it finished. Chat `payload` is the question text. That column is not a metric |
| `chat_history` | User and model lines with `created_at` | Which starter chip was used. Whether they read the reply. Messages older than the prompt window are still stored, which is good for volume and bad if someone treats the table as “what the model saw” |
| `goal` runs | A log line on success (`goal_plan: simulation complete…`) including name, target rupees, years, and score | A row. After the log is gone, the run is gone. The browser map is not queryable |
| Frontend | Nothing durable | Page views, button clicks, wait-and-leave, scroll, PDF click |

Health scores are not their own table. They are computed inside a report job and stored in `reports.health_json` when the essay is saved. A person can open the dashboard and see annual savings before any job. That view is not recorded.

---

## Funnel

“Instrumentation” means a durable signal. A log line without a table is listed as missing for product measurement.

### Landing

| | |
| --- | --- |
| Event | `landing_viewed`, then `signup_opened` or `signin_opened` |
| Current | None. `/` is a static page |
| Missing | Visitor, referrer, button clicked, sample-versus-signup |
| Question | Do people who see the hero start an account, or leave? |

### Signup

| | |
| --- | --- |
| Event | `signup_submitted`, `signup_succeeded`, `signup_failed` |
| Current | `accounts.created_at` on success. Failures (short password, duplicate email) are not stored |
| Missing | Attempt, error code, time from landing view |
| Question | How many visitors become accounts, and why the rest stop? |

### Authentication

| | |
| --- | --- |
| Event | `login_succeeded`, `login_failed`, `session_restored`, `logout`, `session_expired` |
| Current | Logout bumps `accounts.session_version`. No timestamp on that bump. Login and `/auth/me` write no row |
| Missing | Last seen, failure reason, session length actually used |
| Question | Are people coming back, or only creating an account once? |

### Onboarding

| | |
| --- | --- |
| Event | `profile_form_viewed` |
| Current | None. The signed-in app does not record screen views. The nav title is “Onboarding Profile” even on later visits, so a page name would not mean “first run” |
| Missing | View, time to first field, exit without submit |
| Question | Do new accounts reach the form? |

### Profile completion

| | |
| --- | --- |
| Event | `profile_created` |
| Current | `users.created_at` and `users.account_id`. Submit requires age, income, expenses, savings, risk, and a goal sentence, so a row means the form was complete. EMI is optional and its presence can be inferred from the column |
| Missing | Started-but-abandoned, which field blocked them, edits after create |
| Question | What share of accounts produce a usable snapshot? |

This is the first stage that is actually queryable: accounts with at least one `users` row, and the delay from `accounts.created_at` to the first `users.created_at`.

### First financial analysis

| | |
| --- | --- |
| Event | `score_shown` |
| Current | None as its own event. The score is stored only inside `reports.health_json` after a successful report job. The dashboard can show annual savings and monthly surplus from the profile with no report, and that view is not recorded |
| Missing | Score computed at save time, score viewed, which pillar was on screen |
| Question | Did they see a verdict on their numbers, separate from asking for an essay? |

Today this stage collapses into “first report.” The product could split them. The database does not.

### First goal

| | |
| --- | --- |
| Event | `goal_calculated` |
| Current | No table. One info log includes the target amount and the score. That log is not a metric, and it should not be copied into analytics as raw rupees |
| Missing | A row with account, profile, horizon, feasibility band, and time. Not the essay of the result |
| Question | Do people who have a snapshot test a named target, and do they do it before or after the report? |

### First AI interaction

| | |
| --- | --- |
| Event | First succeeded `jobs` row of kind `chat` or kind `report`, whichever `finished_at` is earlier |
| Current | `jobs` can answer this if the worker is writing rows. Chat lines in `chat_history` confirm a saved reply. A queued job that never finishes is a different count (`status` not `succeeded`) |
| Missing | Which UI control started it (dashboard, advisory, starter chip, typed question). Whether they waited on the page |
| Question | Which AI surface do people hit first, and how often does the job fail before a reply? |

### First report

| | |
| --- | --- |
| Event | `report_succeeded` the first time for that profile |
| Current | `jobs` where `kind = 'report'` and `status = 'succeeded'`, earliest `finished_at`. `reports.generated_at` is only the latest overwrite, so it is the wrong column for “first” |
| Missing | Viewed the advisory page, scrolled to section 05, downloaded the PDF. Download is not logged |
| Question | How many completed profiles get a stored essay, and how long did the job take (`finished_at - started_at`)? |

### First successful outcome

| | |
| --- | --- |
| Event | Not defined in the product. A stored essay is an output, not proof they used it |
| Current | None. No “step done,” no download event, no return to the 30-day list |
| Missing | An outcome the team agrees is value: for example the PDF was downloaded, or they came back and opened the same report, or they updated numbers after the plan. The third one cannot happen until edit exists |
| Question | Did the plan change what they can do next, or did it only get generated? |

### Return session

| | |
| --- | --- |
| Event | `session_started` on a day after `accounts.created_at` |
| Current | None. The 12-hour cookie is not a row. `/auth/me` is not logged. Goal memory dies with the tab |
| Missing | `last_seen_at` on the account, and a session id that is not the password cookie |
| Question | Do they come back tomorrow, in seven days, in thirty days? |

D1, D7, and D30 cannot be computed from the tables as they are.

---

## Metrics hierarchy

Use this order. A lower layer explains a higher one. Vanity counts (page views, message volume, “AI calls”) stay at the bottom.

```text
Outcome        Did the plan stay tied to a current snapshot they still use?
Retention      Did they come back on a later day?
Engagement     What did they do in the sessions they had?
Activation     Did the first session produce a verdict and a plan?
Acquisition    Did a visitor become an account and a profile?
```

### North star candidates

Do not pick a single number until return visits and an updated snapshot exist. Three outcome types fit the product that is actually built. None of them is measurable in full today.

| Candidate | Why it would mean value | Why it is not the metric yet |
| --- | --- | --- |
| A profile whose latest numbers and latest plan were both opened again in a later week | Recurring use of the financial picture, not a one-time essay | No return event. No edit. `generated_at` moves on regenerate even if the numbers did not |
| A goal check that is saved and compared with a later check on the same target | The calculator answers a recurring question (“can I still fund this?”) | Goal results are not stored |
| An account that downloads or revisits a plan after the score was shown | Closest to “they took the output with them” | Download and revisit are not recorded. A succeeded job only means the file can exist |

The type of outcome that matches the product’s intent is the first one: **someone keeps a snapshot current and looks at the plan that belongs to that snapshot.** Report-generation count is a factory metric. It rises if people are stuck regenerating, and it rises if they are succeeding. It cannot be the star.

Until return and edit exist, the honest leading indicator is activation only: share of new accounts with a succeeded report job within 24 hours of `accounts.created_at`. Label it activation, not value.

### Acquisition

| Metric | Definition with today’s data | Gap |
| --- | --- | --- |
| Visitor | Not measurable | Needs `landing_viewed` |
| Signup | Count of `accounts` by `created_at` | No failed attempts, no source |
| Signup → profile | Accounts that have a `users` row | This ratio is computable now |
| Activation (narrow) | Accounts whose first succeeded report job is within 24 hours of signup | Computable from `accounts` and `jobs` if workers have been running. It misses people who only ran a goal |

Do not treat email rows as “interested users.” An account with no profile stopped before the product had any numbers.

### Activation

| Metric | Measurable now? | Definition |
| --- | --- | --- |
| Profile completion | Yes | Account has ≥1 `users` row |
| First analysis | No | Score is not stored until the report job saves `health_json` |
| First goal | No | Log only |
| First meaningful recommendation | Partly | First `jobs` report with `status = succeeded`. “Meaningful” still assumes they saw section 05. The table cannot prove that |
| Time to first plan | Yes, with a caveat | `min(jobs.finished_at)` for a succeeded report minus `accounts.created_at`. Ignores clock skew and accounts that never start a worker |

A useful activation definition for this product, once events exist:

1. Profile saved  
2. Score shown (even before Groq)  
3. Either a goal result or a succeeded report  

Step 2 is the verdict. Step 3 is the recommendation. Today only step 1 and the report half of step 3 are in the database.

### Engagement

| Metric | Measurable now? | Note |
| --- | --- | --- |
| Sessions | No | No session table |
| Profiles per account | Yes | `count(users)` per `account_id`. Does not say why a second profile exists |
| Report jobs per profile | Yes | Includes failures and regenerations. `reports` itself hides regenerations |
| Chat turns per profile | Yes | `chat_history` rows with `role = user` |
| Goal runs | No | |
| PDF downloads | No | `pdf_path` means a file was stored, not that a person downloaded it |
| Financial actions | No | Nothing records “they did a 30-day step” |

Chat volume and regenerate volume are easy to over-read. A long chat can mean the essay failed them. Many report jobs can mean the first job failed.

### Retention

| Metric | Measurable now? |
| --- | --- |
| D1, D7, D30 return | No |
| Recurring financial activity | No. The snapshot cannot be updated, so there is no second financial event to recur |
| Profile still present after 30 days | Weak yes | `users.created_at` and the row still existing. Deletion removes it. Survival is not use |

The retention metric that would match the product later: an account with a `session_started` on day 7 or day 30 that opens a profile whose `updated_at` is newer than the previous plan, or that opens the existing plan and marks it current. That event does not exist.

### Outcome

Prefer these over counts of clicks and tokens.

| Outcome metric | Vanity lookalike to avoid |
| --- | --- |
| Share of succeeded plans that are opened again after 7 days | Number of reports generated |
| Share of profiles where the score and the essay refer to the same snapshot date | Number of regenerations |
| Share of goal runs that are still available on the next session | Number of “Calculate” clicks in a log file |
| Time from profile save to first score the person actually saw | Time to Groq response alone |

None of the outcome column is queryable today. The lookalikes are, and they should not be reported as value.

### AI metrics

All of these except feedback and abandonment can be approximated from `jobs` plus `chat_history`.

| Metric | How to compute now | Limit |
| --- | --- | --- |
| Usage | Count of jobs by `kind` and day | Includes retries. Excludes the goal screen, which is not AI |
| Completion | `status = succeeded` / all jobs of that kind | A succeeded report can still have `pdf_path` null. Text and PDF are different completions |
| Failure | `status = failed` by `error_code` (`upstream_timeout`, `upstream_rate_limit`, `upstream_error`, `worker_lost`, `server_error`) | Good operational split. Not a user-visible reason code in a warehouse |
| Duration | `finished_at - started_at` | Missing if the process dies before `finished_at`. Stale running rows become `worker_lost` |
| Regeneration | Count of succeeded report jobs after the first, per profile | Do this from `jobs`, not from `reports` |
| Abandonment | Not measurable | Need “generate clicked” and “left while status was running” |
| User feedback | None | No rating, no “this step was wrong,” no edit of a sentence |
| Truncation | Log only (`finish_reason=length`) | Not a column. A truncated essay can be `succeeded` |

Chat `payload` and message text are content. Metrics should store lengths, latency, and error codes, not the question.

### System and product connection

```text
Product event              Backend                         Durable store              Analytics today
landing_viewed             none                            none                       missing
signup_succeeded           POST /api/auth/signup           accounts.created_at        row exists, no event name
login_succeeded            POST /api/auth/login            cookie only                missing
profile_created            POST /api/profile               users.created_at           row exists
score_shown                none until report save          reports.health_json        tied to the essay
goal_calculated            POST /api/goal-plan             log line only              missing
report_enqueued            POST /api/generate-report       jobs status=queued         row exists
report_succeeded           worker _run_report              jobs succeeded + reports   row exists
report_failed              worker                          jobs.error_code            row exists
pdf_stored                 worker PDF step                 reports.pdf_path           file flag, not a download
pdf_downloaded             GET /api/download-report/<id>   none                       missing
chat_enqueued              POST /api/chat                  jobs + payload (the text)  row exists; do not warehouse payload
chat_succeeded             worker _run_chat                jobs + chat_history        row exists
chat_cleared               DELETE /api/chat/history/<id>   rows removed               the act is not stored
profile_deleted            DELETE /api/profile/<id>        rows removed               the act is not stored
session_returned           GET /api/auth/me                none                       missing
```

Rate-limit buckets and health checks are system metrics. They answer “is the API up,” not “did a person get a plan.”

---

## Minimum analytics system

Keep it smaller than a marketing suite. The financial product should not send income, EMI, goal amounts, or chat text to a third-party tracker. The same notice that should precede Groq should precede any export of behavior, if an outside tool is used.

**1. Account activity, on the account row.** `last_seen_at` updated when a signed-in request succeeds. That single column unlocks D1, D7, and D30 without a page-view firehose.

**2. An append-only event table in the application database.** Columns: `id`, `account_id`, `profile_id` nullable, `name`, `created_at`, and a small `context` jsonb for non-sensitive keys only (`job_id`, `kind`, `status`, `error_code`, `surface`). No message body, no rupees.

Names worth storing first:

- `signup_succeeded`
- `login_succeeded`
- `profile_created`
- `profile_deleted`
- `report_enqueued`
- `report_succeeded`
- `report_failed`
- `pdf_downloaded`
- `chat_enqueued`
- `chat_succeeded`
- `chat_failed`
- `goal_calculated` with horizon and a feasibility band, not the target amount
- `session_started` once per account per day

**3. Client events the server cannot see.** `landing_viewed`, `signup_opened`, `profile_form_abandoned`, `report_wait_abandoned`, `advisory_viewed`. Send them to the same event table through one authenticated or anonymous endpoint. Anonymous landing events need a visitor id that is not the email.

**4. Definitions written down before dashboards.** Activation = profile and first succeeded report within 24 hours. Retention = `session_started` on day 7. Outcome stays unset until “opened again” or “snapshot updated” exists. AI failure rate = failed jobs / jobs, by `error_code`, excluding the stub.

**5. Do not build from the current logs.** Goal logs contain rupees. Chat jobs contain the question. Scraping them recreates a second copy of financial data with worse access control than the tables.

That set answers the funnel through first report and makes return visits possible to count. It still does not prove that the advice helped. Outcome metrics wait on two product facts that are missing in the app itself: a way to update the snapshot, and a way to record that they came back to the plan that matches it.
