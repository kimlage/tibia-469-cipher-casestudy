# Final Inspiration Model Report

Generated: 2026-06-20  
Translation delta: `NONE`

## Verdict

No new real direction toward discovering a translation formula was found.

The pass was still useful because it closed source lanes and turned the
Knightmare/D&D/lore material into a controlled mechanism library. It did not
change the project verdict: the 70-book corpus remains verified non-linguistic
under the current evidence rules, and no plaintext promotion is admissible.

## What Was Researched

| Lane | Result |
|---|---|
| Official/in-game/CipSoft | No `official_gt`; only known official/unglossed strings and lore. |
| EN/global | Duplicate known sources; rejected 2026 fan/GitHub solution claims. |
| PT-BR/BR | Best source hygiene gain: current public URLs for `74032 45331`, Bonelord Tome, Wrinkled transcript, Chayenne/Avar inventory. |
| PL | Strong negative consensus and rejected old forum/numerology routes. |
| ES/LATAM | Duplicate inventory and fan-claim pointers; eye-count variant already covered. |
| DE/other | No promoted/official German ground truth; fan vocabulary rejected. |
| Knightmare/quest corpus | Useful comparandum library, not authorship proof or decoder. |
| D&D/Beholder | Inspiration only; weak clue after controls. |

## New Evidence

No new semantic evidence. New value is limited to source hygiene and closure:

| Evidence | Status |
|---|---|
| Bonelord Tome PT-BR page | Reliable phrase/source provenance; no new gloss. |
| PL negative-consensus pages/forums | Better rejected-route provenance; no new evidence. |
| ES/LATAM inventory | Duplicate known strings; no new evidence. |
| DE/other-language search | Source family closed negative for current pass. |

## Hypotheses Tested

| ID | Hypothesis | Test artifact | Classification |
|---|---|---|---|
| H19 | D&D eye-ray structure inspired a 10-channel digit system | `tests/dnd_eye_ray_d10_channel_test.py` | `weak_clue` |
| H20 | zero / omitted zero may encode central-eye suppression | `tests/central_eye_zero_suppression_test.py` | `weak_clue` |
| H21 | Knightmare quest mechanisms are useful comparanda | `tests/02_extract_quest_mechanisms.py`, `tests/authorial_source_classifier.py` | `accepted_mechanical` as process/ontology only |
| H22 | Excalibug is a language-gated route | `tests/excalibug_bonelord_language_anchor_audit.py` | `blocked_waiting_for_official_source` |
| H23 | Dreamer duality explains phrase/book split | `tests/dreamer_duality_layer_split_test.py` | `watchlist_only` |
| H24 | Books are better modeled as knowledge objects/entities | `tests/library_entity_ontology_crosswalk.py` | `weak_clue` |

## Test Results

All new scripts ran successfully with `translation_delta = NONE`.

Highlights:

- D&D/K5/5x2 eye models remain weak and rejected as row0 origin formulas.
- Zero/central-eye framing reuses an existing render-context signal but does
  not beat the semantic gate or become a compact formula.
- Subjective viewer is accepted as render/orientation mechanics only.
- NPC keyword/source-class routing is useful as a process guard, not prose.
- Excalibug is blocked until an official Bonelord-language prompt/answer or
  gloss appears.
- Yalahar/Dreamer/PoI remain watchlist analogies without fixed predictions.

## Contradictions Found

No contradiction invalidates the frozen report. Repeated community claims that
`1`, `486486`, or `3478` are "known words" must be scoped:

- `1 = Tibia` and `486486 = A Wrinkled Bonelord self-name` are transcript
  anchors.
- They are not book-layer codebook permissions.
- `3478` remains phrase/source context, not a general word key.

## What Really Advanced

- Source-family closure across EN, PT-BR, PL, ES/LATAM, DE/other.
- A structured source registry with allowed and blocked uses.
- A reusable mechanism ontology for quest/lore comparanda.
- Executable audit wrappers that preserve existing controls and blockers.

These are structural/process advances, not semantic progress.

## What Was Rejected

- German/MHG and 94.6% fan solution routes.
- Blog/forum vocabulary mappings.
- Avar Tar as true 469.
- Secret Library `74032 45331` as a translated key.
- Honeminas/Magic Web as direct decoder.
- D&D/Beholder as proof of authorial intent or semantics.

## Outcome Ledger

| Metric | Value after this pass |
|---|---:|
| `CRIBS_REPRODUCED_UNDER_HOLDOUT` | 0 |
| `CODES_CONFIRMED_EXTERNALLY` | 0 |
| `BOOKS_NO_PROSE_TO_ACCEPTED` | 0 |
| `GT_PHRASES_PASSING_EXTERNALLY` | 0 |

Round result: `NEGATIVE / plateau confirmed`.

## Next Steps

Only falsifiable routes remain:

1. Monitor for official CipSoft/in-game ground truth.
2. If client/source data for Bonelord Tome can be independently extracted, use
   it only to confirm phrase-layer provenance.
3. Run no broad decode search unless a new official source supplies a concrete
   target, control, and stop rule.

Conclusion: no new real formula-discovery direction emerged.
