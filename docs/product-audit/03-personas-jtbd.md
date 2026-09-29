# FinPilot AI — personas and jobs to be done

**Date:** 2026-09-29  
**Builds on:** `docs/product-audit/01-product-360-audit.md`, `docs/product-audit/02-feature-service-audit.md`  
**Check against the repo:** Landing copy, the profile form, chat starters, the health scorer, and the goal calculator were read again for this document.  
**What this is not:** Customer research. No interviews, support tickets, or product analytics were found. Usage counts are `UNKNOWN`. Each persona is an inference from what the product asks for, assumes, and shows.

Application code was not changed.

---

## Likely target user

The implementation is built for **one person in India who can state a monthly money picture in their own words** and wants a judgment plus a next step.

Evidence that defines them:

- The form asks for age, monthly income, monthly expenses, monthly savings, an optional monthly EMI, a risk choice, and a goal sentence (`frontend/src/sections/profile/ProfileForm.jsx`). Placeholders are age 28, income ₹1,50,000, expenses ₹80,000, savings ₹40,000. The goal example is “Buy a house in 5 years, retire at 55.”
- Currency is rupees. The scorer uses the Section 80C limit of ₹1,50,000 and assumes retirement at 60 (`services/health_service.py`).
- The goal calculator names Recurring Deposit, liquid funds, PPF, Post Office MIS, Balanced Advantage Fund, ELSS, Nifty 50 index funds, and mid-cap or international funds (`services/goal_service.py`).
- The model is told it specializes in Indian personal finance and should sound like a real advisor (`services/ai_service.py`). The advisory footer says the product is not a SEBI-registered advisor.
- Nothing in the app links a bank, a broker, a CAS, or a market feed. The person types the numbers.

They are comfortable enough to use a web app, wait for a background job, and read a long advisory. They are not asked for holdings, a city, dependents, a tax regime, or an employer. Those facts are `UNKNOWN` because the product never collects them.

The brand line on the landing page is “Premium wealth pilot” (`frontend/src/pages/LoginPage.jsx`). The working product is a typed monthly snapshot and a SIP calculator. The person the screens can actually help is a salaried saver with a goal, not a portfolio client.

---

## Personas

Three personas follow. The first is the person the form and the scorer are built for. The second is the same kind of person on the goal screen, with a sharper job. The third is the person the landing page and the chat starters invite, whom the data model cannot serve.

### 1. The monthly-snapshot saver

**Who they are.** A working adult who thinks about money as a monthly leftover: salary in, bills out, something set aside. The form’s own example is 28, earning ₹1.5 lakh a month, spending ₹80,000, saving ₹40,000, and naming a house or an earlier retirement. That example is a product assumption, not a researched customer.

**Financial situation.** They can name four monthly figures and a goal sentence. They may have one EMI. The product treats monthly savings as both the savings rate and the entire emergency fund: months of cover equal monthly savings divided by monthly expenses (`health_service.py`). It also projects retirement from that same monthly figure at 10% until age 60, with no existing corpus. A person who already holds a separate emergency fund or EPF is invisible to the score.

**Goals.** Hear whether this monthly picture is okay. Get a written list of what to do in the next 30 days. See a house, a retirement age, or another sentence they typed turned into a plan.

**Problems.** They have numbers and no structure. They do not want to build a spreadsheet of pillars, 80C headroom, and a SIP.

**Motivations.** The landing page promises less guesswork and a calmer view. The form says the numbers unlock advisory, chat, and a goal simulation. The dashboard empty state tells them the score appears after they generate a report.

**Frustrations the product creates.**

- The first score waits on a Groq job and a worker they do not start. The empty dashboard says “Generate an AI advisory report to unlock your score,” even though the score is rule-based.
- A wrong number cannot be edited. Fixing it means deleting the profile, which also deletes the report and the chat.
- Emergency-fund and tax lines can feel wrong, because the scorer invents a corpus from one month of savings and assumes about 30% of savings already sits in 80C products.
- The profile is titled with the goal sentence, so “Buy a house in 5 years…” becomes the name in the list.
- Search, notifications, settings, and Upgrade to Elite are on screen and do nothing.

**Technical comfort.** Enough to sign up, fill one form, and wait on “Generating…”. A network error that mentions port 5000, or an unauthorized error that mentions an API key, is operator language. That person will not know what to do with it.

**Financial literacy the product assumes.** They know their monthly income, spend, and savings. They can pick Conservative, Balanced, or Aggressive from short hints (“Preserve Capital”, “Growth & Stability”, “Maximum Returns”). The product then speaks to them in savings rate, DTI, 80C, CAGR, and SIP. It does not teach those words before using them. The advisory page does separate the rule-based score from “AI Advisory,” which helps a careful reader.

**Why they would use FinPilot.** One sitting can turn a monthly picture into a 0–100 score, pillar warnings, a structured write-up, and a PDF they can keep.

**Why they might stop.** The plan does not change until they delete and start over. There is no reminder, no “what did you do with the 30-day list,” and no way to type next month’s numbers. After the first read, the product is a document.

---

### 2. The one-goal planner

**Who they are.** The same account holder, on a day when the question is narrower: a named target, a rupee amount, and a horizon. The landing card says “Model a home, a sabbatical, or financial freedom against the reality of your cash flow.” The goal screen asks for a name, a target amount, and years from 1 to 40, then uses the profile’s monthly savings and risk (`frontend/src/pages/GoalsPage.jsx`, `services/goal_service.py`).

**Financial situation.** They already have a savings figure on the profile. They have a target in mind (the form’s own example is a house in five years). They do not enter current investments toward that goal. The calculator assumes the whole monthly savings can go to a new SIP.

**Goals.** Learn whether today’s savings can fund that target, what monthly SIP the math wants, and which named product the tier suggests.

**Problems.** A goal sentence on the profile is not a calculation. Chat’s starter “Goal Simulation” asks the model to judge feasibility without the calculator’s result. The two paths can disagree, and only one of them is arithmetic.

**Motivations.** “Make ambitious goals feel measurable.” The screen shows a large score, three scenarios, a required SIP, and a gap or surplus.

**Frustrations the product creates.**

- The score is labeled “Pilot AI Confidence Score.” The math does not call Groq.
- Balanced is badged Recommended in the interface even when the person’s risk choice is not medium.
- If coverage is missing, an infeasible scenario still draws the bar at 60%.
- The run lives in browser memory. A new tab, a cleared session, or sign-out drops it. The database does not keep goals.
- The profile goal (“retire at 55”) and the simulated goal are different inputs. The scorer still assumes retirement at 60.
- This screen has no advisory disclaimer.

**Technical comfort.** Same as persona 1. The calculator itself is a short form.

**Financial literacy the product assumes.** They can name a target amount and a year count. They can read “Required SIP” and “Assumed CAGR.” They may treat the Recommended badge and the confidence percentage as a judgment from an advisor. The product presents them that way.

**Why they would use FinPilot.** A concrete answer: this savings rate covers this much of this goal, at these assumed returns, in this product family.

**Why they might stop.** The answer is not saved, not compared with last month, and not tied back to the written advisory. A second goal means overwriting the only result on screen. Changing the savings figure means a new profile.

---

### 3. The cockpit visitor

**Who they are.** Someone the landing page recruits and the signed-in product does not fit. The page shows a live score of 82, “+8.4% this quarter,” a ₹40,000 surplus, and the line “Live financial picture.” The chart’s accessible name says the chart is illustrative. The initials AS, RN, and MK are decoration; the repository does not identify them as customers. Chat offers “Portfolio Analysis” as a one-click question: “Analyze my current financial situation and suggest how to improve my portfolio.”

**Financial situation.** They may already have funds, a demat account, or a quarterly statement. The product never asks. Chat receives age, income, expenses, savings, risk, and the goal sentence. It does not receive holdings, the health score, or the latest goal run.

**Goals.** Open something that already knows their money and shows whether it moved.

**Problems.** They want a picture of what they own. The product asks them to type a monthly budget.

**Motivations.** “Premium wealth pilot,” “Every signal. One calm place,” and “an AI chat that remembers the context.”

**Frustrations the product creates.**

- After sign-up they meet a form titled like onboarding, then an empty gauge.
- “Portfolio” in the chat has no portfolio behind it. The model can only talk about the typed fields and, if a report exists, whatever the person pastes into the chat.
- Quarterly change, live score, and notifications are promised or drawn, and are not features.
- Upgrade to Elite has no plan and no price.

**Technical comfort.** Often high enough to notice dead icons. A polished shell with buttons that do nothing reads as unfinished.

**Financial literacy the product assumes.** Higher than the data it collects. A portfolio question from a confident investor will be answered from a budget snapshot.

**Why they would use FinPilot.** The landing page is specific and calm, and it looks like a product they already want.

**Why they might stop.** The first real screen is a manual form. The first real score is a rule of thumb on that form, delivered only after an AI job. Nothing on screen is their portfolio.

This persona is a **recruiting mismatch**. They are likely to arrive. They are unlikely to be the person the scorer can help.

---

## Jobs to be done

These lines follow screens that exist. A job the product cannot finish is marked.

### Arrive

When I open the site,  
I want to see what I will get before I type my salary,  
so that I can decide whether an account is worth it.

The page shows a finished score of 82 and a ₹40,000 surplus. Those are written into `LoginPage.jsx`. The visitor’s own first screen is an empty dashboard.

### Create an account

When I decide to try it,  
I want an account that keeps this picture private to me,  
so that I can come back to the same plan.

Sign-up collects email and password and sets a 12-hour cookie. The password must be 12 characters; the form says so only after a rejection. There is no terms checkbox, privacy page, or email verification.

### Give the product a picture

When I have a rough monthly budget and a goal in mind,  
I want to enter them once,  
so that the rest of the app can talk about my numbers instead of a generic example.

The form requires age, income, expenses, savings, risk, and a goal sentence. EMI is optional. Success opens the dashboard. The goal sentence becomes the profile’s name.

### Judge the picture

When I have typed those numbers,  
I want a plain verdict on whether the picture is healthy,  
so that I know if the next step is an emergency fund, debt, tax, or a goal.

The verdict exists in `health_service.py` as soon as the profile is saved. The dashboard shows it only after an AI report job. Labels are Healthy at 70 or above, Moderate at 50 or above, otherwise At Risk.

### Get a plan

When the verdict is on screen,  
I want a written plan in ordinary language, with a 30-day list,  
so that I know what to do this month.

Generate queues a report. The model sees age, income, expenses, savings, risk, the goal sentence, the score, insights, and warnings. EMI is not its own line in that prompt. One report is stored per profile. Regenerate replaces it.

### Take the plan with me

When the write-up is something I want to reread or share,  
I want a file,  
so that I am not tied to this browser tab.

Advisory offers a PDF. The text can exist before the file does.

### Ask a follow-up

When the plan skips the question I actually have,  
I want to ask it without retyping my income,  
so that the answer stays about my snapshot.

Chat sends the profile fields and up to 20 recent messages. Starters are Portfolio Analysis, Tax Optimization, and Goal Simulation. The model does not see the score or the goal-calculator result unless those words are already in the chat.

### Test one goal

When I have a target amount and a year,  
I want to know if my current monthly savings can fund it,  
so that I can see the SIP, the gap, and a product family before I commit.

The calculator returns a 0–100 score, three SIP scenarios, and a primary and secondary instrument. The result is not stored in the database.

### Come back

When I return tomorrow or next month,  
I want the same plan, and a way to say what changed,  
so that the advice can move with my life.

Within 12 hours the cookie restores the account, and this tab can restore the last profile. Reports and chats remain in the database. Goal runs do not. The numbers cannot be updated in place.

### Correct a mistake

When I typed the wrong savings or the wrong EMI,  
I want to fix that field and see the score change,  
so that I do not throw away the plan.

This job is unfinished. There is no update route for a profile. Delete removes the profile, the report, and the chat, with no confirmation.

### Leave a shared computer

When I am done on a browser that is not only mine,  
I want to end the session,  
so that the next person does not see the snapshot.

Sign out bumps the session and returns to the landing page.

---

## Journey maps

### Monthly-snapshot saver

| Step | What happens |
| --- | --- |
| Persona | Monthly-snapshot saver |
| Situation | They can state a monthly salary, spend, savings, and a goal sentence. They do not have a spreadsheet they trust. |
| Trigger | Landing line “Less guesswork. More good decisions,” or the button “Start your financial map.” |
| Job | Judge this monthly picture and tell me what to do. |
| Workflow | Sign up → create profile → land on an empty dashboard → generate a report → read score, pillars, and the write-up → download the PDF → maybe ask one chat question. |
| Product interaction | Profile form, dashboard empty state, report poll, Advisory page, PDF, optional chat. |
| Outcome | One stored score, one stored advisory, one PDF. The 30-day list is text. The product does not track whether they did it. |
| Emotional response | Relief when the score and the warnings match their sense of the month. Doubt when the emergency-fund or 80C line describes money they were never asked about. Impatience if “Generating…” runs toward two minutes. |
| Reason to return | Reread the PDF or the chat. There is no new fact waiting for them. |

### One-goal planner

| Step | What happens |
| --- | --- |
| Persona | One-goal planner |
| Situation | A profile already has monthly savings. They have a target, such as a house, and a horizon. |
| Trigger | Dashboard shortcut “Goal Simulator,” or the landing promise to model a home, a sabbatical, or financial freedom. |
| Job | See if this savings rate can fund this amount. |
| Workflow | Open Goals → enter name, amount, years → Calculate → read the three SIP cards. |
| Product interaction | Goal form and scenario cards. The profile’s risk and savings are inputs they do not retype. |
| Outcome | A feasibility percentage, a required SIP, a gap or surplus, and a product name such as a Nifty 50 SIP or a recurring deposit. The outcome stays in browser memory. |
| Emotional response | Clarity when the gap is a number they can compare with their savings. Mistrust when the screen calls that formula an AI confidence score, or when Balanced is Recommended against their own risk choice. |
| Reason to return | Run a second target. The first result will not be there next time unless the tab still holds it. |

### Cockpit visitor

| Step | What happens |
| --- | --- |
| Persona | Cockpit visitor |
| Situation | They expect a live view of money they already have. The hero shows 82 and a quarterly rise. |
| Trigger | “Create your free account,” or “Explore your dashboard.” |
| Job | See my real picture and whether it moved. |
| Workflow | Sign up → profile form that asks for a monthly budget → empty gauge → optional chat starter “Portfolio Analysis.” |
| Product interaction | Landing hero, then the same form and empty dashboard as everyone else. Chat answers from the typed fields. |
| Outcome | A budget snapshot wearing a wealth-cockpit frame. No holdings, no quarterly delta, no notification. |
| Emotional response | The landing page feels finished. The first signed-in screen feels like a different product. Dead search, bell, settings, and Elite reinforce that. |
| Reason to return | Weak. The thing they came for is not in the product. |

---

## Activation

The first **meaningful** value moment is the first time a report exists for their own numbers: the gauge, the seven pillars, the warning sentences, and the written advisory on the Advisory page.

That moment is later than it needs to be. Annual savings and monthly surplus can appear from the profile alone. The score can be computed at save time. The product withholds the score until the AI job finishes, and it tells the person that generating the report is what unlocks it.

A second activation path exists and is easy to miss. Once a profile is selected, Goals and Chat are unlocked. A person can get a SIP result, or a chat reply, without ever generating a report. The empty dashboard still points at the report as the first act.

Activation fails when:

- the worker is down and the wait ends in “took too long”
- the person cannot state monthly savings separately from expenses and abandons the form
- the cockpit visitor realizes the form is not their portfolio and leaves before generate

`UNKNOWN`: how many people who sign up reach a successful report. Nothing in the repo measures that.

---

## Retention

### Tomorrow

The only built-in reason is unfinished curiosity: the report was still generating, the PDF was not downloaded, or a chat question is still open. The cookie lasts 12 hours, so a same-browser return can skip the password. The numbers have not changed. Goal results may already be gone.

### Next week

The session has expired. They sign in with the password they chose; there is no reset if they forgot it. The report and the chat are still there. The product has no prompt to revisit the 30-day list, no “you have not opened this since,” and no notification. Coming back is an act of memory.

### Next month

Their salary, EMI, or savings may have changed. The product cannot record that change without a new profile, which discards the plan they would be comparing against. A monthly check-in has no object. The honest retention story at 30 days is: reread a static PDF, or start over.

---

## Habit

FinPilot does not contain a natural recurring loop.

A habit would need a repeating reason: new numbers, a tracked action, a result, and a better next suggestion. The current chain ends at the suggestion.

| Piece | What the product does with it |
| --- | --- |
| Input | Typed once. No edit. |
| Analysis | Score and advisory stored once per profile. Regenerate replaces them. |
| Recommendation | The 30-day list and the SIP cards are text. |
| Action | Not recorded. |
| Result | Not recorded. |
| Updated data | Requires delete and recreate. |
| Better recommendation | The model sees the same snapshot. |

Chat can be opened again. Each new question still rests on the original fields. That is a conversation, not a habit tied to their money changing.

The goal calculator can be run again. Each run replaces the only result on screen and is not kept. That is a repeated tool use, not a loop the product closes.

The closest gesture toward a habit is the advisory’s 30-day plan. The app never asks, a month later, whether they did it.

---

## Churn

Places a person is likely to leave, in the order they meet them:

1. **Landing versus first screen.** They came for a live 82. They get a form.
2. **Password rule and missing trust pages.** A 12-character rejection after submit, with no privacy or terms page to read before typing income.
3. **The empty dashboard.** An empty gauge and a generate button, before any verdict on the numbers they just typed.
4. **The wait.** Up to about two minutes, then a failure if the worker or Groq is unavailable. They cannot see that dependency.
5. **A score that describes money they do not have.** Emergency cover computed from one month of savings, tax language about 80C they did not declare, retirement at 60 when they wrote 55.
6. **Advice they cannot check.** The model names products and percentages with no source. A cautious reader hits the SEBI line and has no way to verify the paragraph.
7. **A wrong number.** The repair is delete, without a confirm step. Some people will delete by mistake. Others will refuse to delete and then stop, because the plan is stuck on the bad figure.
8. **The goal label.** “AI confidence” and a permanent Recommended badge on Balanced. A numerate user who checks the assumptions may not trust the rest.
9. **The day after.** Nothing asks them back. The 30-day list lives in a PDF.
10. **The forgotten password.** No reset. The account, the report, and the chat become unreachable.
11. **A quota or an operator error.** “Try again in N seconds,” “port 5000,” or “check your API key.” The allowance is not explained up front.

Delete-without-confirm is also a trust churn: the plan and the conversation disappear in one tap.

---

## Product-market signals

These are judgments about fit between an implemented behavior and a concrete user problem. They are not usage evidence. Frequency in the market is `UNKNOWN`.

| Implemented behavior | Concrete problem it touches | How close | Why it does not yet recur |
| --- | --- | --- | --- |
| Rule-based score and pillar warnings | “Is this monthly picture okay?” | Closest durable match. The rules are specific: 30% savings, 6 months emergency, 20% DTI, 80C, retirement at 60. | Shown only after the AI job. Cannot be refreshed when the month changes. Assumptions are easy to misread as facts about a corpus the person never entered. |
| Written advisory with a fixed outline and a 30-day list | “What should I do next, in my numbers?” | Strong one-time match. This is the artifact the dashboard points at. | One version. No follow-through. EMI is a weak input to the model. |
| Goal SIP calculator | “Can this savings rate fund this target?” | Strong match for a single decision. The inputs are exactly the ones a person has on the day they ask. | Not saved. Branded as AI. Second goal overwrites the first. No progress against the target next month. |
| Chat on the saved snapshot | “One more question, without retyping.” | Useful immediately after the report. | The starters (portfolio, tax, goal feasibility) ask for facts the chat does not have. Quotas and the wait make a casual second question expensive. |
| PDF | “Let me keep this.” | Supports the one-time job. | A file does not bring them back into the product. |
| Several profiles on one account | “More than one picture.” | Weak. The screen never says whether the second row is a spouse, a scenario, or a correction. | Easy to create, dangerous to delete, unclear to use. |
| Landing page | “Should I sign up?” | Strong as persuasion. | The promised live picture is the problem the signed-in app does not solve. |

The product is closest to a **one-sitting second opinion** for a person who can type a monthly Indian household snapshot and wants a score, a plan, and a single goal check.

It is far from a **recurring financial product**. The problems that recur in that person’s life — next month’s salary, an EMI that changed, a goal that moved, a 30-day action they did or skipped — have no implemented loop.

The cockpit visitor’s problem, “what do I own and did it move,” is the problem the marketing speaks to and the implementation does not attempt.

---

## Unknowns

- Whether real sign-ups match the form’s ₹1.5 lakh example, or include students, self-employed people, or households. The product does not ask.
- Whether a second profile is used as another person or as another scenario.
- How often the worker is actually up when a new person clicks Generate.
- Whether anyone returns after the 12-hour cookie. No analytics SDK was found.
- Legal fitness of the SEBI sentence and the missing terms. That remains a legal question, as in the 360 audit.
