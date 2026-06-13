# Iter 207 - Semantic/Lore Layer (Display-Only) + Safer Translation Progress

## Goal
- Keep the mechanical decode loop safe/stable (GT live check + StrictPlus coverage + risk caps).
- Add a **semantic + lore-aware layer** that can improve *useful readability/meaning* without touching the core DP/Glossary.
- Make progress reproducible and auditable inside the XLSX (new sheets + per-iteration logs).

## Constraints / Guardrails
- Do not modify `Translation_StrictPlus_v108` outputs except via existing mechanical promotions.
- GroundTruth live check remains a hard guardrail: any GT mismatch blocks.
- New semantic outputs must be **display-only** columns/sheets.

## Tasks (Status)
- [x] Add new FlowSettings knobs for lore/semantic steps (enable flags + canonicalization toggles + thresholds).
- [x] Add new FlowSteps entries (92/93/94/95) kept in-sync by the runner.
- [x] Implement Step 92: ensure lore corpus sheets exist + seed default corpus (idempotent).
- [x] Implement Step 93: compute lore signature hits between corpus words and Glossary leaf tokens.
- [x] Implement Step 94: derive `SemanticMap_Auto` (display-only) from lore hits (conservative selection).
- [x] Implement Step 95: materialize `Translation_Semantic_Auto` for `Books` and `MasterText` (macro-expanded, token-based render).
- [x] Expand auto-seeded EN corpora beyond Jabberwocky (KJV excerpt + Shakespeare excerpt + curated archaic core).
- [x] Add Step 96: optional **semantic->Glossary retext** (string-only) guarded by GT live check + logged in `SemanticPromotions_Auto`.
- [x] Decouple core recompute/metrics/mining from the stored lossless-translation stream so Glossary retext cannot break DP (tokenize base directly).
- [x] Extend iteration outputs: print and log semantic stats each run.
- [x] Update `scripts/bonelord_validate_workbook.py` with invariants for the new semantic layer.
- [x] Update validator + run-until-stale script to account for semantic glossary retext (step 96).
- [x] Run `next iteration` once (Iter207) and validate workbook.

## Implementation Log
- Updated runner:
  - `./scripts/bonelord_flow_next_iteration.py`
  - Added FlowSettings keys + FlowSteps 92/93/94/95 + implementation for Lore/Semantic display layer.
- Updated validator:
  - `./scripts/bonelord_validate_workbook.py`
  - Added expected FlowRunLog steps for lore/semantic.
- Ran Iter207:
  - Backup: `./tmp/spreadsheets/bonelord_469_iter129_backup_iter207.xlsx`
  - Mechanical evolution deltas: all `0` (EvAvg/Weak/Micro/Single/Tokens unchanged).
  - Lore/Semantic outputs:
    - `LoreCorpus_Auto` seeded: `+24` rows (JABBERWOCKY_EN)
    - `LoreAlignment_Auto`: `25` rows
    - `SemanticMap_Auto`: `25` rows
    - Semantic render: `semantic_repl=190`, `Books changed=70`, `MasterText changed=6` (display-only columns)
- Validation:
  - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx` OK at iter207.

## Follow-up (Iter208)
- Tweaked lore signature indexing to store **surface words** (e.g., `and`, `tumtum`) while still matching by canonical signatures.
- Ran Iter208:
  - Backup: `./tmp/spreadsheets/bonelord_469_iter129_backup_iter208.xlsx`
  - Mechanical evolution deltas: all `0` (EvAvg/Weak/Micro/Single/Tokens unchanged).
  - Lore/Semantic: `lore_hits_rows=25`, `semantic_map_rows=25`, `semantic_repl=190`, `semantic_books_changed=63`, `semantic_master_changed=6`.
- Validation OK at iter208.

## Iter209-211 (English/Old-English Push + Plateau Exit)
- Updated runner:
  - Expanded `LoreCorpus_Auto` seed to include:
    - KJV Bible excerpts (public domain; Gutenberg #10)
    - Shakespeare Hamlet excerpt (public domain; Gutenberg #1524)
    - Curated archaic EN function words (manual)
  - Added Step 96 (`Semantic -> Glossary Retext`):
    - Applies high-confidence semantic hints into `Glossary.Translation` (string-only), guarded by GT live check.
    - Syncs `EvidenceLedger_v127.Translation` for consistency.
    - Logs attempts/applied rows in `SemanticPromotions_Auto`.
  - Refactored recompute + metrics + macro mining to avoid using `dp_align_base_to_lossless` (which depends on translation strings):
    - Use `dp_tokenize_base_with_punct` for tokenization everywhere.
    - Recompute `Translation_StrictPlus_LosslessMarkers_v108` from current tokenization so translations can evolve safely.
- Iter209 results (breakthrough):
  - Backup: `tmp/spreadsheets/bonelord_469_iter129_backup_iter209_2.xlsx`
  - Mechanical promotions: `27`
  - Semantic glossary retext applied: `9/10 attempted` (examples: `wit->with`, `than->and`, `nine->mine`, `true->wert`)
  - StrictPlus books changed: `48/70` (expected due to promotions + retext)
  - Token metrics (Books, weighted):
    - EvidenceAvg `2.326444`
    - WeakFrac `0.039798`
    - MicroFrac `0.030023`
    - SingleCharFrac `0.019899`
    - Tokens `893`
  - Lore/Semantic:
    - `LoreAlignment_Auto` rows: `53`
    - `SemanticMap_Auto` rows: `40`
- Iter210 + Iter211: stale (no mech promotions, no semantic retext, no metric deltas); validations OK.
