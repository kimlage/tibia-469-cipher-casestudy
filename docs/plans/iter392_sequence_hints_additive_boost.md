# Iteration 392 - Make SequenceWordHints Actually Influence ContextEnglish (Additive Boost)

## Problem
`SequenceWordHints_Auto` can be non-empty, but `ContextEnglish` often remains unchanged because the current hint logic only boosts a hinted word up to the top-K cutoff. If the hinted word is already in the candidate list (common), its rank rarely changes.

## Fix (Safe, Display-Only)
Change hint application from:
- `cc[word] = max(prev, cutoff + bonus)`
to:
- `cc[word] = max(prev + bonus, cutoff + bonus)`

This keeps the “enter the top-K” property while also allowing hints to change ranking.

## Scope
- Applies to both:
  - `ContextEnglish` candidate selection
  - `CodeAware` candidate selection (uses the same hint mechanism)
- Does **not** touch StrictPlus DP or Glossary (unless downstream retext is enabled and passes GT checks).

## Tasks (Status)
- [x] Patch ContextEnglish hint boosting to be additive.
- [x] Patch CodeAware hint boosting to be additive.
- [x] Run `next iteration` (iter392) and verify ContextEnglish changes when hints exist.
- [x] Validate workbook invariants and report evolution stats.

## Implementation Log
- 2026-02-09: Implemented additive hint boosting in `scripts/bonelord_flow_next_iteration.py`.
- 2026-02-09: Iter `392` results:
  - `ContextEnglish: books_changed_rows=1`, `avg_score` improved slightly (`6.378755 -> 6.378854`)
  - Book 31 changed `played -> albeit` (from `SequenceWordHints_Auto`)
  - `CodeAware: books_changed_rows=1` (mirrors ContextEnglish choice)
  - Validator OK; StrictPlus metrics unchanged
