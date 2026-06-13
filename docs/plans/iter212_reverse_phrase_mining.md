# Iter 212 - Reverse Phrase Mining (Corpus -> Base Search) + Corpus Import Hook

## Goal
Break the plateau safely by adding a new **reverse direction** capability:
- take user-provided *official/lore phrases* (English, possibly archaic),
- canonicalize them via the already-confirmed Rules mapping,
- search for matching **base token signatures** inside `Books.DecodedBase`,
- log hits and optionally emit **inactive candidate tokens** into `Glossary` so the existing SAFE mechanical loop can simulate/promote them.

This keeps the core loop conservative:
- no GroundTruth edits
- no promotions without the existing simulation guardrails (GT live check + no Weak/Micro/Single increases)
- everything logged inside the XLSX (FlowRunLog + new Auto sheets)

## Constraints / Guardrails
- GroundTruth Live Check (Step 12) blocks if mismatching.
- No web scraping in the runner; corpus is user-provided in-sheet or imported from local files by a separate script.
- Any new token candidates must start `Use_StrictPlus_v108=0` and be promoted only through Step 40 simulation.

## Tasks (Status)
- [x] Add Step 28 to the runner: Reverse Phrase Mining (analysis-only + optional candidate token emission).
- [x] Add `ReversePhrase_*` FlowSettings knobs with safe defaults.
- [x] Add new sheets (idempotent): `PhraseCribs_User`, `ReversePhraseHits_Auto`, `ReversePhraseTokenCands_Auto`.
- [x] Add local corpus importer script `scripts/bonelord_import_corpus.py` to append lines into `LoreCorpus_User`.
- [x] Update validator to expect Step 28.
- [x] Run Iter212+ until stale; capture per-iteration evolution stats (mech/semantic/metrics) and reverse-mining stats.

## Implementation Notes
- Phrase canonicalization uses the existing confirmed mapping in `_lore_canon_word`:
  - `th->t`, `w/u->v`, `y->i`, `d->t`, `m->n`, `p->b`, optional drops (`h`, `o`, final `e`).
- Matching is done over **token signatures** (sorted letters, ignoring `*`), allowing each phrase word to match a span of `1..K` current base tokens.
- Output is analysis-only unless `ReversePhrase_AutoEmitCandidates=TRUE`.

## Implementation Log
- Runner updates:
  - `./scripts/bonelord_flow_next_iteration.py`
    - Added FlowSettings keys: `ReversePhrase_*`
    - Added FlowSteps entry: `28 Reverse Phrase Mining`
    - Implemented `PhraseCribs_User` + reverse phrase matcher:
      - writes `ReversePhraseHits_Auto` + `ReversePhraseTokenCandidates_Auto`
      - optional emission of inactive candidates into `Glossary` (EvidenceClass=`PHRASE_CRIB`) for SAFE simulation/promotion
- Validator updates:
  - `./scripts/bonelord_validate_workbook.py`
    - now expects Step `28` and blocks if Step `28` is `FAILED`
- Stale runner updates:
  - `./scripts/bonelord_run_until_stale.py`
    - treats `rev_emit>0` as non-stale progress
- Corpus import hook:
  - `./scripts/bonelord_import_corpus.py`
    - imports plaintext lines into `LoreCorpus_User` from a local file (no network)

- Workbook run:
  - Iter212: reverse phrase mining ran with `0` enabled phrases (no changes)
  - Iter213-214: stale (mech=0, sem_retext=0, rev_emit=0; metric deltas all zero)
  - Iter215: created `ReversePhraseHits_Auto` + `ReversePhraseTokenCandidates_Auto` even with 0 phrases (interface stability)
  - Iter215+: renamed to `ReversePhraseTokenCands_Auto` to satisfy Excel 31-char sheet title limit
  - Iter216: added new `ReversePhrase_Include*` FlowSettings keys into the workbook (no changes)
  - Validation: `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx` OK at iter216
