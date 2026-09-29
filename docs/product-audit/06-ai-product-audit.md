# FinPilot AI — AI product audit

**Date:** 2026-09-29  
**Source:** `services/ai_service.py`, `services/jobs/worker.py`, `routes/report_routes.py`, `routes/chat_routes.py`, `services/health_service.py`, `services/goal_service.py`, `services/pdf_service.py`, `database/repository.py`, and the Advisory, Chat, and Goals screens.  
**Related:** `docs/product-audit/01-product-360-audit.md` (section 6). This pass re-read the prompts and the worker.

Application code was not changed. No live Groq responses were sampled for this document. Behavior of the model’s wording on a given profile is `UNKNOWN` beyond what the prompt asks for.

---

## What counts as AI here

Two calls hit Groq. Both go through `ask_gpt` in `services/ai_service.py`: one system message (`SYSTEM_PROMPT`) and one user message. There is no tool list, no function call, and no retrieval step.

| Capability | Calls the model | Where |
| --- | --- | --- |
| Written advisory | Yes | `generate_financial_report` → worker `_run_report` |
| Advisor chat | Yes | `chat_with_advisor` → worker `_run_chat` |
| Health score | No | `health_service.calculate_health_score` |
| Goal simulator | No | `goal_service` SIP math |
| Landing score of 82 | No | Static copy in `LoginPage.jsx` |

The goal screen labels its formula “Pilot AI Confidence Score.” That label is a presentation choice. The request never reaches Groq.

Defaults from `config.py`: report model `openai/gpt-oss-120b`, chat model `openai/gpt-oss-20b`, temperature `0.7`, report budget 4096 tokens, chat budget 1500 tokens, provider timeout 90 seconds. A worker must be running (`python -m services.jobs.worker`). The web request only queues a job and returns 202.

---

## The ten questions

### 1. What AI capabilities exist?

A structured advisory essay for one profile, and a follow-up chat about that same profile. Both are text in, text out. The essay is stored as `reports.ai_report`. The chat is stored as rows in `chat_history`.

### 2. What user problem does each one solve?

The advisory answers “what should I do with this monthly picture?” The prompt demands a summary, a budget section, an allocation with percentages, risks, a goal strategy, and five steps for the next 30 days.

The chat answers “one more question, without retyping my income.” Starter chips send portfolio, tax, and goal-feasibility questions. The model only has the fields listed below, plus recent turns.

### 3. What context is supplied?

**Both calls** receive the system persona: a professional personal financial advisor for Indian personal finance, told to sound like a real advisor, to be practical, and to use examples such as SIP, index funds, FD, and an emergency fund.

**The report prompt** adds age, monthly income, monthly expenses, monthly savings, risk appetite, the goal sentence, the health score out of 100, the insight sentences, and the warning sentences. It does not add EMI as its own line, pillar point breakdowns, holdings, or the goal calculator’s result.

**The chat prompt** adds the same six profile fields, a flattened recent transcript, and the new question. It does not add the score, the insights, the warnings, EMI, the stored advisory, or the goal run.

Debt can still appear inside a report, because a warning sentence may mention DTI. That sentence is glued into the report prompt. Chat never sees it unless the person types it.

### 4. What data is missing?

For both calls: bank transactions, holdings, city, dependents, tax regime, insurance, an emergency corpus separate from this month’s savings, and any earlier version of the profile. EMI is a column on the profile and is omitted as a field. The goal simulator’s SIP, gap, and product names are not passed in. Prior reports are replaced, not sent. `generated_at` is stored and not given to the model.

Chat also misses the score and the written plan. A question about “my report” or “that SIP number” is answered from the six fields and whatever the transcript already contains.

### 5. What tools can the AI access?

None. `client.chat.completions.create` is called with `model`, `temperature`, `max_tokens`, and `messages` only. A search of the Python tree found no `tools`, function-calling, or embedding path.

The health score and the goal formula run in the worker or the request **before or instead of** the model. The model cannot invoke them, and it cannot see the goal result unless a person pastes it into chat.

### 6. What actions can the AI perform?

It can return a string. The worker then saves that string. For a report, text is saved first; a PDF is built from the text plus the health block; PDF failure still marks the job succeeded. For chat, the user line and the model line are inserted after a successful reply.

The model cannot edit the profile, enqueue another job, change a goal, send email, or place a transaction. “30-day action plan” is sentences, not tasks in the product.

### 7. What information does it return?

An unstructured string. The report prompt asks for six markdown headings. Nothing parses those headings into fields, and a response that ignores the outline is still saved if Groq returned text. Chat has no required shape. A reply cut off because of length (`finish_reason=length`) is logged and still returned as success.

The stub path (`GROQ_STUB`) returns the fixed sentence “Stubbed advisory. Groq was not called.” That path is for tests and local stubs, not the customer default.

### 8. How is output presented?

Advisory section “05. AI Advisory” renders the markdown under “Strategic Recommendations” (`AdvisoryPage.jsx`, `MarkdownRenderer`). Sections 01–04 are the rule score, cash-flow bars, pillars, and the insight and warning strings. Those are not the model’s words. The PDF puts rule-based “Risk Considerations” on one page and “Advisory Recommendations” after a page break (`pdf_service.py`).

Chat renders each `role=ai` row as markdown beside a robot icon. The person’s lines stay plain text.

The goal percentage is presented as an AI confidence score and is not model output.

### 9. How is conversation state maintained?

`chat_history` stores `role` (`user` or `ai`) and `message` for the profile. The worker loads the latest 20 rows (`load_chat_history(..., limit=20)`) **before** saving the new turn, then `format_conversation_context` keeps those rows inside an 8,000-character budget, newest first until the budget fills. The UI fetch uses a limit of 100, so the screen can show a longer thread than the model rereads.

That transcript is pasted into the single user message as `role: text` lines. The API is not a multi-turn `messages` array. Older turns drop out. Clearing chat deletes the rows. Deleting the profile deletes them by cascade. A new report does not enter the transcript.

Report state is one row per profile. Regenerate overwrites `ai_report` and `health_json`. There is no thread of reports.

### 10. How are errors handled?

`ask_gpt` maps a timeout to `upstream_timeout`, a Groq rate limit to `upstream_rate_limit`, and other provider failures to `upstream_error`. The worker marks the job failed with that code and does not save a partial advisory. A failed report leaves the previous row in place. The client toast says the previous report is unchanged, or that generation took too long (including a lost worker). Chat removes the optimistic bubble and toasts. Polling stops around 120 seconds.

Separate from the provider: the account and the profile have request quotas before a job is queued. A full queue or a down worker looks like a long wait, then a timeout. The model’s own mistakes are not an error path. There is no checker on percentages, product names, or invented holdings.

---

## What kind of AI this is

The useful description is a **decision-support writer with a chatbot beside it**. The other labels fit only in pieces.

**Decision-support system.** This is the closest fit for the advisory, and only for one snapshot. The product calculates a score and warnings with rules, shows them as their own sections, then asks the model to interpret that packet in a fixed outline. The person can read the number and the prose apart. That is support for a decision, not a decision the software executes. It is thin support: the interpretation is not tied back to a field, uncertainty is not marked, and the person cannot correct the inputs without deleting the profile.

**Advisor.** This is the persona, not the control loop. `SYSTEM_PROMPT` says “professional personal financial advisor” and “Sound like a real financial advisor.” The report outline is the shape of an advice memo. The product also says it is not a SEBI-registered advisor, on the advisory footer and in the PDF. The model is not told to refuse when data is missing, to label an estimate, or to avoid naming a product it cannot source. The voice and the disclaimer pull in different directions. Calling the feature an advisor describes the prompt. It does not describe a reviewed advice process.

**Chatbot.** This is the accurate label for chat. A question goes in, a paragraph comes out, recent turns are stuffed into the next prompt, and nothing in the product changes except the transcript. Starter chips make it look guided. They still send free text. The model cannot open the goal calculator when the chip says “Goal Simulation.”

**Assistant.** Only in the narrow sense that the profile is already in the prompt, so the person does not retype income. An assistant that could update the snapshot, rerun the score, or fetch the last goal result is not what this call does.

**Copilot.** A copilot works on an artifact the person is editing. Here the artifact is generated once and replaced wholesale. Chat does not revise the stored report. The profile form is not an AI surface.

**Agent.** An agent chooses tools and takes actions across steps. This model has no tools. The worker is a queue consumer: claim a job, call Groq, save text. The job runner is not an agent, and the model cannot plan a second call. `groq/compound` is mentioned in a planning note as unused.

---

## Context

| Memory | In the report prompt | In the chat prompt | Stored, unused by the model |
| --- | --- | --- | --- |
| Profile: age, income, expenses, savings, risk, goal sentence | Yes | Yes | — |
| EMI | Only if a warning sentence mentions debt | No | Column on `users` |
| Health score and the insight / warning sentences | Yes | No | `reports.health_json` |
| Pillar points | No | No | Inside `health_json` |
| Previous conversations | No | Last 20 messages, cut at 8,000 characters | Up to the full table; the screen loads 100 |
| Generated report | The model is writing it | No | `reports.ai_report` until regenerate |
| Goal simulation | No | No | Browser memory only |
| Older profiles, older scores, dates | No | No | `generated_at` exists and is not in the prompt |

The model understands the profile as six lines of text copied at call time. It does not understand a financial history. After the 20-message or 8,000-character window, it does not understand the older conversation either.

---

## Personalization

Personalization is the prompt instruction “Always give personalized advice” plus those six fields and, for the report, the score and the rule sentences. Risk is the word `low`, `medium`, or `high`. The goal is whatever sentence the person typed.

The same outline is required for every profile. Allocation percentages are requested “if possible,” with no catalog and no house limits in the prompt. Two people with the same numbers should receive similar structure. Wording will vary because temperature is 0.7. Nothing in the product adapts the outline to age band, debt, or whether a goal amount exists.

Chat is personalized to the same six fields and to whatever was said in the recent window. It is not personalized to the plan they just read unless they quote it.

---

## Explainability

The person can see **why the score moved** only by reading the insight and warning sentences, which come from the rules, not from the model. Pillar maxima are visible in the UI (25, 20, 20, 15, 10, 5, 5). The assumptions behind emergency months and 80C are in `health_service.py` and are not printed beside the gauge.

The person cannot see **why a model sentence was written**. There is no citation to a field, no “this percentage is from your savings rate,” and no display of the prompt. The section split (01–04 calculated, 05 model) is the only structural explanation. The PDF split does the same job on paper.

Goal CAGR is shown on the scenario card as “Assumed CAGR.” That number is explainable because it is not AI. The screen still titles the result as AI confidence, which removes the explanation the formula could have given.

---

## Reliability

When the provider fails, the product is careful: the old report stays, the job is marked failed, and the toast says so.

When the model is fluent and wrong, the product saves the text. Nothing checks that a recommended percent sums to 100, that a named fund exists, or that a SIP in the essay matches `goal_service`. The prompt asks for percentages and Indian product examples and to sound like an advisor. Truncation is a warning in the server log, not a label in the UI.

The person’s recourse is the one-line disclaimer, the chat line “FinPilot AI can make mistakes,” regenerate (which discards the previous essay), or leaving the paragraph unread. There is no edit of a sentence, no second model, and no human review queue.

A stub or a test double can store “Stubbed advisory. Groq was not called.” if that mode is on. Production depends on `GROQ_STUB` being off. That flag is not a customer control.

---

## Trust in the interface

| Kind of content | How the UI treats it |
| --- | --- |
| User data | Profile fields. The advisory subtitle repeats the goal sentence. Chat does not show the numbers it was given |
| Calculated values | Dashboard gauge, pillars, insight and warning cards, Advisory sections 01–04, goal SIP math |
| AI interpretation | Section 05 and chat bubbles |
| Uncertainty | Not marked on model sentences. The score labels are Healthy / Moderate / At Risk, which read as judgments. The goal figure is a large percent called confidence |

The advisory page is the one place that separates calculation from interpretation. Chat does not. Goals mixes a calculation with an AI name. The landing page shows a score with no separation at all, because the score is not computed.

The system prompt’s “sound like a real financial advisor” is stronger than the 10px disclaimer under the essay. A reader who trusts the voice gets no per-sentence uncertainty.

---

## AI workflow

```text
User intent
  Dashboard or Advisory: "Write the plan"
  Chat: a typed question or a starter chip
→ Context retrieval
  Worker loads the profile for this account
  Report: health_service runs, then the prompt is built from six fields + score + insight/warning strings
  Chat: last 20 messages are flattened under an 8,000-character cap; the new question is appended
  Goal math is not retrieved
→ Calculation / tools
  Health score runs in code for a report
  Goal formula runs only if the person used the Goals screen, and its output is not a tool result
  The model has no tools
→ AI reasoning
  One Groq completion, temperature 0.7
  Report model and chat model can differ
→ Response
  String saved to reports.ai_report or chat_history
  PDF built from the string plus the health block; PDF failure keeps the string
→ User action
  Read, download, ask in chat, regenerate, or clear chat
  Nothing records that a 30-day step was done
→ Feedback
  No rating, no correction, no edited sentence
  The next call sees the same profile
  Chat sees the new turn until the window drops it
```

The loop stops at the response. Regenerate is a new essay on the same snapshot, not a revision based on what the person did.

---

## Opportunities

These are product directions that follow from the current calls. They are not implemented.

**Put the calculated context into the chat prompt.** The score, the warning lines, EMI, and the latest goal result are already computed or sitting in the browser. Chat that cannot see them will invent a second opinion. Passing them in is still a prompt change, not an agent.

**Let “Goal Simulation” call `goal_service`.** The chip asks the model to judge feasibility. The calculator already returns a SIP, a gap, and a named product under stated CAGR assumptions. A workflow would run the formula, then ask the model only to explain that result. That is the first real tool use. It is also the difference between a chatbot and decision support.

**Keep the essay attached to the numbers that produced it.** Show the profile date on the report. If the numbers later change, mark section 05 as older than the score. Today regenerate is the only refresh, and it throws the previous text away.

**Make uncertainty and provenance visible on section 05.** One line per recommendation: which field it used, and that the percentage was written by the model. The rules side already has this in spirit (the warning sentences name the ratio). The model side does not. Saving a truncated completion should say the plan was cut off.

**Turn the 30-day list into the next workflow.** The outline already asks for five steps. The product could keep those steps as the thing the person checks on a return visit, then include “done / not done” in the next prompt. That is the missing feedback edge. It requires storing the steps, which the current free-text column does not do.

**Stop asking the model to sound like a registered advisor.** The disclaimer says the opposite. A prompt that says the writer is explaining a score, must not invent holdings, and must say when EMI or a goal amount was not provided, matches the data the call actually has.

The smallest deepening of the current AI is: one report that interprets the score, and a chat that can see that score and the goal formula’s output. Tools, memory of actions, and a revision loop are how it would stop being only a conversation.
