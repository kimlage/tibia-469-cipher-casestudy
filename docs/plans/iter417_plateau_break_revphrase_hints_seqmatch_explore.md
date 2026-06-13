# Iteration 417 - Plateau Break: ReversePhrase Hints + SequenceMatch Exploration

## Goal
Increase incremental translation progress (display-only layers: `ContextEnglish` / `CodeAware`) without touching StrictPlus/GT guardrails by:
- feeding **ReversePhrase token candidates** into the contextual decoders as extra hints, and
- enabling **SequenceMatches exploration** so we can discover new corpus alignments even when the current rendering is stable.

## Constraints / Safety
- Never break `groundtruth_live_check()`.
- Keep `Coverage_StrictPlus_v108 == 1` for all books.
- Do not mutate StrictPlus text when only display layers change.
- Do not store full external corpora text in the workbook (snippets + URLs only).

## Tasks (Status)
- [x] Add ReversePhrase-derived token->word hints into `materialize_context_english_render()` (display-only).
- [x] Add the same ReversePhrase hints into `materialize_codeaware_homophones_render()` (display-only).
- [x] Add SequenceMatches exploration (rotate/slice candidate n-grams by iteration) to avoid deterministic plateaus.
- [x] Add `SequenceMatchesCache_Auto` for cumulative matches so word-hints can accumulate across iterations.
- [x] Run `next iteration` (iters 417-419); record stats deltas and confirm invariants.
- [x] Run `scripts/bonelord_validate_workbook.py` to confirm invariants.

## Implementation Log
- 2026-02-11:
  - Implemented ReversePhrase token-candidate boosting (display-only) for ContextEnglish + CodeAware.
  - Implemented SequenceMatches exploration knobs + created `SequenceMatchesCache_Auto` for accumulating snippets across iterations.
  - Ran iterations 417-419.
  - Fixed a CodeAware failure introduced during the change (`rev_hints` missing in scope).
  - Validator passed on iter 419.

### Iteration Notes
- Iter 416 (baseline before changes):
  - StrictPlus unchanged: `EvAvg=2.327439`, `Weak=0.036307`, `Micro=0.028452`, `Single=0.018677`, `Tokens=881`
  - ContextEnglish: `avg_score=6.378943`, `oov=0.129736`
  - CodeAware: `map_rows=68`, `overrides=56`
- Iter 417 (after change, first run):
  - ContextEnglish improved slightly: `avg_score=6.378943 -> 6.379675` (streak=1), text unchanged.
  - CodeAware step failed (bug): `name 'rev_hints' is not defined`.
- Iter 418:
  - CodeAware still failed (same bug).
- Iter 419 (bug fixed):
  - CodeAware restored: `map_rows=68`, `overrides=56`, `fp_changed=1`.
  - Workbook invariants: OK (`scripts/bonelord_validate_workbook.py`).
