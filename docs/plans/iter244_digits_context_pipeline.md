# Iter 244 - Digits->Base Map + Context English + Sequence Match (Plateau Exit)

## Goal
Break the “mechanical plateau” safely by formalizing what the workbook already proves:
- The encoding is a deterministic `digits -> codes -> base letters` pipeline with **homophones** (many codes per letter).
- The remaining work is **structure/choice** (omission pattern + token choice) and **contextual disambiguation** for readability.

This iteration adds safe, display-only + audit steps:
- `DigitCodeMap` (analysis-only): extract and persist the global code->base-letter map and homophone sets.
- `ExternalRoundTripCheck` (analysis-only): validate verified external numeric references still decode consistently under current StrictPlus tokenization.
- `CorpusBigramIndex` (derived-only): build a word-bigram index from public corpora (Tibia cache + public-domain lore) without storing full copyrighted text in the XLSX.
- `ContextEnglishRender` (display-only): Viterbi context render using (LoreAlignment candidates + bigram LM) to improve English surface forms without touching core DP.
- `SequenceMatches` (analysis-only): attempt longer-span alignment between ContextEnglish output and corpora, storing only short snippets + URLs.
- Status semantics: keep `RESOLVED` meaning “mechanically stable”, add `PUZZLE_SOLVED` for stronger, roundtrip-based success.

## Guardrails (must hold)
- `Coverage_StrictPlus_v108 == 1` for all 70 books.
- `GroundTruth Live Check` must pass on every iteration (hard block).
- No full external corpus text persisted into workbook (only derived counts/indices + capped snippets + URLs).
- No mechanical relaxations: no increases to WEAK/Micro/Single from promotions.

## Tasks (Status)
- [x] Add new FlowSettings knobs for the new steps (caps, thresholds, alpha smoothing).
- [x] Add new FlowSteps entries (DigitCodeMap / ExternalRoundTripCheck / CorpusBigramIndex / ContextEnglishRender / SequenceMatches / IterMeta).
- [x] Implement Step `101 DigitCodeMap` -> write `DigitCodeMap_Auto` + `DigitLetterCodes_Auto` and log stats to `FlowRunLog`.
- [x] Implement Step `102 ExternalRoundTripCheck` -> write `ExternalRoundTrip_Auto` and log PASS/FAIL counts (Expected_Norm canonized via `normalize_for_match()`).
- [x] Implement Step `103 CorpusBigramIndex` -> write `LoreBigrams_Auto` (top-N) derived from:
  - cached Tibia corpus under `tmp/corpus/` (NPC + books JSON)
  - `LoreCorpus_Auto` (public domain)
- [x] Implement Step `104 ContextEnglishRender` -> write:
  - `Books.Translation_ContextEnglish_Auto`
  - `MasterText.Translation_ContextEnglish_Auto`
  - `EnglishMap_Context_Auto`
  - per-iteration context metrics into `FlowRunLog` + FlowState (`ContextEnglishAvgScore`, `ContextEnglishImproveStreak`)
- [x] Implement Step `105 SequenceMatches` -> write `SequenceMatches_Auto` (snippets only; capped rows) and fingerprint change tracking in FlowState.
- [x] Implement Step `106 IterMeta` -> write `Iter{N}_Meta` diagnostics (lore ambiguity, external pass/fail, context stats).
- [x] Update status logic: allow `PUZZLE_SOLVED`, keep `RESOLVED` as mechanical stability (loop continues regardless).
- [x] Update `scripts/bonelord_validate_workbook.py` expected steps + invariants for new steps.
- [x] Update `scripts/bonelord_run_until_stale.py` to treat context/sequence progress as non-stale.
- [x] Run iterations and validate with `bonelord_validate_workbook.py`.

## Implementation log
- Runner updated: `scripts/bonelord_flow_next_iteration.py` (new steps 101-106 wired into the loop, logged each iter).
- Validator updated: `scripts/bonelord_validate_workbook.py` now requires steps `{101..106}`.
- Stale runner updated: `scripts/bonelord_run_until_stale.py` includes context/sequence fields in the table + staleness checks.

### Verification runs
- Iter 244:
  - Mechanical metrics unchanged and still RESOLVED.
  - Digit map extracted: `codes=99`, `missing=39`, `conflicts=0` (deterministic).
  - Lore bigrams refreshed: `LoreBigrams_Auto` ~43k rows.
  - ContextEnglish rendered (first time): BooksChanged=70, MasterChanged=6.
  - ExternalRoundTrip: 1 pass, 2 fail (tight mismatches; tracked in `ExternalRoundTrip_Auto`).
  - `scripts/bonelord_validate_workbook.py` OK.
- Iters 245-246: stale under the updated definition (no mech changes + no context improvements).
- Iter 247: ContextEnglish improved after loosening logogram gating (avg_score rose; map_rows increased).
- Iter 248: English retext attempted; one unsafe mapping slipped through earlier and was later fixed.
- Iter 261: Added English auto-revert + wordfreq guardrails; reverted the unsafe English retext (GT-safe).
- Iter 263: Context ladder auto-relaxed (rung=2) so `EnglishMap_Context_Auto` emits more stable suggestions.
- Iter 264: Context suggestions attempted, but GT live check correctly blocked unsafe promotions (kept core stable).

### Current known blockers
- ExternalRoundTrip (verified) still has 2 mismatches:
  - `Knightmare1`: extra `*` token in DP_Norm vs expected.
  - `Poll2014_C`: `away` vs `way`.
  These are now canonized consistently, so remaining mismatches are real deltas to investigate.
