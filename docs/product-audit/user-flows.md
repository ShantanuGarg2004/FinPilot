# FinPilot AI — user flows

**Date:** 2026-09-29  
**Pairs with:** `docs/product-audit/04-ux-audit.md`  
**Source:** `frontend/src` routes, pages, and the report, chat, and goal hooks. There is no router library. `resolveRoute` in `frontend/src/lib/routes.js` decides the screen.

Application code was not changed.

Each current workflow uses the same seven steps. The last section is a proposed interaction sequence for the first session. That sequence is a redesign of the logic. It is not how the app behaves today.

---

## Map of paths

| Path | Who can see it | Screen |
| --- | --- | --- |
| `/` | Signed out: landing. Signed in: redirects to `/dashboard` if a profile is selected, otherwise `/profile` | Landing or redirect |
| `/profile` | Signed in | Create form and saved profiles |
| `/dashboard` | Signed in, and a profile is selected. Otherwise redirect to `/profile` | Dashboard |
| `/advisory` | Same lock as dashboard | Advisory report |
| `/chat` | Same lock | Chat |
| `/goals` | Same lock | Goal simulator |
| Any other path | Signed out: sent to `/`. Signed in: sent to `/profile` | Redirect |

A signed-out visit to a known app path keeps that path in memory so sign-in can return to it (`remember` in `resolveRoute`). Unknown paths do not.

---

## 1. First visit

1. **Entry.** Open `/` while signed out. `LoginPage.jsx`.
2. **Goal.** Understand the product and choose sign up or sign in.
3. **Information.** None.
4. **Actions.** “Start your financial map,” “Get started,” or “Create your free account” open the sign-up dialog. “Sign in” opens the same dialog in sign-in mode. “See the platform,” “Platform,” “How it works,” and “Our approach” scroll. Below the `md` breakpoint the in-page nav links are hidden.
5. **Feedback.** The page is static. The hero shows a score of 82, “+8.4% this quarter,” and a ₹40,000 surplus, labeled “Live financial picture.”
6. **Result.** The auth dialog opens, or the visitor leaves.
7. **Next.** Create an account, or sign in.

## 2. Sign up

1. **Entry.** Auth dialog, sign-up mode, from the landing buttons.
2. **Goal.** Own an account.
3. **Information.** Email, password, confirm password. The server requires 12 characters. The dialog does not say so ahead of submit.
4. **Actions.** Submit “Create your account.” Switch to “Already have an account? Sign in.” Close the dialog.
5. **Feedback.** Confirm-password mismatch is inline. Other failures use `err.message` in the dialog. The button loads.
6. **Result.** `POST /api/auth/signup` sets the session cookie. The app stores the account and renders the shell.
7. **Next.** Profile, because no profile is selected. `/` redirects there.

## 3. Sign in

1. **Entry.** Auth dialog in sign-in mode, or a later load where `GET /api/auth/me` succeeds.
2. **Goal.** Reach the same profiles, report, and chat.
3. **Information.** Email and password, or the existing cookie. The cookie lasts 12 hours.
4. **Actions.** “Sign in.” Or do nothing if the cookie is still valid.
5. **Feedback.** Bad credentials: “Email or password is incorrect.” A valid cookie shows a blank view until the check finishes, then the shell. There is no “forgot password.”
6. **Result.** The shell opens on the remembered app path when that path was kept, otherwise the route guard sends `/` to the dashboard or the profile.
7. **Next.** Dashboard if this tab still has a profile id in `sessionStorage`. Profile if it does not.

## 4. Sign out

1. **Entry.** “Sign out” at the bottom of the sidebar.
2. **Goal.** End access on this browser.
3. **Information.** None.
4. **Actions.** One click. No confirm.
5. **Feedback.** Logout is attempted. A failed request still clears the local session.
6. **Result.** `POST /api/auth/logout` bumps the session when it succeeds. Report, chat, and goal memory caches clear. The landing page returns.
7. **Next.** The landing page. The person can sign in again.

## 5. Session ended

1. **Entry.** An API call returns session expired, or a restored page (`pageshow` with `persisted`) finds the account gone or changed.
2. **Goal.** Get back in without seeing another account’s page.
3. **Information.** None from the person.
4. **Actions.** None until they sign in.
5. **Feedback.** Toast: “Your session ended. Sign in again.” A foreign history entry is replaced with a path for the current session (`pathForForeignEntry`).
6. **Result.** Landing page, signed out. In-memory caches clear.
7. **Next.** Sign in. The previous account’s profile is not rendered.

## 6. Create a profile (financial data entry)

1. **Entry.** First sign-in, “Profile” in the sidebar, or the person-add icon in the top bar. Title in the bar: “Onboarding Profile.”
2. **Goal.** Give the product the monthly numbers so the other screens unlock.
3. **Information.** Age, monthly income, monthly expenses, monthly savings, risk (Conservative, Balanced, or Aggressive), and a goal sentence. EMI is optional. Placeholders: 28, ₹150000, ₹80000, ₹40000, and “Buy a house in 5 years, retire at 55…”
4. **Actions.** “Continue to Dashboard.”
5. **Feedback.** Missing fields toast. Submit shows “Creating…”. Success toasts “Profile created successfully.” The badge on the form says ENCRYPTED.
6. **Result.** `POST /api/profile` stores a row. The new id becomes the active profile. The app opens `/dashboard`.
7. **Next.** The empty dashboard asks them to generate a report. Chat and Goals are now unlocked.

There is no edit step after this. Changing a number means another profile, or delete and recreate.

## 7. Select a profile

1. **Entry.** The saved-profile list on `/profile`, or a stored id in this tab on a later visit.
2. **Goal.** Point the dashboard, report, chat, and goals at one snapshot.
3. **Information.** A click on a row.
4. **Actions.** Select. From the profile page, selection navigates to `/dashboard`.
5. **Feedback.** The row highlights. The top bar can show the goal sentence from the `xl` breakpoint up.
6. **Result.** `finpilot.activeUserId` updates. Other pages read that id.
7. **Next.** Dashboard for that profile. Its report and chat are loaded for that id. A goal result appears only if this tab still has one in memory.

If the stored id is no longer in the list, the selection is cleared and locked pages redirect to `/profile`.

## 8. Delete a profile

1. **Entry.** Trash control on a saved-profile row.
2. **Goal.** Remove a snapshot.
3. **Information.** None. There is no confirm.
4. **Actions.** One click. The click does not also select the row.
5. **Feedback.** Success toast “Profile deleted,” or an error toast.
6. **Result.** `DELETE /api/profile/<id>`. The report, chat, and jobs for that profile go with it. If it was the active profile, the app replaces the URL with `/profile`.
7. **Next.** The create form, if no active profile remains. Otherwise the person stays on the profile page with the list updated.

## 9. Dashboard, first value

1. **Entry.** After create, after select, or “Dashboard” in the sidebar. Locked until a profile exists.
2. **Goal.** See whether the picture is healthy, and what to open next.
3. **Information.** The profile. A report, if one exists.
4. **Actions.** “Generate Report” when none exists. Quick Actions: Detailed Report, AI Chat, Goal Simulator.
5. **Feedback.** “Loading health score…” while the report loads. Without a report, an empty gauge and “Generate an AI advisory report to unlock your score and pillar breakdown.” Annual savings and monthly surplus still render. Insights say to generate a report for “AI insights.” With a report: gauge, status word, pillars, up to three warnings and two strengths.
6. **Result.** A home screen. The score appears only after the report job has produced `ai_report`.
7. **Next.** Stay and read, open Advisory, open Chat, or open Goals. If the PDF is not ready, a line says to open Advisory and download to build it.

## 10. Financial health (the score)

1. **Entry.** The dashboard gauge, or Advisory sections 01 and 03. The math runs in `services/health_service.py` when a report is built.
2. **Goal.** Judge savings, spending, emergency cover, debt, retirement, tax, and surplus.
3. **Information.** The profile fields. The person does not enter a separate emergency corpus or 80C amount.
4. **Actions.** None on the score itself. Generating a report is what reveals it.
5. **Feedback.** Status is Healthy at 70 or above, Moderate at 50 or above, otherwise At Risk. Pillars show points out of 25, 20, 20, 15, 10, 5, and 5, and the dashboard also shows that as a percent of the pillar maximum.
6. **Result.** A 0–100 score plus insight and warning sentences.
7. **Next.** Read a warning, open the written advisory, or ignore the score and open chat or goals. The product does not pick one next step.

Emergency months on the advisory summary equal monthly savings divided by monthly expenses. Tax language assumes about 30% of savings is already in 80C products. Retirement assumes age 60 and a 10% return on the monthly savings figure.

## 11. Report generation and the wait

1. **Entry.** “Generate Report” on the dashboard, or “Generate” / “Regenerate” on Advisory.
2. **Goal.** Get a written plan for this profile.
3. **Information.** The selected profile id. The person does not choose a model or a length.
4. **Actions.** One click. A second click while `generating` is ignored. Regenerate does not ask before replacing the stored report.
5. **Feedback.** The button reads “Generating…”. The client polls `GET /api/report/<id>` about every 2 seconds for up to 120 seconds. Success toast “Report generated.” If the text saved and the file did not: “Report saved — PDF will be created when you download.” Failure toast: previous report unchanged, or “Report generation took too long. Try again.”
6. **Result.** One report per profile, with health JSON and advisory text. The PDF may or may not exist yet.
7. **Next.** Read Advisory. Download. Ask in chat. Run a goal. Leaving the page stops the poll. Returning starts it again if the job is still active. The screen does not say that.

Quota failures toast “Too many requests” and a wait when the server sends one. The allowance is not shown before the click.

## 12. Read the report

1. **Entry.** Advisory in the sidebar, or “Detailed Report” on the dashboard.
2. **Goal.** Read the verdict and the plan, then keep a file.
3. **Information.** The stored report.
4. **Actions.** Read. PDF. Regenerate.
5. **Feedback.** “Loading report…”. Empty state “No report yet” with Generate. A non-404 load error uses the banner and Retry, and tells a rate-limited person not to regenerate.
6. **Result.** Sections 01–05: summary, cash-flow bars, pillars, strengths and warnings, model text, then a small disclaimer.
7. **Next.** PDF, regenerate, or leave via the sidebar. The page does not name a single next action.

Cash-flow bars label expenses as “Essential Expenses” and the remainder after the savings ratio and the expense ratio as “Investment Capacity (Surplus).”

## 13. PDF

1. **Entry.** “PDF” on Advisory, only after a report object exists.
2. **Goal.** Take the plan out of the browser.
3. **Information.** None.
4. **Actions.** Click PDF.
5. **Feedback.** A missing file toasts “No PDF available — generate a report first.” A build failure toasts that the PDF could not be built and suggests regenerating. Success downloads `financial_report_profile_<id>.pdf`.
6. **Result.** A file, or a toast. The dashboard line “download to build it” is how a missing file gets created from saved text.
7. **Next.** The person is still on Advisory.

## 14. AI chat

1. **Entry.** Chat in the sidebar, or “AI Chat” on the dashboard. Locked until a profile exists.
2. **Goal.** Ask something the report did not answer, without retyping income and savings.
3. **Information.** Typed text, or one of three starters: Portfolio Analysis, Tax Optimization, Goal Simulation. Each starter sends a full sentence immediately.
4. **Actions.** Send, or click a starter. Clear, once messages exist.
5. **Feedback.** The user bubble appears. “Analyzing…” while history is polled about every 1 second for up to 120 seconds. Empty state: “Ask about investments, budgeting, tax savings, or your goals.” “Active now” under the goal title. Footer: “FinPilot AI can make mistakes. Verify critical financial data.”
6. **Result.** A reply rendered from markdown and stored on the profile. The model sees the profile fields and recent turns. It does not see the score or the goal-calculator result unless those words are already in the chat.
7. **Next.** Another question, clear, or another page. Clear has no confirm. A failed send removes the bubble and toasts.

On a narrow screen the starters and Clear are a horizontal chip row. The left column is hidden below `md`.

## 15. Goal creation and the simulation

1. **Entry.** Goals in the sidebar, or “Goal Simulator” on the dashboard.
2. **Goal.** See if monthly savings can fund a target.
3. **Information.** Goal name (optional; blank becomes “My Goal”), target amount in rupees, horizon from 1 to 40 years, default 5. The profile’s savings and risk are used and not retyped. The profile’s goal sentence is shown as a truncated line and is not copied into the name field.
4. **Actions.** “Calculate Pilot Path.”
5. **Feedback.** Invalid amount or horizon toasts and does not call the API. The button reads “Running Simulation…”. The empty panel says to run the simulation to see a confidence score.
6. **Result.** A percentage labeled “Pilot AI Confidence Score,” a feasible or gap sentence, three scenario cards, current saving, required SIP, gap or surplus, projected corpus, coverage, and a primary and secondary product. Balanced is badged Recommended. The result is kept in browser memory for that profile id only.
7. **Next.** Change the inputs and run again, which replaces the result. Leave the page. Come back in a new session and the result is gone. No disclaimer is on this screen.

## 16. Navigation

1. **Entry.** Sidebar, or the menu button below the `lg` breakpoint.
2. **Goal.** Change screens without losing the profile.
3. **Information.** None.
4. **Actions.** Dashboard, Advisory, Chat, Goals, Profile. Locked items do nothing until a profile is selected. The menu closes after a choice. Person-add goes to Profile. Search, bell, and settings do nothing.
5. **Feedback.** The active item is highlighted. Locked items show a lock. A tooltip on hover says to select or create a profile. The address bar updates with `pushState`.
6. **Result.** The matching page. Profile and chat use a full-bleed layout. The others sit in the padded main column.
7. **Next.** Whatever that page offers. Browser Back follows history. An entry from another signed-in account is not shown; the app replaces it with a path for the current session.

## 17. Empty states

| Place | What the person sees | Action on the empty state |
| --- | --- | --- |
| Profile list | “No profiles yet. Create one with the form.” Plus “You are signed in and have no profiles yet.” | Use the form |
| Dashboard score | “No health score yet” and an empty gauge | Generate Report |
| Dashboard insights | “Generate a report to surface AI insights.” | Generate, or a quick action |
| Advisory | “No report yet” | Generate Report |
| Chat | “Ask about investments, budgeting, tax savings, or your goals.” | Type, or a starter |
| Goals | “Define a goal and run the simulation to see your confidence score.” | Fill the form and calculate |

A 404 on the report is treated as the empty state, not as the error banner. The first time it happens, a toast also says to click Generate.

## 18. Errors and recovery

| Failure | What the person sees | What still works |
| --- | --- | --- |
| Report load, rate limit | Banner “Temporarily rate-limited” and a toast. Copy says to retry and not to regenerate | Retry load |
| Report load, other | Banner “Couldn’t load report” and Retry | Retry. Regenerate remains available and can replace a report they have not seen |
| Report job failed | “Report generation failed. Your previous report is unchanged.” | The old report, if one existed |
| Report job too long, or worker lost | “Report generation took too long. Try again.” | Generate again |
| PDF missing or unbuildable | Info or error toast | The on-screen text |
| Chat history failed | Banner and Retry | The composer |
| Chat reply failed or timed out | Toast. The unsent bubble is removed | Type the question again |
| Goal validation | Toast, no request | The form |
| Goal request failed | Toast | The previous on-screen result, if the tab still has it |
| Network | “Can't reach the FinPilot API. Confirm the backend is running on port 5000.” | Retry |
| Unauthorized | “Unauthorized — check your API key configuration.” | Sign in again if the session actually ended. The React app does not ask for an API key |
| Session expired | “Your session ended. Sign in again.” | Sign in |

Toasts disappear on a timer. They are not a live region.

## 19. Settings

There is no flow. The gear in the top bar has no handler. Password change, export, and account deletion are not screens.

## 20. Return visit

1. **Entry.** Open the site within 12 hours in the same browser, or sign in again after that.
2. **Goal.** See the same picture.
3. **Information.** Cookie, or email and password. This tab’s `sessionStorage` profile id.
4. **Actions.** None if the cookie and the profile id are both still valid.
5. **Feedback.** Blank, then the shell. The dashboard loads the report. Chat loads history. Goals load only a result still in memory.
6. **Result.** The same profile, report, and chat. The numbers are whatever was typed at create time.
7. **Next.** Reread, regenerate, ask again, or run another goal. Nothing in the interface asks what changed, because the profile cannot be edited.

---

## Proposed first-session logic

This replaces the sequence above for a new person. It is a proposal for information architecture and interaction logic. Visual design is out of scope. It is not implemented.

### First visit

The landing hero is a labeled sample of the monthly form and the score that follows it. Primary button: create account. Secondary: sign in. On the page, before the dialog: a short privacy summary, and the line that the product is not a SEBI-registered advisor.

### Onboarding

1. Dialog collects email, password, and confirm password. The 12-character rule is visible. One sentence says a later written plan is sent to the model.
2. The next screen is “Your monthly picture,” not “Onboarding Profile.”
3. Fields are unchanged, plus a short profile name that is separate from the goal sentence. The list and the top bar use the short name.
4. One line under savings, EMI, and risk says what each field means.
5. The button is “See my score.”

### First value

The dashboard opens with the rule score, the status word, the seven pillars, annual savings, and monthly surplus. Emergency months and the tax pillar each show their assumption in one line. No empty gauge. No worker required for this screen.

### Core action

One primary button: “Write my plan.” It is the only generate control. The wait copy is: the plan is being written, it can take about a minute, and leaving the page does not cancel it. Chat and Goals stay in the sidebar and are not required to see the score.

### Result

Advisory keeps the numbered sections. The first section is the monthly picture. Cash-flow labels match the form fields. If income, expenses, and savings do not partition cleanly, the page says so instead of showing a leftover called investable surplus. The model text stays in its own section. The disclaimer uses body text. Download is enabled when the file exists. Otherwise the control is “Prepare PDF” and the page reports the outcome.

### Next best action

One step at the bottom of the plan:

- A goal sentence and no simulation yet → “Check whether your savings can fund this,” with the goal name filled in on the calculator.
- A question left open → “Ask about this plan,” with starters inserted into the composer as drafts that are not sent until the person presses send.
- Otherwise → “Download” and the 30-day section scrolled into view.

The other destinations remain in the sidebar.

### Return

Sign-in with a profile opens the dashboard. The score is already there. The snapshot shows the date it was saved. “Update numbers” edits the profile, rescores immediately, and marks the written plan as older until “Update the written plan.” Sign-out and a 12-hour expiry both land on a page that says the session ended and that sign-in opens the plan.

Delete profile, clear chat, and regenerate each ask before they remove the only copy. Fixing a number is the edit action.

Search, notifications, and Upgrade to Elite are not on this path.

### Proposed sequence, in order

```text
First visit
  sample of the form and the score, labeled as a sample
  privacy summary and the advisor disclaimer
  → create account (password rule visible)
Onboarding
  → monthly picture (short name, goal, income, expenses, savings, optional EMI, risk)
  → See my score
First value
  → dashboard with the rule score, pillars, and assumptions
Core action
  → Write my plan
  → wait copy that allows leaving the page
Result
  → numbered advisory, model text separated, disclaimer in body text
  → Download when the file exists
Next best action
  → one step: check the named goal, ask about the plan, or read the 30-day list
Return
  → sign in
  → same dashboard, score visible, snapshot date visible
  → Update numbers, then optionally update the written plan
```
