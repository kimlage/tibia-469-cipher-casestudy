# Iter301: Public-Domain SigIndex + Bigrams (Plateau Escape, Safe)

Goal: expand semantic/context candidate coverage beyond Tibia-only corpora, without touching the StrictPlus decode mechanics. This is intended to break the current plateau where most tokens have no usable candidates, so ContextEnglish can actually disambiguate and then emit GT-safe promotions.

Constraints (must hold every iteration)
- `Coverage_StrictPlus_v108 == 1` for all 70 books.
- `groundtruth_live_check()` must pass.
- Do not persist full copyrighted corpora in the XLSX. Only derived counts/snippets+URL.
- Public domain corpora are allowed; prefer derived-only even for PD to keep workbook size stable.

## Tasks
- [x] Add PD-derived signature index sheet(s):
  - `LoreSigIndex_PD_Auto` (Sig->Word->Count, derived from PD corpus text)
  - `LoreWordFreq_PD_Auto` (global wordfreq, derived counts only)
- [x] Merge `LoreSigIndex_PD_Auto` into `LoreAlignment_Auto` inputs (alongside Tibia sig-index).
- [x] Extend `LoreBigrams_Auto` builder to optionally ingest PD corpus cache(s) so ContextEnglish can use those words (known_words) and transitions.
- [x] Add FlowStep + FlowRunLog entry for the PD fetch/refresh (`StepID=109`).
- [x] Keep everything idempotent and time-bounded with caching + max-age.
- [x] Update validators:
  - `scripts/bonelord_validate_workbook.py` expected steps include new step.
  - (optional) `scripts/bonelord_run_until_stale.py` can be extended to track PD stats later (not required).
- [x] Run `next iteration` until stale (cap ~10) and record evolution stats per iteration in this doc.
- [x] Expand PD sources beyond KJV (multi-URL ingest) to improve coverage and break plateaus further.
  - Multi-URL support in `LoreSigIndex_PD_Auto`, `LoreBigrams_Auto`, and `SequenceMatches_Auto`.
  - Plateau rung>=2 auto-seeds extra PD URLs (currently: Gutenberg Alice + Sherlock) into FlowSettings.
  - PD sig-index now uses a config fingerprint (`FlowState.PDSigIndexFingerprint`) so changes force refresh even when MaxAgeHours is not exceeded.

## Defaults (can be tuned in `FlowSettings`)
- PD corpus: Project Gutenberg KJV (`https://www.gutenberg.org/files/10/10-0.txt`) (public domain).
- Refresh cadence: weekly (MaxAgeHours=168..720 depending on sheet).
- All downstream promotions remain GT-guarded and safe.

## Implementation Log
- 2026-02-08: implemented PD sig-index + PD bigram ingestion.
- 2026-02-08: ran iterations 301..304 and validated invariants (`Coverage_StrictPlus_v108==1` and GT live check OK).

### Evolution Stats (301..304)
- Iter 301:
  - StrictPlus metrics unchanged: `EvAvg=2.326444`, `Weak=0.039798`, `Micro=0.030023`, `Single=0.019899`, `Tokens=893`
  - LoreAlignment expanded: `lore_hits_rows=201` (was 191), `semantic_map_rows=174` (was 163)
  - LoreBigrams refreshed: `rows=70038` (now includes PD corpus)
  - ContextEnglish improved: `avg_score=5.292172` (prev ~3.909564), `map_rows=4`, `SequenceMatches fp_changed=1`
- Iter 302:
  - English glossary retext applied: `4` (GT-safe)
  - StrictPlus books_changed: `1/70` (expected because we edited translations)
  - ContextEnglish stable: `avg_score=5.292172`, `map_rows=2`
- Iter 303:
  - No further changes (stabilizing)
- Iter 304:
  - No further changes (stale per loop definition)

### Follow-up (Iter305..Iter307)
- 2026-02-08: extended SequenceMatches to also scan the cached PD plaintext (time-budgeted; snippets only).
- Iter 305:
  - `SequenceMatchesCount` increased `7 -> 10` (mostly PD hits), and `SequenceWordHints_Auto` updated accordingly.
- Iter 306..307:
  - Stable (stale by loop definition).

### Follow-up (Iter308..Iter311) - Multi-PD Expansion
- 2026-02-08: enabled multi-PD ingestion (KJV + Alice + Sherlock).
- Iter 308:
  - `LoreSigIndex_PD_Auto` grew `271 -> 362` rows (derived-only).
  - Lore/Semantic: `lore_hits_rows=204`, `semantic_map_rows=176` (both increased).
  - `LoreBigrams_Auto` refreshed `70038 -> 74392` rows (derived-only; includes extra PD sources).
  - ContextEnglish improved: `avg_score=5.381020` (from `5.292172`), `oov=0.140740` (from `0.144226`).
  - SequenceMatches increased: `10 -> 12` (fp_changed=1).
- Iter 309:
  - English retext applied: `3` (GT-safe); minor display-layer changes only (mechanical metrics unchanged).
- Iter 310..311:
  - Stable (stale by loop definition).

### Follow-up (Iter312..Iter329) - PD Expansion + Loop Stabilization
- 2026-02-08: plateau ladder auto-expanded PD extras further (still derived-only) to include:
  - Gutenberg KJV (10) + Alice (11) + Sherlock (1661) + Shakespeare (100) + Paradise Lost (26)
- Iter 312:
  - `LoreSigIndex_PD_Auto` refreshed to `sig_rows=614` (sigs_hit=94 / target_sigs=137).
  - `LoreBigrams_Auto` refreshed to `rows=109528`.
  - ContextEnglish improved materially: `avg_score=6.218555`, `oov=0.121261`.
  - `SequenceMatches` increased: `12 -> 17` (fp_changed=1).
  - Lore/Semantic expanded: `lore_hits_rows=208`, `semantic_map_rows=178`.
- Iter 313..327:
  - Found an oscillation in Step 99 (English retext) flipping `set <-> these` for tokens `EST/STE`.
  - Implemented anti-oscillation guardrail: `EnglishGlossaryRetext_LockIters` (default 5) to prevent repeated flips.
- Iter 328..329:
  - Stable again (stale by loop definition), with GT and coverage invariants preserved.
