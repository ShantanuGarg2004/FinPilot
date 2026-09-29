# FinPilot AI — implicit design system

**Date:** 2026-09-29  
**Source:** `frontend/tailwind.config.js`, `frontend/src/index.css`, `frontend/src/landing.css`, `frontend/index.html`, and the shared components in `frontend/src/components`.  
**Judgment of how the system is applied:** `docs/product-audit/05-ui-design-system-audit.md`.

This file records the system that is already in the repository. It is not a redesign. The last section is a proposed structure, marked as such.

Application code was not changed.

---

## Two surfaces, one background

The signed-in app is a Tailwind theme: near-black surfaces, emerald as the action color, steel blue as the information color, Manrope for headings and figures, Inter for text.

The signed-out page is a separate stylesheet, `landing.css`. It keeps the same near-black page and adds a gold brand, a lilac accent, and display sizes the Tailwind scale does not contain. The auth dialog is styled there, then reuses `TextField` and `Button` from the app.

`index.html` loads Inter (400–700), Manrope (600–700), and Material Symbols Outlined. `<html>` has `class="dark"`. `darkMode: "class"` is set in Tailwind, and no light theme exists.

---

## Typography

### Families

| Role | Family | Where it is set |
| --- | --- | --- |
| Body, labels, inputs | Inter, then system-ui | `body` in `index.css`; Tailwind `font-sans` and the `font-body-*` / `font-label-sm` keys |
| Headings | Manrope, then Inter | Element rule for `h1–h4` in `index.css` |
| Display and currency | Manrope, then Inter | Tailwind `font-display`, `font-headline-*`, `font-currency-xl` |
| Icons | Material Symbols Outlined | `Icon.jsx`, variation FILL / weight / opsz |
| Code in advisory markdown | monospace, inline style | `markdownText.js` |

Landing headlines do not use the Tailwind display token. `.hero-copy h1` is `clamp(48px, 6vw, 78px)`. Section `h2` is `clamp(36px, 4vw, 56px)`.

### Size tokens

Defined in `tailwind.config.js` `fontSize`. A token is applied only when a component uses both the family class and the size class, for example `font-headline-md text-headline-md`.

| Token | Size / line / weight | Intended role | Actually used for |
| --- | --- | --- | --- |
| `label-sm` | 11 / 16, medium, +0.04em | Labels | Uppercase field labels, pillar names, stat labels. Screens also use raw `text-[10px]`, `text-[11px]`, `text-[12px]` |
| `body-md` | 14 / 22, regular | Body | Inputs, and one profile helper. Most body copy is `text-[12px]` or `text-[13px]` |
| `body-lg` | 15 / 24, regular | Larger body | Defined. No component was found using `text-body-lg` |
| `headline-md` | 18 / 26, semibold | Section title | Section titles, and also rupee amounts inside `StatCard` |
| `headline-lg` | 24 / 32, bold | Page title | “Create profile.” The advisory title overrides it to 22px until the `sm` breakpoint. The top bar uses 16px until `sm` |
| `currency-xl` | 28 / 34, bold | Money and scores | Gauge value. Savings rate on Advisory. Not the stat tiles, not the goal percentage |
| `display-lg` | 32 / 40, bold, −0.02em | Display | Defined. No component was found using `text-display-lg`. The goal score is `text-[40px]` / `sm:text-[48px]` |

### Heading hierarchy, as practiced

1. Landing hero, outside the scale.
2. Landing section titles, outside the scale.
3. App page title in the top bar: Manrope, 16px then the 18px headline token.
4. In-page title: 24px headline, except Advisory at 22px on small screens.
5. Card titles: 18px headline.
6. Uppercase labels: 11px, wide tracking, muted.

There is no `h1` scale inside the app. The sidebar wordmark is an `h1` at 18px.

### Body hierarchy, as practiced

The token says 14px. The screens mostly use 12px and 13px for descriptions, insights, chat, and scenario copy. Advisory markdown forces 13px and the muted gray `#9AA8BC` in inline styles (`markdownText.js`).

### Label hierarchy

Field labels are uppercase Inter, 11px, muted (`Field.jsx`). Section kickers on the landing page are 9–10px gold, letter-spacing about 0.15–0.18em. Status chips (“Recommended”, the warning count, “Live financial picture”) are 9–10px, bold, uppercase.

### Numbers

| Kind | Treatment |
| --- | --- |
| Rupees in tiles | `formatINR` (`en-IN`) or `compactINR` (L / Cr). Drawn at 18px (`StatCard`), the same size as a section title |
| Gauge score | 28px Manrope, emerald gradient when `gradient` is set |
| Goal score | 40px or 48px, color chosen in the page, a `%` suffix at headline size |
| Savings rate on Advisory | 28px emerald |
| Pillar points | 12px, `tabular-nums` on the dashboard grid only |
| Landing score | 53px Manrope, plus a 104px conic ring |

`tabular-nums` is not applied to currency. Positive, warning, and risk colors are chosen at the call site, not by a number component.

---

## Color

Hex values below are the ones in `tailwind.config.js` unless noted. Many role names share one hex.

### Foundation

| Role | Token | Hex | Notes |
| --- | --- | --- | --- |
| Background | `background`, `surface-dim`, `surface-container-lowest` | `#050505` | Also `--ink` and `body` |
| Surface | `surface`, `surface-container-low` | `#0E0E10` | Sidebar, page field fill |
| Raised surface | `surface-container` | `#16161A` | Cards that are not glass, chat bubbles’ neighbor |
| Higher surface | `surface-container-high` | `#1C1C22` | Hover, user chat bubble |
| Highest / outline | `surface-container-highest`, `surface-bright`, `surface-variant`, `outline`, `outline-variant` | `#2A2A32` | The same hex is a fill and a border |

Glass panels use `rgba(22, 22, 26, 0.78)` plus a 14px blur (`.glass-panel` in `index.css`). `.glass-card` is the opaque twin and is not referenced by a component.

### Brand and action

| Role | Token | Hex |
| --- | --- | --- |
| Primary | `primary`, `primary-fixed-dim`, `inverse-primary`, `surface-tint` | `#18B981` |
| Primary container | `primary-container`, `primary-fixed` | `#22C995` |
| On primary | `on-primary` and the other `on-primary-*` tokens | `#050505` |
| Premium / Elite button | `premium` | `#D6B56A` |
| Landing gold | `--gold` | `#e6c47a` |
| Landing gold, bright | `--gold-bright` | `#f2d58c` |
| Landing gold gradient | `.button-gold`, `.brand-mark` | `#e8c97f` → `#c9a45a`, and `#f4d68e` → `#b78e3d` |

Emerald is the app’s action color, the healthy score, and the default chart stroke. Gold is the landing brand and the Elite button. They are not one token.

### Text

| Role | Token | Hex |
| --- | --- | --- |
| Text | `on-surface`, `on-background` | `#F4F7FB` |
| Muted | `on-surface-variant`, `secondary`, and the `secondary-fixed*` tokens | `#9AA8BC` |
| Landing muted | `--muted` | `#9aa0af` |
| Landing body grays | raw CSS | about `#767b87` through `#bbbfc9`, many one-off values |

`--muted` and `on-surface-variant` are different grays.

### Secondary, info, and the extra accent

| Role | Token | Hex |
| --- | --- | --- |
| Secondary | `secondary` | `#9AA8BC` (same as muted text) |
| Info / tertiary | `tertiary`, `tertiary-container`, `tertiary-fixed`, `info` | `#6B9BCF` |
| Tertiary dim | `tertiary-fixed-dim` | `#5A88B8` |
| Landing lilac | `--lilac` | `#c1a4ff` |

Lilac exists only on the landing feature card. It is not in the Tailwind theme.

### Status

| Role | Token | Hex | Used for |
| --- | --- | --- | --- |
| Success / healthy | `primary` `#18B981` | Score ≥ 70 in `scoreStatus`. Pillar fill ≥ 70% in `pctColor`. Goal score ≥ 75 on `GoalsPage.jsx` |
| Warning | `warning` `#F4B740` | Score ≥ 50 and under the healthy cut. Pillar fill ≥ 40%. PDF-not-ready line. Rate-limit banner |
| Error | `error` `#F06A6A` | Below those cuts. Form and request failures. `error-container` is `#3A1A1A` |
| On error | `on-error` `#050505`, `on-error-container` `#F06A6A` | The count chip on the dashboard uses the container pair |

There is no separate success token. Healthy money and the primary button are the same emerald.

### Financial indicators

| Meaning | Color in the app |
| --- | --- |
| Healthy / feasible / savings bar | `#18B981` |
| Moderate / gap timeline / aggressive scenario | `#F4B740` |
| At risk | `#F06A6A` |
| Expenses bar | `#9AA8BC` |
| “Investable” bar and the conservative scenario | `#6B9BCF` |
| Balanced scenario | `#18B981` |
| Dashboard warning card | error red, left border |
| Advisory “Areas to Improve” | primary emerald at low opacity |
| Advisory “Strengths” | tertiary blue at low opacity |
| Landing “+8.4% this quarter” | `--green` `#22c995` |

The gauge track is `rgba(244,247,251,0.08)`. A gradient gauge runs `#22C995` to `#18B981`.

---

## Spacing

### Tokens

From `theme.extend.spacing`:

| Token | Value |
| --- | --- |
| `xs`, `base` | 4px (the same value twice) |
| `sm` | 8px |
| `md` | 16px |
| `gutter` | 20px |
| `lg` | 24px |
| `xl` | 32px |
| `2xl` | 40px |
| `container-max` | 1180px, also a `maxWidth` |

Tailwind’s default scale is also used everywhere (`gap-2`, `py-1.5`, `px-3`, `space-y-1`). The custom names do not replace it.

### Patterns that repeat in the app

- Page padding: `px-4` then `sm:px-gutter` (20px) then `md:px-lg` (24px), with `pt-lg` and `md:pt-2xl`.
- Card padding: `p-md` (16) or `p-lg` (24). Profile sections use `p-gutter` (20).
- Stack gap: `space-y-sm` (8), `space-y-md` (16), `space-y-xl` (32).
- Sidebar width: `w-56` (224px). The top bar offset matches `lg:left-56`.
- App bar height: `--app-bar` = 3.5rem plus the safe-area inset.

### Landing spacing

The landing page does not use these tokens. Horizontal padding is 28px, then 20px under 640px. Section padding-top is 132px, 156px, or 160px. The content width is 1184px or 1240px, beside the app’s 1180px.

---

## Radius, border, shadow

### Radius

Tailwind overrides: default 6px, `lg` 8px, `xl` 12px, `2xl` 16px, full pill.

App practice: glass panels `rounded-xl`, buttons and inputs `rounded-lg`, chips and the search field `rounded-full`, a few chat rows `rounded-md`. Profile sections are `rounded-xl`. Goal cards are `rounded-lg`.

Landing practice: hero card 14px, auth panel 14px, feature cards square, gold button 5px, nav button and pills fully round, showcase frame 24px.

### Border

The app border is 1px `outline` (`#2A2A32`), often at 60% opacity. Emphasis uses `border-primary/30` or `border-info/30`. Empty states use a dashed outline. Warning and error banners use those hues at about 40–50% opacity.

Landing borders are a family of near-black grays (`#292a2f`, `#3a3a3e`, `#3b3c42`) written per component.

### Shadow

| Name | Value | Where |
| --- | --- | --- |
| `shadow-panel` | 1px white hairline at 4% plus `0 8px 24px rgba(0,0,0,0.45)` | `GlassPanel`, toasts |
| `shadow-glow` | emerald ring and a soft emerald drop | Defined. No component reference found |
| `.accent-glow` | almost the same emerald ring | Defined in CSS. No component reference found |
| Landing cards | `0 30px 70px` and gold hairline | Hero, auth, screenshots |

Focus on fields is an emerald ring: `focus:shadow-[0_0_0_3px_rgba(24,185,129,0.15)]`.

---

## Icons

One set: Material Symbols, wrapped by `Icon.jsx`. Decorative icons set `aria-hidden`. Sizes in the app are 13, 14, 15, 16, 18, 20, 22, 28, 32, and 36. Active navigation and a few primary actions set `fill`. There is no second icon library and no app logo component in the shell. The landing mark is three rotated squares in `.brand-mark`.

---

## Components that exist

| Piece | File | Role |
| --- | --- | --- |
| `Button` | `components/Button.jsx` | `primary`, `container`, `ghost`, `outline`, `subtle`, `danger`. Sizes `sm`, `md`, `lg`. Loading swaps in `Spinner` |
| `TextField`, `TextArea`, `SelectField`, `RangeField` | `components/Field.jsx` | Shared label class and control class. `SelectField` has no caller outside this file |
| `GlassPanel` | `components/GlassPanel.jsx` | Blurred surface, 12px radius, panel shadow |
| `StatCard` | `components/StatCard.jsx` | Icon, uppercase label, 18px value, 12px subline |
| `GaugeRing` | `components/GaugeRing.jsx` | SVG ring, animated dash, center value |
| `ProgressBar` | `components/ProgressBar.jsx` | Clamped 0–100 bar. Color is a prop, default emerald |
| `PillarPerformance` | `sections/shared/PillarPerformance.jsx` | `grid` or `list` of the seven pillars |
| `EmptyState` | `components/EmptyState.jsx` | Dashed frame, icon, title, optional button |
| `LoadErrorBanner` | `components/LoadErrorBanner.jsx` | Rate-limit or error row with Retry |
| `Toast` | `components/Toast.jsx` | Fixed stack, four tones, timed dismiss |
| `Icon`, `Spinner` | `components/Icon.jsx`, `Spinner.jsx` | Symbol and  the spinning ring |
| `AppShell`, `Sidebar`, `TopBar` | `components/layout/` | Fixed sidebar, fixed bar, padded or full-bleed main |
| `MarkdownRenderer` | `lib/markdown.jsx` | Advisory and chat prose, including a hand-built table |
| `Reveal` | `components/Reveal.jsx` | Landing scroll-in. Reduced motion is handled in CSS |

`Button` variants `ghost`, `outline`, and `danger` have no call site in the pages. Pages use `primary`, `subtle`, and `container`.

---

## Layout

| Breakpoint | What changes |
| --- | --- |
| default | Single column. Sidebar off-canvas. Landing hero stacks under 900px |
| `sm` (640px) | Advisory title grows. Bell and settings appear. Goal score grows to 48px. Profile list is still under the form |
| `md` (768px) | Landing nav links return. Chat’s left column returns. Page padding grows |
| `lg` (1024px) | Sidebar is fixed. Dashboard becomes 8/4. Goals form becomes 4/8. Profile list becomes a right column |
| `xl` (1280px) | Active goal pill appears in the top bar |

Chat and profile use `100dvh` minus `--app-bar`. The chat composer pads for `safe-area-inset-bottom`. The viewport meta includes `viewport-fit=cover`.

Charts in the product are the gauge, horizontal bars, and one illustrative SVG on the landing page. There is no table component. Markdown tables scroll horizontally inside the prose block.

---

## Motion

Page enter is a 8px rise over 0.45s. View enter is a fade over 0.55s. Toasts slide from the right. Gauge and bars animate width over 1s. Landing cards float unless `prefers-reduced-motion: reduce`. The app’s page animation is also disabled under that preference. Button press uses `active:scale-[0.98]`.

---

## Proposed structure

This is a target for a later design pass. It is not implemented.

Keep one theme file as the source of hex values. Point both Tailwind and `landing.css` at those values. Collapse the Material-style aliases that repeat `#050505`, `#18B981`, `#6B9BCF`, and `#9AA8BC`.

Roles to keep:

- `bg`, `surface`, `surface-raised`, `border`
- `text`, `text-muted`
- `action` (emerald), `brand` (one gold, shared by landing and Elite)
- `info` (one blue)
- `positive`, `caution`, `risk` — separate from the button color so a warning can be red and a primary button can stay emerald
- Type: `display`, `title`, `section`, `body`, `label`, `figure`, `figure-lg`
- Space: 4, 8, 16, 24, 32 only, plus the page gutter
- Radius: 8 for controls, 12 for cards, pill for chips
- One shadow for cards

Components to treat as the kit: Button, Field, Card, Metric, Gauge, Bar, Badge, Banner, Toast, Modal, and a prose style for the advisory. Landing display type can stay larger, using the same color roles.
