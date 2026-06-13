# Iter 291: Canonicalization Into Base Alphabet Buckets (g/k/q/j/z/x)

## Why
The 469 base alphabet extracted from `DigitLetterCodes_Auto` is:
`A B C E F I L N O R S T V` (+ `*` wildcard).

Many real English/Tibia/Jabberwocky words contain letters outside this alphabet (notably `g/j/k/q/z/x/h`).
Without mapping those letters into base buckets, signature-based alignment cannot ever match them,
which stalls:
- `LoreAlignment_Auto` candidate coverage
- `SequenceMatches_Auto` yield
- `ContextEnglish` disambiguation quality

## What Changed
### Runner
Updated `./scripts/bonelord_flow_next_iteration.py`:
- `_lore_canon_word()` now maps letters not present in the base alphabet into stable buckets:
  - `j -> i`
  - `k -> c`
  - `q -> c`
  - `g -> c`
  - `z -> s`
  - `x -> cs`

This is still *semantic-layer only* (display + retext, guarded by GT live check). It does not change StrictPlus DP tokenization or mechanical metrics directly.

### Workbook
- Continued incremental iteration on `./bonelord_469_iter129.xlsx`
- Backups written under `./tmp/spreadsheets/bonelord_469_iter129_backup_iter*.xlsx`

## Results (Run Until Stale)
Ran `bonelord_run_until_stale.py` (max 10, stale=2) starting at iter 287. Workbook advanced to iter 291.

Key deltas across the run:
- ContextEnglish improved:
  - AvgScore: `3.878663 -> 3.890758`
  - OOVFrac: `0.158585 -> 0.152035`
  - ImproveStreak reached `2` at iter 289
- SequenceMatches increased: `5 -> 7` (fingerprint changed at iter 288)
- EnglishLayer expanded: map rows `5 -> 6`, repl `33 -> 47`
- English glossary retext (GT-safe) applied at iter 289:
  - token `II`: `yi -> joy`

Guardrails still pass:
- `Coverage_StrictPlus_v108 == 1` (all books)
- GroundTruth live check OK
- External roundtrip: `pass=3 fail=0`

## Notes / Next Levers
- Reverse phrase mining is still at `hits=0`; likely remaining blocker is word-boundary/segmentation mismatch rather than canon buckets.
- Next safe exploration knobs (if needed):
  - `Lore_Canon_DropAllH` (base alphabet has no `h`), test ON/OFF under the same GT guardrails.
  - Add a letter-stream reverse phrase matcher (base letters, not DP-token boundaries) to recover anchors even when segmentation is wrong.

