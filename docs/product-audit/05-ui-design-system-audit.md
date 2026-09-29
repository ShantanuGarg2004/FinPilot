# FinPilot AI — visual and UI audit

**Date:** 2026-09-29  
**Inspected:** `frontend/tailwind.config.js`, `frontend/src/index.css`, `frontend/src/landing.css`, `frontend/index.html`, shared components, and the page layouts that consume them.  
**Token catalog:** `docs/product-audit/design-system.md`.

Application code was not changed. Breakpoint behavior below is what the classes and media queries specify. A device lab pass was not run, so real-device overflow is `UNKNOWN` beyond what those rules do.

The product already has an implicit system. It is a dark emerald finance UI, with a second gold editorial system on the landing page. The tokens are broader than the UI that uses them. The screens then bypass the tokens with one-off sizes and hex colors.

---

## Visual hierarchy

**Whitespace.** The signed-in pages are loose on purpose: `space-y-xl` (32px) between dashboard bands, `p-lg` inside glass, a max width of 1180px. Advisory is a single 840px column. That reads as calm on a desktop window. The landing page is much airier (section padding above 130px) and visually a different product.

**Density.** Inside the cards, type drops to 11–13px. A dashboard tile has an 18px number and a 12px caption. Chat, insights, and scenario rows are a small-type layer on a large-type frame. The result is a spacious page that still asks the eye to read captions.

**Grouping.** Glass panels and `rounded-xl` sections group the dashboard and the profile form. Goal results mix `StatCard` (glass, 12px radius, shadow) with flat `rounded-lg` scenario cards, so the answer does not sit in one container family. Quick Actions are a second button style inside a glass panel.

**Alignment.** Labels are uppercase and left-aligned. The goal score and the empty goal prompt are centered. Gauges are centered in their cell and left-aligned in the dashboard row from `lg` up. Rupee figures do not share a baseline or a width, because `tabular-nums` is only on pillar percents and the profile count.

**Emphasis.** Emerald means the primary button, a healthy score, the savings bar, the balanced scenario, and the “Areas to Improve” panel on Advisory. Gold means the landing brand and the Elite button, and also “moderate” when it is `#F4B740`. The eye cannot treat one hue as one meaning.

**Scanning.** A completed dashboard scans in this order: gauge, pillar grid, two money tiles, warning cards, three shortcuts. That is a sound order. Before a report, the empty gauge is the largest object and the two real figures sit below it. The goal page scans as a giant percentage first, then three equal cards. The percentage is the loudest object, and it is the figure with the weakest caption (“Pilot AI Confidence Score”).

---

## Financial data visualization

What exists: `GaugeRing`, `ProgressBar`, pillar rows, `StatCard`, the goal scenario cards, and the landing hero (conic ring, area chart, three stats). Markdown can emit a table. There is no time series, no delta, and no axis.

| Question | What the screen can show | Gap |
| --- | --- | --- |
| Current state | Gauge 0–100 with Healthy / Moderate / At Risk. Two tiles for annual savings and monthly surplus. Advisory repeats the score, savings rate, and emergency months | The first paint is an empty ring. Surplus and savings rate can describe different formulas, and they share one card row |
| Change | The landing hero shows “+8.4% this quarter” in green | The signed-in product has no previous value and no delta. A green arrow on the landing page is the only change mark |
| Risk | Color plus a word on the gauge. Pillar bars recolor at 70% and 40% of that pillar’s points (`pctColor`) | Goal risk uses another cut: green from 75, gold from 50 (`GoalsPage.jsx`). Aggressive is gold, the same hue as “moderate” on the health score. Advisory paints improvements in emerald |
| Goal progress | Coverage percent in a stat tile. Scenario bars | A feasible scenario draws the bar at 100%. An infeasible one uses `coverage ?? 60`, so the bar reads as partial progress when the number is missing. There is no marker for “you are here” against the target |
| Recommendations | Warning sentences, the model section, scenario SIP amounts, primary and secondary product names | The recommended badge is a visual treatment on Balanced, not a style tied to the person’s risk choice. Product names are 12px text in a flat card, quieter than the percentage above them |

Numbers that should be one family are four sizes: 18px tiles, 28px gauge and savings rate, 40/48px goal score, 53px landing score. Only the gauge and the savings rate use `currency-xl`.

---

## Responsive behavior

Rules that are in the source:

- **Desktop (`lg` and up).** Sidebar stays open at 224px. Dashboard is eight columns plus a four-column rail. Goals is a four-column form and an eight-column score. Profile is a form plus a 320px list. Search is a 192px pill. The active goal shows only from `xl`.
- **Tablet (`md` to `lg`).** Sidebar becomes an overlay with a named menu button. Dashboard and goals stack. Chat regains its prompt column at `md`. Landing in-page links return at `md`, while the hero grid stacks at 900px, so between 768px and 900px the nav is horizontal and the hero is still one column.
- **Mobile (under `sm` / 640px).** Landing “Sign in” is `display: none` inside `.landing-nav`. Only “Get started” remains in the header. The hero card scales to 0.9 and rotates 1deg. The floating insight anchors to the right edge. Feature cards become one column. The app’s bell and settings hide. Profile fields become one column. The profile list is capped at `46vh` under the form. Chat prompts become a horizontal scroller. The composer adds safe-area padding.

**Overflow.** `body` sets `overflow-x: hidden`. The landing showcase image uses a negative right margin (`-150px`, `-90px`, `-55px` as the width shrinks) and a 3D rotate, so the screenshot is intentionally clipped. Chat transcript uses `min-w-0` and `break-words`. Markdown tables wrap in `overflow-x: auto`. Stat values use `break-words`. Long goal titles truncate.

**Cramped regions.** The top bar packs the menu, a 16px title, and up to five icons into one row. Icon buttons there are `p-1.5` around an 18px glyph, about 30px square. Chat’s send control is 36px (`w-9 h-9`). The auth close control is 30px. `Button` size `sm` is `py-1.5` and 12px type, under a 44px touch target. Sidebar rows are `py-3` and closer to that target. Delete, the menu, and sign-out set `min-h-11`.

**Navigation.** The overlay sidebar is the mobile nav and it locks the body scroll while open. There is no bottom nav. Search disappearing below `lg` removes a control that does not work on desktop either. Hiding Sign in on small landing screens leaves account return to the dialog toggle after Get started.

**Charts.** The gauge is a fixed pixel size (148, 128, or 100) and does not reflow. Bars are `w-full` and do adapt. There is no table in the app chrome. A model-written table can scroll inside chat or the advisory column. The landing chart is an SVG with a fixed view box inside a card that scales down.

---

## 1. Existing design-system inventory

The catalog of tokens, type, and components is `docs/product-audit/design-system.md`. Short form:

- **Type.** Inter for text, Manrope for headings and the one currency token. Seven size tokens. Landing display sizes live only in CSS.
- **Color.** About eight distinct paints, published under many Material-style names. Emerald action, steel info, muted gray, gold premium, red error, amber warning.
- **Space.** 4, 8, 16, 20, 24, 32, 40, plus Tailwind’s default scale.
- **Chrome.** 6 / 8 / 12px radii, 1px `#2A2A32` borders, one panel shadow, Material icons.
- **Kit that pages import.** Button, fields, glass panel, stat card, gauge, progress bar, pillar block, empty state, error banner, toast, shell.
- **Second system.** `landing.css`: gold, lilac, square cards, 5px buttons, its own gray ramp.

---

## 2. Inconsistency map

| Topic | System A | System B |
| --- | --- | --- |
| Brand color | App actions and healthy scores are `#18B981` | Landing brand, links, and the Elite button are three different golds (`#e6c47a`, `#D6B56A`, and the button gradient) |
| Muted text | `#9AA8BC` | Landing `--muted` is `#9aa0af`, and many headings use further one-off grays |
| Body size | Token is 14px | Pages use 12px and 13px. Markdown hard-codes 13px |
| Page title | Token is 24px | Top bar is 16px then 18px. Advisory title is 22px until `sm` |
| Money | `currency-xl` is 28px | Tiles are 18px. Goal score is 40px or 48px. Landing score is 53px |
| Healthy cut | Gauge: 70 and 50 | Goal percentage: 75 and 50 |
| “Needs work” | Dashboard warning cards are red | Advisory improvement cards are emerald |
| Cards | `GlassPanel`: blur, 12px, shadow | Profile sections and goal cards: flat fill, 12px or 8px, no shadow |
| Buttons | `Button` | Quick Actions, chat send, Elite, landing `.button-gold`, and `.nav-cta` are separate |
| Empty | `EmptyState` on Advisory | Dashboard, chat, goals, and the profile list each draw their own |
| Radius | 8px controls, 12px glass | Landing feature cards are square. Gold buttons are 5px. Hero and auth are 14px |
| Focus | Fields use an emerald ring | Chat input clears the ring (`focus:ring-0`) |
| Status copy color | `scoreStatus` returns a hex | The same hues exist as `text-primary`, `text-warning`, and `text-error`, and the pages use the hex anyway |

`info` and `tertiary` are the same blue. `secondary` and `on-surface-variant` are the same gray. `outline` and `surface-container-highest` are the same `#2A2A32`. The token list looks like a full Material theme. The palette is small.

---

## 3. Component reuse opportunities

These are already built. Pages reach around them.

| Existing piece | Where it is skipped | What reuse would unify |
| --- | --- | --- |
| `Button` | Dashboard quick actions, chat send, Elite, landing CTAs, prompt chips | One height, one radius, one loading treatment |
| `GlassPanel` | Profile form sections, goal definition, scenario cards, insight rows | One card elevation |
| `EmptyState` | Dashboard empty gauge, chat welcome, goal placeholder, profile list | One empty pattern: icon, sentence, action |
| `StatCard` | Advisory’s savings / emergency pair, the investable chip | One metric tile, with a size prop for the 28px figure |
| `LoadErrorBanner` | Auth dialog error is a bare paragraph. Toasts repeat some of the same failures | One inline error, one toast |
| `PillarPerformance` | Already shared by Dashboard and Advisory | Keep it. It is the best reuse in the app |
| `Field` | Chat composer | One input, including the focus ring |
| `ProgressBar` | Already shared | Pass semantic names (`positive`, `caution`, `risk`, `neutral`) instead of hex at each call |

`Button` already has `ghost`, `outline`, and `danger`, and nothing uses them. `SelectField`, `.glass-card`, `.accent-glow`, and `shadow-glow` are unused. Those are leftovers, not missing tools.

---

## 4. Missing component primitives

| Primitive | Why the UI needs it |
| --- | --- |
| Metric | One component for a rupee or a score: figure style, optional delta, optional status color. Stops 18px and 48px amounts from being invented per page |
| Badge | Recommended, Healthy, the warning count, ENCRYPTED, and “Active now” are five hand-built chips |
| Modal | The auth dialog is the only modal, and it is landing CSS. Delete, regenerate, and clear have nowhere to ask |
| Banner | A page-level note for “PDF not ready” and the disclaimer. Today one is 12px warning text and the other is 10px at 40% opacity |
| Table | Only the markdown parser builds a table, with inline styles. A profile or a report has no table primitive |
| Chart frame | Gauge and bar do not share padding, a caption slot, or a “no data” state |
| Skeleton | Loads are a 14px spinner sentence |
| Confirm | Not visual chrome so much as a missing dialog on destructive buttons |
| Tooltip | Disabled nav uses the `title` attribute |

A full chart library is not implied by the current screens. The gauge and the bar are enough for the data the product stores, once the bar cannot draw a stand-in percent.

---

## 5. UI problems by severity

### Critical

| Problem | Where | Why it is visual, not only copy |
| --- | --- | --- |
| Infeasible goal bars draw at 60% | `GoalsPage.jsx` `ProgressBar pct={coverage ?? 60}` | The bar is the progress picture. A missing coverage still looks like a majority fill |
| “Areas to Improve” uses the healthy color | `AdvisoryPage.jsx` improvement panel is `bg-primary/5` and `text-primary` | Emerald is also the primary button and the healthy gauge. A risk list looks like a success panel. Dashboard warnings are red, so the two screens disagree |

### High

| Problem | Where |
| --- | --- |
| Landing and app are two visual systems | Gold display page, then an emerald tool. The hero score does not use `GaugeRing` |
| Money has no single figure style | `StatCard` 18px, gauge 28px, goal 40/48px, landing 53px |
| Two healthy thresholds | 70 on the gauge, 75 on the goal score, both green / gold / red |
| Disclaimer is the smallest, faintest text on the report | `text-[10px] text-on-surface-variant/40` |
| Icon buttons and small buttons sit under a 44px target | Top bar, chat send, auth close, `Button` `sm` |
| Elite is the only gold control in the app and it is a full-width button | `Sidebar.jsx` `bg-premium`, no action |

### Medium

| Problem | Where |
| --- | --- |
| Body token unused; 12px and 13px are the real body | Pages and `markdownText.js` |
| Cards, radii, and shadows differ for the same kind of group | Glass versus flat sections versus goal cards |
| Quick actions, chips, and send are one-off buttons | Dashboard, chat |
| Empty states do not share `EmptyState` | Dashboard, chat, goals, profiles |
| Focus ring removed on the chat field | `ChatPage.jsx` |
| Sign in hidden on small landing headers | `landing.css` at 640px |
| Landing screenshots use negative margins and rotation | Clipped by design; easy to feel broken on a narrow phone |
| Uppercase 11px labels on every field and every stat | High tracking, low size, slows scanning of the form and the tiles |
| `tabular-nums` missing on currency | Columns of rupees will not align |

### Low

| Problem | Where |
| --- | --- |
| Unused tokens and variants | `body-lg`, `display-lg`, `ghost` / `outline` / `danger`, `SelectField`, `.glass-card`, `shadow-glow` |
| `spacing.base` duplicates `xs` at 4px | `tailwind.config.js` |
| Material token names repeat the same hex | Makes the theme look larger than the palette |
| Sidebar wordmark is an `h1` at 18px | Heading level and size disagree |
| Reduced motion is respected for page fades and the landing float | Gauge and bar transitions are not gated |

---

## 6. Recommended design-system structure

A target, not a change in the repo. The token list to aim at is also at the end of `docs/product-audit/design-system.md`.

**One palette, two densities.** Landing may keep large display type. It should use the same emerald, the same gold, the same text gray, and the same risk colors as the app. Lilac either joins the theme as a single accent or leaves the feature cards.

**Separate action from status.** The primary button stays emerald. Positive, caution, and risk are the only colors for scores, bars, and warning panels. “Areas to Improve” uses risk. Strengths use positive. Balanced is not painted as the recommended choice unless the person’s risk says so.

**One figure style.** `figure` for tiles, `figure-lg` for the gauge and the goal score. Same Manrope, same `tabular-nums`, same rules for ₹ and %. The landing hero can be a larger step on that same ramp, built from `GaugeRing` so the sample and the product match.

**One card, one button, one field.** Glass panel for grouped content. `Button` for every action, including the landing primary, with a `brand` variant if gold remains the marketing button. Fields keep the emerald focus ring, including chat.

**One status badge and one banner.** Healthy / Moderate / At Risk, Recommended, and the PDF note all go through the badge. The SEBI line is a banner at body size, not 10px at 40% opacity.

**Bars draw data or they draw nothing.** No fallback width. A goal bar’s width is coverage. Color comes from the status ramp.

**Touch.** Controls that stand alone (icons, send, close, small buttons) use at least 44px in the hit area. The sidebar already approaches this. The top bar does not.

**Do not add a chart library for the current data.** Keep the gauge and the bar. Add a caption slot and an empty state. Add a table primitive only when a screen, not the model’s markdown, needs rows.

**Drop the unused layer.** Unused button variants, `SelectField`, `.glass-card`, and the duplicate Material aliases can leave when a cleanup happens. Until then they are noise in the theme, not part of the visual language.
