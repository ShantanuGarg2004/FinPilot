# Review follow-up 5 — advisory HTML escaping

**Date:** 2026-09-27
**Plan:** `docs/planning/ARCHITECTURE_REVIEW_FOLLOWUP_PLAN.md` issue 5
**Verdict:** Advisory text that contains a script tag, an image with an event handler, or a `javascript:` link is rendered as text. `npm test` locks that behavior. No sanitizer package was added.

---

## 1. What shipped

The parser moved from `frontend/src/lib/markdown.jsx` into `frontend/src/lib/markdownText.js` so `node --test` can import it. The React component still calls `parseMarkdown` and passes the string to `dangerouslySetInnerHTML`. The escape rules are unchanged: `&`, `<`, and `>` are escaped before tags are added, and a markdown link keeps only its label.

## 2. Tests

`npm test` in `frontend/` — **10 passed** (7 before this issue, plus 3). Vite was not started.

| Case | Result |
| --- | --- |
| `<script>alert(1)</script>` | No `<script` tag. The text is `&lt;script&gt;...` |
| `<img src=x onerror="alert(1)">` | No `<img` tag. The source is escaped text |
| `[click](javascript:alert(1))` | No `javascript:` and no `<a` tag. The label `click` remains |
