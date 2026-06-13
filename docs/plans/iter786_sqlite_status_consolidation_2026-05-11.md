# Iter 786 - SQLite status consolidation and next gates

Date: 2026-05-11

This file supersedes the tactical March workbook-era ledger for day-to-day decisions. It does not replace `AGENTS.md`; it compresses the current operational state so future batches do not reopen stale branches by inertia.

## Canonical state

- Operational DB: `./data/bonelord_operational.sqlite`
- Historical/lossless DB: `./data/bonelord_workbook.sqlite`
- Live substrate: `row0` code-symbol reconstruction and `row0_variant_book_tokens`
- Legacy `.xlsx`: migration input or narrow confirmation artifact only, not live operational state

Latest status surfaces:

| surface | run | decision | key result |
|---|---:|---|---|
| `translation_progress_status_runs` | 46 | `FUNCTIONAL_PROGRESS_LEXICAL_TRANSLATION_UNSOLVED` | operational `100%`, functional books `100%`, semantic gloss `0%`, phrase GT `2`, book decode anchors `0`, actionable frontier `0` |
| `convergence_state_snapshot_runs` | 2 | `CONVERGENCE_STATE_FUNCTIONAL_COMPLETE_LEXICAL_UNSOLVED` | functional classes `13`, retext policies `18`, accepted external semantic anchors `0`, open targets `2` |
| `final_honest_reading_v19_runs` | 1 | `FINAL_HONEST_READING_V19_ALL_BOOKS_FUNCTIONALLY_TAGGED_NO_GLOSS` | `70/70` books functionally tagged, `0` gloss allowed |
| `functional_grammar_synthesis_v1_runs` | 22 | `FUNCTIONAL_GRAMMAR_COVERS_CONTIGS_NO_HUMAN_GLOSS` | `70` functional books, `8/8` contig edges covered, `0` human gloss |
| `goal_completion_audit_v1_runs` | 8 | `NOT_COMPLETE` | fails `C2_ALL_BOOKS_HUMAN_TRANSLATION` and `C4_EXTERNAL_TEXTS_TRANSLATED` |

Interpretation:

- The project is mechanically and functionally covered.
- The project is not lexically translated.
- `MODEL_CONVERGED`, functional tags, literal homophonic books, display shadows, and formula shadows must not be presented as human prose.

## Row0 invariant

`row0_code_symbol_probe_runs` run `1` validates the mechanical base:

- `70/70` books valid
- `0` invalid books
- `5729` base symbols
- `11263` observed digits
- `195` omitted leading-zero codes represented
- `99` distinct codes
- `0` conflicting codes
- `14` distinct symbols

`row0_variant_frontier_runs` run `1` preserves variants `00`, `02`, `20`, `23`, `32`, `68`, and `86`. This is the normal corpus for template, slot, variant, and boundary analysis.

## Latest convergence cycle

Cycle run on 2026-05-11:

- `best_shadow=31`
- `microtoken=28`
- `formula=26`
- `anomaly=31`
- `frontier=28`
- actionable semantic targets: `0`
- known/suspect exclusions: `34`
- blocked/audit-only exclusions: `46`
- known unresolved slots: `2`
- blocked phrases: `17`
- formula families: `1`

Meaning: the current internal semantic frontier is exhausted after excluding known slots and blocked/audit-only families. More smooth English from this layer would likely be false progress.

## Reliable knowledge

| class | evidence | use |
|---|---|---|
| Mechanical row0 | `row0_code_symbol_probe_runs=1`, `row0_omission_probe_runs=1` | primary base model |
| Functional grammar | `functional_grammar_synthesis_v1_runs=22` | structure, transitions, edge coverage |
| Functional book status | `final_honest_reading_v19_*` | audit-safe no-gloss book roles |
| Phrase-level holdouts | `phrase_level_gt_gate_runs=2` | validation holdouts only |
| Anti-hallucination masks | `semantic_known_unresolved_slots`, `semantic_blocked_phrases`, `formula_shadow_runs` | prevent stale/display text from becoming prose |
| Literal homophonic layer | `literal_homophonic_books_v1_runs=1` | segmentation and external alignment only |

Phrase-level GT currently has two useful holdouts:

- `Knightmare1`
- `Poll2014_C`

Both are phrase-level validation only. They do not allow component gloss, word dictionary derivation, or book-level prose promotion.

## Stale or dangerous surfaces

- `translation_progress_snapshots`: useful historical context, but last meaningful entries are from the April cutover and can overemphasize mechanical convergence.
- `translation_progress_status_runs_v2`: useful benchmark history, but current run is `translation_progress_status_runs=46`.
- `final_honest_reading_v2` through `v18`: lineage only; current book status is v19.
- `sheet__*` tables: imported legacy sheets for recovery and narrow source lookup, not status truth.
- `best_shadow`, `microtoken_neutral`, `formula_shadow`: audit/display layers only, not decode-core truth.
- Any external German/MHG-like full-corpus reading: shadow/audit candidate only unless it passes exact phrase GT and provenance gates.

Hard query rule:

- Prefer latest run tables with their explicit run IDs.
- Do not use `MAX(run_id)` from an item table alone as proof of current status unless the corresponding run table has been checked.

## Branch taxonomy

| category | examples | current action | reopen condition |
|---|---|---|---|
| Dead / discarded | direct `3478`, `Crib6/IIN-family/Book60/BTILBETA`, `Book38/Hellgate`, `AC010`, `AC013/017/019`, Chay1/AETT, Chay2/mid-right, direct `SA001/SA002` | do not reopen | only with a mechanically different SQLite precheck and new evidence source |
| Shadow-only / mechanical scaffold | `Book55 exactmacroblock`, `best_shadow`, `microtoken_neutral`, `formula_shadow` | keep for audit and comparison | only if it predicts a held-out structural class without toxic regression |
| Display-only | Book `6/32/36` display controls, BTII/NSBVN/ATFNAAST drift, FATCTIVVTISETE seams, ILEEI drift, stale stopword/macro seams | display/audit layer only | only for containment or readability marking, not core mutation |
| Anti-toxic containment | safer Books `5/9/53`, `<UNK:TTNVVN>`, `<SUSPECT:VTLRNEFIE>` | can remain canonical as containment | never count as translation progress |
| Local-context / no-gloss functional | Book30 context, C68 `8/23`, zero pairs `20/54` and `25/39`, VNCTIIN/C86/O23/VINVIN scoped frames | useful structural constraints | promote only as no-gloss functional class after contrast |
| Truly promotable prose | none currently | blocked | requires external/provenance or predictive validation plus `gloss_allowed=1` |

## Open semantic blockers

`remaining_five_evidence_requirements_v1_runs=2` reports five remaining evidence blockers:

| book | blocker | safest next probe |
|---|---|---|
| `6` | `DISPLAY_CONTINUITY_PHASE` | row0 phase/path disambiguation using operator selectors and 3478 boundary controls |
| `7` | `RARE_PHASE_CONTINUITY` | row0 phase/path disambiguation using operator selectors and 3478 boundary controls |
| `14` | `R02_LTAST_WEAK_BOUNDARY` | no immediate rerun unless new phase evidence appears |
| `32` | `FNAAST_DISPLAY_LOW_SIGNAL` | display-tail masking with held-out payload prediction |
| `36` | `DISPLAY_DRIFT_CONTROL` | display-tail masking with held-out payload prediction |

## Next hypotheses

Each lane must start with a SQLite precheck row and must end with `observed_outcome`, `dead_or_alive`, and `next_action`.

| family | reason_selected | prior_failures | expected_failure_mode | why_this_run_is_different |
|---|---|---|---|---|
| `C86_NONDELTA_PAYLOAD_CLASSIFIER` | `C68/C86` is the strongest current variant contrast; open non-delta payloads remain in books `5,18,31,36,57` | global C68/C86 collapse rejected; EVIEFIIN split firewalled; Book42 surface control | non-delta payloads collapse into same-family parallels | occurrence-native payload classes only, compared against resolved delta13 and EBFAI controls; no global C86 meaning |
| `TTNVVN_CONDITIONAL_LTAST_TAIL_SLOT` | existing gate promoted only books `35/58`; candidates remain `0,9,10,59,66` | tail-peel and exact-token holdouts had no independent promotable core | formula drift or toxic parent dependency | tests TTNVVN only under typed-exit chain support, not generic LTAST macro peeling |
| `O23_EXACT_PAYLOAD_WITH_O32_GUARD` | exact `O23 NAFIEI + VEINLETFNAAST` holds for `13/38`; controls `24/52/56/62` | global FNAAST rejected; O32 singleton audit-only; broad O23/ONAF blocked | Book56 or VINVIN suffix controls contaminate endpoint class | exact payload gate with O32 guard; no global O/O23/FNAAST gloss |
| `BOOK69_ALT_FORMULA_HEAD_TO_35` | `69->35` is a high-overlap non-contig BENNA formula-to-handoff edge | AC010 wrapper branch exhausted; `58->35` remains stronger control | transitive formula parallel, not hidden edge | tests one edge against controls, not workbook tuning |
| `R20_R02_SUPPORT_HOLD_RECHECK` | strict bridge is `51/53`; `46` support-only, `17/45` hold, 19 rejects | aggregate R20/R02 already represented; R20/VTLRNEFIE abandoned | support/hold classes do not reduce to ordered NAESE bridge | occurrence-pair gate by distance/status, no broad R20/R02 promotion |
| `EXPLICIT_SEQUENCE_MEANING_SOURCE_ONLY` | lexical progress needs source-attested sequence-to-meaning evidence | prior external sources mostly attest copied sequences, co-utterance, or fan guesses | no exact meaning found | accept only exact sequence plus explicit meaning/provenance; ingest as audit-only until contrast passes |
| `PARADOX_TOWER_MATHEMAGIC_MODEL` | in-game math/operator lore may constrain function without prose shadow | prior text smoothing and external candidates failed phrase GT | produces numerology without held-out prediction | pre-register operators, then require prediction of held-out external phrase or functional class |
| `FUNCTIONAL_TAG_TO_LORE_ROLE_CONTRAST` | current functional tags may map to library/Hellgate roles without lexical gloss | lore adjacency is not translation evidence | broad lore narrative overfits | accept only if it predicts held-out book grouping or external corpus placement |

## Batch outcomes after consolidation

Two no-gloss SQL-native probes were run immediately after this consolidation:

| family | run | observed_outcome | dead_or_alive | next_action |
|---|---:|---|---|---|
| `C86_NONDELTA_PAYLOAD_CLASSIFIER` / `sqlite_c86_payload_class_probe.py` | `c86_payload_class_probe_runs=2` | `17` C86 occurrences across `17` books split into `7` payload classes; `contig_supported_count=0`; decision `C86_PAYLOAD_CLASSES_CONTEXT_ONLY`; `gloss_allowed=false` | alive only as context/contradiction layer; not a prose or promotion lane | keep payload classes as no-gloss context; do not prioritize unless a held-out prediction appears |
| `C86_SUBFAMILY_PREDICTIVENESS` / `sqlite_c86_subfamily_predictiveness_probe.py` | `c86_subfamily_predictiveness_probe_runs=4` | split precision `0.1111` ties aggregate precision `0.1111`; decision `C86_SPLIT_TIES_EDGE_SPECIFICITY_KEEP_FOR_CONTRADICTION_REDUCTION_NO_GLOSS` | alive for contradiction reduction only | keep C86 subfamilies no-gloss; no global C86 meaning |
| `TTNVVN_FORMULA_SLOT` / `sqlite_resolve_ttnvvn_formula_slot.py` | `ttnvvn_formula_slot_probe_runs=2` | `10` hits in `10` books; `33` anomaly phrases in latest anomaly run; decision `TTNVVN_FORMULA_SLOT_RESOLVED_AS_UNKNOWN_NO_GLOSS` | alive as known structural unknown/formula slot | keep `<UNK:TTNVVN>` behavior; only `35/58` have prior conditional LTAST-tail structural promotion |
| `TTNVVN_ANOMALY_RESOLUTION` / `sqlite_resolve_ttnvvn_anomalies.py` | `semantic_anomaly_resolution_runs=2` | `33` TTNVVN anomaly phrases resolved as no-gloss formula-slot unknowns | dead as lexical/prose target | do not reopen `tumtum` or any TTNVVN gloss without independent evidence |

Post-batch convergence cycle still reports `actionable_count=0`, with `34` known/suspect exclusions and `46` blocked/audit-only exclusions. The next real frontier is therefore external/provenance evidence or a mechanically different structural prediction, not another C86/TTNVVN prose attempt.

## Promotion gates

No branch can count as strong promotion unless all apply:

- `GT bad_enforced=0`
- `soft=0`
- `ExternalRoundTrip` stable or explicitly irrelevant for a no-gloss structural class
- no toxic regression in known protected corridors
- local reading improvement or contradiction reduction is defensible
- `gloss_allowed=1` only after external/provenance or predictive validation

Current default: promote structural/no-gloss packages only; keep prose blocked.

## Commands used for this consolidation

```bash
python scripts/sqlite_convergence_cycle.py --discord
python scripts/sqlite_translation_progress_status.py --discord
python scripts/sqlite_convergence_state_snapshot.py
python scripts/sqlite_goal_completion_audit_v1.py
python scripts/sqlite_remaining_five_evidence_requirements_v1.py
python scripts/sqlite_unresolved_function_frontier_rank_v1.py
python scripts/sqlite_semantic_question_queue_v1.py
python scripts/sqlite_frontier_precheck.py --family BENNA_FORMULA --search BENNA --limit 5
python scripts/sqlite_frontier_precheck.py --family NAESE_SLOT --search NAESE --limit 5
python scripts/sqlite_frontier_precheck.py --family VINVIN_BRANCH --search VINVIN --limit 5
python scripts/sqlite_frontier_precheck.py --family O23_ENDPOINT --search ONAF --limit 5
python scripts/sqlite_frontier_precheck.py --family DISPLAY_TAIL_PAYLOAD --search FNAAST --limit 5
python scripts/sqlite_frontier_precheck.py --family LTAST_TAIL --search LTAST --limit 5
```

## Status fix applied

`scripts/sqlite_translation_progress_status.py` was updated on 2026-05-11 to prefer `final_honest_reading_v19` before older `v16..v3` fallback layers. The previous `95.714%` status was a stale fallback to v16, not a real regression. Re-run after the fix posted `functional_tagged_book_pct=100.0`.

## Completion audit for this review goal

Thread objective: review the project, understand and consolidate current Bonelord translation status, clear stale learning paths, identify replicable hypotheses, and advance the translation process without overstating lexical completion.

| requirement | evidence | status |
|---|---|---|
| Understand current translation status | `translation_progress_status_runs=46`, `final_honest_reading_v19_runs=1`, `goal_completion_audit_v1_runs=9` | done |
| Separate functional progress from lexical translation | this file records `100%` functional books and `0%` semantic gloss; goal audit fails `C2` and `C4` | done |
| Consolidate reliable knowledge | sections `Canonical state`, `Row0 invariant`, `Reliable knowledge`, and `Latest convergence cycle` | done |
| Clean stale paths and dangerous surfaces | sections `Stale or dangerous surfaces` and `Branch taxonomy`; status script fixed to prefer v19 | done |
| Identify new replicable hypotheses | section `Next hypotheses` with family, reason, prior failures, expected failure mode, and why different | done |
| Advance the translation process after consolidation | C86 and TTNVVN SQL-native no-gloss probes were run and recorded; post-batch cycle still reports actionable frontier `0` | done |
| Avoid false lexical promotion | promotion gates require `gloss_allowed=1` only after external/provenance or predictive validation; C86 and TTNVVN were kept no-gloss | done |
| Verify current project translation completion honestly | `goal_completion_audit_v1_runs=9` is `NOT_COMPLETE`, with failures `C2_ALL_BOOKS_HUMAN_TRANSLATION` and `C4_EXTERNAL_TEXTS_TRANSLATED` | done |

Conclusion for this thread goal:

- The review/consolidation objective is complete.
- The full Bonelord translation objective is not complete.
- Future work should continue from external sequence-meaning evidence, predictive structural models, or the explicitly listed no-gloss structural gates.
