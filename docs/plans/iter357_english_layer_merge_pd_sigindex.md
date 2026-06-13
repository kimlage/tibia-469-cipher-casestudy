# Iteration 357 - English Layer: Merge Tibia + PD SigIndex and WordFreq (Safe Coverage Boost)

## Goal
Improve readability progress beyond the plateau by increasing the number and stability of `EnglishMap_Auto` entries:
- `EnglishMap_Auto` previously derived only from `LoreSigIndex_Tibia_Auto`.
- Many plausible mappings are supported better by public-domain corpora (older/archaic English), but were not considered.

This iteration broadens the English layer (display + retext source) by:
1. Merging derived signature indexes from:
   - `LoreSigIndex_Tibia_Auto`
   - `LoreSigIndex_PD_Auto`
2. Using a combined derived word frequency for retext word-quality guardrails:
   - `LoreWordFreq_Tibia_Auto` + `LoreWordFreq_PD_Auto`

Guardrails unchanged:
- Tokenization/coverage must remain strict (`Coverage_StrictPlus_v108 == 1`).
- Any Glossary retext is still gated by the GT live check policy.

## Tasks
- [ ] Update `materialize_english_layer_display()` to use combined sig-index.
- [ ] Update `apply_english_promotions_to_glossary()` word-quality checks to use combined wordfreq.
- [ ] Run `next iteration` and inspect:
  - `EnglishMap_Auto` row count
  - `EnglishPromotions_Auto` applied/skipped reasons
  - StrictPlus metrics (EvAvg/Weak/Micro/Single/Tokens)
- [ ] Run validator.

## Implementation Log
- Files changed:
  - `./scripts/bonelord_flow_next_iteration.py`
  - `./docs/plans/iter357_english_layer_merge_pd_sigindex.md`

## Verification
- Ran:
  - `python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx` -> iter `357`
  - (no regressions; validator run later still passed after further iters)
- Outcome:
  - No new progress at iter 357 (`mech_promoted=0`, `books_changed=0/70`).
  - English layer remained at `map_rows=3` for that iteration; PD merge did not materially change mappings under current thresholds.
