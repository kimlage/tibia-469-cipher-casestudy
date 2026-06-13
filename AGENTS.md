# AGENTS.md — working notes for agents & contributors

**Status: this project is CLOSED (archival).** The decode effort is concluded —
the 70-book "469" corpus is verified non-linguistic. The definitive verdict is
[docs/469_final_report.md](docs/469_final_report.md); the navigable overview is
the [project wiki](docs/wiki/README.md). No further internal decode work is
warranted — the remaining failure mode would be pareidolia, which this project
spent its discipline learning to refuse. This file orients anyone (human or
agent) who works in the repository.

## Documentation mode: "frozen artifact" wiki-viva

This repo follows the documentation conventions of the **wiki-viva kit** (an
external Markdown/Git living-wiki toolkit) in **frozen-artifact mode**: pages
carry lightweight frontmatter and a declared page type, the wiki has a
map-of-contents and diagrams, and the public/private boundary is respected
(see `private/` in `.gitignore`). The kit's *live-operational* machinery —
ingestion pipeline, LLM context pass, daily cockpit, freshness/staleness gates,
karma — is intentionally **NOT** run here, because the project is finished.
Do not try to "re-enliven" a closed case study; that is precisely the
activity-over-outcome failure mode the project itself diagnosed. The repo's
conventions are declared in [`wiki.config.yaml`](wiki.config.yaml) and
[`wiki.page-types.yaml`](wiki.page-types.yaml).

## Data & reproduction

- Canonical evidence for every number in the report is committed under
  [`analysis/audit_20260609/`](analysis/audit_20260609/) (scripts + raw outputs).
- The operational SQLite DB (`data/bonelord_operational.sqlite`) is **not
  committed** (large, regenerable). Regenerate it from the committed `.xlsx`
  workbooks with `scripts/export_workbook_to_sqlite.py` (see
  [`scripts/README.md`](scripts/README.md)). Open the DB read-only
  (`file:...?mode=ro`).
- `row0` — the code→symbol reconstruction, byte-exact on 70/70 books — is the
  canonical mechanical substrate. Treat any external German/MHG-style "readings"
  as audit-only shadow candidates, **never** as truth for promotion.
- Known pitfall: SQL queries in some terminals can silently return 0 rows —
  always print row counts.

## The Outcome Ledger (the reusable discipline — keep it)

Activity is **not** progress. Session count, iteration number, and number of
scripts/tables created must never be reported as progress. A round counts as
semantic progress ONLY if, under an honest, reproducible check, at least one of
these strictly increases:

1. **CRIBS_REPRODUCED_UNDER_HOLDOUT** — plaintexts reproduced by a method that
   did not see that item's answer. *(0 books.)*
2. **CODES_CONFIRMED_EXTERNALLY** — digit→word codes attested by a CipSoft /
   in-game source — not the project's own decoder, not a fan guess.
   *(0 at word level; 13 internally-consistent codebook entries, validation-only.)*
3. **BOOKS_NO_PROSE_TO_ACCEPTED** — books crossing PROMOTED_NO_PROSE → an
   accepted, non-pareidolic reading. *(0/70.)*
4. **GT_PHRASES_PASSING_EXTERNALLY** — phrases passing against attested external
   text, not round-trip against the project's own decoder. *(0.)*

Decoder self-output and fan guesses are inadmissible for these metrics. A round
that moves no metric is logged "NEGATIVE / plateau confirmed" — a valid,
acceptable outcome, not a failure to paper over. Structural fixes (e.g. the
70/70 reconstruction fix) are logged separately as `STRUCTURAL_FIX` and do not
count as semantic progress.

## If you extend the analysis

- Keep changes analysis-only; the decode core is frozen.
- Promotion gates remain strict: assign no plaintext meaning to a `row0`
  template until it survives contrastive slot checks, contig/overlap validation,
  and a contradiction audit.
- The only thing that could reopen the verdict is **CipSoft-attested ground
  truth** (an official book→plaintext pair or symbol table). See report §9.
