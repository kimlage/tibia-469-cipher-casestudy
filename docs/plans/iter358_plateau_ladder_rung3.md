# Iteration 358 - Plateau Ladder Rung 3 (Safe Search-Space Expansion)

## Goal
We gained real progress at iter `353` (mechanical promotions + some English retext), then plateaued again (`354..357` all-stale). The existing plateau ladder capped at rung `2`, so it cannot expand search space further.

This change extends the ladder to rung `3` with **still-safe** relaxations (all guardrailed by GT policy + metric checks):
- Macro mining: allow longer macros and slightly lower dominance share.
- English/context layers: emit more mappings for display and (guarded) retext.
- Sequence match + reverse phrase: increase recall budgets to find new hints.

## Tasks
- [ ] Extend `PlateauLadder_Rung` cap from `2` to `3`.
- [ ] Add rung-3 settings for:
  - `MacroMine_MinShare=0.80`, `MacroMine_MaxLen=32`, `MacroMine_MaxCandidates=300`, `MacroMine_NValues=2..12`
  - `MaxEvidenceAvgDrop=0.007`
  - English layer: `min_total=3`, `min_share=0.85`
  - ContextEnglish: `max_cands=12`, `map_min_total=5`, `map_min_share=0.85`
  - SequenceMatch: `cand_max_freq=4`, `n_list=3..8`, `time_budget_s=70`, `max_matches=160`
  - ReversePhrase: `MaxSpanTokens=12`
- [ ] Run `next iteration` and check for new `mech_promoted` / `seq_fp_changed` / `ctx_score` changes.
- [ ] Run validator.

## Implementation Log
- Files changed:
  - `./scripts/bonelord_flow_next_iteration.py`
  - `./docs/plans/iter358_plateau_ladder_rung3.md`

## Verification
- Ran:
  - `python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx` -> iter `358`
  - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx` OK
- Iter 358 highlights (runner stdout):
  - `mech_promoted=2`, `Tokens 887 -> 881` (-6)
  - `Weak 0.037703 -> 0.036307` (-0.001396)
  - `Single 0.019026 -> 0.018677` (-0.000349)
  - `SequenceMatches 34 -> 36` (`fp_changed=1`)
  - `ContextEnglish map_rows=2` (new stable context hints emitted)
  - `MacroMine ladder rung=3`
