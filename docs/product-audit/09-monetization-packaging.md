# FinPilot AI — monetization and packaging

**Date:** 2026-09-29  
**Method:** What the signed-in product can deliver, and what the codebase spends to deliver it. No price list, conversion rate, or willingness to pay was found. Groq’s price per token is `UNKNOWN` from this repository.  
**This is not a pricing recommendation.** It separates units the product can already meter from packages that would require a different product.

The landing page says “Create your free account.” The sidebar has “Upgrade to Elite” with no plan, price, or checkout. No billing provider was found. Those two strings are not a business model.

Application code was not changed.

---

## Value the product provides today

One person can type a monthly Indian household snapshot and, in the same sitting, receive:

- a rule-of-thumb score and seven pillar notes
- one written plan, stored, with a PDF
- a chat that answers from that snapshot
- one SIP check against a target, using fixed return tiers, kept only in the browser

That is a **one-time second opinion** on numbers they already know. It does not watch a bank account, update itself next month, or record whether they followed the 30-day list. Return value is “the essay is still there,” not a new financial result.

Anything sold as a subscription has to survive that fact. People pay repeatedly for something that changes or that they use again. This product’s expensive step happens once per profile unless they regenerate.

---

## Units that match real capabilities

| Unit | Exists as a thing a person receives | Already metered in code | Natural cost |
| --- | --- | --- | --- |
| Account | Yes | Signup row | Low. A hash and a session |
| Profile / snapshot | Yes | Row in `users` | Low. A few numbers |
| Score | Yes, after a report job | Inside `reports.health_json` | Negligible CPU. No model |
| Written report | Yes, one stored per profile | `jobs` of kind `report`, quotas on enqueue | The large model call, then a PDF |
| Chat reply | Yes | `jobs` of kind `chat`, quotas | The smaller model call |
| Goal run | Yes, on screen | Quota on `POST /api/goal-plan`. Result not stored | CPU only. No Groq |
| PDF file | Yes | `pdf_path`, rebuild quota | Local CPU and one file on disk |
| Extra profile | Yes, unnamed | Another `users` row | Another report if they generate one |
| Household / advisor seat | No | API keys are an operator script, not a customer console | Would be a new product |

Abuse caps are not packages. Defaults in `config.py`: report enqueue 5 per minute per key and 10 per hour per profile; chat 15 per minute and 60 per hour per profile; goal 20 per minute and 60 per hour per profile; PDF rebuild 5 per minute. A person never sees an allowance. Hitting the cap is an error, not an upgrade screen.

---

## Packaging models

Usage frequency below is the role in the journey, not a measured rate. Measured frequency is `UNKNOWN`.

### Free, as the product is now

**Customer value.** The whole current job: snapshot, score, one plan, chat, one goal check.  
**Usage frequency.** Once, then rare rereads.  
**Cost to serve.** One large completion and a handful of smaller ones per active profile, plus a PDF and a few rows. Idle accounts cost almost nothing.  
**Differentiation.** None inside the product. There is no second tier.  
**Upgrade trigger.** The Elite button, which does not lead anywhere.  
**Retention potential.** Weak. The plan does not change.  
**Product complexity.** Lowest. It is what already ships. Calling it “free” in the headline is accurate only while Groq and the worker are paid by the operator.

### Subscription (Pro), sold as access

**Customer value.** Would have to be “I come back and the picture is still worth opening.” The stored PDF already does that at no extra model cost.  
**Usage frequency.** The product does not create a weekly reason. A subscription would bill a habit the loop does not support.  
**Cost to serve.** Predictable revenue, uneven cost: heavy users regenerate and chat; most users, if the journey holds, cost one report.  
**Differentiation.** A login wall already exists. A paid wall on the same screens does not add a capability.  
**Upgrade trigger.** Unclear, unless the paid tier adds edit, history, or saved goals.  
**Retention potential.** Churn follows the missing monthly loop. People cancel when the essay is stale and cannot be updated in place.  
**Product complexity.** Medium if the tier is only a flag. High if the flag is honest and the product grows a recurring job.

### Usage-based, per report

**Customer value.** The artifact they came for. Easy to understand: one plan, one charge.  
**Usage frequency.** Low per person. High if failure and regenerate are each billed.  
**Cost to serve.** Aligns with the expensive call. Report model default `openai/gpt-oss-120b`, up to 4096 output tokens, timeout 90 seconds. One active report job per profile.  
**Differentiation.** The score and the form stay outside the meter. The essay is the meter.  
**Upgrade trigger.** A second plan, a regenerate after they change numbers, or a longer essay. Weak until they can edit the snapshot. Regenerating the same numbers is a poor thing to charge for.  
**Retention potential.** They return only when they want another document. That matches current behavior better than a monthly fee.  
**Product complexity.** Low to meter (`jobs` already counts succeeded reports). Medium to explain failures so a timeout is not a charge.

### Usage-based, per AI call (report and chat together)

**Customer value.** “Help writing and answering.” Chat is the open-ended part.  
**Usage frequency.** Chat can be repeated. The starters invite more questions than the data can answer.  
**Cost to serve.** Chat default `openai/gpt-oss-20b`, up to 1500 tokens, plus up to 20 prior messages in the prompt. Cheaper per call than a report, easier to run up.  
**Differentiation.** Splits “the plan” from “more questions.”  
**Upgrade trigger.** The free essay is done and they still have questions. Legitimate if the chat can see the score and the goal result. Weak if it cannot, because they are paying to hear a thinner answer.  
**Retention potential.** A conversation can last an evening and then stop. It does not, by itself, bring them back next month.  
**Product complexity.** Medium. Need a visible balance, a distinction between a failed job and a billed job, and no billing of the question text into an analytics tool.

### Premium / Elite, as the button implies

**Customer value.** Unknown. The button does not say what Elite is.  
**Usage frequency.** None. The control has no handler.  
**Cost to serve.** Zero, because nothing is delivered.  
**Differentiation.** A gold button under the email.  
**Upgrade trigger.** Curiosity, then distrust when nothing happens.  
**Retention potential.** Negative. A dead upgrade teaches that the product is unfinished.  
**Product complexity.** High if Elite is invented as “more wealth.” The app has no holdings, no market feed, and no second score. Shipping a price on that button without a new capability is the artificial limit to avoid.

### Advanced planning (saved goals, scenarios, later comparison)

**Customer value.** The calculator is already the clearest numeric answer in the product. Saving runs and comparing them would be a planning tool, not a chat.  
**Usage frequency.** Occasional, and it could become the reason to return if a second run is kept.  
**Cost to serve.** Low. `goal_service` does not call Groq. Storage is a small row the database does not have yet.  
**Differentiation.** Strong against the free one-off screen, weak against a spreadsheet, unless it stays tied to their saved snapshot.  
**Upgrade trigger.** “Keep this goal and check it again.” That is a real reason. Paywalling the first calculation is a weak one, because the first run is cheap and is how they learn the product.  
**Retention potential.** Better than the essay, if the result survives the session.  
**Product complexity.** Medium. A goals table, a disclaimer, and honest labels. Not a new model.

### Family or shared finance

**Customer value.** Several profiles can already sit on one account. The screen does not say whether the second row is a spouse, a scenario, or a correction.  
**Usage frequency.** Unknown. Easy to create, dangerous to delete.  
**Cost to serve.** Linear in profiles that generate reports. The cost is the extra Groq call, not the extra form.  
**Differentiation.** A household plan is a different job from “delete and retype.” It is not implemented.  
**Upgrade trigger.** Would be “add a named person and see both pictures.” Charging for a second unnamed profile today would tax a confused control.  
**Retention potential.** Households can be sticky. This product has no shared login, no permissions, and no combined view.  
**Product complexity.** High. Names, roles, and a reason for the second profile. Until then, extra profiles are not a family plan.

### Advisory features (deeper than the current essay)

**Customer value.** The essay and the chat already claim an advisor voice. A paid advisory layer would need something the free essay does not do: a sourced allocation, a human review, or a plan that updates.  
**Usage frequency.** The current advisory is once per profile.  
**Cost to serve.** Another large completion, or a person’s time if a human is involved. Human review is not in the product.  
**Differentiation.** The free tier already says “AI Advisory Report.” Charging the same sections under a new name is the same artifact.  
**Upgrade trigger.** Legitimate if the paid output cites the fields, keeps old versions, and is marked when the numbers change. Not legitimate if it is only a longer temperature-0.7 essay.  
**Retention potential.** Follows whether they can act and return. The 30-day list is text.  
**Product complexity.** High. Trust work from the safety audit (assumptions, disclaimer, provenance) belongs in the base experience, not behind a fee.

### B2B or B2B2C

**Customer value.** A scoped API key can be issued with `scripts/issue_api_credential.py`. It is not offered in the React app. There is no advisor console, no organization, and no white-label report.  
**Usage frequency.** Not a customer journey.  
**Cost to serve.** The same report and chat jobs, plus support for someone else’s clients.  
**Differentiation.** The API is an operator tool. A firm would need tenant isolation, their own disclaimer, and a reason to embed a typed snapshot instead of their existing planning software.  
**Upgrade trigger.** None on the current site.  
**Retention potential.** Depends on a buyer the product does not address.  
**Product complexity.** High. Do not describe the existing key script as a B2B product.

---

## What could stay free, what could be paid, what should not be sold

### A free experience that still has a point

- Create an account and one profile  
- See the rule score and the pillar notes as soon as the profile is saved, without a model call  
- Run the goal calculator at least once and read the assumptions  
- Generate **one** written plan and its PDF  
- A short chat about that plan, with the score included in the prompt  
- Sign out, come back, and read what was saved  
- Export and delete their data, reset a password, and read the disclaimer  

The free score matters because it is the first verdict and it costs almost nothing. Hiding it behind the paid model repeats the current empty gauge and makes the paid step feel like a ransom for a number the rules already computed.

### A paid experience that matches cost and a new capability

Pick from capabilities that are either expensive or not built yet. Do not stack all of them into Elite.

- Further **report regenerations** after the numbers change, not after an identical click  
- **More chat** once the first questions are included  
- **Saved goal runs** and a second check against the same target  
- **Named extra profiles** only after the product defines what a second profile is  
- **Older versions** of the essay kept when they regenerate  

A faster queue or the larger model for every chat is an operator lever, not a story a household will understand. Lead with the artifact, not the model name.

### What should not be paywalled

- The score and the statement of how it was estimated  
- The disclaimer, and the sentence that says what is sent to the model  
- Reading a plan they already generated  
- Download of that plan’s PDF  
- Correcting their own numbers  
- Account deletion, export, and password reset  
- Seeing why a job failed  

Charging to fix a wrong salary, or to hear that the emergency-fund line is an estimate, sells the trust gap.

### Artificial limitations to avoid

- A cap that blocks the first score  
- Billing a failed or truncated generation the same as a finished plan  
- Billing every regenerate while regenerate is the only repair  
- A family price on unnamed duplicate profiles  
- A Premium label on the same six-section essay  
- Quotas that appear as “too many requests” with no stated allowance and no upgrade path  
- Putting “Upgrade to Elite” back on screen before a tier exists  

### A legitimate upgrade reason

The person already has a verdict and one plan. They pay when the next unit is a **new result they can keep**: another plan after their numbers change, a goal they can reopen next month, or a household member with a name. They do not pay to unlock the judgment of the numbers they just typed.

---

## Cost to serve, from the codebase

Prices are not in the repo. The cost drivers are.

| Driver | What the code does | Economic shape |
| --- | --- | --- |
| LLM, report | Groq chat completion, default `openai/gpt-oss-120b`, temperature 0.7, max 4096 tokens, 90 second timeout. Prompt includes the profile, the score, and the insight and warning strings | Dominates cost per activated profile. One succeeded job per profile unless they regenerate. Failures still consume a call before the job is marked failed |
| LLM, chat | Default `openai/gpt-oss-20b`, max 1500 tokens, up to 20 messages / 8,000 characters of history pasted into the prompt | Smaller per reply, unbounded if chat is unlimited. History grows the prompt |
| PDF | Built in-process after the text is saved. File under `PDF_STORAGE_DIR` (default `data/pdfs`), one `profile_<id>.pdf` per profile. Rebuild if the file is missing, capped at 5 per minute | Cheap next to the report call. Disk grows by one file per profile, replaced on rebuild |
| Database | PostgreSQL. One report row per profile (upsert). Chat rows accumulate. Jobs accumulate, including failures. Rate-limit counters live in a **second** database (`finpilot_ratelimit`) | Small rows. Chat and jobs are the tables that grow with use. No retention job was found for old jobs or old chat |
| Background jobs | A separate worker process. Default one claim thread. Report and chat both wait on it. A dead worker fails the job after `WORKER_TIMEOUT_SECONDS` (120) | The worker is required for the paid artifact. Capacity is a host limit, not a per-user plan. Extra OS worker processes were the wrong scale lever in earlier capacity work |
| Other external APIs | None for market data, email, or payments. Goal CAGR tiers are constants | No data-vendor bill. Also no email for a paywall receipt or a password reset |

The score and the goal formula can be offered widely without tracking a model bill. The report cannot. A free tier that includes unlimited regenerate on the large model is the configuration most likely to cost more than the account is worth. A free tier that includes one succeeded report, and treats timeouts as not consumed, matches the way `jobs` already records status.

Chat should be bounded in the product the person can see, using the same `jobs` rows, not only by the silent hourly cap. The hourly cap is an abuse control. It is a poor receipt.

---

## Implication

FinPilot can be given away as a single plan plus a score, because that is the whole product and the marginal cost is one large completion per profile. It can meter **additional** plans and **additional** chats, because those are the calls that repeat. It should not be sold as a family suite, a wealth tier, or a monthly advisor until those products exist.

Elite, on the current sidebar, is not one of those units. It is a button.
