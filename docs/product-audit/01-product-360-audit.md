# FinPilot AI — product 360 audit

**Date:** 2026-09-28  
**Method:** The repository was read as a product. Routes, screens, copy, models, and services are the evidence. Nothing here was measured with live customers.  
**Unknowns** are marked `UNKNOWN`.

This is not a legal or compliance opinion. Places that need a legal review are named as such.

---

## 1. Product identity

### What exists today

FinPilot is a signed-in web app for one person. They type a monthly money picture, then receive three things from that picture:

- a rule-based health score from 0 to 100
- a written advisory, plus a PDF, produced by Groq
- a chat about that same picture
- a goal calculator that uses fixed return assumptions and Indian product names

The marketing page calls this a financial map and a calm cockpit. The working app is a profile form, a dashboard, an advisory page, a chat, and a goal simulator. Currency in the product is rupees. Tax logic uses the Section 80C limit of ₹1,50,000. The advisory footer says the product is not a SEBI-registered advisor.

### Core problem

The implementation tries to answer: given the numbers I type, am I in decent shape, what should I do next, and can I afford a named goal?

It does not connect to a bank, a broker, or a market feed. Those integrations were not found.

### Primary user

A person who can state age, monthly income, monthly expenses, monthly savings, an optional EMI, a risk level, and a goal in their own words. The product speaks Indian personal finance: SIP, PPF, Nifty 50, ELSS, FD, 80C.

### Secondary users

`UNKNOWN` as a designed customer. A script can issue a scoped API key (`scripts/issue_api_credential.py`). That key is not offered in the React app. No advisor console, household admin, or support inbox was found.

Several profiles can sit on one account. The screen calls them saved profiles and titles each one with the goal text. Whether a second profile is meant to be a spouse, a child, or another scenario is `UNKNOWN`.

### Value proposition, as implemented

Type your monthly numbers once. Get a score you can see, a written plan, a place to ask follow-ups, and a check on whether a goal fits those savings.

### Outcomes the product can actually produce

- A stored profile the person can reopen while the session lasts (12 hours, `services/sessions.py`)
- A 0–100 score with seven named pillars, insights, and warnings
- One saved advisory per profile, and a PDF
- A chat history stored for that profile
- A one-time goal simulation that stays in the browser until the page memory is cleared

### Jobs to be done

- Tell me if this monthly picture is healthy
- Tell me what to change
- Let me ask a follow-up without retyping the numbers
- Tell me if a specific goal is affordable
- Let me come back and see the same picture

### Promise versus the screen

The landing page (`frontend/src/pages/LoginPage.jsx`) promises a live financial picture, a score of 82, “+8.4% this quarter,” a ₹40,000 surplus, privacy “by design,” and an account created free in minutes. The score card is labeled “Live financial picture.” The chart next to it is marked illustrative in its accessible name. The numbers themselves are written into the page. They are not the visitor’s data.

Inside the app, the first real score appears only after the person generates an AI report. The dashboard empty state says so. Search, notifications, settings, and Upgrade to Elite are visible and do nothing. The goal screen calls a formula “Pilot AI Confidence Score.”

The promise is emotionally clear on the landing page. It is not the same promise the signed-in product keeps.

---

## 2. Product surface area

Status words: **exists**, **partial**, **planned but not implemented**, **missing**.

| Capability | Class | Status | What the customer gets |
| --- | --- | --- | --- |
| Landing page | Supporting | Exists | A story, three feature cards, screenshots, sign-up |
| Sign-up and sign-in | Core | Exists | Email, password of at least 12 characters, session cookie |
| Sign-out | Core | Exists | Ends the session from the sidebar |
| Email verification | Supporting | Missing | Signup is open. A planning note says verification is not in that plan |
| Password reset | Supporting | Missing | No reset flow was found |
| Create a financial profile | Core | Exists | Age, income, expenses, savings, optional EMI, risk, goal text |
| Edit a profile | Core | Missing | Create and delete only. No update route |
| Delete a profile | Supporting | Partial | Deletes immediately. No confirmation was found |
| Several profiles | Core | Exists | Meaning of a second profile is `UNKNOWN` |
| Health score | Core | Partial | Computed without the model, shown only after a report job |
| AI advisory and regenerate | Core | Exists | One stored report per profile |
| PDF | Supporting | Exists | Download from Advisory. Text can exist before the file does |
| Advisor chat | Core | Exists | Per profile, with three starter prompts |
| Goal simulator | Core | Partial | Works, is not saved in the database, UI calls the score AI |
| Live market data | Core | Planned, not implemented | README roadmap. Calculator uses fixed CAGR tiers |
| Search | Peripheral | Partial | Field only |
| Notifications | Peripheral | Partial | Icon only |
| Settings | Supporting | Partial | Icon only |
| Upgrade to Elite | Peripheral | Partial | Button only. No price, plan, or billing was found |
| Billing | Supporting | Missing | Landing says “Create your free account” |
| Privacy policy and terms | Supporting | Missing | Footer has a copyright line and a back-to-top link |
| Disclaimers | Supporting | Partial | Advisory page and PDF. Chat has a short mistakes line. Goals and landing do not |
| Product analytics | Infrastructure-only | Missing | No analytics SDK was found in the frontend |
| Bank linking | Core | Missing | Numbers are typed |
| Background jobs | Infrastructure-only | Exists | Report and chat wait on a worker the customer never starts |
| Quotas | Infrastructure-only | Exists | Report and chat are capped. The allowance is not explained up front |
| Scoped API keys | Infrastructure-only | Exists | Operator script, not a customer screen |

---

## 3. User journey

### Visitor

The landing page is the signed-out experience. Primary actions are “Start your financial map,” “Get started,” and “Create your free account.” “See the platform” scrolls to screenshots. Initials AS, RN, and MK sit beside “Built for real life.” The repository does not identify those initials. Treat them as decoration, not as evidence of customers.

There is no pricing, no sample of a real report, and no disclaimer on this page.

### Signup and authentication

A dialog collects email and password. Sign-up is the default mode. The form does not say the password must be 12 characters; the server rejects a shorter one after submit. There is no checkbox for terms or privacy, because those pages were not found. There is no email verification and no “forgot password.”

Success sets a cookie and enters the app. A 12-hour session is the return path. After that, the person is told the session ended.

### Onboarding

There is no separate onboarding. The profile page is titled “Onboarding Profile” in the nav model even on later visits. If the account has no profiles, one sentence says so. The form says the numbers unlock advisory, chat, and goal simulation.

Dashboard, Advisory, Chat, and Goals stay locked until a profile is selected.

### Profile setup

Required: age, monthly income, expenses, savings, a risk choice (Conservative, Balanced, Aggressive), and a goal of at least a few words. EMI is optional. A badge on the form says ENCRYPTED. Profile amounts are stored as ordinary numeric columns. Password storage is a hash. Field-level encryption of the financial snapshot was not found. Whether the connection is HTTPS depends on deployment and is `UNKNOWN` from the UI alone.

Creating a profile jumps to the dashboard.

### First value

The dashboard, with no report yet, shows an empty gauge and “Generate an AI advisory report to unlock your score.” The score itself does not need the model. The product withholds it until Groq finishes a job.

If the worker is not running, the person waits through “Generating…” and can later see that generation took too long. That wait is up to about two minutes in the client poll.

Chat and Goals are reachable from the dashboard once a profile exists, so a person can get a goal result or a chat reply without a report. The empty dashboard still points at the report as the first act.

### Core financial workflow

Select a profile. Read the score and pillars. Read warnings. Open the advisory. Download a PDF. Ask the chat. Run a goal.

Changing the numbers means deleting the profile and creating another one. That also removes the report and the chat for that profile, because those rows belong to the profile.

### AI interaction and the report

Generate queues work and returns while the person waits on the page. One report is kept per profile. Regenerate replaces it. The advisory page shows the score, cash-flow bars, pillars, strengths, warnings, then the model’s write-up, then a small disclaimer.

### Return and continued engagement

Coming back within 12 hours restores the account and the last selected profile in this browser tab. Reports and chats are still in the database. Goal simulations are not. Nothing in the product invites a weekly check-in, a reminder, or an update of the numbers. Search, notifications, and settings do not create a reason to return.

### Friction and drop-off

- The landing picture is not the product’s first screen after sign-up
- Password rules appear only as an error
- No terms or privacy step, so a cautious person has nowhere to read them
- First score is blocked on an AI job and a worker the customer cannot see
- Numbers cannot be corrected in place
- Delete has no “are you sure”
- Goal results disappear from the product’s memory when the browser memory is cleared
- Dead controls (search, bell, settings, Elite) make the shell look unfinished
- Quotas can stop a report or a chat with “try again in N seconds,” without saying what the allowance is

### Where value actually lands

The moment a report exists: a score, pillar bars, warnings in plain language, and a structured write-up tied to the typed numbers. The goal calculator is the other clear moment, if the person already knows a target amount and a horizon. Chat is useful only after the profile exists, and only as a conversation about those fields.

---

## 4. Product experience

### First impression

The landing page is polished and specific in tone. It over-claims relative to the app: a live score, a quarterly change, and a finished cockpit. After sign-up the person meets a form titled like onboarding, then an empty dashboard.

### Clarity

Inside a completed report, the hierarchy is clear: score, pillars, insights, write-up. Before that, “Onboarding Profile,” “Pilot AI Confidence Score,” and “Upgrade to Elite” use words the product does not define.

### Discoverability

The five-item sidebar is understandable. Locked items explain that a profile is required. Starter chat prompts are visible on a wide screen and as chips on a narrow one. Search looks like a way to find past work and is not one.

### User control

The person can create, select, and delete profiles, regenerate a report, clear a chat, and rerun a goal. They cannot edit a number, save a goal, export data except the PDF, close the account, or change the password.

### Feedback

Toasts cover create, generate, failure, and rate limits. Report and chat show a spinner and a wait state. Empty states exist for no profiles, no report, and no chat. Delete gives a success toast and no undo.

### Trust

See section 7. Short version: the score is explainable; the model’s advice is not sourced; the marketing page and the goal label blur rule-based math with AI; the ENCRYPTED badge is stronger than the storage the repository shows.

### Personalization

Advice is personalized to the typed snapshot and, in chat, to recent turns. It does not learn spending categories, city, dependents, existing holdings, or tax regime beyond an 80C estimate. Dependents, city, and tax regime are `UNKNOWN` because the product never asks.

### Consistency

Rupees, dark surfaces, and the same score colors repeat. The landing page is a different visual system from the app, which is normal for a marketing front. Inside the app, “AI” is applied to the goal score even though that path does not call Groq.

### Cognitive load

The happy path is short: one form, then four destinations. The form is one screen. The advisory page is long but sectioned. Load rises when a control does nothing, or when generate sits in “Generating…” with no explanation of the worker.

### Information hierarchy

Dashboard leads with the score, then two money stats, then insights, then jumps to report, chat, and goals. That order matches the job. The top bar’s search and icons compete with that hierarchy and do not pay off.

### Error recovery

Load failures offer retry. A failed report job says the previous report is unchanged, or that it took too long. Session expiry returns the person to sign-in. A network error tells them the API on port 5000 must be running, which is operator language for a customer. An `unauthorized` error tells them to check an API key, which the React app does not use.

### Accessibility

Some controls have names (menu, close, home). Icons used as decoration are hidden from assistive tech. No skip link was found. No `aria-live` region was found, so toast feedback may be silent to a screen reader. That was not tested with a screen reader. Status uses color plus a word on the score (“Healthy”, “Moderate”, “At Risk”), which helps. A full accessibility audit was not run. Compliance level is `UNKNOWN`.

### Mobile

The landing nav links hide below the `md` breakpoint. The app sidebar is off-canvas with a menu button. Profile fields stack. Chat prompts become a horizontal row. The top search is hidden below the large breakpoint. Safe-area padding is used on the chat composer. A device lab pass was not run, so real-device behavior is `UNKNOWN`.

---

## 5. Feature quality

### Financial profile

- **Problem:** the product has no picture of the person until they type one
- **Who:** the account holder
- **Trigger:** sign-up, or “new profile”
- **Input:** age, monthly income, expenses, savings, optional EMI, risk, goal text
- **Output:** a saved profile and a pass into the rest of the app
- **Value:** high, because everything else hangs on it
- **Adoption blockers:** no edit, no bank import, EMI easy to skip, goal text becomes the profile’s name so a long goal is a clumsy label
- **Complete:** no
- **Missing:** edit, confirmation before delete, any sense of what a second profile is for

### Health score

- **Problem:** “am I okay?”
- **Who:** the profile that was just saved or reopened
- **Trigger:** the dashboard after a report exists; the empty state asks them to generate
- **Input:** the profile. EMI changes the debt pillar. Tax uses an assumption that about 30% of savings goes to 80C instruments
- **Output:** 0–100, seven pillars with known maximums, insight strings, warning strings
- **Value:** high if they understand it is a rule of thumb, not a credit score
- **Adoption blockers:** it is locked behind the AI job; the assumptions are not shown next to the gauge
- **Complete:** the math exists; the product moment is incomplete
- **Missing:** a score on save, without waiting for Groq; a plain explanation of each pillar’s rule

### AI advisory and PDF

- **Problem:** “what should I do?”
- **Who:** someone who already entered a profile
- **Trigger:** Generate on the dashboard or Advisory
- **Input:** age, income, expenses, savings, risk, goal text, score, insight list, warning list. EMI is not a separate line in the prompt. Holdings are not collected
- **Output:** a fixed outline (summary, budget, investments, risks, goal strategy, 30-day plan) and a PDF with a short educational disclaimer
- **Value:** this is the main artifact
- **Adoption blockers:** wait time, quota (default 5 per minute on the account and 10 per hour on the profile), worker must be up, one report only so regenerate throws away the previous text
- **Complete:** enough for a first read and a download
- **Missing:** version history, a way to correct a number and refresh, sources for any product it names

### Chat

- **Problem:** a follow-up the report did not answer
- **Who:** the same profile
- **Trigger:** AI Chat, or a starter prompt (portfolio, tax, goals)
- **Input:** the question, the profile fields, and up to 20 recent messages within an 8,000-character budget
- **Output:** a markdown reply stored as history
- **Value:** medium, as a conversation on a thin snapshot. It does not see the health score or the goal simulation unless those words are already in the chat
- **Adoption blockers:** quotas, wait, no memory of goals, starter prompts can send a long question in one click with no edit step
- **Complete:** send, history, clear
- **Missing:** the score and the latest goal in the prompt; a refusal or redirect when the question needs a fact the product does not have

### Goal simulator

- **Problem:** “can I fund this?”
- **Who:** a profile with a monthly savings figure
- **Trigger:** Goal Simulator, then Calculate Pilot Path
- **Input:** name, target amount in rupees, horizon from 1 to 40 years, plus the profile’s savings and risk
- **Output:** a 0–100 feasibility score, three SIP scenarios, a gap or surplus, a suggested timeline, and a primary and secondary product name
- **Value:** high as a calculator, if the fixed returns are understood as assumptions
- **Adoption blockers:** the score is branded as AI confidence; Balanced is always badged Recommended in the interface even when the person’s risk is not medium; infeasible scenarios draw the progress bar at 60 percent when coverage is unknown (`GoalsPage.jsx`); results are not saved
- **Complete:** one calculation, yes. A planning habit, no
- **Missing:** saved goals, assumption controls, the market-data roadmap item, a disclaimer on this screen

### Account

- **Problem:** keep this person’s profiles private to them
- **Who:** one email
- **Trigger:** sign-up or sign-in
- **Input:** email and password
- **Output:** a 12-hour cookie
- **Value:** necessary, not delightful
- **Adoption blockers:** no reset, no verification, 12-character rule discovered late
- **Complete:** no
- **Missing:** reset, verification, close account, password change, session list

---

## 6. AI product audit

### What the AI actually does

Groq writes the advisory and answers chat. The system persona says it is a professional personal financial advisor for Indian personal finance, and that it should sound like a real advisor. Report and chat use different default models (`openai/gpt-oss-120b` for reports and `openai/gpt-oss-20b` for chat, unless overridden). Temperature is 0.7.

The health score and the goal math do not call the model.

### Where AI is useful

Turning a score and a short snapshot into a structured plan and a 30-day list. Answering a follow-up in the same vocabulary as that snapshot.

### Where AI is unnecessary

The goal “confidence” label. The health score. The landing page’s suggestion that the pictured 82 is a live AI result.

### Context the model has

Report: the profile fields listed in section 5, the score, and the insight and warning strings. Chat: those profile fields, the new question, and a recent slice of the chat. The worker runs this off the web request so the page can wait.

### Context the model lacks

Bank transactions, holdings, city, dependents, insurance, existing EMIs as a schedule (only one optional monthly EMI number, and chat/report prompts do not even pass that number as its own line), the health-score breakdown in chat, goal results, and any retrieved market or tax source. If the person disagrees with a number, they cannot correct the profile in place, so the model keeps the old snapshot until they delete it.

### How the person understands and checks the output

The advisory page separates the rule-based sections from “05. AI Advisory.” That split is the best explanation the product has. The model text is rendered from markdown the model wrote. There is no citation, no “this number came from your income field,” and no confidence on a sentence. The footer says it is not a SEBI-registered advisor and that investments carry market risk. Chat says the AI can make mistakes and to verify critical data. Neither screen shows the prompt or the assumptions beside the answer.

Verification is left to the person. The product does not offer a second calculation, a source link, or a human review.

### How long context lasts

The profile lasts until it is deleted. The report lasts until it is regenerated. Chat history lasts until it is cleared or the profile is deleted. The model only rereads the recent window, not the whole life of the account. Goal runs last in browser memory for that profile id.

### When AI fails

The client polls for about two minutes. Failures surface as toasts: too long, provider timeout, provider rate limit, provider unavailable, or the previous report left in place. A PDF can fail while the text is kept; the dashboard says to open Advisory and download to build the file.

### Incorrect financial information

Nothing in the product checks the model’s percentages or product names against a catalog. The system prompt tells it to give personalized advice and to sound like an advisor. It does not tell it to refuse when data is missing, to label estimates, or to avoid naming a product it cannot source. Hallucination handling is therefore: a short disclaimer, plus the person’s own caution. That is a product gap, not a control.

### Capability or chatbot

The report is a product capability: queued, stored, laid out, downloadable. The chat is a chatbot wrapped around the same snapshot, with starter prompts. Together they feel like one advisor feature. The goal tool is a calculator wearing an AI name.

---

## 7. Trust

### Explainability

Pillars have names and point ceilings the UI can show (savings 25, expenses 20, emergency 20, debt 15, retirement 10, tax 5, surplus 5). The sentences under insights come from the scoring rules. The model’s allocation percentages do not trace back to a rule the person can read. Goal CAGR tiers exist in code (for example 8/10/12 percent in the medium band) and are shown as “Assumed CAGR” on the scenario card. The reason a band was chosen is a short rationale string when the strategy block renders.

### Data transparency

The person is not shown a list of what is stored, for how long, or who can see it. Profiles, reports, chat, and jobs live in the application database. PDFs are files on the server disk. Goal runs are not stored there. A privacy policy was not found.

### Consent

Sign-up does not ask for a consent to process financial data or to send it to Groq. Whether that is required is a legal question, not a finding this audit can settle. The product gap is that the screen never asks.

### Privacy-related UX

Landing lines say “Private by design,” “Yours, always,” and the form says ENCRYPTED. The repository supports “this account sees only its profiles” and a hashed password. It does not support the word ENCRYPTED as a description of the financial fields. No privacy page, export, or account-deletion flow was found.

### Security-related UX

Sign-out exists. The session ends after 12 hours or on sign-out. There is no password reset, no step-up before delete, and no list of sessions. Those are product gaps. A security review of the implementation is a separate document and was not repeated here.

### Disclaimers and limits

The advisory footer and the PDF disclaimer say the output is educational and not regulated advice, and that a professional should be consulted. Chat asks the person to verify critical data. The goal screen and the landing page do not carry that advisory disclaimer. The model is instructed to sound like a real advisor, which pulls against the disclaimer.

Legal sufficiency of the SEBI sentence, the PDF wording, and the absence of terms is `UNKNOWN`. It should get a legal and compliance review before this is offered as a financial product to the public.

### Uncertainty

The health labels are Healthy, Moderate, and At Risk at 70 and 50. They read as judgments, not as “this rule of thumb says.” The goal score is shown as a large percentage called confidence. The model output has no uncertainty.

### Confirmation and recovery

No confirmation was found before delete or before regenerate. Regenerate replaces the only stored report. Delete removes the profile and, with it, the report and chat. There is no undo. An incorrect number is fixed by deleting and retyping. An incorrect model paragraph can be regenerated, which discards the previous text, or ignored. It cannot be edited.

---

## 8. UX and UI

### What is on screen

The signed-in shell is a fixed sidebar, a top bar, and a page. Navigation is Dashboard, Advisory, Chat, Goals, and Profile. Pages use cards, a gauge, stat tiles, progress bars, and one form. There is no data table. Charts in the product are the gauge, pillar rows, and goal progress bars. The landing chart is a static illustration.

Buttons have loading labels (“Creating…”, “Generating…”, “Running Simulation…”). Empty states exist for no report, no chat, and no goal result. Errors use a banner plus a toast. The design of the app is one dark palette with emerald, gold, and warning red used in the same roles on the score.

### Breaks in the system

- Landing and app do not share one component library. That is acceptable. Dead controls inside the app are not
- Search, notifications, and settings are visual only
- Upgrade to Elite is a filled button with no destination
- “Recommended” on the Balanced goal card is hardcoded
- The infeasible goal bar uses 60 percent as a stand-in
- Disclaimer type on the advisory page is about 10px and low contrast (`text-on-surface-variant/40`)
- Profile title in the nav is “Onboarding Profile” forever
- The unauthorized error mentions an API key

### Responsive behavior found in code

Sidebar collapses to a drawer. Forms go to one column. Chat’s prompt column hides and chips replace it. Whether every state is comfortable on a phone was not verified on a device. `UNKNOWN` beyond the breakpoints in the components.

### Design-system consistency

Inside the app, cards, fields, and buttons repeat. Empty and loading patterns repeat on dashboard, advisory, and chat. Goals uses a different empty treatment and an “AI” label the others reserve for Groq. That is the main inconsistency a customer will feel.

---

## 9. Product gaps

### Critical

- The landing page presents a live score and a quarterly change the product does not have
- The first health score is withheld until an AI job succeeds
- Profiles cannot be edited; delete is immediate and destroys the report and chat
- The goal score is labeled as AI confidence, and Balanced is always “Recommended”
- Financial fields are badged ENCRYPTED without a matching control in the product
- There is no privacy notice, terms, or consent before financial data is sent to the model. Legal review is required; the product currently has nowhere to put that consent
- Dead shell controls (search, notifications, settings, Elite) undermine trust in a money product

### Important

- Password rules, reset, and verification
- Save goal runs
- Put the health score and the latest goal into the chat’s context
- Show the scoring assumptions next to the gauge
- Explain quotas before they block a report
- Replace operator errors (“port 5000”, “API key”) with customer language
- Let the person keep the previous advisory when they regenerate
- A disclaimer on the goal screen, written with counsel
- Stop the infeasible progress bar from drawing a fake 60 percent

### Opportunity

- Bank or statement import, if the product wants “live picture” to be true
- The README’s live market data for CAGR, with the assumption shown as an assumption
- Reminders to refresh a monthly snapshot
- A household explanation for multiple profiles, or a single profile if that was never the job
- An honest free tier, if Elite is ever a real offer
- Export and account deletion, which also serve trust

---

## 10. Product strengths

- The signed-in job is narrow and learnable: one snapshot, four tools
- The health score is deterministic, pillar-based, and written in sentences a person can read
- The advisory layout separates the score from the model’s prose
- Chat keeps history per profile and offers starter questions
- The goal tool answers a concrete question with SIP math, a gap, and a timeline, and it shows an assumed CAGR
- Empty, loading, and failure states exist on the main waits (report, chat, profile list)
- The person’s data is scoped to their account in the product’s navigation; they do not see a global directory
- Rupee formatting and Indian examples match the scoring and the model persona, so the product is not a generic US template with a new logo

---

## 11. Product risks

### Adoption

People who believed the landing score will meet an empty dashboard and a form. People who do not know their monthly savings as a single number will stall. There is no import.

### Retention

Nothing prompts a return. Goals are not kept. Numbers cannot be updated. The session ends in 12 hours and there is no password reset if they are locked out. `UNKNOWN` whether 12 hours is noticed in practice.

### Trust

Decorative social proof, a non-functional Elite upgrade, an ENCRYPTED badge, and an AI label on a formula. Any one of these is a crack in a money product. Together they are a positioning risk.

### UX

Dead controls, no edit, no delete confirmation, and operator wording in errors.

### AI

The persona says “sound like a real financial advisor” while the disclaimer says this is not regulated advice. The model can name products and percentages with no source check. Chat does not see EMI, the score, or the goal result unless the person repeats them.

### Technical-product

If the worker is down, the core promise stalls in “Generating…”. Quotas can block the same promise. The customer cannot tell those apart from “the AI is thinking” until the toast.

### Monetization

“Free account” is a promise. Elite is a button. There is no price, no plan difference, and no billing. Asking for payment later has no product place to land. Willingness to pay is `UNKNOWN`.

### Positioning

“Wealth cockpit” and “live financial picture” describe a monitoring product. The implementation is a snapshot advisor and a calculator. Buyers looking for account aggregation will leave. Buyers looking for a planner may stay if the first report is fast and the disclaimer matches the voice.

---

## 12. Product maturity

| Area | Level | Evidence |
| --- | --- | --- |
| Problem clarity | Solid | The app repeatedly does one job: snapshot, score, plan, ask, test a goal. The landing page blurs that job with a live monitoring story |
| Value proposition | Developing | The in-app value is real after a report exists. The front door oversells it, and Elite/free is unresolved |
| Core workflows | Developing | Create, generate, chat, and simulate work. Edit, save-a-goal, and recover-from-delete do not |
| UX maturity | Developing | Empty, loading, and error patterns exist on the main paths. Dead controls, no confirmation, and operator errors keep it short of solid |
| UI maturity | Solid | The signed-in UI is consistent enough to feel like one product. Landing is a separate, finished marketing surface. Fake chrome holds the app back from mature |
| AI experience | Developing | The report is a real capability with a wait, a layout, and a failure path. Checks, sources, and honest labeling of non-AI math are missing |
| Personalization | Developing | Advice uses the typed snapshot and recent chat. It has no holdings, household, or corrected numbers |
| Trust | Weak | Explainable score, weak consent, overstated privacy badge, disclaimers easy to miss, AI voice that claims to be an advisor |
| Retention | Weak | No reminders, no editable snapshot, goals not stored, no reset password |
| Monetization | Weak | A free-account sentence and a dead upgrade button. No plan |
| Analytics | Weak | No product analytics SDK was found. What people finish or abandon is `UNKNOWN` |
| Operational maturity | Developing | Jobs, quotas, and health checks exist for operators. The customer still depends on a worker they cannot see, and there is no in-product status for it |

---

## 13. Executive summary

### A. What FinPilot is today

A personal snapshot advisor for someone using rupees. They type monthly numbers, then get a rule-based score, a Groq advisory and PDF, a chat, and a SIP goal check. It is not yet a live picture of their money.

### B. What it could become

Either an honest “type your numbers, get a plan” product, tightened so the score, the edit path, and the disclaimers match that job, or a true monitoring product later, if bank data and saved goals are actually built. The landing page already sells the second. The code is the first.

### C. Biggest strengths

A short loop from numbers to a readable score and a stored plan. Indian context is in the math and the model, not only in the currency symbol. The advisory page separates the score from the prose.

### D. Biggest problems

The front door shows a live score the user does not have. The real score waits on an AI job. Profiles cannot be fixed without deletion. The shell advertises search, settings, notifications, and Elite without behavior. Trust copy (encrypted, AI confidence, advisor persona) runs ahead of the product.

### E. Biggest opportunities

Show the score as soon as the profile is saved. Let people edit. Save goals. Put assumptions next to every percentage. Make the landing page a true preview of the empty-to-report journey. Add the market-data idea from the roadmap only when the assumption can be shown as an assumption.

### F. Biggest risks

A person acts on an unsourced allocation because the product told the model to sound like an advisor. A person deletes a profile by mis-tap and loses the plan. A person hits a dead upgrade or a privacy badge and stops believing the numbers. Legal exposure from missing consent and uneven disclaimers is `UNKNOWN` and needs counsel.

### G. Most important unknowns

- Who a second profile is for
- Whether anyone completes a report without a worker already running
- Whether customers understand the score is a rule of thumb
- Willingness to pay, and what Elite was meant to be
- What counsel will require before public financial use
- Real-device accessibility and mobile behavior
- Any production analytics, because none exist in the repo

---

## 14. Files

This audit is `docs/product-audit/01-product-360-audit.md`.

The structured inventory is `docs/product-audit/product-inventory.json`.
