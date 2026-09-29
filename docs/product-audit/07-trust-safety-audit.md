# FinPilot AI — trust and safety audit

**Date:** 2026-09-29  
**Scope:** What a person can believe from the screens, the scores, and the model text. Authentication and deletion are included only where they change that belief or the person’s control of the data.  
**Not in scope:** A legal opinion, a penetration test, or a code change. This document does not say that any screen complies or fails a statute.  
**Sources:** `frontend/src/pages/LoginPage.jsx`, `AdvisoryPage.jsx`, `ChatPage.jsx`, `GoalsPage.jsx`, `DashboardPage.jsx`, `sections/profile/ProfileForm.jsx`, `sections/profile/SavedProfiles.jsx`, `services/health_service.py`, `services/ai_service.py`, `services/goal_service.py`, `services/pdf_service.py`, `services/jobs/worker.py`.

`Legal/compliance review required?` means a lawyer should look at the wording, the consent, or the retention. **YES** is a review flag. It is not a finding that the product is unlawful. **NO** means the issue is product clarity or interaction safety, and this audit is not asking counsel to interpret it.

---

## Where a person can mix up the kinds of information

| What they see | What it actually is |
| --- | --- |
| Landing score 82, “+8.4% this quarter,” ₹40,000 surplus | Copy written into `LoginPage.jsx` |
| Health score, pillars, Healthy / Moderate / At Risk | Rules in `health_service.py`, shown only after a report job |
| “Emergency fund covers N months” | Monthly savings ÷ monthly expenses, one decimal |
| “80C limit appears well-utilised” | About 30% of the savings field, compared with ₹1,50,000 |
| Retirement corpus in rupees | Monthly savings compounded at 10% until age 60. No existing corpus |
| Advisory sections 01–04 | The same rules, plus labels such as “Portfolio Health” and “Essential Expenses” |
| Section 05 and chat replies | Groq text. Temperature 0.7. No check on percentages or product names |
| “Pilot AI Confidence Score” and Recommended on Balanced | SIP formula. Balanced is hardcoded as recommended |
| Goal bar on an infeasible scenario | 100% if feasible, otherwise 60% when coverage is missing |
| ENCRYPTED, “Private by design,” “Yours, always” | Account separation and a hashed password. Financial columns are ordinary numerics. No privacy page |

The advisory page is the only screen that puts calculated blocks and model text in different sections. Chat, Goals, the dashboard empty state, and the landing page do not keep that split.

---

## Issues

### 1. The landing page shows a live financial picture

**Problem.** A visitor sees “Live financial picture,” a score of 82, “+8.4% this quarter,” and a ₹40,000 surplus before they have an account.

**User risk.** They expect the product to know their money and to show change over time. The first signed-in screen is an empty form. Trust drops, or they treat the sample as proof of a result the app cannot produce.

**Current implementation.** Those figures are written into `LoginPage.jsx`. The chart’s accessible name says the chart is illustrative. The numbers are not labeled as a sample. There is no disclaimer on this page.

**Recommended UX improvement.** Label the card “Sample.” Remove “Live” and the quarterly change until a second snapshot exists. Use the same gauge as the product, with sample numbers called out as sample.

**Engineering implication.** Copy and layout in `LoginPage.jsx` only, until a real delta exists.

**Legal/compliance review required?** YES

---

### 2. Privacy and encryption are stated more strongly than the product implements

**Problem.** The landing strip says “Private by design” and “Yours, always.” The profile form shows a badge, ENCRYPTED.

**User risk.** Someone may type income, EMI, and a goal because they believe the fields are encrypted and that a privacy promise has been spelled out. The badge does not describe the storage this repository shows.

**Current implementation.** Passwords are Werkzeug hashes. Profiles, reports, chat, and jobs are rows in PostgreSQL. PDFs are files on disk. A search of the app found no field-level encryption of the financial columns and no privacy page. The badge is a `span` in `ProfileForm.jsx`.

**Recommended UX improvement.** Replace the badge with a sentence that matches storage: this account can see its own profiles. Link a privacy summary before the first number is saved. Keep “encrypted” for a control that is actually on.

**Engineering implication.** Remove or rewrite the badge. A privacy summary is content. Field-level encryption would be a separate project and is not required to stop the overclaim.

**Legal/compliance review required?** YES

---

### 3. Financial data is sent to the model without a notice on the way there

**Problem.** Generate and chat send age, income, expenses, savings, risk, and the goal sentence to Groq. The report also sends the score and the insight and warning text. The screens do not say that before the click.

**User risk.** A person who would not send a salary to a third-party model still clicks “Generate Report,” because the button describes an advisory, not a transfer.

**Current implementation.** `generate_financial_report` and `chat_with_advisor` in `services/ai_service.py` put those values in the user message. Sign-up has no consent checkbox. The advisory footer is shown after the text exists. Chat’s mistakes line is under the composer and does not mention the provider.

**Recommended UX improvement.** On the first generate, and on the first chat send, one sentence: the monthly picture and the question are sent to the model provider to write the reply. Let them continue or go back. Repeat it in a short privacy summary, not only in a toast.

**Engineering implication.** A one-time acknowledgement stored on the account, checked before enqueue. The worker already receives the profile. No change to the prompt is required for the notice itself.

**Legal/compliance review required?** YES

---

### 4. There is no privacy notice, export, or way to delete the account

**Problem.** The person can delete a profile. They cannot read what is stored, download their rows, or delete the account. There is no terms page and no privacy page. The footer is a copyright line.

**User risk.** They cannot see the full set of data the product holds, and they cannot close the account if they used the wrong email or want to leave. The PDF is the only file export.

**Current implementation.** `DELETE /api/profile/<id>` removes that profile and, by cascade, its report, chat, and jobs. No account-delete route was found. Goal runs are not in the database. Settings is an icon with no screen.

**Recommended UX improvement.** A privacy summary that lists profiles, reports, chat, jobs, and PDF files, how long the session lasts, and that goal runs stay in the browser. Actions: download a copy, delete the account. Until those exist, do not show a settings icon.

**Engineering implication.** New account routes and a dump of that account’s rows and PDF files. Deletion must cover `accounts` and the files under the PDF directory, not only `users`.

**Legal/compliance review required?** YES

---

### 5. Emergency “months of cover” treats one month of savings as a fund

**Problem.** The advisory summary shows “Emergency Fund: N mo.” Warning text says the fund “covers” that many months.

**User risk.** A person with a separate emergency balance they were never asked for looks unprepared. A person who saves a lot this month looks protected, even when that money is not a stock of cash. They may skip a real buffer or feel wrongly alarmed.

**Current implementation.** `emg_months = savings / expenses` in `health_service.py`, rounded to one decimal. The copy does not say “estimated from this month’s savings.” Six months is full marks. The model then sees that sentence in the report prompt and can repeat it as fact.

**Recommended UX improvement.** Rename the line “Savings this month, as months of expenses.” Ask for an actual emergency balance if the score is going to talk about a fund. Keep the one-decimal figure next to the formula.

**Engineering implication.** Either a new optional field that the scorer prefers when present, or a label change and a prompt change so the model cannot say “your emergency fund.”

**Legal/compliance review required?** YES

---

### 6. Tax language states an 80C position the person did not declare

**Problem.** Insights say the 80C limit “appears well-utilised based on savings pattern.” Warnings quote a utilisation percent and name ELSS, PPF, and EPF.

**User risk.** They may believe the product knows their tax filings. They may contribute, or not, based on a percent that was never measured. The model can repeat the sentence in the essay.

**Current implementation.** `estimated_80c = savings * 0.30`, compared with ₹1,50,000 (`SECTION_80C_LIMIT`). The code comment calls it a heuristic. The UI shows the resulting sentence with no “estimate” in the high-score branch. The word “Estimated” appears only on the middle warning.

**Recommended UX improvement.** Always prefix with “Estimate, not your tax return.” Show the assumption: 30% of monthly savings, times 12, against the 80C cap. If they have not entered 80C investments, the pillar should say “not enough information” instead of a utilisation percent.

**Engineering implication.** Change the insight strings and pass the assumption into the report prompt as an assumption, not as a finding. An optional 80C field would replace the proxy.

**Legal/compliance review required?** YES

---

### 7. Retirement is a precise forecast from hidden assumptions

**Problem.** Warnings name a rupee target (“25× annual expenses”) and a coverage percent at age 60. The profile example says “retire at 55.” The scorer does not use 55.

**User risk.** A rupee corpus looks like a plan. It ignores money they already have, and it ignores the retirement age they typed in the goal sentence. They may think they are on track, or far behind, for the wrong date.

**Current implementation.** Target corpus is 25 × annual expenses. Projected value is the future value of the monthly savings field at 10% until age 60. Age at or above 60 skips the projection and still awards half the pillar points. No existing corpus is collected.

**Recommended UX improvement.** Call it a projection. Show the three assumptions beside the number: start from zero, 10% a year, retire at 60. If the goal sentence names another age, do not present 60 as their plan. Round the corpus in words (“about ₹X”) rather than a full rupee figure.

**Engineering implication.** The strings in `_score_retirement` and the report prompt. A real projection needs inputs the form does not collect today.

**Legal/compliance review required?** YES

---

### 8. The score reads as a verdict, and the weights stay off the gauge

**Problem.** 0–100 is labeled Healthy, Moderate, or At Risk. The dashboard says an AI report unlocks the score. Pillar rows show a percent of that pillar’s maximum, which is easy to read as a percent of income.

**User risk.** “At Risk” feels like a credit or health judgment. “Unlock with AI” makes the rules look like a model opinion. A 40% pillar can be misread as “40% of my salary.”

**Current implementation.** Cuts are 70 and 50 in `scoreStatus`. Maxima are 25, 20, 20, 15, 10, 5, 5. The empty dashboard copy tells them to generate an AI report to unlock the score. The math does not need the model. Missing EMI still grants half of the 15 debt points (`_score_debt`), so leaving the field blank raises the total versus a high EMI, while the warning only says data was not provided. An entered 0 is treated as missing because the scorer treats 0 as absent.

**Recommended UX improvement.** Title it “Rule-of-thumb score.” Show the cuts and a one-line key: “percent of this pillar’s points, not of income.” Show the score when the profile is saved. If EMI is blank, show the debt pillar as “Not scored” and do not add half credit. Say that 0 means no EMI.

**Engineering implication.** Dashboard can render `health_json` without waiting for `ai_report`, or the score can be computed at save time. Debt scoring changes the number, so existing stored reports would differ if recalculated.

**Legal/compliance review required?** YES

---

### 9. Calculated blocks use words the person did not use

**Problem.** Advisory section 01 is “Portfolio Health.” Expenses are “Essential Expenses.” A third bar is “Investment Capacity (Surplus).”

**User risk.** “Portfolio” implies holdings. “Essential” implies a split they did not make. The third percent is whatever is left after the savings ratio and the expense ratio. Someone who saved the leftover of income minus expenses can see about 0% “investable” and think they cannot invest. Monthly surplus on the dashboard is income minus expenses and can disagree with the savings field. The two sit near each other without a note.

**Current implementation.** Labels are in `AdvisoryPage.jsx`. `investable = max(0, 100 - savings - expenses)` using the ratios from the health payload. Dashboard surplus is `income - expenses`.

**Recommended UX improvement.** Use the form’s words: expenses, savings, and the gap if those two do not add up to income. Drop “portfolio” until holdings exist. Put one sentence under the tiles when surplus and the savings field differ.

**Engineering implication.** Label and formula changes in `AdvisoryPage.jsx` and `DashboardPage.jsx`. The model prompt should use the same words so section 05 does not reintroduce “portfolio.”

**Legal/compliance review required?** YES

---

### 10. The essay states allocations and product ideas with no source

**Problem.** Section 05 is model prose. The prompt asks for allocation percentages “if possible,” Indian product examples, and a voice that sounds like a real advisor. Nothing checks the numbers.

**User risk.** A percent and a fund name look like a recommendation they could act on. A wrong figure is stored, shown, and copied into the PDF. They cannot see which sentence used their savings field and which sentence was invented. A reply cut off for length is still saved. The log records `finish_reason=length`. The screen does not.

**Current implementation.** `SYSTEM_PROMPT` says to sound like a real financial advisor. `generate_financial_report` requires the six headings. `ask_gpt` returns the string on success, including a truncated one. The worker saves it, then builds the PDF. There is no citation, no refusal when EMI or holdings are absent, and no second check. Temperature is 0.7.

**Recommended UX improvement.** Keep section 05 visually separate, and title it “Model notes on your score,” not an advisor’s allocation. Ask the prompt to tie each step to a field it was given, to skip products it cannot source, and to say when EMI or a goal amount was absent. If the completion is truncated, show “This plan was cut off” and do not present it as complete.

**Engineering implication.** Prompt text in `ai_service.py`, and a branch on `finish_reason` before save. A numeric checker is a larger step. The disclaimer change in the next issue should ship with this, not instead of it.

**Legal/compliance review required?** YES

---

### 11. The disclaimer is easy to miss, and several screens have none

**Problem.** The on-screen line is 10px type at 40% opacity: generated by FinPilot AI, market risks, not a SEBI-registered advisor. The PDF uses a different paragraph: educational guidance, not regulated investment advice, consult a professional. Goals, the dashboard, the landing page, and the score itself have no equivalent line. Chat says the AI can make mistakes and to verify critical data. That line does not mention advice or the score.

**User risk.** The strongest voice in the product is the essay and the large score. The limit is the faintest text, and it is missing where the goal screen names a product and a SIP.

**Current implementation.** `AdvisoryPage.jsx` footer. `pdf_service.py` disclaimer string. `ChatPage.jsx` composer caption. No disclaimer string was found in `GoalsPage.jsx` or `LoginPage.jsx`.

**Recommended UX improvement.** One short block, body size, on the landing page, under the score, under section 05, on the goal result, and in the PDF. Same sentences in each place. Do not leave the limit only in the PDF.

**Engineering implication.** One shared snippet used by those screens and by the PDF builder, so the wording cannot drift.

**Legal/compliance review required?** YES

---

### 12. Chat invites questions the transcript cannot answer

**Problem.** One-click prompts ask for a portfolio analysis, tax optimization, and a goal-feasibility judgment. The chat prompt does not include holdings, the score, EMI, the essay, or the goal result.

**User risk.** The reply will sound specific. It is filled in from six fields and the recent messages. A tax or portfolio answer can be read as based on records the product does not have. “Active now” under the goal title sounds like a person is present.

**Current implementation.** `PROMPTS` in `ChatPage.jsx` send the full question immediately. `chat_with_advisor` builds the user message from the six fields, up to 20 prior messages, and an 8,000-character cap. The UI can show up to 100 messages, so the person sees a longer memory than the model uses.

**Recommended UX improvement.** Prompts should be drafts in the composer, not instant sends. Replace “Portfolio Analysis” until holdings exist. Point goal questions at the calculator. Show the six fields the reply will use. Remove “Active now.” Say that only the recent part of the thread is reread.

**Engineering implication.** Chat UI, plus adding the score, EMI, and the latest goal payload to the prompt if those answers are still offered. That is a context change, not a new model call.

**Legal/compliance review required?** YES

---

### 13. The goal screen presents a formula as AI confidence and a fixed recommendation

**Problem.** The large figure is “Pilot AI Confidence Score.” Balanced is badged Recommended for every person. An infeasible scenario draws its bar at 60% when coverage is null. The result names a primary product (recurring deposit, balanced advantage fund, Nifty 50 SIP, and so on) from risk and horizon.

**User risk.** They can act on a badge that ignored their risk choice, read 60% as progress, and treat the product name as a picked investment. The percent is not a probability and not a model score. A second run replaces the first. Nothing tells them the result was not saved on the server.

**Current implementation.** Feasibility is `_feasibility_score` in `goal_service.py`. CAGR bands are 5/6/7, 8/10/12, or 10/12/15. `SCENARIO_META.Balanced.recommended` is `true`. `GoalsPage.jsx` uses `coverage ?? 60`. “Assumed CAGR” is visible on the card, which is the one explicit assumption. There is no disclaimer on the page. Results live in `goalStore` in the browser.

**Recommended UX improvement.** Call the figure a feasibility score from a savings-and-return formula. Recommend the scenario that matches the profile’s risk. Draw the bar only from coverage. Show the CAGR band as an assumption they could change later. Say the run stays on this device until they leave. Add the same disclaimer as the report.

**Engineering implication.** `GoalsPage.jsx` and the strategy picker in `goal_service.py`. Persistence is a separate table if the result should survive a new browser.

**Legal/compliance review required?** YES

---

### 14. Destructive actions have no confirmation, and a wrong number is fixed by deleting

**Problem.** Delete profile, clear chat, and regenerate each run in one click. Delete removes the profile, the report, and the chat. Regenerate replaces the only essay. There is no undo. There is no edit.

**User risk.** A mis-tap destroys the plan they might have been relying on. A person who notices a wrong salary cannot correct it. They either keep a report built on the wrong number or delete the record to start over.

**Current implementation.** `SavedProfiles.jsx` calls delete immediately. `useChat` clear deletes history immediately. `useReport` generate does not ask before a second run. No `window.confirm` was found. No `PUT` or `PATCH` for a profile was found.

**Recommended UX improvement.** Confirm delete with a sentence that names the report and the chat. Confirm regenerate and clear. Make “Update numbers” the way to fix a field, then rescore, and mark the old essay as tied to the previous numbers.

**Engineering implication.** Dialogs in the client. An update route and a report stamp (`profile` version or `generated_at` compared with the profile) so the essay can be marked stale. Cascade delete can stay as the confirmed path.

**Legal/compliance review required?** YES

---

### 15. The account can be lost, and the session end is easy to miss

**Problem.** There is no “forgot password,” no email verification, and no password change. The session lasts 12 hours. Sign-out does not ask for confirmation. After expiry, a toast says the session ended and the landing page returns.

**User risk.** A forgotten password leaves the financial profile, the report, and the chat unreachable. An unverified email means a typo may be the only key. On a shared computer, twelve hours is a long open session, and nothing warns that it will end.

**Current implementation.** Sign-up stores a hash and sets `finpilot_session`. Logout bumps `session_version`. No reset route was found. Verification is called out in planning notes as not part of that plan. The landing page does not explain the 12-hour limit.

**Recommended UX improvement.** Show the session length at sign-up. Offer a reset path before people store a salary. After expiry, keep one line on the landing page: the session ended, sign in to open the plan. Sign-out can stay one click if the landing page says they are signed out.

**Engineering implication.** Email delivery for reset, which the app does not have. Until that exists, the honesty fix is to say that a lost password cannot be recovered.

**Legal/compliance review required?** YES

---

### 16. Failures talk like an operator, and limits appear only after they hit

**Problem.** A network error mentions port 5000. An unauthorized error mentions an API key. Report and chat quotas are enforced and not explained before the click. A down worker looks like “Generating…” for up to about two minutes, then “took too long.”

**User risk.** They may paste an API key into a page that does not use one, retry in a tight loop, or think the advice failed because their numbers were rejected. They do not learn the allowance until the toast.

**Current implementation.** Messages are in `frontend/src/lib/apiErrors.js`. Quotas are server-side (report and chat limits are documented in the architecture notes, not in the UI). The poll budgets are 120 seconds in `useReport` and `useChat`.

**Recommended UX improvement.** Customer sentences: “We couldn’t reach FinPilot. Try again.” “Sign in again.” Before generate: “A written plan can take about a minute. You can leave this page.” If a quota exists, say the limit in the same unit the server uses, at the moment they hit it, without asking them to regenerate.

**Engineering implication.** Copy in `apiErrors.js` and the wait states. The quota numbers should be read from the same configuration the limiter uses so the sentence cannot drift.

**Legal/compliance review required?** NO

---

### 17. Goal runs look like part of the saved plan

**Problem.** After “Calculate Pilot Path,” the score, the SIP, and the product names stay on screen. Nothing says they will vanish in another browser or after the memory is cleared. The profile’s goal sentence is a different field from “Goal Name,” so two goals appear to be one.

**User risk.** They think the feasibility result is stored with the report. They return and it is gone. Or they think the calculator used “retire at 55” when it used a new name, the savings field, and a default five-year horizon.

**Current implementation.** `useGoalPlan` writes `goalStore`, a module map keyed by profile id. The database has no goals table. The profile line above the form is `userGoal`, truncated. The name input starts empty. Blank name becomes “My Goal.”

**Recommended UX improvement.** “Saved on this device only” under the result. Prefill the name from the profile goal and mark it editable. If the horizon was not taken from the sentence, say the horizon is the slider, not the sentence.

**Engineering implication.** Copy and prefill in `GoalsPage.jsx`. Server storage is only needed if “saved” should mean the account.

**Legal/compliance review required?** NO

---

## What the product already does carefully

Sign-out bumps the session and the client drops in-memory report, chat, and goal caches. A history entry from another account is not rendered as that account’s page. A failed report job leaves the previous essay in place, and the toast says so. A rate limit on load tells them not to regenerate. Advisory sections 01–04 are the rules, and section 05 is the model, which is the right split when the person reaches that page. The PDF repeats a short educational limit after the essay. Chat asks them to verify critical figures. Goal cards show “Assumed CAGR,” so that one assumption is visible. The health-score code comments already call the 80C line a heuristic. The screens do not say so.

The trust gap is that the loudest objects — the landing score, the gauge, the emergency and tax sentences, the goal percentage, and the essay’s percentages — speak as if they were measured, while the limits and the assumptions are quiet, missing, or worded as a different product.
