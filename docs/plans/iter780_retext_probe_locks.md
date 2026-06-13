# Iter 780: Probe locks for retext-safe shadow experiments

## Goal
Add a per-token lock/denylist so shadow probes can pin selected glossary translations during one iteration without reverse/english/semantic retext overwriting them.

## Tasks
- [done] Patch runner settings + helpers for token-level retext lock.
- [done] Apply the lock inside reverse/semantic/english glossary retext passes.
- [done] Validate the lock in a shadow probe with `IVNA -> vain`.
- [done] Promote the successful stabilization to the canonical workbook.
- [pending] Prepare the next structural probe for the `Book 55` macro family.

## Implementation log
- [done] Reviewed runner hotspots for reverse phrase retext, semantic glossary retext, english glossary retext, and semantic reverts.
- [done] Added `GlossaryRetext_LockedTokens` to `FlowSettings` parsing/ensure path in `./scripts/bonelord_flow_next_iteration.py`.
- [done] Threaded `locked_tokens` through:
  - `apply_semantic_promotions_to_glossary`
  - `apply_english_promotions_to_glossary`
  - `revert_semantic_promotions_if_unsafe`
  - `apply_reverse_phrase_retext_existing_tokens`
- [done] Guarded both forward and auto-revert English retext paths so a shadow probe cannot be undone in the same iteration.
- [done] Confirmed the historical oscillation on `IVNA`: repeated `yawn -> vain` by English retext, then `vain -> yawn` by reverse retext through many iterations.
- [done] Ran shadow workbook `./tmp/p54_ivna_probe_lock.xlsx` with `GlossaryRetext_LockedTokens=IVNA` and forced `IVNA -> vain`.
- [done] Shadow result: `IVNA` remained `vain`; no GT or mechanical regressions (`Iter 781`, `GT 0/0/0`, `Tokens 311`, `EvAvg 2.333950`).
- [done] Promoted `IVNA -> vain` to `./bonelord_469_iter129.xlsx` and added canonical lock for `IVNA`.
- [done] Canonical result: `Iter 781` passed with unchanged hard metrics and local reading improvement in `Book 54`.
- [done] Inspected the `Book 55` family and confirmed the next issue is parse/macro competition rather than a simple retext drift.
