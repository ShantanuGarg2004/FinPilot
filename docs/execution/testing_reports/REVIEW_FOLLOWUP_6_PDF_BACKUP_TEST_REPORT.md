# Review follow-up 6 — PDF backup rule

**Date:** 2026-09-27
**Plan:** `docs/planning/ARCHITECTURE_REVIEW_FOLLOWUP_PLAN.md` issue 6
**Verdict:** The architecture doc now says to back up `data/pdfs` with the `finpilot` database, and that a database restore does not bring the PDF files back. No code change. No pytest.

---

## Checklist

Sentences added to the data section of `docs/architecture/ARCHITECTURE.md`:

| Sentence | Present |
| --- | --- |
| Back up the directory `data/pdfs` in the same breath as the `finpilot` database, and restore both. | Yes |
| The PDF directory is a separate backup: a database restore does not bring the files back. | Yes |
| `resolve` trusts only the file name, so a stored path cannot leave that directory. | Yes |
| Those files are on this machine's disk. Object storage is not part of this layout. | Yes |

`database/pdf_files.py` was not changed. PDFs were not moved to object storage.
