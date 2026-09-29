# FinPilot AI — UX audit

**Date:** 2026-09-29  
**Method:** Every signed-out and signed-in screen in `frontend/src` was read, plus the hooks that load, poll, and fail (`useReport`, `useChat`, `useGoalPlan`, `useProfiles`) and the route guard in `frontend/src/lib/routes.js`. There is no router package. Paths are `/`, `/profile`, `/dashboard`, `/advisory`, `/chat`, and `/goals`.  
**Builds on:** `docs/product-audit/01-product-360-audit.md`, `02-feature-service-audit.md`, `03-personas-jtbd.md`.  
**Flows:** Step-by-step workflows and the proposed first-session logic are in `docs/product-audit/user-flows.md`.

Application code was not changed. This pass did not include a screen reader, a device lab, or live customers. Those gaps are marked `UNKNOWN`.

Severity used in the table:

- **Critical** — the person can destroy their only plan, or the screen can push a financial decision on a false signal
- **High** — the main path is blocked, misleading, or much harder than the task
- **Medium** — the screen is usable and still confusing, inconsistent, or weak on recovery
- **Low** — polish, or chrome that does not block the job

---

## What the interface is

A visitor sees a marketing page, then a dialog for email and password. After sign-in, a shell with five destinations: Dashboard, Advisory, Chat, Goals, and Profile. The first four stay locked until a profile exists. Profile is a create form plus a list. Dashboard, Advisory, and Chat all wait on a background job the person never starts. Goals is a calculator that answers in the same view.

The visual system inside the app is consistent: dark surfaces, one gauge, pillar rows, and a toast. The problems are in the sequence, the labels, and what the interface claims while it waits.

---

## Screen notes

Each screen is judged on clarity, hierarchy, actionability, feedback, trust, friction, consistency, recovery, and obvious accessibility gaps.

### Landing (`/`, signed out) — `LoginPage.jsx`

**Clarity.** The page is about feeling in control of money. Three cards name a score, a goal model, and an advisor. **Hierarchy.** The hero score of 82 dominates the story. **Actionability.** “Start your financial map” and “Get started” open sign-up. “See the platform” only scrolls. **Feedback.** None until the dialog. **Trust.** The card says “Live financial picture.” The chart’s accessible name says the chart is illustrative. The numbers are written into the page. Avatars AS, RN, and MK are not identified customers. “Private by design” has no privacy page behind it. **Friction.** Pricing, a sample of the empty first screen, and terms are absent. **Consistency.** The brand line is “Premium wealth pilot.” The signed-in sidebar says “Wealth Manager.” The first signed-in screen is a form. **Recovery.** A bad path that is not an app route is sent back to `/`. **Accessibility.** Primary nav links hide below the `md` breakpoint, so phone visitors get Sign in and Get started only. The auth entry points remain.

### Auth dialog — `LoginPage.jsx`

**Clarity.** “Build your money map” versus “Welcome back” matches the mode. **Hierarchy.** Email, password, and the submit button are the whole dialog. **Actionability.** Sign-up is the default. The toggle between modes is clear. **Feedback.** A mismatch on confirm password is inline. Server errors render in the dialog. The button uses the shared loading state. **Trust.** Nothing says the password must be 12 characters, that financial numbers will later be sent to Groq, or that there are terms. There is no “forgot password.” **Friction.** The 12-character rule appears only as a failed submit. **Consistency.** Errors here stay in the dialog. Later errors use toasts. **Recovery.** Wrong email or password says they are incorrect. An existing email says the account exists. Closing the backdrop returns to the landing page. **Accessibility.** The dialog has `role="dialog"` and `aria-modal="true"`. No focus trap or initial focus was found. The error paragraph has no `role="alert"`. Backdrop click closes it, which is easy to do by mistake.

### Session boot — `App.jsx`

**Clarity.** While `GET /api/auth/me` runs, the app renders nothing (`!ready ? null`). **Feedback.** A blank view, with no “Checking your session.” **Recovery.** Failure clears the local session and shows the landing page. A persisted page (`pageshow`) re-checks the account and, if the account changed, opens the profile path for the new session. **Accessibility.** A blank load is silent.

### App shell — `AppShell.jsx`, `Sidebar.jsx`, `TopBar.jsx`

**Clarity.** Five labels are plain. The page title in the top bar comes from `PAGE_TITLES`. Profile’s title is “Onboarding Profile” on every visit. **Hierarchy.** The sidebar is the way around. The top bar adds search, a person-add icon, a bell, a settings gear, and a generic account glyph. **Actionability.** Locked items show a lock and a `title` of “Select or create a profile first.” The person-add icon goes to Profile. Sign out is labeled. **Feedback.** The active item is a highlight and a left border. **Trust.** “Upgrade to Elite” sits under the email with no plan. Search, bell, and settings have no action. **Friction.** On a small screen the nav is behind a menu. Search is hidden below `lg`. Bell and settings are hidden below `sm`. **Consistency.** “New profile” does not start a blank wizard. It opens the same create form beside existing profiles. **Recovery.** Sign out still runs if logout fails, and returns to `/`. **Accessibility.** Menu open and close have names. Search has placeholder text and no label. Bell, settings, person-add, and the account glyph have no accessible name (`title` only on person-add). Elite is a `<button>` that does nothing. Disabled nav items expose the reason only through `title`, which touch users often never see; the lock icon is `aria-hidden` with the other icons. No skip link was found.

### Profile and financial entry — `ProfilePage.jsx`, `ProfileForm.jsx`

**Clarity.** The heading is “Create profile.” The helper says the numbers unlock advisory, chat, and goal simulation. **Hierarchy.** Snapshot fields, then risk, then the goal sentence, then “Continue to Dashboard.” **Actionability.** One submit. Required gaps toast “Please fill in all required fields” or “Please enter your financial goals.” **Feedback.** “Creating…” then “Profile created successfully,” then the dashboard. **Trust.** A badge says ENCRYPTED. Amounts are ordinary numeric columns. The goal example (“Buy a house in 5 years, retire at 55…”) becomes the profile’s name in the list, truncated at 52 characters. **Friction.** EMI is optional and easy to skip, which later yields a half-credit debt warning. There is no edit. A correction is a new profile or a delete. Risk buttons do not explain that the choice changes the goal calculator’s product and return tier. **Consistency.** The top bar still says “Onboarding Profile” after the first profile exists. **Recovery.** A failed create stays on the form and toasts the API message. **Accessibility.** `TextField` renders a `<label>` with no `htmlFor` and an input with no `id`, so the label is not tied to the control. Risk choices are buttons with visible text. The goal field is a textarea whose visible heading is not passed as the field label.

### Saved profiles — `SavedProfiles.jsx`

**Clarity.** “Saved profiles” and a count. Empty copy says “Create one with the form.” **Hierarchy.** The goal sentence is the title. Age, risk code (`low` / `medium` / `high`, not the button label), and monthly income are the subtitle. **Actionability.** A click selects and, from this page, opens the dashboard. **Feedback.** The active row is highlighted. Delete toasts “Profile deleted.” **Trust.** Delete is immediate. It removes the profile and, by cascade, the report and the chat. **Friction.** No confirm, no undo, and no statement of what a second profile is for. **Consistency.** The risk subtitle uses the stored value, while the form shows Conservative / Balanced / Aggressive. **Recovery.** A failed delete toasts the error and leaves the row. **Accessibility.** The delete control has `title="Delete profile"` and no `aria-label`. The row itself is a clickable `div`, not a button.

### Dashboard, no report — `DashboardPage.jsx`

**Clarity.** “No health score yet” is clear. The sentence under it is not: the score is rules, and the copy says an AI report unlocks it. **Hierarchy.** An empty gauge leads. Annual savings and monthly surplus, which need only the profile, sit underneath and are easy to miss. “Critical Insights” says “Generate a report to surface AI insights.” **Actionability.** “Generate Report” is the obvious button. Quick Actions already offer Detailed Report, AI Chat, and Goal Simulator, so three other next steps compete with the first one. **Feedback.** “Generating…” on the button, plus a toast when the job ends. No explanation that a worker has to be running, and no sense of progress across the two-minute poll. **Trust.** Monthly surplus is income minus expenses. The savings-rate line can describe the savings field instead. Those two figures can disagree, and the screen does not say so. **Friction.** First value waits on Groq. **Recovery.** See Job processing below. **Accessibility.** The empty gauge’s center is an icon. The status is not exposed as text until a report exists.

### Dashboard, with a report

**Clarity.** A score, “Pillar Performance,” and a status word (Healthy, Moderate, At Risk). **Hierarchy.** The gauge leads, then pillars, then two money stats, then up to three warnings and two strengths, then shortcuts. That order matches “how am I doing, then where do I go.” **Actionability.** Quick Actions are equal. The warnings do not name a single next step. **Feedback.** A line appears if `pdf_ready` is false: open Advisory and download to build the PDF. **Trust.** Pillar percents are the share of each pillar’s maximum, not a percent of income. The screen does not say that. Warning text can describe an emergency fund and 80C use that were estimated, not declared. **Consistency.** “Critical Insights” includes strengths. The same score appears again on Advisory. **Accessibility.** Status uses a word and a color. Pillar percents are numeric. The gauge value is drawn as text inside the ring (`GaugeRing.jsx`).

### Advisory, empty and filled — `AdvisoryPage.jsx`

**Clarity.** The title is “AI Advisory Report.” The subtitle is the goal sentence. Empty state: “No report yet.” **Hierarchy.** After a report, sections are numbered: summary, cash flow, pillars, strengths and warnings, then “05. AI Advisory,” then a footer. That split is the clearest structure in the product. **Actionability.** Generate, or Regenerate, is beside PDF in the header. The empty state repeats Generate. **Feedback.** “Loading report…”, “Generating…”, toasts, and the load-error banner. **Trust.** The summary is titled “Portfolio Health” for a budget snapshot. “Essential Expenses” is the monthly-expenses field, which was not limited to essentials. “Investment Capacity (Surplus)” is `100 - savings ratio - expense ratio`, so a person who saved the leftover of income minus expenses sees about 0% investable. Emergency months are monthly savings divided by monthly expenses (`health_service.py`), shown as “Emergency Fund: N mo.” The disclaimer is 10px type at 40% opacity: not a SEBI-registered advisor, market risk. **Friction.** Regenerate replaces the only stored report with no confirm. PDF can be clicked before the file exists. **Consistency.** Generate also lives on the dashboard. **Recovery.** A failed job says the previous report is unchanged, or that it took too long. A rate limit tells them to retry the load and not to regenerate. **Accessibility.** Section headings are visual. The disclaimer is easy to miss by size and contrast.

### Chat — `ChatPage.jsx`

**Clarity.** Empty copy invites investments, budgeting, tax, or goals. The sidebar title is “Strategic Prompts.” **Hierarchy.** On a wide screen, prompts and a “Conversation” card sit left, the thread sits right, the composer sits last. On a narrow screen the prompts become a horizontal chip row. **Actionability.** The composer is obvious. A prompt chip sends a full question immediately, with no chance to edit it. **Feedback.** “Loading conversation…”, then “Analyzing…” while the reply is polled for up to two minutes. The user bubble appears at once and is removed if the send fails. **Trust.** The footer says the AI can make mistakes. “Active now” sits under the goal title and does not mean a person is present. “Portfolio Analysis” asks for a portfolio the product did not collect. “Goal Simulation” asks the model to judge a goal the calculator would compute. Clear has no confirm. **Consistency.** Chat does not show the score or the latest goal result. **Recovery.** History load uses the banner and Retry. A failed reply toasts and restores the composer text by dropping the unsent bubble. **Accessibility.** The composer is an unlabeled input. The send button is an icon. Clear is text on wide screens and a chip on narrow ones. No `aria-live` region announces the new reply.

### Goals, before and after a run — `GoalsPage.jsx`

**Clarity.** “Goal Definition” is clear. The profile’s goal sentence is a small line above the form, and the form asks for another “Goal Name.” **Hierarchy.** Before a run, the right side is an empty prompt. After a run, a large percentage leads, then three scenario cards, then gap stats, then a strategy. **Actionability.** “Calculate Pilot Path” is the only action. **Feedback.** “Running Simulation…” and a toast on failure. Success is the result itself. There is no “saved” message, because it is not saved in the database. **Trust.** The percentage is labeled “Pilot AI Confidence Score.” The path does not call Groq. Balanced is always badged Recommended (`SCENARIO_META`). An infeasible card draws the bar at 60% when coverage is null (`coverage ?? 60`). Assumed CAGR is visible, which helps. There is no disclaimer on this screen. The strategy names a primary and secondary product. **Friction.** The profile goal is not copied into the name field. Horizon defaults to 5. A second run replaces the only result. **Consistency.** Chat’s “Goal Simulation” prompt is a different tool with the same words. **Recovery.** Invalid amount or horizon toasts and does not call the API. A server error toasts and leaves the previous result if one was already on screen. **Accessibility.** The range input’s label is not tied with `htmlFor`. The result percentage is text, so it is not color-only. “Recommended” is text.

### Job wait (report and chat)

**Clarity.** The button or the line says generating or analyzing. **Feedback.** Report polls about every 2 seconds for up to 120 seconds (`useReport.js`). Chat polls about every 1 second for the same budget (`useChat.js`). Leaving the page stops that poll. Coming back starts it again if the job is still active. The person is not told the work continues in the background. **Recovery.** Timeout: “Report generation took too long. Try again.” Worker loss uses the same sentence. Other report failure: “Your previous report is unchanged.” Chat timeout becomes the provider-timeout toast. **Friction.** A down worker looks like a slow advisor.

### Errors, empty states, and toasts

Empty states exist for no profiles, no report (dashboard and advisory), no chat, and no goal result. Load failures that are not “not found” use `LoadErrorBanner` with Retry. Toasts cover success, error, warning, and info, and disappear on a timer (`Toast.jsx`). They are not an `aria-live` region, so a screen reader may not hear them. A network failure says the API must be running on port 5000. An unauthorized error says to check an API key. Those sentences are for an operator. Session expiry says “Your session ended. Sign in again.”

### Settings, search, notifications

There is no settings screen, no search results, and no notification list. The controls are in the top bar. Settings is an account job (password, export, delete account) with no page behind the icon.

### Sign out and session

Sign out is a text button in the sidebar. It posts logout, ends the local session, clears in-memory report, chat, and goal caches, and opens the landing page. There is no confirm. The cookie lasts 12 hours. After that, the next API call ends the session. Nothing warns that the session is about to end. A return to a previous account’s history entry is replaced with a path for the current session. That behavior is in `historySession.js` and `App.jsx`. The landing page does not explain why the person was sent back.

---

## Screen table

| Screen | Purpose | User goal | UX strengths | UX problems | Severity | Recommended change |
| --- | --- | --- | --- | --- | --- | --- |
| Landing | Explain the product and open an account | Decide whether to sign up | Specific tone, one primary button, screenshots of real pages | Hero shows a live score of 82 and a quarterly change that are not the visitor’s data. No privacy, terms, or disclaimer | High | Show a labeled sample of the first real screen: a form, then a score. Put the SEBI line and a privacy summary on this page |
| Sign-up dialog | Create the account | Keep the snapshot private to this email | Short form, inline confirm-password error, clear mode switch | 12-character rule only after failure. No consent. No statement that a later report is sent to a model | Medium | Show the password rule before submit. One sentence on what is stored and what is sent to the model |
| Sign-in dialog | Return to the same profiles | Open the last plan | Same dialog, plain error for a bad password | No reset. No hint that the session lasts 12 hours | High | Add a reset path. After sign-in, land on the dashboard if a profile exists |
| Session check | Restore a valid cookie | Skip the password when the session is still valid | Silent success is fast | The screen is blank until `/auth/me` returns | Low | A one-line “Checking your session” state |
| Sidebar | Move between the five jobs | Reach the screen for the current task | Lock plus label until a profile exists. Sign out is text. Email is visible | “Wealth Manager” and “Onboarding Profile” do not match the task. Elite does nothing | Medium | Rename Profile to “Monthly picture” after the first save. Remove Elite until a plan exists |
| Top bar | Name the page and offer account tools | Find search, alerts, settings, or a new profile | Page title is always visible. Menu button is named | Search, bell, and settings do nothing. Person-add has only a tooltip. Account glyph is decorative | High | Remove search, bell, and settings until they perform. Make “New profile” a text action on the profile page |
| Create profile | Capture the monthly picture | Unlock the rest of the app | One screen, required fields, risk hints, a single continue button | ENCRYPTED overclaims storage. Goal sentence becomes the profile name. No edit later | High | Say who can see the data. Ask for a short profile name separately from the goal. After save, show the score on the next screen |
| Saved profiles | Pick or remove a snapshot | Switch the picture the app uses | Active row is obvious. Empty state points at the form | Delete has no confirm and removes the report and chat. Risk shows as `low` / `medium` / `high`. A second profile is unexplained | Critical | Confirm delete and name what will be removed. Show Conservative / Balanced / Aggressive. One line on what a second profile is |
| Dashboard, no report | Home after the form | See whether the picture is okay | Surplus and annual savings already render from the profile. Generate is visible | Empty gauge and “unlock your score” hide a score the rules can already compute. Insights are called AI | High | Show the rule score and pillars on arrival. Offer “Write my plan” as the next action |
| Dashboard, with report | Home on a later visit | See standing and where to go | Gauge, status word, pillars, then warnings | Quick Actions are three equal doors. Pillar percents lack a one-line key. PDF-not-ready copy is easy to miss | Medium | Lead with the worst warning and one next step. Say pillar percents are points out of that pillar’s maximum |
| Advisory, empty | Start the written plan | Get advice from this profile | Empty state names the action. Retry is separate from regenerate when the load fails | Generate is duplicated with the dashboard. The page title says the report is AI before any score is explained | Medium | If the score is already on the dashboard, this empty state only offers the written plan |
| Advisory, filled | Read the plan | Decide what to do, and keep a file | Numbered sections. Score is separated from the model text. Rate-limit copy says not to regenerate | “Portfolio Health,” “Essential Expenses,” and investable surplus can describe the wrong thing. Disclaimer is tiny. Regenerate has no confirm. PDF may not exist yet | Critical | Rename the summary to the monthly picture. Explain emergency months and the cash-flow bars in one line each. Confirm regenerate. Enable Download only when the file is ready. Set the disclaimer in normal type |
| Chat, empty | Ask a first question | Get an answer that uses the saved numbers | Composer is fixed. Prompts exist on small screens as chips | “Active now” is misleading. Portfolio and Goal Simulation prompts promise data the chat does not have. A chip sends immediately | High | Prompts fill the composer and wait for send. Drop the portfolio prompt until holdings exist. Point goal questions at the calculator |
| Chat, thread | Continue the conversation | Ask a follow-up | User text stays if they typed it. A failed send removes the bubble and toasts. History survives in the database | “Analyzing…” can last two minutes with no job explanation. Clear has no confirm. The thread does not show the score | Medium | Say the reply can take up to a minute. Confirm clear. Show the score and the profile name above the thread |
| Goals, empty | Describe one target | See if savings can fund it | Short form, default horizon, obvious calculate button | The profile goal and Goal Name look like the same fact. The empty panel says “confidence score” | Medium | Prefill the name from the profile goal and label it editable. Say the result is a savings-and-return calculation |
| Goals, result | Read the SIP answer | Compare required SIP with current savings | CAGR is on the card. Gap, corpus, and coverage are separate stats. Rationale text exists | “Pilot AI Confidence Score.” Balanced is always Recommended. Infeasible bar falls back to 60%. No disclaimer. Result is not kept | Critical | Call it a feasibility score. Recommend the scenario that matches the profile’s risk. Draw the bar from coverage only. Add the same disclaimer as Advisory. Keep the last run on the profile |
| Report wait | Wait for the written plan | Know whether to stay, leave, or retry | Button stays in “Generating…”. Success and failure toasts are specific. A previous report is kept when a new job fails | No progress, no worker status, no “you can leave.” Timeout and a lost worker share one sentence | High | “Writing your plan. You can leave this page.” On failure: “The plan was not written. Your score is unchanged.” Offer Retry |
| Chat wait | Wait for a reply | Know the question was received | The question appears immediately. “Analyzing…” is visible | Same two-minute silence. A timeout is phrased as an AI-provider problem, which may be the worker | Medium | “Still writing a reply.” If it fails, restore the question in the composer, which the hook already drops from the thread |
| Load error banner | Recover a failed read | Try again without destroying data | Retry is explicit. Rate-limit copy says the saved report may still be there | Network and unauthorized copy mention port 5000 and an API key | Medium | Customer sentences: “We couldn’t load this. Try again.” Keep the rate-limit guidance |
| Toasts | Hear the outcome | Confirm create, generate, delete, or failure | Four tones. Rate limits include a wait when the server sends one | They vanish on a timer and are not announced to assistive tech. Delete success has no undo | Medium | Use a live region. Keep destructive results until dismiss |
| Settings | Manage the account | Change password, export, or delete the account | The gear looks like a standard control | There is no screen | High | Remove the icon, or open a page with password, export, and delete account |
| Search | Find a past plan or message | Jump to something already saved | The field looks like search | It accepts typing and does nothing | Medium | Remove it until profiles, reports, or chats can be found from it |
| Notifications | Hear that something changed | Act on a new event | The bell is a familiar icon | No events exist. The product does not notify | Medium | Remove the bell until a real alert exists |
| Sign out | End the session | Leave a shared browser | One labeled control. Local caches clear. Landing page returns | No confirm. A failed logout still drops the local session, which is safe, and the landing page does not say the session ended | Low | Optional confirm only on shared-device copy. A one-line “You have signed out” on the landing page |
| Session ended | Come back after 12 hours or a bumped session | Sign in again without seeing another account | The message is “Your session ended. Sign in again.” History from another account is not rendered | The message is a toast on the way out, then the landing page. Nothing explains the 12-hour limit | Medium | On the landing page, keep a short line: “Your session ended. Sign in to open your plan.” |

---

## Cross-cutting findings

**The first session hides the first answer.** After “Continue to Dashboard,” the useful numbers (annual savings, monthly surplus) sit under an empty gauge. The sentence that should be the score is postponed until a job the person cannot see.

**Money labels drift.** Portfolio, essential expenses, investable surplus, emergency months, AI confidence, and Recommended are stronger than the inputs. A careful reader can make a decision from the label rather than from the field they typed.

**Destructive actions are quiet.** Delete profile and clear chat run on one click. Regenerate replaces the only advisory. None ask for confirmation. Delete is the only way to fix a number, so the dangerous action is also the edit path.

**Dead controls sit on the primary chrome.** Search, notifications, settings, and Elite teach the person that some of the interface is scenery. That tax falls on every later screen.

**Feedback is better on failure than on waiting.** Rate-limit and “previous report unchanged” are specific. The wait itself is a spinner and a verb. Operator errors (port 5000, API key) leak into the customer path.

**Accessibility, from the code.** Icons are hidden from assistive tech, which is right for decorative icons and wrong for icon-only buttons that have no name. Field labels are not programmatically associated. Toasts and new chat messages are not in a live region. The auth dialog does not trap focus. Status words exist beside the gauge colors, which avoids a color-only score. A full assistive-technology pass was not run. Conformance level is `UNKNOWN`.

---

## Conceptual redesign of the main journey

This is information architecture and interaction logic. It is not a visual design. It is a proposal. It is not the current product.

The journey to fix is the first sitting of the monthly-snapshot saver: they should see a verdict on their own numbers before they are asked to wait for a model, and the next step should be one action.

### First visit

The landing page’s job is to preview the first session. The hero is a sample, labeled sample, of the monthly form and the score that follows. It does not show a live score, a quarterly change, or a portfolio. Primary action remains create account. Secondary action is sign in. Before the account exists, the page shows a short privacy summary and the same “not a SEBI-registered advisor” line the report already uses.

### Onboarding

Account, then one screen titled “Your monthly picture.” Fields stay age, income, expenses, savings, optional EMI, risk, and goal. A short profile name is separate from the goal sentence, and that name is what the list and the top bar show. Each field has one line of meaning: savings is the amount set aside each month, EMI is the monthly debt payment, risk chooses the later goal scenario. The password rule and the model-sharing sentence happened in the dialog, so this screen does not repeat them. The continue button is “See my score.”

### First value

The next screen is the dashboard with the rule score, the seven pillars, the status word, and the two money figures. Under the emergency and tax pillars, one line states the assumption (one month of savings divided by expenses; about 30% of savings treated as 80C). The person can read a verdict without a worker. The primary action is “Write my plan.” The secondary action is “Check a goal.”

### Core action

“Write my plan” is the only generate control. It lives on the advisory page and is linked from the dashboard. The wait state says the plan is being written, that it can take about a minute, and that leaving the page does not cancel it. Chat and goals stay available, and they are not presented as required to see the score.

### Result

The advisory page keeps the numbered order. The first section is titled for the monthly picture. Cash-flow labels match the form: expenses, savings, and the gap between income and those two if they do not add up. The model’s text stays in its own section. The disclaimer is the last block, in the same size as body text. Download is available when the file exists. When it does not, the control says “Prepare PDF” and reports success or failure in the page, not only in a toast.

### Next best action

The page ends with one recommended step, chosen from the lowest pillar or from the goal sentence:

- Emergency or savings warning → the written plan’s 30-day list is the step, and the dashboard later asks whether they did it only after an edit exists. Until edit exists, the step is simply “Read the 30-day list” and “Download.”
- A named goal with no simulation → “Check whether your savings can fund this,” opening Goals with the name filled in.
- A question the plan did not answer → “Ask about this plan,” opening chat with the composer empty and the prompts as drafts.

Quick Actions become that one step plus a quiet list of the other two destinations.

### Return

Sign-in with an existing profile opens the dashboard, score already visible. The snapshot shows the date it was saved. The action “Update numbers” edits in place, rescores immediately, and leaves the written plan marked as older than the numbers until they choose “Update the written plan.” Sign-out and a 12-hour expiry both return to the landing page with the sentence “Your session ended. Sign in to open your plan.” Settings, once it exists, holds password, export, and delete account. Search, the bell, and Elite stay off this journey until they have a real job.

Destructive rules on this journey: delete profile and clear chat ask what will be removed; regenerate asks before replacing the only plan; a wrong number is an edit, not a delete.

The step-by-step version of today’s flows and of this proposed sequence is in `docs/product-audit/user-flows.md`.
