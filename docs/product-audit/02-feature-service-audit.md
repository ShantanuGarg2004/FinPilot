# FinPilot AI — feature and service audit

**Date:** 2026-09-29  
**Builds on:** `docs/product-audit/01-product-360-audit.md`  
**Check against the repo:** Routes, pages, services, and tables were read again. Claims below match that code. Measured usage is `UNKNOWN`. No product analytics SDK was found in the frontend.

This document maps features and services. It does not change the product.

Class labels used here:

- **CORE PRODUCT** — the financial job a customer came for
- **SUPPORTING PRODUCT** — helps that job, or sells it
- **AI CAPABILITY** — Groq writes or answers
- **UTILITY** — chrome around the job
- **ACCOUNT/PLATFORM** — identity and return
- **INFRASTRUCTURE** — the customer should not have to think about it

`FUTURE OPPORTUNITY` means a proposal. It is not in the product.

---

## How to read a feature

Each feature uses the same seventeen fields. Status is one of: **exists**, **partial**, **planned but not implemented**, **missing**, **visible but not a feature**.

---

## 1. Landing page

| Field | Finding |
| --- | --- |
| Class | SUPPORTING PRODUCT |
| 1. Name | Marketing landing page |
| 2. Problem | A visitor needs a reason to create an account |
| 3. User | Someone who is not signed in |
| 4. Trigger | Opens the site |
| 5. Entry | `/` while signed out (`frontend/src/pages/LoginPage.jsx`) |
| 6. Input | None |
| 7. Workflow | Story, three cards, screenshots, then a sign-up or sign-in dialog |
| 8. Output | A decision to sign up, sign in, or leave |
| 9. Value | Explains the intended feeling: a calmer view of money |
| 10. Dependencies | None |
| 11. AI | None. The hero score of 82 and “+8.4% this quarter” are written into the page |
| 12. Database | None |
| 13. Status | Exists |
| 14. UX | Strong as a page. Weak as a preview of the real first screen |
| 15. Friction | “Live financial picture” is not the visitor’s data. “See the platform” only scrolls |
| 16. Missing | A true sample of the empty dashboard, pricing, privacy, terms |
| 17. Evolution | `FUTURE OPPORTUNITY` — a landing page that shows the real first-run, not a finished score |

---

## 2. Sign up

| Field | Finding |
| --- | --- |
| Class | ACCOUNT/PLATFORM |
| 1. Name | Create account |
| 2. Problem | The snapshot has to belong to someone |
| 3. User | A new person with an email |
| 4. Trigger | Get started, Start your financial map, or Create your free account |
| 5. Entry | Auth dialog, sign-up mode by default |
| 6. Input | Email, password, confirm password. Server requires 12 characters (`schemas.py`) |
| 7. Workflow | `POST /api/auth/signup` sets `finpilot_session` and opens the app |
| 8. Output | An account and a signed-in profile screen |
| 9. Value | Required to keep profiles private to that person |
| 10. Dependencies | PostgreSQL `accounts` |
| 11. AI | None |
| 12. Database | `accounts` |
| 13. Status | Exists. Email verification is missing. A planning note says verification is not in that plan |
| 14. UX | Adequate dialog. The 12-character rule appears only after a failed submit |
| 15. Friction | No terms, no privacy, no statement that numbers will be sent to Groq |
| 16. Missing | Verification, consent, password hint before submit |
| 17. Evolution | `FUTURE OPPORTUNITY` — verify the email before the first report is sent to the model |

---

## 3. Sign in and return

| Field | Finding |
| --- | --- |
| Class | ACCOUNT/PLATFORM |
| 1. Name | Sign in |
| 2. Problem | Come back to the same profiles, report, and chat |
| 3. User | Someone who already has an account |
| 4. Trigger | Sign in, or a later visit while the cookie is still valid |
| 5. Entry | Auth dialog, or `GET /api/auth/me` on load |
| 6. Input | Email and password, or the existing cookie |
| 7. Workflow | Cookie lasts 12 hours (`services/sessions.py`). The last profile id for this tab is kept in `sessionStorage` |
| 8. Output | The signed-in shell |
| 9. Value | The report and chat are still there |
| 10. Dependencies | `accounts.session_version` |
| 11. AI | None |
| 12. Database | `accounts` |
| 13. Status | Exists |
| 14. UX | Adequate |
| 15. Friction | No “forgot password.” After 12 hours the only recovery is remembering the password |
| 16. Missing | Reset, password change, “this is a new device” |
| 17. Evolution | `FUTURE OPPORTUNITY` — reset by email. Not built |

---

## 4. Sign out

| Field | Finding |
| --- | --- |
| Class | ACCOUNT/PLATFORM |
| 1. Name | Sign out |
| 2. Problem | Leave a shared browser without leaving the session open |
| 3. User | The signed-in person |
| 4. Trigger | Sign out in the sidebar |
| 5. Entry | `frontend/src/components/layout/Sidebar.jsx` |
| 6. Input | None |
| 7. Workflow | `POST /api/auth/logout` bumps `session_version`, clears the cookie, and drops in-memory report, chat, and goal caches |
| 8. Output | The landing page |
| 9. Value | Ends access |
| 10. Dependencies | Session cookie |
| 11. AI | None |
| 12. Database | `accounts.session_version` |
| 13. Status | Exists |
| 14. UX | Adequate. Easy to find |
| 15. Friction | None major |
| 16. Missing | A list of other sessions. `UNKNOWN` if that is needed |
| 17. Evolution | None required for the current job |

---

## 5. Create a financial profile

| Field | Finding |
| --- | --- |
| Class | CORE PRODUCT |
| 1. Name | Create profile |
| 2. Problem | Nothing else can run until the product has monthly numbers |
| 3. User | The account holder. A second profile’s meaning (another person, or another scenario) is `UNKNOWN` |
| 4. Trigger | First sign-in, or New profile |
| 5. Entry | Profile in the sidebar, or the person-add icon in the top bar. Page title is “Onboarding Profile” even on later visits |
| 6. Input | Age, monthly income, expenses, savings, risk (Conservative / Balanced / Aggressive), goal text. EMI is optional |
| 7. Workflow | `POST /api/profile`. On success the app opens the dashboard |
| 8. Output | A row in `users`, titled in the UI by the goal text |
| 9. Value | This is the raw material for the score, the plan, the chat, and the goal check |
| 10. Dependencies | Signed-in account |
| 11. AI | None at save time |
| 12. Database | `users` |
| 13. Status | Exists. Edit is missing. No `PUT` or `PATCH` for a profile was found |
| 14. UX | Adequate form, one screen, clear “Continue to Dashboard” |
| 15. Friction | The form badge says ENCRYPTED. Amounts are stored as ordinary numeric columns. The goal sentence becomes the profile name, so a long goal is a clumsy label |
| 16. Missing | Edit in place, dependents, city, holdings, a named person for the profile |
| 17. Evolution | `FUTURE OPPORTUNITY` — edit the snapshot and refresh the score without deleting the plan |

---

## 6. Saved profiles

| Field | Finding |
| --- | --- |
| Class | CORE PRODUCT |
| 1. Name | Choose or delete a profile |
| 2. Problem | More than one snapshot may exist; the rest of the app follows the one that is selected |
| 3. User | The account holder |
| 4. Trigger | Open Profile, or return with a stored profile id |
| 5. Entry | Right-hand list on the profile page (`SavedProfiles.jsx`) |
| 6. Input | A click, or the trash icon |
| 7. Workflow | Select stores the id and, from the profile page, opens the dashboard. Delete calls `DELETE /api/profile/<id>` immediately |
| 8. Output | The active profile changes, or the profile, its report, and its chat are removed |
| 9. Value | Lets one account hold more than one picture |
| 10. Dependencies | `GET /api/users` |
| 11. AI | None |
| 12. Database | `users`, and by cascade `reports`, `chat_history`, `jobs` |
| 13. Status | Partial. Select and delete exist. Delete has no confirmation. No undo |
| 14. UX | The list is clear. Delete is too easy |
| 15. Friction | One tap destroys the plan and the conversation |
| 16. Missing | Confirm, undo, edit, an explanation of what a second profile is |
| 17. Evolution | `FUTURE OPPORTUNITY` — household profiles with a name, if that is the job. Otherwise keep one profile and drop the extra concept |

---

## 7. Dashboard

| Field | Finding |
| --- | --- |
| Class | CORE PRODUCT |
| 1. Name | Dashboard |
| 2. Problem | “Where do I stand, and what can I open next?” |
| 3. User | Someone with a selected profile |
| 4. Trigger | After create, after select, or Dashboard in the nav. Nav stays locked until a profile is selected |
| 5. Entry | `/dashboard` |
| 6. Input | The selected profile. A report, if one exists |
| 7. Workflow | Loads `GET /api/report/<id>`. Annual savings and monthly surplus are computed from the profile even before a report. The gauge, pillars, and insight cards wait for the report |
| 8. Output | Two money stats always. Score, pillars, warnings, and shortcuts after a report |
| 9. Value | The home of the product once a report exists |
| 10. Dependencies | Profile. Report job for the score |
| 11. AI | Indirect. The score is rules (`services/health_service.py`). The screen tells the person to generate an AI report to unlock it |
| 12. Database | `users`, `reports` |
| 13. Status | Exists, with an empty state that blocks the score |
| 14. UX | Strong after a report. Weak before one: an empty gauge and a generate button |
| 15. Friction | The first useful picture is tied to Groq and to a worker the customer does not start |
| 16. Missing | A score on save. A note that surplus is income minus expenses, which can disagree with the savings field |
| 17. Evolution | `FUTURE OPPORTUNITY` — show the rule-based score the moment the profile is saved. Keep Groq for the written plan only |

---

## 8. Health score

| Field | Finding |
| --- | --- |
| Class | CORE PRODUCT |
| 1. Name | Seven-pillar health score |
| 2. Problem | “Is this monthly picture okay?” |
| 3. User | The selected profile |
| 4. Trigger | A successful report job, then Dashboard or Advisory |
| 5. Entry | Gauge on those two pages. Pillar labels live in `frontend/src/lib/format.js` |
| 6. Input | Age, income, expenses, savings, optional EMI, risk. Tax uses an assumption that about 30% of savings goes toward Section 80C |
| 7. Workflow | `calculate_health_score` runs in the worker before Groq. The result is stored in `reports.health_json` |
| 8. Output | 0–100, labels Healthy / Moderate / At Risk, seven pillars, insight strings, warning strings |
| 9. Value | The most checkable number in the product. The person can read why |
| 10. Dependencies | A report row. The math itself does not need Groq |
| 11. AI | None |
| 12. Database | `reports.health_json` |
| 13. Status | Partial as a product. The service exists. The customer cannot see it without the AI job |
| 14. UX | Good once visible. Pillars have names and point ceilings |
| 15. Friction | Assumptions (80C share, emergency months) are not shown next to the gauge |
| 16. Missing | A standalone “score my snapshot” action that does not call the model |
| 17. Evolution | `FUTURE OPPORTUNITY` — financial health monitoring: rescore when numbers change, and show what moved. Monitoring over time is not built. There is no history of scores |

---

## 9. AI advisory report

| Field | Finding |
| --- | --- |
| Class | AI CAPABILITY |
| 1. Name | Advisory report |
| 2. Problem | “What should I do with this picture?” |
| 3. User | The selected profile |
| 4. Trigger | Generate on the dashboard or on Advisory. Regenerate if a report already exists |
| 5. Entry | `/advisory`, and the dashboard empty state |
| 6. Input | Profile fields sent in the prompt: age, income, expenses, savings, risk, goal text, score, insights, warnings. EMI is not its own line in `generate_financial_report` |
| 7. Workflow | `POST /api/generate-report` returns 202. `python -m services.jobs.worker` calls Groq, saves text, then tries the PDF. The page polls for about two minutes |
| 8. Output | One stored write-up per profile, in a fixed outline: summary, budget, investments, risks, goal strategy, 30-day plan |
| 9. Value | The main artifact. This is the plan they can read |
| 10. Dependencies | Profile, health score, Groq, a running worker, quotas (default 5 per minute on the account and 10 per hour on the profile) |
| 11. AI | Yes. Default report model is `openai/gpt-oss-120b` unless overridden. Temperature 0.7. The system persona says to sound like a real advisor |
| 12. Database | `jobs`, `reports.ai_report`, `reports.health_json` |
| 13. Status | Exists |
| 14. UX | Strong layout: score and pillars first, model text in section 05, then a disclaimer |
| 15. Friction | Wait with no worker status. Regenerate replaces the only copy. Quota errors say to wait, not what the allowance is |
| 16. Missing | Version history, sources for named products, EMI in the prompt, a way to keep the old text |
| 17. Evolution | `FUTURE OPPORTUNITY` — coaching that checks off the 30-day steps. Those steps are prose today, not tasks |

---

## 10. PDF download

| Field | Finding |
| --- | --- |
| Class | SUPPORTING PRODUCT |
| 1. Name | Advisory PDF |
| 2. Problem | Take the plan out of the browser |
| 3. User | Someone who already has advisory text |
| 4. Trigger | PDF on the advisory page |
| 5. Entry | Advisory, only after a report exists |
| 6. Input | The profile id |
| 7. Workflow | `GET /api/download-report/<id>` after an ownership check. If the file is missing, the server can rebuild it from saved text without another model call |
| 8. Output | A PDF file. The PDF disclaimer says the report is educational and not regulated advice |
| 9. Value | A shareable or printable copy of the same plan |
| 10. Dependencies | Saved advisory text. Disk under `data/pdfs` |
| 11. AI | No new model call on download |
| 12. Database | `reports.pdf_path`. The file is not in the database |
| 13. Status | Exists. The dashboard warns when text is saved and the file is not ready |
| 14. UX | Adequate. One button |
| 15. Friction | The person is told to download in order to build the file. That is an operator detail |
| 16. Missing | Any other export (CSV of the snapshot, chat transcript) |
| 17. Evolution | `FUTURE OPPORTUNITY` — a household or advisor pack. Not implied by a second profile until that concept is defined |

---

## 11. Advisor chat

| Field | Finding |
| --- | --- |
| Class | AI CAPABILITY |
| 1. Name | Advisor chat |
| 2. Problem | A follow-up the report did not answer |
| 3. User | The selected profile |
| 4. Trigger | Chat in the nav, or AI Chat on the dashboard |
| 5. Entry | `/chat` |
| 6. Input | A question, max 2000 characters, or one of three starter prompts (portfolio, tax, goals) |
| 7. Workflow | `POST /api/chat` returns 202. The worker calls Groq with the profile and up to 20 recent messages inside an 8,000-character budget. History is `GET /api/chat/history/<id>` |
| 8. Output | A stored thread of user and AI messages |
| 9. Value | Questions without retyping income and goals |
| 10. Dependencies | Profile, worker, Groq, quotas (default 15 per minute and 60 per hour per profile) |
| 11. AI | Yes. Default chat model is `openai/gpt-oss-20b` unless overridden. The prompt does not include the health score, EMI, or the latest goal result |
| 12. Database | `chat_history`, `jobs` |
| 13. Status | Exists |
| 14. UX | Adequate. Empty state, wait state, and a mistakes line under the composer |
| 15. Friction | Starter prompts send immediately, with no chance to edit. “Active now” does not mean a person is online |
| 16. Missing | Score and goal context. A refusal when the question needs data the product never collected |
| 17. Evolution | `FUTURE OPPORTUNITY` — coaching on the saved plan. Today it is a chatbot on a thin snapshot |

---

## 12. Clear chat

| Field | Finding |
| --- | --- |
| Class | UTILITY |
| 1. Name | Clear conversation |
| 2. Problem | Start over |
| 3. User | Someone with messages |
| 4. Trigger | Clear |
| 5. Entry | Chat sidebar, or a chip on a narrow screen |
| 6. Input | A click. No confirmation was found |
| 7. Workflow | `DELETE /api/chat/history/<id>` |
| 8. Output | An empty thread |
| 9. Value | Small. Privacy of a conversation on a shared machine, or a fresh question |
| 10. Dependencies | Chat history |
| 11. AI | None |
| 12. Database | `chat_history` |
| 13. Status | Exists |
| 14. UX | Weak. Same one-tap risk as profile delete |
| 15. Friction | No confirm, no undo |
| 16. Missing | Confirmation |
| 17. Evolution | None beyond a confirm step |

---

## 13. Goal simulator

| Field | Finding |
| --- | --- |
| Class | CORE PRODUCT |
| 1. Name | Goal feasibility simulator |
| 2. Problem | “Can my monthly savings fund this amount in this many years?” |
| 3. User | A selected profile |
| 4. Trigger | Goals in the nav, or Goal Simulator on the dashboard |
| 5. Entry | `/goals` |
| 6. Input | Goal name, target amount in rupees, horizon 1–40 years. Savings and risk come from the profile |
| 7. Workflow | `POST /api/goal-plan` runs in the web request. No Groq. CAGR tiers are fixed in `services/goal_service.py` (for example 8/10/12 percent in the medium band). The last result is kept in a browser `Map` (`goalStore.js`), not in PostgreSQL |
| 8. Output | A 0–100 score, three SIP scenarios, gap or surplus, a timeline, and a primary and secondary product name |
| 9. Value | A concrete yes, no, or “later,” with an assumed return shown on the card |
| 10. Dependencies | Profile savings and risk |
| 11. AI | None. The screen title for the score is “Pilot AI Confidence Score” |
| 12. Database | None for the result. The profile is read from `users` |
| 13. Status | Partial. The calculator exists. It is not a saved plan. README line “Support live market data for CAGR assumptions instead of static tiers” is not built |
| 14. UX | The form and the three cards are clear. The AI label and the always-on Recommended badge on Balanced are misleading. If a scenario is not feasible, the bar falls back to 60 percent (`GoalsPage.jsx`) |
| 15. Friction | The profile’s free-text goal is not the goal being simulated. The person types a second goal here. Results vanish when the tab’s memory is cleared |
| 16. Missing | Save, compare, edit assumptions, disclaimer on this screen, market data from the roadmap |
| 17. Evolution | `FUTURE OPPORTUNITY` — scenario planning: save several goals, change the return, see the gap. That is the next step from this calculator, not a new business |

---

## 14. Quick actions

| Field | Finding |
| --- | --- |
| Class | UTILITY |
| 1. Name | Dashboard shortcuts |
| 2. Problem | Where to go after the score |
| 3. User | Someone on the dashboard |
| 4. Trigger | Detailed Report, AI Chat, Goal Simulator |
| 5. Entry | Dashboard right column |
| 6. Input | A click |
| 7. Workflow | Client navigation only |
| 8. Output | Advisory, chat, or goals |
| 9. Value | Shortens the first tour |
| 10. Dependencies | A selected profile, or the nav would have been locked |
| 11. AI | None |
| 12. Database | None |
| 13. Status | Exists |
| 14. UX | Adequate |
| 15. Friction | None |
| 16. Missing | Nothing required |
| 17. Evolution | None |

---

## 15. Search

| Field | Finding |
| --- | --- |
| Class | UTILITY |
| 1. Name | Search |
| 2. Problem | Would be “find a profile, report, or message.” The product does not do that |
| 3. User | Someone who sees the top bar on a wide screen |
| 4. Trigger | The field is visible. Typing does nothing |
| 5. Entry | `TopBar.jsx`. Hidden below the large breakpoint |
| 6. Input | None that is read |
| 7. Workflow | No handler |
| 8. Output | None |
| 9. Value | None today |
| 10. Dependencies | None |
| 11. AI | None |
| 12. Database | None |
| 13. Status | Visible but not a feature |
| 14. UX | Non-functional |
| 15. Friction | Looks like a product and is not |
| 16. Missing | Any search |
| 17. Evolution | `FUTURE OPPORTUNITY` only after there is enough saved material to search. Not justified for one report and one thread |

---

## 16. Notifications

| Field | Finding |
| --- | --- |
| Class | UTILITY |
| 1. Name | Notifications |
| 2. Problem | Would be “something changed while I was away.” Nothing raises an alert |
| 3. User | Wide screens, where the icon is not `hidden` |
| 4. Trigger | The icon is visible. It is not a button with an action |
| 5. Entry | `TopBar.jsx` |
| 6. Input | None |
| 7. Workflow | None |
| 8. Output | None |
| 9. Value | None |
| 10. Dependencies | None |
| 11. AI | None |
| 12. Database | None. No notification table |
| 13. Status | Visible but not a feature |
| 14. UX | Non-functional |
| 15. Friction | Implies a feed |
| 16. Missing | Any alert |
| 17. Evolution | `FUTURE OPPORTUNITY` — “your snapshot is a month old” or “report is ready,” only after edit and a real wait-state exist |

---

## 17. Settings

| Field | Finding |
| --- | --- |
| Class | ACCOUNT/PLATFORM |
| 1. Name | Settings |
| 2. Problem | Would be password, export, or delete-account. None of those exist |
| 3. User | Wide screens |
| 4. Trigger | A settings icon that is not wired |
| 5. Entry | `TopBar.jsx` |
| 6. Input | None |
| 7. Workflow | None |
| 8. Output | None |
| 9. Value | None |
| 10. Dependencies | None |
| 11. AI | None |
| 12. Database | None |
| 13. Status | Visible but not a feature |
| 14. UX | Non-functional |
| 15. Friction | The one place a person would look for password and privacy is inert |
| 16. Missing | The account tools themselves |
| 17. Evolution | `FUTURE OPPORTUNITY` — password, export, delete account. Those follow from having an account that stores financial text |

---

## 18. Upgrade to Elite

| Field | Finding |
| --- | --- |
| Class | SUPPORTING PRODUCT |
| 1. Name | Upgrade to Elite |
| 2. Problem | Would be “pay for more.” No plan, price, or checkout was found |
| 3. User | Everyone who sees the sidebar |
| 4. Trigger | A button with no `onClick` |
| 5. Entry | Bottom of `Sidebar.jsx` |
| 6. Input | None |
| 7. Workflow | None |
| 8. Output | None |
| 9. Value | None. The landing page says the account is free |
| 10. Dependencies | None |
| 11. AI | None |
| 12. Database | None |
| 13. Status | Visible but not a feature. No planning document that defines Elite was found |
| 14. UX | Non-functional, and it looks like the primary commercial offer |
| 15. Friction | A money button that does nothing, inside a money product |
| 16. Missing | An offer |
| 17. Evolution | `FUTURE OPPORTUNITY` only after the free job is complete. Do not invent Elite until edit, score-on-save, and saved goals exist |

---

## 19. Failure, wait, and quota feedback

| Field | Finding |
| --- | --- |
| Class | UTILITY |
| 1. Name | Toasts, empty states, and retries |
| 2. Problem | The person must know whether to wait, retry, or generate |
| 3. User | Anyone in a long or failed action |
| 4. Trigger | Generate, chat send, save, load error, rate limit |
| 5. Entry | Banners and toasts on dashboard, advisory, chat, profile |
| 6. Input | The API error code |
| 7. Workflow | Report and chat poll about every 2 seconds, up to about 120 seconds |
| 8. Output | “Generating…”, “Analyzing…”, “too long”, “try again in N seconds”, or a retry |
| 9. Value | The waits are acknowledged |
| 10. Dependencies | The worker and the rate-limit gateway |
| 11. AI | Surfaces AI failures. Does not explain them beyond the toast |
| 12. Database | `jobs` status |
| 13. Status | Exists |
| 14. UX | Adequate on the main paths. Some copy is for operators (“port 5000”, “check your API key”) |
| 15. Friction | A down worker and a slow model look the same until the toast. Quotas are not explained in advance |
| 16. Missing | A customer-facing “the plan service is not running” |
| 17. Evolution | `FUTURE OPPORTUNITY` — a single status for “your plan is still being written” |

---

## Services behind the features

These are not separate products. They are how the features run.

| Service | Serves | Customer-visible? |
| --- | --- | --- |
| `health_service` | Score and pillar text | Yes, after a report |
| `ai_service` plus Groq | Advisory and chat text | Yes |
| `pdf_service` | PDF file | Yes, on download |
| `goal_service` | SIP math and product names | Yes |
| `jobs` worker | Report and chat off the web request | Only as a wait |
| Rate-limit gateway | Caps on reports, chat, goals, sign-in | Only as “too many requests” |
| `accounts` / session cookie | Sign-in | Yes |
| Scoped API keys | Scripts, not the React app | No |
| Swagger | Local API docs with `API_SECRET_KEY` | No in the app |

There is no notification service, billing service, mailer, market-data service, or analytics service in the repository.

---

## Feature matrix

Measured frequency is `UNKNOWN`. The frequency column is the role in the journey, not a count of users.

| Feature | User problem | Value | Usage frequency | Current status | UX quality | Missing pieces | Priority candidate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Landing page | Why sign up | Medium | Once | Exists | Strong page, weak promise | Real preview, privacy | Medium |
| Sign up | Own the snapshot | High | Once | Exists | Adequate | Consent, password hint, verification | Medium |
| Sign in | Come back | High | Every return | Exists | Adequate | Password reset | High |
| Sign out | Close the session | Medium | Occasional | Exists | Adequate | None for the current job | Low |
| Create profile | Give the product numbers | High | First session, rarely again | Exists | Adequate | Edit | High |
| Select profile | Pick which picture | High | Every session with more than one | Exists | Adequate | What a second profile means | Medium |
| Delete profile | Remove a picture | Medium | Rare | Partial | Weak | Confirm, undo | High |
| Dashboard | See standing and next steps | High | Every session | Exists | Strong after a report, weak before | Score before the AI job | High |
| Health score | Is this picture okay | High | Every session after a report | Partial | Good when shown | Show it on save; show assumptions | High |
| AI advisory | What should I do | High | First session, then rare | Exists | Strong | Keep old versions; cite products | High |
| PDF | Take the plan with me | Medium | Occasional | Exists | Adequate | Clearer “file not ready” | Low |
| Advisor chat | Ask a follow-up | Medium | Occasional | Exists | Adequate | Score and goal in context | Medium |
| Clear chat | Start over | Low | Rare | Exists | Weak | Confirm | Low |
| Goal simulator | Can I fund this | High | Occasional | Partial | Mixed | Save, honest label, real bar | High |
| Quick actions | Where next | Low | First session | Exists | Adequate | None | Low |
| Search | Find something | None today | Never | Not a feature | Non-functional | Remove or build | High to remove |
| Notifications | Hear about a change | None today | Never | Not a feature | Non-functional | Remove until alerts exist | High to remove |
| Settings | Manage the account | None today | Never | Not a feature | Non-functional | Password, export, delete account | High to replace |
| Upgrade to Elite | Pay for more | None today | Never | Not a feature | Non-functional | An offer, or remove the button | High to remove |
| Wait and error feedback | Know what happened | Medium | When something is slow or fails | Exists | Adequate | Worker status in customer language | Medium |

The same rows are in `docs/product-audit/feature-matrix.csv`.

---

## Product loops

### The loop a financial product needs

User → input data → analysis → recommendation → action → result → updated data → better recommendation.

### What FinPilot has

| Step | Present? | Where |
| --- | --- | --- |
| Input data | Yes | Profile form |
| Analysis | Yes | Health score, and the goal formula |
| Recommendation | Yes | Advisory text, chat, goal product names |
| Action | Only as words | The 30-day plan is prose. Nothing is checked off |
| Result | No | No outcome is recorded |
| Updated data | No | Profiles cannot be edited. Goals are not stored |
| Better recommendation | No | Regenerate replaces the report from the same snapshot. Chat does not see a new snapshot unless the person deletes and recreates |

The loop stops at the recommendation. It does not come back.

### Smaller loops that do exist

- **Ask again.** Chat stores history and sends recent turns with the next question. That is a conversation loop, not a money loop. It still uses the original profile.
- **Read again.** A return visit within 12 hours shows the same report. That is recall, not an update.
- **Recalculate a goal.** The person can change the target and run again. The profile’s savings stay the same, and the run is not kept.

### What would close the main loop

`FUTURE OPPORTUNITY`, not built: edit the monthly numbers, rescore immediately, keep the previous plan, and show what changed. Alerts and coaching sit on top of that loop. They do not replace it.

---

## Core product

The smallest product that still helps with money:

1. One profile the person can create and correct.
2. The seven-pillar score, shown when they save, without waiting for Groq.
3. One written advisory, with the disclaimer that is already on that page, and a PDF.

Chat, the goal calculator, several profiles, and the marketing cockpit are additions. The goal calculator is the strongest addition because it answers a different question (“can I afford this amount?”) with the same savings figure. It is not required for the smallest product.

What is not the core, even though it is on screen: search, notifications, settings, Elite, and the landing page’s live score.

---

## Product expansion

Each item follows from something the product already does. Each is a `FUTURE OPPORTUNITY`.

| Adjacent offer | Why it follows | What would have to be true first |
| --- | --- | --- |
| Financial health monitoring | A score already exists | Edit the snapshot, store more than one score, show the delta |
| Goal planning | The simulator already answers one goal | Save goals against the profile |
| Budgeting | Expenses are one number, and the advisory has a “Budget Optimization” section | Categories, not a single expenses field. Not justified as a new app until edit exists |
| AI financial coaching | The report already ends in a 30-day list, and chat already follows up | Tasks the person can mark done. Chat should see the score and the goal |
| Reports | Advisory and PDF already exist | Version history, so regenerate does not erase the last plan |
| Alerts | The product already knows a snapshot can go stale, but it never says so | A date the person recognizes, and a channel. The bell icon is not this |
| Scenario planning | Three CAGR cases already exist | Let the person change the assumption and keep both runs |
| Financial education | Pillars and 80C are already rules | Explain the rule beside the points. A course is not implied |
| Portfolio tools | The model already suggests allocations and fund types | Holdings the person actually has. Do not add a portfolio screen before that input exists |

Live market data is already a README roadmap line. It belongs under scenario planning, as a better assumption, not as a trading product.

---

## Feature bloat

### Unclear value

- **Upgrade to Elite.** No plan, no price, no destination. It conflicts with “Create your free account.”
- **Several unnamed profiles.** Useful only if the second profile has a job. That job is `UNKNOWN`.
- **Search.** There is almost nothing to search: one report and one thread per profile.

### Duplicated

- **Generate** on the dashboard and **Generate / Regenerate** on Advisory call the same job. The duplication is a reasonable shortcut, not two products. The empty dashboard copy makes them feel like the score and the essay are one feature.
- **Goal text on the profile** and **goal name on the simulator** are two different goals. The profile goal is a label. The simulator goal is the calculation. The UI does not say that.
- **Chat starter “Goal Simulation”** asks the model to judge a goal. The goal page already calculates one. Two answers can disagree.

### Confusing

- “Pilot AI Confidence Score” on a formula.
- Balanced always marked Recommended.
- A 60 percent bar when the scenario is not feasible.
- “Onboarding Profile” as the permanent name of the profile page.
- “Live financial picture” and “+8.4% this quarter” on the landing page.
- “Active now” on a chat that has no other person.
- ENCRYPTED on a form whose amounts are ordinary stored numbers.

### Infrastructure shown to customers

- Errors that mention port 5000 and an API key (`frontend/src/lib/apiErrors.js`). The React app does not use an API key.
- “Download to build the PDF” describes server files.
- Quotas appear as a surprise wait, not as a limit the person was told.

Scoped keys and Swagger stay off the customer UI. That split is correct.

### Built, but not productized

- The health score service can run without Groq. The product hides it behind Generate.
- Goal results are computed and then kept only in memory.
- Chat history, report text, and the score are stored, but there is no settings surface to export or delete the account.
- The worker, quotas, and session length are real operating rules with almost no customer explanation.

---

## What this audit does not know

- How often any feature is used
- Whether a second profile is intentional
- What Elite was supposed to include
- Whether the disclaimers are legally enough
- Whether people finish a report when the worker is slow

Those stay `UNKNOWN`.
