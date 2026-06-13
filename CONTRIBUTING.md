# Contributing

**This project is closed.** The 469 decode effort reached a verified verdict
(the 70-book corpus is non-linguistic — see
[docs/469_final_report.md](docs/469_final_report.md)), and no further internal
decode work is warranted. The repository is published as an **archival case
study** in honest, adversarially-verified analysis, not as an actively developed
tool. Please set expectations accordingly.

## What is welcome

- **Corrections.** If a number, citation, or claim is wrong or unsupported by
  the committed evidence in [`analysis/audit_20260609/`](analysis/audit_20260609/),
  open an issue or PR with the specific file/line and the corrected value. The
  project keeps an explicit corrections ledger (final report §7) — accuracy
  matters more than tidiness.
- **Reproduction reports.** If you re-run the audit pipeline and get different
  numbers, that is a first-class contribution. Say what you ran and what you got.
- **The one thing that could reopen the verdict:** **CipSoft-attested ground
  truth** — an official book→plaintext pair, an official symbol/code table, or a
  new officially-glossed phrase long enough to test the book map. If you have a
  primary, citable source (not a fan decode, not an LLM output), open an issue.
  The `row0` mechanical model is the validated substrate to test it against.

## What is out of scope

- New speculative "solutions" of the books produced by substitution search,
  an LLM, or pattern-matching. The project's whole discipline is to **refuse**
  plausible-looking decodes that cannot beat a self-anagram / null control.
  A proposed reading must come with the control it beats; otherwise it is
  pareidolia (final report §4.6, case study).

## Ground rules

- Be honest about uncertainty; cite a reproducible source for any quantitative
  claim (a DB query rerun or a primary web page actually read).
- Respect the IP boundary: this repo studies a CipSoft game nominatively and is
  not affiliated with CipSoft (see [NOTICE](NOTICE)). Do not add ripped game
  assets or original book prose.
- By contributing you agree your contribution is licensed under the repository's
  [MIT License](LICENSE).
