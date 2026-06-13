# Iter 787 - Human Translation Routes

Date: 2026-05-11
Coordinator: main thread
Canonical DB: `data/bonelord_operational.sqlite`
New registry: `human_translation_route_v1_*`

## Objective

Move the project from a purely defensive "no gloss until proven" posture into a
controlled human-translation workflow.

The canonical state is unchanged: the project still has functional coverage but
no accepted human translation for the books. Human-readable versions are now
allowed as shadow artifacts only when they are tied to in-game anchors, source
risks, functional tags, and falsifiable next probes.

## Current Status

- `translation_progress_status_runs` latest decision:
  `FUNCTIONAL_PROGRESS_LEXICAL_TRANSLATION_UNSOLVED`
- Functional coverage: `100%`
- Semantic gloss: `0%`
- Phrase-level GT: `2`
- Book decode anchors: `0`
- Actionable semantic frontier: `0`
- Final honest layer: `final_honest_reading_v19`
- Human route registry run: `human_translation_route_v1_runs.run_id=1`
- Registry decision: `HUMAN_TRANSLATION_ROUTES_READY_SHADOW_ONLY`
- Canonical gloss promoted by the registry: `0`
- First human shadow seed run: `human_shadow_reading_v1_runs.run_id=1`
- Revised human shadow seed run: `human_shadow_reading_v1_runs.run_id=2`
- Latest human shadow seed run: `human_shadow_reading_v1_runs.run_id=3`
- Latest Book12/21-aware shadow seed run:
  `human_shadow_reading_v1_runs.run_id=4`
- Shadow readings seeded: `7`
- Canonical promotions from shadow seed: `0`
- External phrase corpus run: `human_external_phrase_corpus_v1_runs.run_id=1`
- Shadow contradiction check run:
  `human_shadow_contradiction_check_v1_runs.run_id=4`
- Shadow contradiction result:
  `7/7` passed, `0` contradictions, `0` promotions
- Book30 family probe run:
  `human_book30_family_shadow_probe_v1_runs.run_id=1`
- Book7 phase probe run:
  `human_book7_phase_shadow_probe_v1_runs.run_id=1`
- Book49 repeat probe run:
  `human_book49_repeat_shadow_probe_v1_runs.run_id=1`
- Book54 pair probe run:
  `human_book54_pair_shadow_probe_v1_runs.run_id=1`
- Book12/21 tail probe run:
  `human_book12_21_tail_shadow_probe_v1_runs.run_id=1`
- Chayenne shape human probe run:
  `human_chayenne_shape_shadow_probe_v1_runs.run_id=1`
- Human Mathemagic synthesis run:
  `human_mathemagic_shadow_synthesis_v1_runs.run_id=1`
- In-game anchor corpus run:
  `human_ingame_anchor_corpus_v1_runs.run_id=1`
- Anchor-to-shadow bridge run:
  `human_anchor_to_shadow_bridge_v1_runs.run_id=1`
- Human translation atlas run:
  `human_translation_atlas_v1_runs.run_id=1`
- Chayenne branch shadow run:
  `human_chayenne_branch_shadow_v1_runs.run_id=1`
- Human translation atlas v2 run:
  `human_translation_atlas_v2_runs.run_id=1`
- Human completion audit run:
  `human_translation_completion_audit_v1_runs.run_id=1`
- C86/VNCTIIN bridge run:
  `human_c86_vnctiin_bridge_v1_runs.run_id=1`
- C86/VNCTIIN shadow run:
  `human_c86_vnctiin_shadow_v1_runs.run_id=1`
- Human translation atlas v3 run:
  `human_translation_atlas_v3_runs.run_id=1`
- Human completion audit v2 run:
  `human_translation_completion_audit_v2_runs.run_id=1`
- R20/R02 phase bridge run:
  `human_r20_r02_phase_bridge_v1_runs.run_id=1`
- R20/R02 phase shadow run:
  `human_r20_r02_phase_shadow_v1_runs.run_id=1`
- Human translation atlas v4 run:
  `human_translation_atlas_v4_runs.run_id=1`
- Human completion audit v3 run:
  `human_translation_completion_audit_v3_runs.run_id=1`
- Slot/formula bridge run:
  `human_slot_formula_bridge_v1_runs.run_id=1`
- Latest slot/formula shadow run:
  `human_slot_formula_shadow_v1_runs.run_id=2`
- Latest human translation atlas v5 run:
  `human_translation_atlas_v5_runs.run_id=2`
- Latest human completion audit v4 run:
  `human_translation_completion_audit_v4_runs.run_id=2`
- Residual bridge run:
  `human_residual_bridge_v1_runs.run_id=1`
- Residual shadow run:
  `human_residual_shadow_v1_runs.run_id=1`
- Human translation atlas v6 run:
  `human_translation_atlas_v6_runs.run_id=1`
- Human completion audit v5 run:
  `human_translation_completion_audit_v5_runs.run_id=1`
- Atlas v6 contradiction audit run:
  `human_atlas_v6_contradiction_audit_v1_runs.run_id=2`
- Current human atlas coverage: `70/70` books (`100.0%`)
- Current human atlas promotions: `0`

This means the project has a reliable mechanical skeleton, but not a solved
canonical plaintext translation. The project now has full shadow coverage:
plausible human readings exist for every book, but they remain review/falsify
artifacts, not promoted gloss.

## Web And In-Game Anchor Pass

Checked sources and current use:

| Source | In-game anchor value | Use | Risk |
| --- | --- | --- | --- |
| `https://tibia.fandom.com/wiki/469` | Hellgate and Isle of the Kings 469 books; public status that no solid proof exists | Status guard and corpus locator | Secondary wiki, no exact plaintext |
| `https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts` | Hellgate librarian dialogue: `486486`, `1`, `0`, numbers, mathemagic, name-as-formula | Primary semantic constraint | Transcript source, not a book gloss |
| `https://www.tibiawiki.com.br/469` | Knightmare phrase, Chayenne phrase, Avar Tar poem, Wyrdin, A Prisoner, Hellgate matrix, Great Calculator | Source inventory for cross-corpus comparison | Mixed provenance; verify each anchor |
| `https://www.tibia-wiki.net/wiki/Paradox_Tower_Quest/Spoiler` | Riddler/Mintwallin prisoner, surreal numbers, variable `1+1`, mathemagics | Operator and quest-context bridge | Spoiler source; per-player variation |
| `https://www.tibiawiki.com.br/wiki/You_Cannot_Even_Imagine_%28Book%29` | Great Calculator helped gather Bonelord language | Corpus-structure hypothesis | Translated wiki page, not a key |
| `https://www.tibiawiki.com.br/Honeminas_Formula` | Explicit Tibia formula notation tied to magic/web creation | Parallel formula grammar | Not Bonelord-specific unless bridged |
| `https://www.tibiaqa.com/20625/which-npcs-are-speaking-bonelord-469-language` | Avar Tar numeric poem and Wyrdin line | Out-of-book style/register comparator | Fansite answer, not exact meaning |
| `https://www.tibiaqa.com/9729/how-to-speak-bonelord-language-469` | Community math/cryptography/binary/skull-matrix clues | Anti-repeat weak hypothesis catalog | Community speculation |

Official `tibia.com` searches for direct current evidence did not produce a
usable exact phrase-plus-meaning source in this pass. Official/archived sources
remain higher priority if found later.

## In-Game Anchor Corpus

Persisted in `human_ingame_anchor_corpus_v1_*`.

Decision:
`HUMAN_INGAME_ANCHOR_CORPUS_READY_NO_BOOK_GLOSS`

Result:

- Anchor count: `10`
- Scoped anchors: `4`
- Operator anchors: `1`
- Register anchors: `2`
- Accepted book gloss: `0`

Anchors:

| Anchor | Type | Human use | Promotion status |
| --- | --- | --- | --- |
| `AWB_SELF_NAME_486486` | NPC numeric lore | proper-name/formula constraint | `SCOPED_LORE_ANCHOR_NO_BOOK_GLOSS` |
| `AWB_TIBIA_ONE` | NPC numeric lore | world/one numeric constraint | `SCOPED_LORE_ANCHOR_NO_BOOK_GLOSS` |
| `AWB_ZERO_TABOO` | NPC numeric lore | zero/taboo boundary constraint | `SCOPED_LORE_ANCHOR_NO_BOOK_GLOSS` |
| `AWB_469_LANGUAGE_MATHEMAGIC` | NPC language/method | method constraint | `METHOD_ANCHOR_NO_BOOK_GLOSS` |
| `PARADOX_1_PLUS_1_KEYS` | quest mathemagic operator | operator-key inventory | `OPERATOR_ANCHOR_NO_PLAINTEXT` |
| `GREAT_CALCULATOR_GATHER_LANGUAGE` | book lore/corpus structure | corpus-structure hypothesis | `CORPUS_STRUCTURE_ANCHOR_NO_BOOK_GLOSS` |
| `HONEMINAS_FORMULA_PARALLEL` | formula parallel | parallel formula grammar | `PARALLEL_FORMULA_ANCHOR_NO_BOOK_GLOSS` |
| `CHAYENNE_EXTERNAL_FRAME` | external shape holdout | register/frame holdout | `REGISTER_FRAME_ANCHOR_NO_SINGLE_GLOSS` |
| `KNIGHTMARE_3478_PHRASE` | external phrase holdout | name/formula phrase holdout | `PHRASE_HOLDOUT_NO_COMPONENT_GLOSS` |
| `AVAR_TAR_POEM_REGISTER` | NPC style/register holdout | poem/register comparator | `REGISTER_HOLDOUT_NO_BOOK_GLOSS` |

The important distinction: these anchors are now operational evidence rows, not
just source links in prose. Each anchor says what it allows and what it blocks.

## Anchor-To-Shadow Bridges

Persisted in `human_anchor_to_shadow_bridge_v1_*`.

Decision:
`HUMAN_ANCHOR_TO_SHADOW_BRIDGES_READY_NO_GLOSS`

Result:

- Bridges: `8`
- Targets: `8`
- Promoted gloss: `0`

Bridge map:

| Bridge | Target | Support level | Shadow claim |
| --- | --- | --- | --- |
| `B_BOOK49_MATH49_REGISTER` | Book `49` | `MECHANICAL_PLUS_LORE_OPERATOR` | self-contained repeat/formula witness and possible register selector |
| `B_BOOK7_PHASE_MATHEMAGIC` | Book `7` | `STRUCTURAL_WITH_METHOD_ANCHOR` | phase-continuity bridge rather than independent prose |
| `B_BOOK30_SPINE_GREAT_CALCULATOR` | Books `12/21/26/30` | `STRUCTURAL_PLUS_CORPUS_LORE` | spine/subfamily map, not linear prose |
| `B_BOOK12_21_NO_O23_IMPORT` | Books `12/21` | `NEGATIVE_CONTROL_PLUS_METHOD_ANCHOR` | tail/endpoint wording must stay structural, not O23-derived |
| `B_BOOK54_PAIR_LOCAL_SPINE` | Books `20/54` | `STRUCTURAL_WITH_ZERO_BOUNDARY_CONTEXT` | shared local-pair spine with own tail |
| `B_CHAYENNE_FRAME_REGISTER` | Chayenne -> Books `8/37/63/66` | `EXTERNAL_SHAPE_PLUS_BRANCH_TOPOLOGY` | reusable register/frame, not fixed sentence |
| `B_KNIGHTMARE_NAME_FORMULA_HOLDOUT` | Knightmare phrase | `SCOPED_NAME_ANCHOR_HOLDOUT` | 3478/name material remains formula/name holdout |
| `B_AVAR_REGISTER_HOLDOUT` | Avar Tar poem | `REGISTER_HOLDOUT_ONLY` | poem/register comparator, not Hellgate plaintext |

This bridge table is the current answer to "anchor the human translation in the
game": every plausible reading now has a declared source support level and a
declared overreach it is not allowed to make.

## Human Translation Atlas

Persisted in `human_translation_atlas_v1_*`.

Decision:
`HUMAN_TRANSLATION_ATLAS_READY_SHADOW_REVIEW_ONLY`

Result:

- Atlas items: `7`
- Anchored items: `7`
- Ready for human review: `7`
- Promoted gloss: `0`

Atlas:

| Book | Confidence tier | Bridge | Human reading |
| --- | --- | --- | --- |
| `7` | `STRUCTURAL_STRONG_SHADOW` | `B_BOOK7_PHASE_MATHEMAGIC` | phase-continuity line carrying a sequence through a local phase anchor |
| `12` | `STRUCTURAL_STRONG_WITH_NEGATIVE_ENDPOINT_CONTROL` | `B_BOOK12_21_NO_O23_IMPORT` | short Book30-family witness, almost entirely the shared `TAESESTIEN/VNSBLFSINNAI` base also present in Book `21`, with no direct `O23/ONAF/FNAAST` marker |
| `21` | `STRUCTURAL_STRONG_WITH_NEGATIVE_ENDPOINT_CONTROL` | `B_BOOK12_21_NO_O23_IMPORT` | Book30-family shared-base witness preserving nearly all of Book `12` and adding `TIVNSENI*LAELBEV` |
| `26` | `STRUCTURAL_MODERATE_FAMILY_SPINE` | `B_BOOK30_SPINE_GREAT_CALCULATOR` | branch-prefixed transition into the shared `VNSBLFSINNAI` spine and long-tail form |
| `30` | `STRUCTURAL_MODERATE_FAMILY_SPINE` | `B_BOOK30_SPINE_GREAT_CALCULATOR` | alternate Book30-family witness preserving `TAESESTIEN` and `VNSBLFSINNAI`, but diverging from the long-tail form |
| `49` | `STRUCTURAL_STRONG_SHADOW` | `B_BOOK49_MATH49_REGISTER` | closed formula/refrain, possibly calibration or self-binding register |
| `54` | `STRUCTURAL_STRONG_SHADOW` | `B_BOOK54_PAIR_LOCAL_SPINE` | local-pair member preserving the shared `LTFNTFEIFAIFAINIIETNEEIVN` block from Book `20`, with own wrapper/tail |

This is the first practical human-translation panel. It is still a shadow atlas,
but every row has a source bridge, a blocked overreach, a falsifier, and a next
probe.

## Chayenne Branch Shadow Expansion

Persisted in `human_chayenne_branch_shadow_v1_*`.

Decision:
`HUMAN_CHAYENNE_BRANCH_SHADOW_READY_NOT_PROMOTED`

Result:

- Items: `4`
- Branches: `4`
- Canonical promotions: `0`

Branch readings:

| Book | Branch | Confidence | Human reading |
| --- | --- | --- | --- |
| `8` | `VNCTIIN_CONTEXT_BRANCH` | `STRUCTURAL_STRONG_EXTERNAL_FRAME` | clean `VNCTIIN`-context branch carrying the Chayenne external frame as register/context material |
| `37` | `LTAST_TO_VNCTIIN_BRANCH` | `STRUCTURAL_STRONG_EXTERNAL_FRAME` | `LTAST/TTNVVN` boundary-handoff into the same Chayenne frame and then `VNCTIIN` context |
| `63` | `RESIDUAL_CONTINUATION_BRANCH` | `STRUCTURAL_MODERATE_AUDIT_FRAME` | residual-continuation branch preserving the Chayenne frame; audit witness, not translation witness |
| `66` | `BENNA_LTAST_FORMULA_BRANCH` | `STRUCTURAL_STRONG_FORMULA_FRAME` | formula/boundary branch where the Chayenne frame appears inside a `BENNA/LTAST` context |

## Human Translation Atlas V2

Persisted in `human_translation_atlas_v2_*`.

Decision:
`HUMAN_TRANSLATION_ATLAS_V2_READY_11_SHADOW_READINGS`

Result:

- Total readings: `11`
- New readings: `4`
- Anchored readings: `11`
- Ready for human review: `11`
- Promoted gloss: `0`

Added to the previous `7`-book atlas:

| Book | Source layer | Bridge | Confidence |
| --- | --- | --- | --- |
| `8` | `human_chayenne_branch_shadow_v1` | `B_CHAYENNE_FRAME_REGISTER` | `STRUCTURAL_STRONG_EXTERNAL_FRAME` |
| `37` | `human_chayenne_branch_shadow_v1` | `B_CHAYENNE_FRAME_REGISTER` | `STRUCTURAL_STRONG_EXTERNAL_FRAME` |
| `63` | `human_chayenne_branch_shadow_v1` | `B_CHAYENNE_FRAME_REGISTER` | `STRUCTURAL_MODERATE_AUDIT_FRAME` |
| `66` | `human_chayenne_branch_shadow_v1` | `B_CHAYENNE_FRAME_REGISTER` | `STRUCTURAL_STRONG_FORMULA_FRAME` |

The atlas now covers the initial frontier books plus the strongest external
shape-anchored branch family.

## Completion Audit

Persisted in `human_translation_completion_audit_v1_*`.

Decision:
`HUMAN_TRANSLATION_OBJECTIVE_NOT_COMPLETE_EXPAND_ATLAS`

Result:

- Total books: `70`
- Atlas books: `11`
- Atlas coverage: `15.71%`
- Missing books: `59`
- Promoted gloss: `0`

Missing-family summary:

| Missing group | Count |
| --- | ---: |
| no targeted human shadow route assigned yet | `19` |
| C86/VNCTIIN context/payload split needed | `14` |
| R20/R02 phase bridge reading needed | `14` |
| BENNA/formula family reading needed | `7` |
| NAESE/C68 slot reading needed | `5` |

This is why the objective is not complete. The atlas is now usable, but it is a
partial translation-shadow layer, not a full human solution.

## C86/VNCTIIN Bridge Expansion

Persisted in `human_c86_vnctiin_bridge_v1_*`.

Decision:
`HUMAN_C86_VNCTIIN_BRIDGES_READY_NO_GLOSS`

Result:

- Bridges: `4`
- Promoted gloss: `0`
- Principle: split context, payload, branch, and endpoint before prose.

Bridge map:

| Bridge | Target family | Support level | Next probe |
| --- | --- | --- | --- |
| `B_C86_VNCTIIN_PAYLOAD_CORRIDOR` | `C86_VNCTIIN_PAYLOAD` | `STRUCTURAL_PAYLOAD_WITH_EXTERNAL_CONTEXT_FRAME` | split payload books by `BENNA`, `TAILBETFTE`, `NAESE`, and clean context controls |
| `B_C86_VINVIN_BRANCH` | `C86_VINVIN_VTLR_BRANCH` | `STRUCTURAL_BRANCH_WITH_OPERATOR_GUARDRAIL` | contrast `VINVIN/VTLR` branch books against C86/VNCTIIN payload and R20/R02 phase controls |
| `B_VNCTIIN_PHASE_CONTEXT` | `VNCTIIN_PHASE_CONTEXT` | `STRUCTURAL_CONTEXT_WITH_PHASE_CONTROL` | separate `VNCTIIN`-only context, `VNCTIIN+TIINNEF` phase, and Chayenne-frame contexts |
| `B_O23_VNCTIIN_ENDPOINT_CONTEXT` | `O23_VNCTIIN_ENDPOINT` | `STRUCTURAL_ENDPOINT_WITH_NEGATIVE_CONTROL` | keep Books `13/38` direct endpoint controls separate from Books `12/21` terminal readings |

This bridge uses the same human rule as the Chayenne and Mathemagic passes:
operators and context frames can guide plausible readings, but they do not
become dictionary entries.

## C86/VNCTIIN Shadow Expansion

Persisted in `human_c86_vnctiin_shadow_v1_*`.

Decision:
`HUMAN_C86_VNCTIIN_SHADOW_READY_NOT_PROMOTED`

Result:

- Items: `14`
- Subfamilies: `5`
- Canonical promotions: `0`

Subfamily distribution:

| Subfamily | Count | Human use |
| --- | ---: | --- |
| `C86_VINVIN_VTLR_BRANCH` | `5` | C86-opened branch/phase selector, not VNCTIIN prose |
| `C86_VNCTIIN_PAYLOAD` | `3` | C86 payload-open into VNCTIIN/C68 context |
| `VNCTIIN_PHASE_CONTEXT` | `3` | VNCTIIN context carrying `TIINNEF` phase anchors |
| `VNCTIIN_CONTEXT_ONLY` | `2` | context frame without C86 payload evidence |
| `O23_VNCTIIN_ENDPOINT` | `1` | direct O23 endpoint control inside VNCTIIN context |

Book assignments:

| Books | Subfamily | Confidence |
| --- | --- | --- |
| `2`, `27`, `67` | `C86_VNCTIIN_PAYLOAD` | `STRUCTURAL_STRONG_PAYLOAD_CONTEXT` |
| `3`, `17`, `44`, `52`, `62` | `C86_VINVIN_VTLR_BRANCH` | `STRUCTURAL_MODERATE_BRANCH_CONTROL` |
| `13` | `O23_VNCTIIN_ENDPOINT` | `STRUCTURAL_STRONG_ENDPOINT_CONTROL` |
| `19`, `31`, `57` | `VNCTIIN_PHASE_CONTEXT` | `STRUCTURAL_STRONG_PHASE_CONTEXT` |
| `23`, `24` | `VNCTIIN_CONTEXT_ONLY` | `STRUCTURAL_MODERATE_CONTEXT_CONTROL` |

The key cleanup is negative as much as positive: C86, VNCTIIN, VINVIN, and O23
are not promoted as words. They are kept as corridor, context, branch, and
endpoint roles that make the next human readings less arbitrary.

## Human Translation Atlas V3

Persisted in `human_translation_atlas_v3_*`.

Decision:
`HUMAN_TRANSLATION_ATLAS_V3_READY_25_SHADOW_READINGS`

Result:

- Total readings: `25`
- New readings: `14`
- Anchored readings: `25`
- Ready for human review: `25`
- Promoted gloss: `0`

Source layers:

| Source layer | Count |
| --- | ---: |
| `human_translation_atlas_v1` | `7` |
| `human_chayenne_branch_shadow_v1` | `4` |
| `human_c86_vnctiin_shadow_v1` | `14` |

The atlas now covers the initial frontier, the Chayenne frame branches, and the
C86/VNCTIIN context/payload frontier. This is a stronger human translation map,
but it remains a map of plausible readings, not solved plaintext.

## Completion Audit V2

Persisted in `human_translation_completion_audit_v2_*`.

Decision:
`HUMAN_TRANSLATION_OBJECTIVE_NOT_COMPLETE_ATLAS_V3_EXPAND_REMAINING_FAMILIES`

Result:

- Total books: `70`
- Atlas books: `25`
- Atlas coverage: `35.71%`
- Missing books: `45`
- Promoted gloss: `0`

Missing-family summary:

| Missing group | Count |
| --- | ---: |
| no targeted human shadow route assigned yet | `19` |
| R20/R02 phase family needs bridge/phase shadow reading | `15` |
| BENNA/formula family not yet converted to human shadow reading | `6` |
| NAESE/C68 slot family needs slot shadow reading | `5` |

The objective is still not complete. The next highest-yield route is no longer
C86/VNCTIIN; it is the R20/R02 phase family, followed by BENNA/formula and then
NAESE/C68 slot readings.

## R20/R02 Phase Bridge Expansion

Persisted in `human_r20_r02_phase_bridge_v1_*`.

Decision:
`HUMAN_R20_R02_PHASE_BRIDGES_READY_NO_GLOSS`

Result:

- Bridges: `6`
- Promoted gloss: `0`
- Principle: split R02 slot bridge, R20 phase, VINVIN branch, and LIVRN micro
  before prose.

Bridge map:

| Bridge | Target family | Support level | Human use |
| --- | --- | --- | --- |
| `B_R02_NAESE_SLOT_BRIDGE` | `R02_NAESE_SLOT_BRIDGE` | `STRUCTURAL_STRONG_PHASE_SLOT_BRIDGE` | Books `51/53` as strong R02 phase-to-NAESE/C68 slot controls |
| `B_R02_R20_CONTEXT_CONNECTOR` | `R02_R20_CONTEXT_CONNECTOR` | `STRUCTURAL_CONTEXT_CONNECTOR_NO_PROSE` | Books `45/46` as related connector material, not clean slot proof |
| `B_VINVIN_R20_COVERED_BRANCH` | `VINVIN_R20_COVERED_BRANCH` | `STRUCTURAL_BRANCH_COVERED_BY_VINVIN` | R20/VTLR material subordinated to VINVIN branch mechanics |
| `B_R20_PHASE_BLOCK` | `R20_PHASE_BLOCK` | `STRUCTURAL_PHASE_BLOCK_NO_GLOSS` | repeated local R20 phase block, not a lexical root |
| `B_R_LIVRN_MICRO_AUDIT` | `R_LIVRN_MICRO_AUDIT` | `AUDIT_MICRO_CONTEXT_NO_PROMOTION` | low-support LIVRN microcontexts as audit controls |
| `B_R02_LTAST_BOUNDARY_AUDIT` | `R02_LTAST_BOUNDARY_AUDIT` | `WEAK_BOUNDARY_AUDIT_NO_PROMOTION` | Book `14` as weak boundary audit only |

This bridge explicitly preserves the earlier failed/held gates: Book `14` stays
weak, LIVRN stays audit-only, and R20/VTLR stays covered by VINVIN when that is
the stronger structural explanation.

## R20/R02 Phase Shadow Expansion

Persisted in `human_r20_r02_phase_shadow_v1_*`.

Decision:
`HUMAN_R20_R02_PHASE_SHADOW_READY_NOT_PROMOTED`

Result:

- Items: `15`
- Subfamilies: `7`
- Canonical promotions: `0`

Subfamily distribution:

| Subfamily | Count | Human use |
| --- | ---: | --- |
| `VINVIN_R20_COVERED_BRANCH` | `4` | R20/VTLR branch material covered by VINVIN mechanics |
| `R_LIVRN_MICRO_AUDIT` | `3` | audit-only LIVRN microcontexts |
| `R02_NAESE_SLOT_BRIDGE` | `2` | strong R02 phase bridge into NAESE/C68 slot |
| `R02_R20_CONTEXT_CONNECTOR` | `2` | connector material adjacent to the slot bridge |
| `VINVIN_R20_PHASE_ENDPOINT` | `2` | VINVIN branch reaching R20 phase endpoint |
| `R02_LTAST_BOUNDARY_AUDIT` | `1` | weak R02/LTAST boundary audit |
| `R20_PHASE_WITH_LIVRN_MICRO` | `1` | R20 phase block with audit-only microcontext |

Book assignments:

| Books | Subfamily | Confidence |
| --- | --- | --- |
| `14` | `R02_LTAST_BOUNDARY_AUDIT` | `STRUCTURAL_WEAK_BOUNDARY_AUDIT` |
| `15`, `16`, `29`, `68` | `VINVIN_R20_COVERED_BRANCH` | `STRUCTURAL_COVERED_BRANCH_CONTROL` |
| `45`, `46` | `R02_R20_CONTEXT_CONNECTOR` | `STRUCTURAL_MODERATE_CONTEXT_CONNECTOR` |
| `51`, `53` | `R02_NAESE_SLOT_BRIDGE` | `STRUCTURAL_STRONG_PHASE_SLOT_BRIDGE` |
| `58`, `59`, `60` | `R_LIVRN_MICRO_AUDIT` | `STRUCTURAL_AUDIT_MICRO_ONLY` |
| `61`, `65` | `VINVIN_R20_PHASE_ENDPOINT` | `STRUCTURAL_MODERATE_BRANCH_ENDPOINT` |
| `64` | `R20_PHASE_WITH_LIVRN_MICRO` | `STRUCTURAL_PHASE_WITH_AUDIT_MICRO` |

This is a human-usable split, not a plaintext claim. It lets a reader say what
kind of line each book likely is while still blocking R20/R02 as translated
words.

## Human Translation Atlas V4

Persisted in `human_translation_atlas_v4_*`.

Decision:
`HUMAN_TRANSLATION_ATLAS_V4_READY_40_SHADOW_READINGS`

Result:

- Total readings: `40`
- New readings: `15`
- Anchored readings: `40`
- Ready for human review: `40`
- Promoted gloss: `0`

Source layers:

| Source layer | Count |
| --- | ---: |
| `human_translation_atlas_v1` | `7` |
| `human_chayenne_branch_shadow_v1` | `4` |
| `human_c86_vnctiin_shadow_v1` | `14` |
| `human_r20_r02_phase_shadow_v1` | `15` |

The atlas now covers the initial frontier, Chayenne frame branches,
C86/VNCTIIN, and R20/R02 phase-family material.

## Completion Audit V3

Persisted in `human_translation_completion_audit_v3_*`.

Decision:
`HUMAN_TRANSLATION_OBJECTIVE_NOT_COMPLETE_ATLAS_V4_EXPAND_BENNA_NAESE_RESIDUALS`

Result:

- Total books: `70`
- Atlas books: `40`
- Atlas coverage: `57.14%`
- Missing books: `30`
- Promoted gloss: `0`

Missing-family summary:

| Missing group | Count |
| --- | ---: |
| no targeted human shadow route assigned yet | `19` |
| BENNA/formula family not yet converted to human shadow reading | `6` |
| NAESE/C68 slot family needs slot shadow reading | `5` |

The objective remains incomplete. R20/R02 is no longer the largest named
missing family; the next work should either assign routes for the 19 residual
books or convert BENNA/formula and NAESE/C68 into equally explicit shadow
families.

## Slot/Formula Bridge Expansion

Persisted in `human_slot_formula_bridge_v1_*`.

Decision:
`HUMAN_SLOT_FORMULA_BRIDGES_READY_NO_GLOSS`

Result:

- Bridges: `6`
- Promoted gloss: `0`
- Principle: combined BENNA/formula and NAESE/C68 so overlapping books do not
  get conflicting readings.

Bridge map:

| Bridge | Target family | Human use |
| --- | --- | --- |
| `B_NAESE_BENNA_COMPOSITE` | `NAESE_BENNA_COMPOSITE_FRAME` | Books `5/9` as slot-to-formula composite controls |
| `B_NAESE_CANONICAL_SLOT` | `NAESE_CANONICAL_SLOT` | clean NAESE/C68/FATCT slot classifier |
| `B_NAESE_VARIANT_WINDOW` | `NAESE_VARIANT_WINDOW` | controlled NAESE variant windows |
| `B_NAESE_WEAK_HYBRID_AUDIT` | `NAESE_WEAK_HYBRID_AUDIT` | weak/hybrid NAESE audit cases |
| `B_BENNA_C86_VNCTIIN_FORMULA_HANDOFF` | `BENNA_C86_VNCTIIN_FORMULA_HANDOFF` | BENNA formula handoff into C86/VNCTIIN context |
| `B_BENNA_FORMULA_BODY` | `BENNA_FORMULA_BODY` | BENNA formula body/local controls |

## Slot/Formula Shadow Expansion

Persisted in `human_slot_formula_shadow_v1_*`.

Latest decision:
`HUMAN_SLOT_FORMULA_SHADOW_READY_NOT_PROMOTED`

Latest run:
`human_slot_formula_shadow_v1_runs.run_id=2`

Result:

- Items: `11`
- Subfamilies: `9`
- Canonical promotions: `0`

Book assignments:

| Book | Subfamily | Confidence |
| --- | --- | --- |
| `5` | `NAESE_BENNA_COMPOSITE_FRAME` | `STRUCTURAL_STRONG_COMPOSITE_FRAME` |
| `9` | `NAESE_BENNA_COMPOSITE_WITH_LTAST_TAIL` | `STRUCTURAL_STRONG_COMPOSITE_WITH_TAIL` |
| `10`, `35` | `BENNA_C86_VNCTIIN_FORMULA_HANDOFF` | `STRUCTURAL_STRONG_FORMULA_HANDOFF` |
| `22` | `NAESE_CANONICAL_SLOT` | `STRUCTURAL_SLOT_CLASSIFIER` |
| `28`, `48` | `NAESE_VARIANT_WINDOW` | `STRUCTURAL_SLOT_VARIANT` |
| `40` | `BENNA_FORMULA_BODY_WITH_LTAST_TAIL` | `STRUCTURAL_FORMULA_BODY_NO_GLOSS` |
| `42` | `NAESE_WEAK_HYBRID_AUDIT` | `STRUCTURAL_WEAK_AUDIT` |
| `50` | `BENNA_FORMULA_COMPOSITE_VARIANT` | `STRUCTURAL_FORMULA_VARIANT` |
| `69` | `BENNA_LOCAL_CLEAN_H2_CONTROL` | `STRUCTURAL_LOCAL_CONTROL_NO_EDGE` |

The important correction in run `2`: Book `42` is not treated as a clean
variant merely because of C68 surface shape. `naese_slot_core_v1` keeps it as
`BOOK42_HYBRID`, so the human layer keeps it audit-only.

## Human Translation Atlas V5

Persisted in `human_translation_atlas_v5_*`.

Latest decision:
`HUMAN_TRANSLATION_ATLAS_V5_READY_51_SHADOW_READINGS`

Result:

- Total readings: `51`
- New readings: `11`
- Anchored readings: `51`
- Ready for human review: `51`
- Promoted gloss: `0`

## Completion Audit V4

Persisted in `human_translation_completion_audit_v4_*`.

Latest decision:
`HUMAN_TRANSLATION_OBJECTIVE_NOT_COMPLETE_ATLAS_V5_EXPAND_RESIDUAL_ROUTES`

Result:

- Total books: `70`
- Atlas books: `51`
- Atlas coverage: `72.86%`
- Missing books: `19`
- Promoted gloss: `0`

Missing-family summary after slot/formula:

| Missing group | Count |
| --- | ---: |
| display-drift residual needs audit-only shadow route | `4` |
| local-pair residual needs pair shadow reading | `3` |
| residual template alignment needs cluster shadow route | `3` |
| LTAST/TTNVVN boundary residual needs human route | `2` |
| O23/FNAAST endpoint or Book38 component residual needs route | `2` |
| single-book residual routes | `5` |

## Residual Bridge Expansion

Persisted in `human_residual_bridge_v1_*`.

Decision:
`HUMAN_RESIDUAL_BRIDGES_READY_NO_GLOSS`

Result:

- Bridges: `10`
- Promoted gloss: `0`
- Principle: residual readings are route labels plus guarded shadow prose, not
  decoded plaintext.

Bridge families:

| Family | Human use |
| --- | --- |
| `DISPLAY_DRIFT_RESIDUAL` | BTII/NSBVN/ATFNAAST display-drift audit controls |
| `LOCAL_PAIR_RESIDUAL` | pair/truncation and FAST/BEIE microtemplate controls |
| `RESIDUAL_TEMPLATE_CLUSTER` | residual alignments to stronger neighboring books |
| `LTAST_BOUNDARY_RESIDUAL` | LTAST/TTNVVN boundary-only controls |
| `O23_FNAAST_ENDPOINT_RESIDUAL` | direct endpoint and Book38 component controls |
| `469_MARKER_METAFORMULA_RESIDUAL` | Book `4` special marker/metaformula audit |
| `BOOK55_INTERNAL_REPEAT_RESIDUAL` | Book `55` internal repeat control |
| `CHAYENNE_NEAR_VARIANT_RESIDUAL` | Book `41` near-frame witness |
| `NEIAAETTA_CONTINUITY_RESIDUAL` | Book `6` continuity-only phase control |
| `UNIQUE_SCRAMBLED_HEADER_RESIDUAL` | Book `34` unique header/scrambled assembly audit |

## Residual Shadow Expansion

Persisted in `human_residual_shadow_v1_*`.

Decision:
`HUMAN_RESIDUAL_SHADOW_READY_NOT_PROMOTED`

Result:

- Items: `19`
- Subfamilies: `12`
- Canonical promotions: `0`

Book assignments:

| Books | Subfamily | Confidence |
| --- | --- | --- |
| `0`, `33` | `LTAST_BOUNDARY_RESIDUAL` | `STRUCTURAL_BOUNDARY_OPERATOR` |
| `1`, `18`, `47` | `RESIDUAL_TEMPLATE_CLUSTER` | `STRUCTURAL_TEMPLATE_ALIGNMENT` |
| `4` | `469_MARKER_METAFORMULA_RESIDUAL` | `SPECIAL_METAFORMULA_AUDIT` |
| `6` | `NEIAAETTA_CONTINUITY_RESIDUAL` | `STRUCTURAL_CONTINUITY_ONLY` |
| `11`, `32`, `36`, `43` | `DISPLAY_DRIFT_RESIDUAL` | `AUDIT_DISPLAY_DRIFT` |
| `20` | `LOCAL_PAIR_20_54_TRUNCATION` | `STRUCTURAL_LOCAL_PAIR_STRONG` |
| `25`, `39` | `LOCAL_PAIR_25_39_FAST_BEIE` | `STRUCTURAL_LOCAL_PAIR_MICRO` |
| `34` | `UNIQUE_SCRAMBLED_HEADER_RESIDUAL` | `UNIQUE_HEADER_AUDIT` |
| `38` | `O23_FNAAST_ENDPOINT_PAYLOAD` | `STRUCTURAL_ENDPOINT_PAYLOAD` |
| `41` | `CHAYENNE_NEAR_VARIANT_RESIDUAL` | `STRUCTURAL_NEAR_FRAME` |
| `55` | `BOOK55_INTERNAL_REPEAT_RESIDUAL` | `STRUCTURAL_INTERNAL_REPEAT` |
| `56` | `BOOK56_BOOK38_CLEAN_COMPONENT` | `STRUCTURAL_COMPONENT_CONTROL` |

## Human Translation Atlas V6

Persisted in `human_translation_atlas_v6_*`.

Decision:
`HUMAN_TRANSLATION_ATLAS_V6_READY_70_SHADOW_READINGS`

Result:

- Total readings: `70`
- New readings: `19`
- Anchored readings: `70`
- Ready for human review: `70`
- Promoted gloss: `0`

Source layers:

| Source layer | Count |
| --- | ---: |
| `human_residual_shadow_v1` | `19` |
| `human_r20_r02_phase_shadow_v1` | `15` |
| `human_c86_vnctiin_shadow_v1` | `14` |
| `human_slot_formula_shadow_v1` | `11` |
| `human_translation_atlas_v1` | `7` |
| `human_chayenne_branch_shadow_v1` | `4` |

This is the first full human-readable atlas: every book has a plausible,
source-anchored, falsifiable shadow reading.

## Completion Audit V5

Persisted in `human_translation_completion_audit_v5_*`.

Decision:
`HUMAN_SHADOW_ATLAS_COMPLETE_CANONICAL_TRANSLATION_UNSOLVED`

Result:

- Total books: `70`
- Atlas books: `70`
- Atlas coverage: `100.0%`
- Missing books: `0`
- Promoted gloss: `0`
- Anchored readings: `70`
- Readable shadow readings: `70`

Objective checklist:

| Requirement | Status | Gap |
| --- | --- | --- |
| human-readable plausible versions for the 70 book texts | `covered_as_shadow` | needs human review/falsification before accepted translation |
| anchor translations in game relationships/books first | `covered_as_anchor_bridge` | anchors constrain structure; they are not exact phrase keys |
| consider Mathemagica and related quests | `covered_as_method_constraint` | no exact official phrase-plus-meaning source for book plaintext |
| consistent/reliable replicable method | `covered_as_sqlite_pipeline` | shadow readings are not canonical decode promotions |
| actual translation solved | `not_complete` | no canonical book gloss or accepted plaintext translation promoted |

The practical objective advanced materially: we now have plausible human
versions for all books. The strict translation objective is still unsolved
because the atlas is shadow-only and must survive contradiction review before
any small piece can be promoted.

## Atlas V6 Contradiction Audit

Persisted in `human_atlas_v6_contradiction_audit_v1_*`.

Latest decision:
`HUMAN_ATLAS_V6_CONTRADICTION_AUDIT_PASS_NO_PROMOTION`

Latest run:
`human_atlas_v6_contradiction_audit_v1_runs.run_id=2`

Result:

- Items audited: `70`
- Pass: `70`
- Warn: `0`
- Fail: `0`
- Promotion-review candidates: `15`
- Stable/control shadow readings: `39`
- Audit-only readings: `16`
- Promoted gloss: `0`

Review-tier summary:

| Review tier | Count |
| --- | ---: |
| `CONTROL_OR_VARIANT_SHADOW` | `32` |
| `AUDIT_ONLY_SHADOW` | `16` |
| `PROMOTION_REVIEW_CANDIDATE` | `15` |
| `STABLE_SHADOW_REVIEW` | `7` |

Promotion-review candidate books:

| Books | Route |
| --- | --- |
| `2`, `27`, `67` | C86 payload into VNCTIIN/C68 context |
| `5`, `9` | NAESE/C68 to BENNA composite |
| `10`, `35` | BENNA formula handoff into C86/VNCTIIN |
| `7` | Book7 phase/mathemagic bridge |
| `8`, `37`, `66` | Chayenne external frame branches |
| `49` | repeat/formula register candidate |
| `51`, `53` | R02 phase bridge into NAESE/C68 slot |
| `54` | local-pair shared spine |

This audit does not promote any text. It identifies where the next human review
should start if the project wants small, falsifiable promotion packages.

## External Phrase Corpus

Persisted in `human_external_phrase_corpus_v1_*`.

Input runs:

- `confirmed_external_row0_projection_runs.run_id=2`
- `external_row0_lcs_probe_runs.run_id=2`
- `chayenne_external_shape_gate_runs.run_id=2`

External phrase corpus summary:

- Phrase count: `5`
- Exact full-book hits: `0`
- Strong shape-overlap phrase count: `1`
- Accepted semantic gloss count: `0`

Phrase inventory:

| Phrase | Human use | Result |
| --- | --- | --- |
| `AVAR_ORIGINAL_POEM` | out-of-book poem/register comparator | external-only; no book semantic promotion |
| `CHAYENNE_REPLY` | strong structural holdout | overlaps Books `8`, `37`, `63`, `66` on block `AEFIEIEFIIVFAEATVAT`; no meaning promoted |
| `KNIGHTMARE_PHRASE` | name/formula and 3478 holdout | external-only; no book semantic promotion |
| `POLL_2020_OPTION_C` | phrase-level holdout | external-only; no book semantic promotion |
| `ELDER_BONELORD_SOUNDS` | NPC speech/sound comparator | external-only; no book semantic promotion |

This is useful because it lets the human workflow use out-of-book 469 phrases
as style/register/shape tests without pretending they are translations of the
Hellgate books.

## Chayenne Shape Probe

Persisted in `human_chayenne_shape_shadow_probe_v1_*`.

Decision:
`CHAYENNE_EXTERNAL_SHAPE_IS_REGISTER_FRAME_NOT_SINGLE_GLOSS`

Result:

- Phrase: `CHAYENNE_REPLY`
- Shared block: `AEFIEIEFIIVFAEATVAT`
- Books: `8`, `37`, `63`, `66`
- Branch count: `4`
- Direct meaning allowed: `0`
- Accepted human gloss: `0`

Branching:

| Book | Branch | Human role |
| --- | --- | --- |
| `8` | `VNCTIIN_CONTEXT_BRANCH` | external shape frame embedded in `VNCTIIN` context |
| `37` | `LTAST_TO_VNCTIIN_BRANCH` | external shape frame after `LTAST` boundary handoff into `VNCTIIN` |
| `63` | `RESIDUAL_CONTINUATION_BRANCH` | external shape frame in residual continuation template |
| `66` | `BENNA_LTAST_FORMULA_BRANCH` | external shape frame inside `BENNA/LTAST` formula branch |

This is a major constraint for the human route: the Chayenne overlap is useful
as an external register/frame anchor, but because the same block appears across
four internal branches it should not be translated as one fixed sentence.

## New Translation Routes

Persisted in `human_translation_route_v1_routes`:

1. `R1_INGAME_CONTEXT_CORPUS`
   - Build the full in-game context corpus first.
   - No prose draft can exist without book/NPC/quest/location provenance.

2. `R2_NPC_PHRASE_STYLE_COMPARATOR`
   - Tokenize Avar Tar, Chayenne, Knightmare, Wyrdin/NPC-style phrases using the
     same row0 rules.
   - Compare register and structure to books, not plaintext.

3. `R3_MATHEMAGIC_OPERATOR_GRID`
   - Treat mathemagics as operators/selectors, not as dictionary keys.
   - Active operator family: `1`, `13`, `49`, `94`, `+49 mod70`, `94->24`,
     `delta13`, Hellgate 4x4 matrix, zero/one inversion, formula composition.

4. `R4_NAME_AS_FORMULA`
   - Stop forcing `bonelord/beholder` as a fixed word.
   - Treat `486486`, `3478`, `4378`, `469`, `1`, `0` as numeric lore
     constraints until a formula explains them together.

5. `R5_PLAUSIBLE_PROSE_SHADOW`
   - Draft human paraphrases as research artifacts only.
   - Each draft must include functional tags, anchors, confidence, risks, and
     blocked claims.

6. `R6_LOCATION_ROLE_ALIGNMENT`
   - Map shelf/library/location and duplicate placement to functional clusters.

7. `R7_GREAT_CALCULATOR_LINEAGE`
   - Test whether the library is a gathered/compiled corpus rather than one
     continuous plaintext.

8. `R8_MINOTAUR_MAGE_TRUTH_BRIDGE`
   - Test the bridge from Wrinkled Bonelord's minotaur-mage remark to
     Mintwallin/Paradox mathemagics.

9. `R9_ZERO_ONE_TABOO_INVERSION`
   - Test `Tibia=1` and `0` taboo as boundary/operator behavior, not as simple
     vocabulary.

10. `R10_EXTERNAL_EXACT_GLOSS_ROUTE`
    - Continue exact-source search only for exact sequence plus explicit meaning
      and provenance.

## Human Mathemagic Synthesis

Persisted in `human_mathemagic_shadow_synthesis_v1_*`.

Decision:
`HUMAN_MATHEMAGIC_SYNTHESIS_READY_OPERATORS_NOT_PLAINTEXT`

Result:

- Hypotheses: `5`
- Active tests: `3`
- Guardrails: `2`
- Accepted human gloss: `0`

Synthesis:

| Hypothesis | Operator/anchor | Status | Implication |
| --- | --- | --- | --- |
| `MATH_49_REGISTER_SELECTOR_NOT_DICTIONARY` | `+49/mod70` and Book `49` | `ACTIVE_TEST` | `49` may select register/formula behavior, not a word key |
| `MATH_13_DELTA_LOCAL_GUARDRAIL` | `13/delta13` | `GUARDRAIL` | keep `13` local to vetted C86/C68 contexts |
| `MATH_94_24_AUDIT_SELECTOR` | `94->24` | `ACTIVE_TEST` | can rank candidates, cannot create prose |
| `MATHEMAGIC_REGISTER_FRAME_BRANCHING` | Chayenne external shape frame | `ACTIVE_TEST` | external 469 may behave as reusable register/frame |
| `MATHEMAGIC_SPINES_NOT_LINEAR_PROSE` | Book30 spine/formula families | `GUARDRAIL` | translate by spines/subfamilies first, not continuous sentence assumptions |

This is the current role of Mathemagic in the human route: it generates
operator tests and constraints. It does not provide a dictionary.

## Frontier For Human Shadow Drafting

Persisted in `human_translation_route_v1_frontier_books`.

Eligible now:

| Book | Prior anchor | Route focus |
| --- | --- | --- |
| `49` | `28`, `<NAESE_VARIANT>` | R5 shadow prose after R1/R3 checks |
| `12` | `13`, `<O23:SCOPED_ENDPOINT>` | R5 shadow prose after R1/R3 checks |
| `30` | `28`, `<NAESE_VARIANT>` | R5 shadow prose after R1/R3 checks |
| `26` | `17`, `<VINVIN:C86_PAYLOAD_BRANCH>` | R5 shadow prose after R1/R3 checks |
| `7` | `17`, `<VINVIN:C86_PAYLOAD_BRANCH>` | R5 shadow prose after R1/R3 checks |
| `21` | `51`, `<R02_SLOT_BRIDGE>` | R5 shadow prose after R1/R3 checks |
| `54` | `29`, `<VINVIN:R20_CONNECTOR_BRANCH_HEAD>` | R5 shadow prose after R1/R3 checks |

Hold/control:

- `45`, `18`: audit/control only; do not draft prose first.
- `1`, `20`, `25`, `34`, `39`, `14`, `41`, `63`: hold until non-circular
  in-game evidence exists.

## Shadow Reading Template

Every human candidate should be recorded with:

- `bookid`
- `source route`
- `in-game anchors used`
- `functional tags used`
- `literal unknowns kept visible`
- `plausible human paraphrase`
- `why this is plausible`
- `what would falsify it`
- `what source search it triggers`
- `canonical promotion status = NOT_PROMOTED`

Draft example shape, not content:

```text
Book X
Layer: shadow human paraphrase
Anchors: Wrinkled Bonelord numbers/mathemagic; Mathemagic route R3; tag cluster Y
Likely speech act: formula handoff / ritual instruction / catalog note / endpoint
Human paraphrase candidate: ...
Blocked claims: no word-level gloss for token A; no proof of phrase B
Falsifier: if held-out book Z has same function but opposite context
Next probe: ...
```

## First Human Shadow Seed

Persisted in `human_shadow_reading_v1_items`.

These are controlled human-readable hypotheses, not translations.

| Book | Likely speech act | Shadow paraphrase | Status |
| --- | --- | --- | --- |
| `49` | self-contained repeat formula or chant | A closed formula that appears to bind or repeat itself; likely a calibration/refrain rather than narrative prose. | `NOT_PROMOTED` |
| `12` | compact Book30-family shared-base terminal witness | A short Book30-family witness: it is almost entirely the shared `TAESESTIEN/VNSBLFSINNAI` base also present in Book `21`, with no direct `O23/ONAF/FNAAST` endpoint marker. | `NOT_PROMOTED` |
| `30` | alternate Book30-family spine witness | An alternate Book30-family witness: it preserves `TAESESTIEN` and the shared `VNSBLFSINNAI` spine, but diverges from the long-tail form used by Books `12/21/26`. | `NOT_PROMOTED` |
| `26` | Book30-family spine introduced from a branch/prefix | A branch-prefixed transition into the shared `VNSBLFSINNAI` spine and long-tail form, notably without the `TAESESTIEN` subcomponent seen in Books `12/21/30`. | `NOT_PROMOTED` |
| `7` | phase continuation or handoff line | A phase-continuity line: it appears to carry a sequence through a local phase anchor rather than introduce a new independent message. | `NOT_PROMOTED` |
| `21` | Book30-family spine plus bridge/tail extension | A Book30-family shared-base witness that preserves nearly all of Book `12`'s base and adds the `TIVNSENI*LAELBEV` tail extension, without direct `O23/ONAF/FNAAST` markers. | `NOT_PROMOTED` |
| `54` | shared-core local pair member with its own tail | An abbreviated member of a local pair that preserves the shared `LTFNTFEIFAIFAINIIETNEEIVN` block from Book `20` while using a shorter prefix and its own small tail. | `NOT_PROMOTED` |

The useful output here is not the prose itself. The useful output is the new
testing burden each paraphrase creates: formula/refrain, endpoint, core
classifier, branch transition, phase continuation, bridge/tail, and truncation
can now be attacked as separate falsifiable claims.

Important correction from the first probe: "Book30-family core" was too broad.
The current supported wording is "Book30-family spine":

- shared by all Books `12/21/26/30`: `VNSBLFSINNAI`
- partial components:
  `TAESESTIEN`, `FALVNALVEEIIV`, `VIEITAIFASIATFTEIEFIINI`,
  `VNAIFEEIIET`, `NSETIEFIEIEFIIN`, `TIVNSENI`, `LAELBEV`,
  `FLEEIIFTEI`, `NBLIBEIEFSEENEIEN`
- Book `30` is not proven as the full long-tail centroid; it is an alternate
  spine witness.

## Shadow Contradiction Audit

Persisted in `human_shadow_contradiction_check_v1_*`.

Audit result:

- Checked: `7`
- Passed: `7`
- Contradictions/incomplete: `0`
- Canonical promotions: `0`
- Decision:
  `HUMAN_SHADOW_READINGS_CONSISTENT_NEXT_PROBES_READY`

The audit checked that each shadow reading:

- stays `NOT_PROMOTED`
- has a live route in `human_translation_route_v1_routes`
- contains blocked claims
- contains a falsifier
- contains a next probe
- does not use direct-gloss wording
- matches the expected functional tag family
- does not ignore any strong external phrase overlap

Expected functional matches:

| Book | Required functional support |
| --- | --- |
| `49` | `SELF_CONTAINED_REPEAT_FORMULA` |
| `12`, `21`, `26`, `30` | `BOOK30_CORE_CONTEXT` |
| `7` | `BOOK7_NEIAAETTA_CONTINUITY`, `BOOK7_TIINNEF_PHASE_ANCHOR` |
| `54` | `ZERO_PAIR_LOCAL_PAIR_20_54_TRUNCATION_ALIGNMENT` |

## Book30 Family Probe

Persisted in `human_book30_family_shadow_probe_v1_*`.

Decision:
`BOOK30_SHADOW_SPINE_CONFIRMED_CORE_LANGUAGE_NEEDS_TIGHTENING`

Result:

- Target books: `12`, `21`, `26`, `30`
- Components shared by all: `VNSBLFSINNAI`
- Partial components: `9`
- Accepted human gloss: `0`

Classification:

| Book | Classification | Implication |
| --- | --- | --- |
| `12` | `LONG_TAIL_SPINE_WITH_TAESESTIEN` | compact/extended long-tail witness |
| `21` | `LONG_TAIL_SPINE_WITH_TAESESTIEN` | long-tail witness with bridge/tail extension |
| `26` | `LONG_TAIL_SPINE_WITH_BRANCH_PREFIX` | branch-prefixed witness; do not call `TAESESTIEN` universal |
| `30` | `SPINE_PLUS_TAESESTIEN_ALT_TAIL` | alternate-tail witness, not full family centroid |

This is the first useful "human" correction: it does not translate a word, but
it makes the plausible reading sharper and less likely to invent a fake core.

## Book7 Phase Probe

Persisted in `human_book7_phase_shadow_probe_v1_*`.

Decision:
`BOOK7_PHASE_SHADOW_BRIDGE_SUPPORTED_NO_GLOSS`

Result:

- Target books: `6`, `7`, `19`, `31`, `57`
- Bridge books: `1`
- Continuity-only controls: `1`
- Phase-context controls: `3`
- Accepted human gloss: `0`

Classification:

| Book | Classification | Implication |
| --- | --- | --- |
| `6` | `CONTINUITY_ONLY_CONTROL` | `NEIAAETTA` continuity marker without phase anchor |
| `7` | `PHASE_BRIDGE_CONTINUITY_TO_ANCHOR` | supports Book `7` as bridge from continuity into phase anchor |
| `19` | `PHASE_CONTEXT_CONTROL` | `TIINNEF` phase anchor embedded in `VNCTIIN` context |
| `31` | `PHASE_CONTEXT_CONTROL` | `TIINNEF` phase anchor embedded in `VNCTIIN` context |
| `57` | `PHASE_CONTEXT_CONTROL` | `TIINNEF` phase anchor embedded in `VNCTIIN` context |

This strengthens the Book `7` human shadow reading: "phase-continuity handoff"
is now supported structurally by controls on both sides. It still does not
license an English lexical translation.

## Book49 Repeat Probe

Persisted in `human_book49_repeat_shadow_probe_v1_*`.

Decision:
`BOOK49_REPEAT_SHADOW_SUPPORTED_NO_GLOSS`

Result:

- Target repeat coverage: `0.85`
- Target repeat rank in corpus: `1`
- Control Book `55` repeat coverage: `0.6441`
- Accepted human gloss: `0`

Top repeat controls:

| Book | Repeat coverage | Rank | Classification |
| --- | --- | --- | --- |
| `49` | `0.85` | `1` | `SELF_CONTAINED_REPEAT_FORMULA_SUPPORTED` |
| `31` | `0.8268` | `2` | `HIGH_REPEAT_CONTROL` |
| `57` | `0.7119` | `3` | `HIGH_REPEAT_CONTROL` |
| `6` | `0.6484` | `4` | `HIGH_REPEAT_CONTROL` |
| `55` | `0.6441` | `5` | `INTERNAL_REPEAT_CONTROL` |

This supports the human shadow phrase "closed formula/refrain", but it also
keeps strong controls visible: repetition alone is not semantic meaning.

## Book54 Pair Probe

Persisted in `human_book54_pair_shadow_probe_v1_*`.

Decision:
`BOOK54_PAIR_SHADOW_SHARED_CORE_WITH_OWN_TAIL_NO_GLOSS`

Result:

- Shared block: `LTFNTFEIFAIFAINIIETNEEIVN`
- LCS length: `25`
- LCS ratio to shorter book: `0.8621`
- LCS ratio to longer book: `0.7812`
- Accepted human gloss: `0`

Segmentation:

| Book | Prefix | Shared block | Suffix | Classification |
| --- | --- | --- | --- | --- |
| `20` | `NEIEBNB` | `LTFNTFEIFAIFAINIIETNEEIVN` | empty | `LONGER_PAIR_MEMBER_WITH_LEFT_PREFIX` |
| `54` | `F` | `LTFNTFEIFAIFAINIIETNEEIVN` | `ALN` | `SHORTER_PAIR_MEMBER_WITH_MINIMAL_PREFIX_AND_EXTRA_TAIL` |

This corrects the first human wording. Book `54` is not merely "the ending of a
longer formula"; it is a shared local-pair spine with its own wrapper/tail.

## Book12/21 Tail Probe

Persisted in `human_book12_21_tail_shadow_probe_v1_*`.

Decision:
`BOOK12_21_TAIL_SHADOW_SHARED_BASE_PLUS_EXTENSION_NO_O23_GLOSS`

Result:

- Shared block length: `69`
- Shared ratio to Book `12`: `0.9857`
- Shared ratio to Book `21`: `0.7753`
- Direct O23 marker count in Books `12/21`: `0`
- Accepted human gloss: `0`

Segmentation:

| Book | Prefix | Shared base | Suffix | O23 markers | Classification |
| --- | --- | --- | --- | --- | --- |
| `12` | `T` | `TAESESTIENVNSBLFSINNAI...VNAIFEEIIET` | empty | none | `SHARED_BASE_TERMINAL_WITNESS_NO_DIRECT_O23` |
| `21` | `TEBE` | `TAESESTIENVNSBLFSINNAI...VNAIFEEIIET` | `TIVNSENI*LAELBEV` | none | `SHARED_BASE_WITH_EXTRA_TAIL_EXTENSION` |
| `13` | n/a | n/a | n/a | `ONAF`, `FNAAST`, `VEINLETFNAAST` | `O23_ENDPOINT_CONTROL` |
| `38` | n/a | n/a | n/a | `ONAF`, `FNAAST`, `VEINLETFNAAST` | `O23_ENDPOINT_CONTROL` |

This prevents a likely human-translation mistake: Books `12/21` may be terminal
or tail-like structurally, but their evidence is not the same as the direct
O23/ONAF/FNAAST endpoint family in Books `13/38`.

## Immediate Next Batch

1. Build/import the in-game context corpus rows for the eight source families in
   the registry.
2. Tokenize the out-of-book 469 phrases (`Avar Tar`, `Knightmare`, `Chayenne`)
   with the same row0 assumptions.
3. Run contradiction checks for the seven seeded shadow readings against
   `final_honest_reading_v19`, route gates, and held-out family controls.
4. Promote only the next probe question, not the prose, when a shadow reading
   creates a falsifiable test.
5. Expand or revise the shadow prose only after a test changes evidence.

Done in this iteration:

- Produced shadow readings for all seven currently eligible books:
  `49`, `12`, `30`, `26`, `7`, `21`, `54`.
- Stored them in SQLite with `canonical_promotion_status=NOT_PROMOTED`.
- Kept canonical gloss promotions at `0`.
- Bound out-of-book 469 phrases into the human route layer:
  Avar Tar, Chayenne, Knightmare, Poll option, Elder Bonelord sounds.
- Verified the revised seven shadow readings against functional tags and
  source-route gates; all passed as next-probe-ready.
- Ran the first next-probe on the Book30 family and tightened the wording from
  "core" to "`VNSBLFSINNAI` spine plus subfamilies".
- Ran the Book7 phase probe and confirmed the shadow reading as a structural
  bridge from `NEIAAETTA` continuity into `TIINNEF` phase/context controls.
- Ran the Book49 repeat probe and confirmed it as the corpus's highest-repeat
  self-contained formula/refrain witness, while preserving repeat controls.
- Ran the Book54 pair probe and corrected the shadow wording to shared
  local-pair spine with its own tail.
- Ran the Book12/21 tail probe and corrected endpoint wording: no direct
  O23/ONAF/FNAAST marker is present in Books `12/21`.
- Ran the Chayenne external-shape probe and classified the overlap as a
  register/frame anchor across four branches, not a single-gloss translation.
- Consolidated the Mathemagic route into active tests/guardrails:
  `49` as register selector candidate, `13` as local delta guardrail,
  `94->24` as audit selector, Chayenne as register frame, and Book30 as
  anti-linear-prose guardrail.
- Materialized the in-game anchor corpus and bridge map so each human reading
  can cite exactly which game/source evidence supports it and what that evidence
  does not allow.
- Built the human translation atlas: `7/7` current shadow readings are now
  anchored and ready for human review as shadow readings, with `0` promoted
  glosses.
- Expanded the atlas to `11` readings by adding Books `8/37/63/66` from the
  Chayenne frame branch family. These are register/frame branch readings, not
  Chayenne phrase translations.
- Ran a completion audit: current human atlas covers `11/70` books, so the next
  expansion should prioritize the largest missing families: C86/VNCTIIN and
  R20/R02, then BENNA and NAESE/C68.
- Built the C86/VNCTIIN bridge layer with four source-to-family routes:
  payload corridor, VINVIN/VTLR branch, VNCTIIN phase/context, and O23 endpoint
  control.
- Seeded `14` C86/VNCTIIN-family shadow readings while explicitly blocking any
  lexical promotion for C86, VNCTIIN, VINVIN, or O23.
- Expanded the atlas to `25/70` books (`35.71%`) by adding those 14 readings.
- Ran the v2 completion audit: `45` books remain outside the atlas, with R20/R02
  now the largest named next family.
- Built the R20/R02 phase bridge layer with six routes that preserve the
  slot-bridge, connector, VINVIN-covered branch, phase-block, LIVRN micro, and
  weak LTAST-boundary distinctions.
- Seeded `15` R20/R02-family shadow readings, all `NOT_PROMOTED`, with `7`
  subfamilies and explicit blocked claims against lexical R20/R02 gloss.
- Expanded the atlas to `40/70` books (`57.14%`) by adding the R20/R02 phase
  readings.
- Ran the v3 completion audit: `30` books remain outside the atlas. The largest
  remaining blocker is no longer R20/R02, but unassigned residuals plus
  BENNA/formula and NAESE/C68.
- Built the combined slot/formula bridge and shadow layer for BENNA/formula and
  NAESE/C68. The latest shadow run covers `11` books and preserves Book `42` as
  weak/hybrid audit instead of a clean NAESE variant.
- Expanded the atlas to `51/70` books (`72.86%`) with slot/formula readings.
- Built the residual bridge and shadow layer for the final `19` books: display
  drift, local pairs, residual templates, LTAST boundary, endpoint/component,
  marker/metaformula, repeat, near-frame, continuity-only, and unique-header
  residuals.
- Expanded the atlas to `70/70` books (`100.0%`) with `70` anchored,
  human-readable shadow readings and `0` canonical gloss promotions.
- Ran the v5 completion audit: human shadow coverage is complete, but canonical
  translation remains unsolved until review/falsification promotes small,
  auditable pieces.
- Ran the atlas v6 contradiction audit: `70/70` shadow readings passed required
  bridge/anchor/falsifier/no-promotion checks, with `15` promotion-review
  candidates, `16` audit-only rows, and `0` canonical promotions.
- Materialized the promotion-review queue from the clean atlas v6 audit:
  `8` packages, `15` candidate books, and `0` canonical gloss promotions.
  The queue is explicitly for falsification and narrow human-functional labels,
  not for whole-book plaintext.

## Promotion Review Queue

Latest SQLite run:
`HUMAN_PROMOTION_REVIEW_QUEUE_READY_NO_CANONICAL_PROMOTION`.

| Priority | Package | Books | Next falsification test | Blocked promotion |
| --- | --- | --- | --- | --- |
| 1 | `PKG_R02_NAESE_SLOT_BRIDGE_51_53` | `51,53` | Contrast against Book `22` canonical NAESE slot, Book `46` connector, Book `42` weak hybrid, and R02/LIVRN micro controls. | No R02/NAESE/C68 lexical gloss and no full-book plaintext. |
| 2 | `PKG_NAESE_BENNA_COMPOSITE_5_9` | `5,9` | Contrast against Book `22` slot-only, Books `40/50/69` BENNA body, and O23/C86 negatives. | No BENNA or NAESE word gloss and no copied prose between Books `5/9`. |
| 3 | `PKG_BENNA_C86_VNCTIIN_HANDOFF_10_35` | `10,35` | Contrast against C86 payload corridor Books `2/27/67` and BENNA body controls `40/50/69`. | No BENNA/C86/VNCTIIN/LTAST lexical gloss. |
| 4 | `PKG_C86_VNCTIIN_PAYLOAD_2_27_67` | `2,27,67` | Split Book `2` NAESE/C68 slot from Books `27/67` TAILBETFTE suffix and compare against VNCTIIN-only controls `23/24`. | No C86/VNCTIIN/C68 lexical gloss and no single corridor sentence. |
| 5 | `PKG_BOOK54_LOCAL_PAIR_SPINE` | `54` | Contrast Book `54` against Book `20`, Book `25/39` local pair, and zero-boundary controls. | No shared-block word gloss and no zero/taboo semantic import. |
| 6 | `PKG_BOOK7_PHASE_BRIDGE` | `7` | Contrast Book `7` against Book `6` continuity-only and Books `19/31/57` TIINNEF+VNCTIIN phase controls. | No NEIAAETTA or TIINNEF lexical gloss. |
| 7 | `PKG_BOOK49_REPEAT_REGISTER` | `49` | Contrast Book `49` against Book `55` internal repeat and other high-repeat controls. | No `49` dictionary key and no refrain plaintext. |
| 8 | `PKG_CHAYENNE_FRAME_BRANCHES_8_37_66` | `8,37,66` | Keep Book `63` audit-frame as control and verify exact/near-frame boundaries before promotion. | No Chayenne phrase translation and no single English sentence for the shared frame. |

Interpretation: the first likely promotion path is a narrow functional label, not
a lexicon entry. Book pair `51/53` can be tested as an R02 bridge into the
NAESE/C68 slot frame, but any directional reading, word gloss, or full prose
translation remains blocked until it survives the listed controls.

## Package 1 Falsification

Latest SQLite run:
`PROMOTE_HUMAN_FUNCTIONAL_LABEL_NO_GLOSS_DIRECTION_BLOCKED`.

Result for `PKG_R02_NAESE_SLOT_BRIDGE_51_53`:

- Positive evidence: `10` pass signals across queue candidacy,
  `r02_naese_slot_bridge_v1`, `naese_slot_core_v1`, `c68_fatct_slot_items`,
  `r20_r02_naese_phase_gate_v1`, and `r02_narrow_bridge_decision_v1`.
- Controls: `5` pass controls and `1` expected warning.
- Fails: `0`.
- Promoted human-functional labels: `1`.
- Promoted plaintext/lexical glosses: `0`.

Promoted human-functional reading:
Books `51/53` are a phase-to-slot bridge where the
`R02/TRVEIIVNTBB` context enters the `NAESE/C68` slot frame. This is a usable
human reading for review and comparison, but not a sentence translation.

Blocked claims:

- Do not translate `R02`, `NAESE`, or `C68` as standalone words.
- Do not infer a full-book sentence for Books `51` or `53`.
- Do not promote `51->53` directional order; the pair is only a codescribed
  bridge until a direction gate passes.
- Do not propagate the R02 bridge to Book `45`, Book `42`, or LIVRN micro
  controls.

## Package 2 Falsification

Latest SQLite run:
`PROMOTE_HUMAN_FUNCTIONAL_COMPOSITE_LABEL_NO_GLOSS_SUBTYPES_SPLIT`.

Result for `PKG_NAESE_BENNA_COMPOSITE_5_9`:

- Positive evidence: `6` pass signals across
  `naese_benna_composite_probe_v1`, `c68_fatct_slot_items`, and
  `human_slot_formula_shadow_v1`.
- Controls: `18` pass controls and `4` expected warnings.
- Fails: `0`.
- Promoted human-functional labels: `1`.
- Promoted plaintext/lexical glosses: `0`.

Promoted human-functional reading:
Books `5/9` are a slot-to-formula composite where the `NAESE/C68` surface slot
window feeds a `BENNA` formula/concordance frame. Book `5` remains the weaker
template/composite member because its BENNA side is variant/audit-only. Book
`9` carries the cleaner `BENNA` + `LTAST` tail subtype. This is not a plaintext
translation.

Blocked claims:

- Do not translate `NAESE`, `C68`, `BENNA`, `C86`, or `LTAST` as standalone
  words.
- Do not promote Book `5` as a clean BENNA formula body.
- Do not copy prose between Books `5` and `9`; they share a composite frame but
  have different tails.
- Do not use Book `5` terminal `C86` as a semantic bridge; that route is
  unsupported/local.
- Do not collapse this package into O23/FNAAST endpoint readings.

Interpretation: the second package is important because it gives the human layer
a repeatable way to say "slot material entering formula register" without
pretending we know the words. It also preserves a useful internal contrast:
Book `5` is the weaker composite/template witness, while Book `9` is the cleaner
formula-tail witness.

## Package 3 Falsification

Latest SQLite run:
`PROMOTE_HUMAN_FUNCTIONAL_HANDOFF_LABEL_NO_GLOSS_CANONICAL_SHADOW_SPLIT`.

Result for `PKG_BENNA_C86_VNCTIIN_HANDOFF_10_35`:

- Positive evidence: `15` pass signals across `human_slot_formula_bridge_v1`,
  `human_slot_formula_shadow_v1`, `benna_formula_bridge_gate_items`,
  `benna_ordered_core_v2_items`, `c86_payload_operator_gate_items`,
  Q2 handoff state/matrix tables, typed-exit reduction, `35->67` handoff edge,
  and `contig1_handoff_corridor_v1`.
- Controls: `11` pass controls and `4` expected warnings.
- Fails: `0`.
- Promoted human-functional labels: `1`.
- Promoted plaintext/lexical glosses: `0`.

Promoted human-functional reading:
Books `10/35` are a formula-to-context handoff where a `BENNA/LTAST`
formula-concordance tail routes into the `C86/VNCTIIN` payload corridor. Book
`35` is the canonical handoff source into `67->2`. Book `10` is a shadow
handoff that matches the same role through the `10->27->2` path. This is not a
plaintext translation.

Blocked claims:

- Do not translate `BENNA`, `C86`, `VNCTIIN`, `C68`, `TAILBETFTE`, or `LTAST`
  as standalone words.
- Do not promote Book `10` as canonically equivalent to Book `35`.
- Do not collapse Books `2/27/67` payload-corridor readings into the `10/35`
  handoff label.
- Do not use `LTAST` boundary evidence alone as clean lexical or phrase
  translation.
- Do not invent or require a `69->35` contig edge for this package.

Interpretation: the third package gives the human layer a repeatable way to
read "formula register handing off into payload/context corridor". This is the
first promoted human package that explicitly crosses from formula material into
the C86/VNCTIIN corridor while preserving a canonical/shadow distinction.

## Package 4 Falsification

Latest SQLite run:
`PROMOTE_HUMAN_FUNCTIONAL_PAYLOAD_CORRIDOR_LABEL_NO_GLOSS_SLOT_PAYLOAD_SPLIT`.

Result for `PKG_C86_VNCTIIN_PAYLOAD_2_27_67`:

- Positive evidence: `25` pass signals across `human_c86_vnctiin_bridge_v1`,
  `human_c86_vnctiin_shadow_v1`, `c86_payload_operator_gate_items`,
  `c86_naese_parallel_route_contrast_v3`, Q2 state/matrix tables,
  `vnctiin_context_frame_gate_items`, C86/C68/NAESE chain gates, typed-exit
  occurrence gates, and `contig1_handoff_corridor_v1`.
- Controls: `4` pass controls and `4` expected warnings.
- Fails: `0`.
- Promoted human-functional labels: `1`.
- Promoted plaintext/lexical glosses: `0`.

Promoted human-functional reading:
Books `2/27/67` are a `C86/VNCTIIN` payload corridor where `C86 EVIEFIINI`
opens into the `VN C68 TIIN` context frame. Book `67` is the canonical
context-payload bridge in the `35->67->2` path. Book `27` is the shadow
context-payload bridge in the `10->27->2` path. Book `2` is the payload-to-slot
exit where the route reaches the `NAESE/C68` slot. This is not plaintext.

Blocked claims:

- Do not translate `C86`, `VNCTIIN`, `C68`, `NAESE`, `VINVIN`, `O23`, or
  `TAILBETFTE` as standalone words.
- Do not collapse Book `2`'s `NAESE/C68` slot exit into the `27/67` payload
  subtype.
- Do not let Book `2`'s extra C68 occurrence inherit the payload-route
  promotion.
- Do not treat VNCTIIN-only Books `23/24` as payload-open books without C86
  evidence.
- Do not merge the separate `C86->VINVIN` branch into the `C86/VNCTIIN`
  corridor.

Interpretation: the fourth package is the first promoted human package for the
payload corridor itself. It gives us a controlled way to say "C86 opens a
VNCTIIN/C68 context route" while preserving the slot exit and avoiding a global
meaning for C86, VNCTIIN, or C68.

## Package 5 Falsification

Latest SQLite run:
`PROMOTE_HUMAN_FUNCTIONAL_LOCAL_PAIR_LABEL_NO_GLOSS_SHARED_SPINE_ONLY`.

Result for `PKG_BOOK54_LOCAL_PAIR_SPINE`:

- Positive evidence: `8` pass signals across `row0_variant_book_tokens`,
  `human_book54_pair_shadow_probe_v1`, `zero_pair_alignment_items`,
  `zero_pair_local_context_gate_items`, `human_residual_bridge_v1`, and
  `human_residual_shadow_v1`.
- Controls: `15` pass controls and `1` expected warning.
- Fails: `0`.
- Promoted human-functional labels: `1`.
- Promoted plaintext/lexical glosses: `0`.

Promoted human-functional reading:
Book `54` is the shorter member of a local pair with Book `20`. It preserves
the shared spine `LTFNTFEIFAIFAINIIETNEEIVN` with minimal prefix `F` and tail
`ALN`, while Book `20` preserves the same spine after the longer prefix
`NEIEBNB`. This promotes only a local-pair/shared-spine label, not a plaintext
translation.

Blocked claims:

- Do not translate `LTFNTFEIFAIFAINIIETNEEIVN` as a standalone word or phrase.
- Do not translate `F`, `ALN`, or `NEIEBNB` from this package.
- Do not infer zero/taboo semantics; Book `20/54` have no promoted
  zero-operator, recurrent zero-context, or zero-boundary cluster support.
- Do not treat truncation alignment as a plaintext abbreviation.
- Do not collapse the separate Book `25/39` `FAST/BEIE` microtemplate into the
  Book `20/54` pair.
- Do not promote Book `20` or Book `54` as sentence-level translations from
  this evidence.

Interpretation: the fifth package gives the human layer a narrow way to say
"Book 54 is a shorter local-pair member sharing a spine with Book 20". This is
useful because it converts a residual line into an auditable relation without
pretending that the shared block, prefix, or tail has a known lexical meaning.

## Package 6 Falsification

Latest SQLite run:
`PROMOTE_HUMAN_FUNCTIONAL_PHASE_BRIDGE_LABEL_NO_GLOSS_HIGH_PHASE_RISK_HELD`.

Result for `PKG_BOOK7_PHASE_BRIDGE`:

- Positive evidence: `7` pass signals across `book7_phase_anchor_probe_runs`,
  `human_book7_phase_shadow_probe_v1`, `book7_phase_anchor_items`,
  `book7_phase_continuity_gate_items`, and
  `phase_boundary_control_gate_v1`.
- Controls: `18` pass controls and `2` expected warnings.
- Fails: `0`.
- Promoted human-functional labels: `1`.
- Promoted plaintext/lexical glosses: `0`.

Promoted human-functional reading:
Book `7` is a phase-continuity bridge: it combines a `TIINNEF` local phase
anchor with `NEIAAETTA` local continuity. This differs from Book `6`, which is
continuity-only, and from Books `19/31/57`, where `TIINNEF` appears inside
`VNCTIIN`/context material. This remains under high row0 phase risk and is not a
plaintext translation.

Blocked claims:

- Do not translate `NEIAAETTA`, `TIINNEF`, `VNCTIIN`, `BENNA`, `AAETTA`,
  `EIEINT`, or `NENIIF` as words from this package.
- Do not promote `3478`/beholder semantics from Book `7`'s boundary-control
  evidence.
- Do not import Book `7`'s phase-bridge label into Book `6`.
- Do not treat Books `19/31/57` `TIINNEF+VNCTIIN` contexts as the same Book `7`
  bridge.
- Do not override the active high row0 phase-risk warning.
- Do not promote Book `7` as a sentence-level translation.

Interpretation: the sixth package is deliberately conservative. It gives the
human layer a usable phrase for Book `7` -- "phase-continuity bridge" -- while
keeping the phase-risk warning visible. That lets us compare nearby books
without pretending that `NEIAAETTA`, `TIINNEF`, or the `3478` window has become
a dictionary entry.

## Package 7 Falsification

Latest SQLite run:
`PROMOTE_HUMAN_FUNCTIONAL_REPEAT_REGISTER_LABEL_NO_GLOSS_RESIDUAL_COMPONENTS_HELD`.

Result for `PKG_BOOK49_REPEAT_REGISTER`:

- Positive evidence: `6` pass signals across
  `book49_selfcontainment_gate_runs`, `human_book49_repeat_shadow_probe_v1`,
  and `book49_residual_negative_items`.
- Controls: `23` pass controls and `1` expected warning.
- Fails: `0`.
- Promoted human-functional labels: `1`.
- Promoted plaintext/lexical glosses: `0`.

Promoted human-functional reading:
Book `49` is a self-contained repeat/register formula. Its row0 line has the
strongest repeat profile in the reviewed set, with repeated-token coverage
`0.85` and a self-containment audit note. The package promotes only a functional
register label, while `O32`/`NEEI`/`EEILEE`/`LEII` remain residual audit
components with no word gloss.

Blocked claims:

- Do not use `49` as a dictionary key or numeric plaintext key.
- Do not translate `IAEN`, `NEEN`, `O32`, `NEEI`, `EEILEE`, `LEII`, or any
  Book `49` repeat component as a word.
- Do not convert the repeat/register label into a refrain, chant, spell, or
  sentence translation.
- Do not use repetition alone as semantic evidence; high-repeat controls exist
  outside Book `49`.
- Do not collapse Book `55`'s `VFETTIITAV` repeat/variant frame into Book `49`.
- Do not override the Book `49` residual audit context for `O32/NEEI`.

Interpretation: the seventh package lets the human layer say "Book 49 is a
self-contained repeat/register line" without making the old mistake of treating
`49` as a key or treating repeated fragments as translated words. The useful
advance is classificatory, not lexical.

## Package 8 Falsification

Latest SQLite run:
`PROMOTE_HUMAN_FUNCTIONAL_CHAYENNE_FRAME_BRANCH_LABEL_NO_GLOSS_BOOK63_AUDIT_HELD`.

Result for `PKG_CHAYENNE_FRAME_BRANCHES_8_37_66`:

- Positive evidence: `15` pass signals across
  `chayenne_external_shape_gate_items`,
  `human_chayenne_shape_shadow_probe_v1`,
  `human_chayenne_branch_shadow_v1`, `chayenne_role_bridge_gate_v1`, and
  `chayenne_shape_topology_probe_items`.
- Controls: `15` pass controls and `0` expected warnings.
- Fails: `0`.
- Promoted human-functional labels: `1`.
- Promoted plaintext/lexical glosses: `0`.

Promoted human-functional reading:
Books `8/37/66` carry the Chayenne external 469 shape frame
`AEFIEIEFIIVFAEATVAT` in distinct functional branches: Book `8` as a clean
`VNCTIIN` context branch, Book `37` as an `LTAST/TTNVVN` handoff into
`VNCTIIN`, and Book `66` as a `BENNA/LTAST` formula branch. This is a
register/frame classification only; the external sequence has no accepted
gloss.

Blocked claims:

- Do not translate the Chayenne phrase or shared block `AEFIEIEFIIVFAEATVAT`.
- Do not assign one English sentence to Books `8/37/66`.
- Do not treat Book `63` as promoted; it remains residual/audit control.
- Do not promote near variants such as `TAEFIEIEFIIVFATFT` as equivalent
  plaintext.
- Do not use community/context sources as explicit gloss sources; they attest
  sequence/context only.
- Do not translate `VNCTIIN`, `LTAST`, `TTNVVN`, `BENNA`, or `C68` from this
  package.

Interpretation: the eighth package is the external-shape package the project
needed, but it is still not a Chayenne translation. It gives us a source-linked
frame to compare against the in-game books while preserving the strict rule that
sequence attestation is not semantic gloss.

## Post-Promotion Synthesis

Latest SQLite run:
`HUMAN_FUNCTIONAL_PROMOTION_MAP_READY_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_functional_promotion_synthesis_v1.py`.

Result:

- Packages consolidated: `8/8`.
- Books with promoted human-functional labels: `15`.
- Functional clusters: `3`.
- Control fails: `0`.
- Promoted plaintext/lexical glosses: `0`.
- Next falsification questions: `5`.

Promoted human-functional clusters:

| Cluster | Books | Human-functional use |
| --- | --- | --- |
| `PHASE_SLOT_TO_FORMULA_CHAIN` | `51/53`, `5/9`, `10/35`, `2/27/67` | Test a chained route from R02/NAESE slot mechanics into BENNA/LTAST formula handoff and C86/VNCTIIN payload corridor. |
| `LOCAL_PAIR_AND_RESIDUALS` | `54`, `7`, `49` | Keep narrow residual/local readings: Book `54` pair spine, Book `7` phase bridge, Book `49` repeat/register. |
| `EXTERNAL_FRAME_BRANCH` | `8/37/66` | Use Chayenne external-shape overlap as a branch/register frame, not a translated phrase. |

Next falsification questions now registered in SQLite:

1. `Q1_PHASE_SLOT_FORMULA_PAYLOAD_CHAIN`: can the promoted `51/53 -> 5/9 ->
   10/35 -> 2/27/67` chain predict held-out transitions as a procedural
   register without adding prose?
2. `Q2_CHAYENNE_PRIMARY_EXPLICIT_GLOSS`: can any primary or trusted in-game
   source give the exact Chayenne sequence plus explicit meaning?
3. `Q3_BOOK49_REGISTER_FUNCTION`: does Book `49`'s repeat/register pattern
   correlate with calibration/operator-reset use in in-game context?
4. `Q4_BOOK7_PHASE_DIRECTION`: does Book `7` directionally bridge
   `NEIAAETTA` continuity into `TIINNEF` phase, or is it local co-occurrence?
5. `Q5_BOOK20_54_LOCAL_PAIR_CONTEXT`: can Book `20/54`'s shared spine be
   anchored to physical book adjacency, shelf context, or a repeated in-game
   pair convention?

Interpretation: after the eight packages, the useful object is no longer a loose
list of plausible readings. We now have a compact promoted functional map:
fifteen books have falsified human-functional labels, all still barred from
word/prose gloss. The next work should test these clusters as systems, starting
with the `PHASE_SLOT_TO_FORMULA_CHAIN`, because that is the only promoted path
that currently behaves like a multi-stage route rather than a single local
classification.

## Q1 Chain Probe

Latest SQLite run:
`CHAIN_DOWNSTREAM_ROUTE_CONFIRMED_UPSTREAM_INTERFACES_HELD_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_chain_phase_slot_formula_payload_probe_v1.py`.

Result:

- Chain books tested: `9`.
- Promoted cluster books confirmed: `9`.
- Positive stage signals: `21`.
- Positive ordered edges: `7`.
- Held interfaces: `3`.
- Control fails: `0`.
- Promoted plaintext/lexical glosses: `0`.

Accepted downstream route:

| Route | Evidence | Human-functional reading |
| --- | --- | --- |
| `35 -> 67 -> 2` | `q2:CANONICAL_35_67_2` plus contig overlaps `35 -> 67 -> 2` | Canonical handoff/context source moves into `C86/VNCTIIN` context-payload bridge and then the terminal `NAESE/C68` slot/operator. |
| `10 -> 27 -> 2` | `q2:SHADOW_10_27_2` | Shadow handoff/context path mirrors the same payload-to-slot convergence, but remains shadow rather than canonical. |

Held interfaces:

- `51 -> 53`: direct overlap exists and supports the R02/NAESE pair, but the
  package still blocks direction and gloss.
- `53 -> 5`: functional adjacency exists from the R02/NAESE slot bridge to the
  NAESE/BENNA composite, but no ordered contig/Q2 edge promotes it.
- `9 -> 10`: functional adjacency exists from the NAESE/BENNA composite to the
  BENNA/C86 handoff, but no ordered contig/Q2 edge promotes it.

Blocked claims:

- Do not translate stage labels as words.
- Do not claim `51/53 -> 5/9 -> 10/35` is a fully ordered contig or prose path.
- Do not convert the Q2 routes into English sentence translations.

Interpretation: Q1 upgrades the promoted chain from a list of compatible
functional packages into a partial route. The downstream handoff/payload
sequence is now ordered and usable for future human readings. The upstream
phase-slot and slot-formula side remains useful as a search frame, but it is not
yet a single ordered sentence or a solved translation.

## Q2 Chayenne Explicit Gloss Audit

Latest SQLite run:
`Q2_CHAYENNE_EXPLICIT_GLOSS_REJECTED_SEQUENCE_ATTESTED_FRAME_ONLY`.

Materialized by:
`scripts/sqlite_human_q2_chayenne_explicit_gloss_live_audit_v1.py`.

Result:

- Sources checked: `5`.
- Sources attesting the exact Chayenne sequence: `4`.
- Method/context-only source: `1`.
- Explicit glosses found: `0`.
- Plaintext promotions allowed: `0`.

Audited source status:

| Source | Status | Use |
| --- | --- | --- |
| `portaltibia_interview_pt` | `EXACT_SEQUENCE_REPLY_NO_GLOSS` | Direct interview context: question about Beholder language, numeric answer, no meaning. |
| `portaltibia_forum_interview_en` | `EXACT_SEQUENCE_REPLY_NO_GLOSS` | English forum mirror preserves the same question and answer, no meaning. |
| `tibiawiki_br_469_chayenne` | `EXACT_SEQUENCE_CONTEXT_NO_GLOSS` | Wiki context records the sequence and frames it as a CipSoft joke, not a translation. |
| `s2ward_469_chayenne_corpus` | `EXACT_SEQUENCE_CORPUS_NO_GLOSS` | Corpus quotes the sequence and links it to in-game anchors, no explicit meaning. |
| `tibiasecrets_hellgate_averages_chayenne` | `METHOD_CONTEXT_NO_EXACT_GLOSS` | Treats Chayenne/NPC/poll phrases as excerpts/context, not complete translated books. |

Allowed inference:
The Chayenne reply remains strong evidence for an external 469 frame/register
that appears inside Books `8/37/66` and an audit-only Book `63` branch.

Blocked claims:

- Do not translate the Chayenne reply.
- Do not infer that Chayenne gave a phrase-plus-meaning Rosetta stone.
- Do not treat the shared row0 shape `AEFIEIEFIIVFAEATVAT` as a fixed English
  sentence.
- Do not promote the Chayenne branch family beyond functional frame/register
  behavior unless a future source gives exact sequence plus explicit meaning.

Interpretation: Q2 closes the tempting "maybe Chayenne already translated it"
path. The answer is no under the project's acceptance gate. The useful route is
not to force a Chayenne gloss, but to use Chayenne as a live external-shape
constraint when searching for repeated frame behavior in in-game books and NPC
phrases.

## Q3 Book49 Register Function Probe

Latest SQLite run:
`Q3_BOOK49_REGISTER_CONTROL_ONLY_CALIBRATION_RESET_NOT_SUPPORTED_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q3_book49_register_function_probe_v1.py`.

Result:

- Target book: `49`.
- Support signals for register/control: `5`.
- Control signals: `25`.
- Missing required evidence: `3`.
- Calibration context signals: `0`.
- Operator-reset context signals: `0`.
- Promoted plaintext/lexical glosses: `0`.

Supported reading:
Book `49` can be used as a self-contained repeat/register formula and as a
selector/control witness. This support comes from the rank-1 repeat profile,
the self-containment gate, package 7's promoted functional label, the
post-Mathemagic `<O32_SINGLETON_SELECTOR_CONTROL>` classification, and the
s2ward `B20` self-containment note.

Blocked stronger reading:
Book `49` does not currently support a human reading of calibration,
operator-reset, chant, spell, refrain, dictionary key, or translated sentence.

Key controls:

- High repetition exists outside Book `49`: Books `31`, `57`, `6`, `55`, `10`,
  `35`, `4`, `46`, `51`, `58`, and `62` prevent repetition alone from carrying
  semantic force.
- Book `55` is an internal repeat/variant control, not the same Book `49`
  register.
- `O32`, `NEEI`, `EEILEE`, and `LEII` remain residual/audit components and
  occur outside Book `49` as well.
- `+49/mod70` is only an audit selector: it ties with controls and does not
  produce held-out calibration/reset improvement.
- The `49/94` window remains a ranking signal, not semantic proof.

Missing evidence that blocks calibration/reset:

- No verified book-location or shelf-neighborhood evidence links Book `49` to
  calibration/operator-reset.
- No independent repeated-register parallel gives the same function.
- No in-game, NPC, or quest text states that the Book `49` pattern performs
  reset/calibration.

Interpretation: Q3 trims Book `49` back to the useful version. It remains a
strong functional control for repeated register behavior, but it should not be
used as prose or as a ritual/reset instruction unless new in-game placement or
parallel evidence appears.

## Q4 Book7 Phase Direction Probe

Latest SQLite run:
`Q4_BOOK7_PHASE_BRIDGE_CONFIRMED_DIRECTION_HELD_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q4_book7_phase_direction_probe_v1.py`.

Result:

- Target book: `7`.
- Support signals for the Book `7` bridge shape: `9`.
- Control signals: `7`.
- Held direction/risk signals: `2`.
- Surface-order conflict: `1`.
- Book `7` swallow controls: `3`.
- Promoted plaintext/lexical glosses: `0`.

Supported reading:
Book `7` is stronger than simple local co-occurrence. It is the inspected row
that combines `NEIAAETTA` continuity evidence and `TIINNEF` phase-anchor
evidence without the `VNCTIIN` context seen in Books `19`, `31`, and `57`.
This supports a human-functional label: Book `7` phase-continuity bridge /
bridge-control.

Blocked stronger reading:
The directional claim "`NEIAAETTA` into `TIINNEF`" is not promoted. In Book `7`,
the observed surface order is `TIINNEF` at position `8` before `NEIAAETTA` at
position `23`. That makes the bridge useful as a functional contrast, but not
as a literal order-of-meaning claim.

Key controls:

- Book `6` has `NEIAAETTA` without `TIINNEF`, so the Book `7` label cannot be
  imported into Book `6`.
- Books `19`, `31`, and `57` have `TIINNEF` inside `VNCTIIN`/context material,
  so they remain phase-context controls rather than the same Book `7` bridge.
- Book `7` local `AAETTA`, `EIEINT`, and `NENIIF` hits are swallow/superset
  controls and must not become word glosses.
- High row0 phase risk remains active.

Interpretation: Q4 keeps Book `7` alive as a useful human-translation route,
but only as a bridge/control label. It should help compare nearby phase texts,
not generate prose or a lexical mapping for `NEIAAETTA`, `TIINNEF`, `VNCTIIN`,
`BENNA`, `3478`, or the Book `7` sentence.

## Q5 Book20/54 Local Pair Context Probe

Latest SQLite run:
`Q5_BOOK20_54_SAME_LIBRARY_NOT_PHYSICALLY_ADJACENT_NO_STRONGER_PARAPHRASE`.

Materialized by:
`scripts/sqlite_human_q5_book20_54_local_pair_context_probe_v1.py`.

Result:

- Target pair: Book `20` / Book `54`.
- Support signals: `12`.
- Control signals: `3`.
- External location sources: `2`.
- Same-library confirmations: `2`.
- Physical adjacency confirmations: `0`.
- Shelf-separation controls: `1`.
- Independent in-game pair conventions beyond internal alignment: `0`.
- Promoted plaintext/lexical glosses: `0`.

Supported reading:
The internal pair remains real. Book `20` and Book `54` share the spine
`LTFNTFEIFAIFAINIIETNEEIVN`, with Book `20` using the longer prefix `NEIEBNB`
and Book `54` using prefix `F` plus tail `ALN`. Both source texts are also
confirmed in the Hellgate Library corpus.

Blocked stronger reading:
The external location evidence does not support physical adjacency or shelf
neighborhood. The project Book `20` text maps to `Nieznana 6` on the third
shelf of the Hellgate Library listing, while the project Book `54` text maps to
`Nieznana 14` on the seventh shelf. That means the same-library context is
valid, but the stronger "adjacent books" explanation is rejected.

Key controls:

- `PAIR_25_39_FAST_BEIE` shows another internal pair/microtemplate, so internal
  pair behavior is not automatically prose.
- `PAIR_60_64_R20_LIVRN` remains audit-only, showing that pair-like similarity
  is not enough for promotion.
- There is still no independent in-game convention saying separated Hellgate
  books should be read as a physical pair.

Interpretation: Q5 narrows Book `20/54` to the honest version: a strong
internal local-pair/shared-spine control inside the same Hellgate corpus, not a
physical shelf-neighbor argument and not a Book `54` paraphrase.

## Completion Audit After Q1-Q5

Latest SQLite run:
`HUMAN_SHADOW_ATLAS_COMPLETE_CANONICAL_TRANSLATION_UNSOLVED`.

Materialized by:
`scripts/sqlite_human_translation_completion_audit_v5.py`.

Result:

- Total books: `70`.
- Human shadow atlas rows: `70`.
- Atlas coverage: `100.0%`.
- Missing shadow rows: `0`.
- Anchored rows: `70`.
- Readable shadow rows: `70`.
- Promoted canonical/plaintext glosses: `0`.

Interpretation: the project now has full human-shadow coverage, but this is not
a solved canonical translation. The honest status is: plausible source-anchored
reading layer exists for review; no book plaintext/gloss has been promoted.

## Remaining Residual Evidence Requirements

Latest SQLite run:
`REMAINING_FIVE_REQUIRE_NEW_EVIDENCE`.

Materialized by:
`scripts/sqlite_remaining_five_evidence_requirements_v1.py`.

Result:

- Remaining residual books requiring stronger evidence: `6`, `7`, `14`, `32`,
  `36`.
- Immediately actionable: `6`, `7`, `32`, `36`.
- Not immediately actionable: `14`.
- Accepted prose glosses: `0`.

Safest next probes:

- Books `6/7`: row0 phase/path disambiguation using operator selectors and
  `3478` boundary controls.
- Books `32/36`: display-tail masking with held-out payload prediction; promote
  only if independent payload emerges.
- Book `14`: hold unless new R02/LTAST phase evidence beats the failed weak
  boundary gate.

## Q6 External Corpus Order Residual Probe

Latest SQLite run:
`Q6_EXTERNAL_ORDER_SUPPORTS_BOOK6_7_ADJACENCY_DISPLAY_RESIDUALS_HELD_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q6_external_corpus_order_residual_probe_v1.py`.

Result:

- Target residuals checked: `4`.
- Source digit matches: `4`.
- Book `6/7` external-order adjacency support: `1`.
- Book `32/36` display-residual separation control: `1`.
- Promoted plaintext/lexical glosses: `0`.

Source:
`https://linguagem469.wordpress.com/wp-content/uploads/2012/01/padrc3b5es469.pdf`
(`Padroes469`, "Livro | Original" table).

Supported reading:
The external corpus order places the project Book `6` text as `Livro 42` and
the project Book `7` text as `Livro 43`. This gives a new audit-only relation:
Book `6` is an even stronger immediate continuity control for Book `7`.

Blocked stronger reading:
External order is not a translation key. It does not translate `NEIAAETTA`,
`TIINNEF`, `3478`, Book `6`, or Book `7`.

Display residual control:
The same external source places Book `36` as `Livro 46` and Book `32` as
`Livro 53`. That does not create an adjacent-pair explanation for the display
residuals, so Books `32/36` stay closed as display controls unless new
independent payload evidence appears.

Interpretation: Q6 gives the next best route: reopen Book `6/7` only as a
narrow phase/path precheck, using external order as support and Q4's surface
direction warning as a guardrail.

## Q7 Book6/7 Phase-Path Precheck

Latest SQLite run:
`Q7_BOOK6_TO_BOOK7_SEQUENCE_SUPPORTED_INTERNAL_BOOK7_DIRECTION_HELD_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q7_book6_7_phase_path_precheck_v1.py`.

Result:

- Support signals: `4`.
- Control signals: `2`.
- Book-order direction support: `1`.
- Internal Book `7` direction held: `1`.
- Promoted plaintext/lexical glosses: `0`.

Supported reading:
Book `6 -> 7` can now be used as a directional sequence/control relation for
phase-path testing. Q6 supplies the external corpus order (`Livro 42 -> 43`),
while the internal shadow split keeps Book `6` as continuity-only and Book `7`
as phase-continuity bridge.

Blocked stronger reading:
This does not reverse Q4. Inside Book `7`, the surface order still has `TIINNEF`
before `NEIAAETTA`, so the claim "`NEIAAETTA` becomes `TIINNEF`" remains held.
No translation of Book `6`, Book `7`, `NEIAAETTA`, `TIINNEF`, or `3478` is
promoted.

Interpretation: Q7 turns Q6 into a usable next-lane precheck. The next
mechanical experiment should test row0 phase/path behavior over `6 -> 7` with
operator selectors and `3478` boundary controls, while explicitly refusing any
Book `7` sentence-level prose.

## Q8 Book6/7 3478 Phase-Path Transition Probe

Latest SQLite run:
`Q8_BOOK6_7_3478_WINDOW_TRANSITION_PHASE_PATH_SUPPORTED_NO_PAYLOAD_GLOSS`.

Materialized by:
`scripts/sqlite_human_q8_book6_7_phase_path_3478_transition_probe_v1.py`.

Result:

- Support signals: `7`.
- Control signals: `4`.
- Component transition signal: `1`.
- Dominant/common `3478` window control: `1`.
- Rare `3478` window signal: `1`.
- Row0 path-resolved count: `2`.
- Promoted plaintext/lexical glosses: `0`.

Supported reading:
Book `6 -> 7` is now a defensible continuity-to-phase path/control relation.
Book `6` has the dominant/common `3478` window `6151353478019288` and
`NEIAAETTA` without `TIINNEF`. Book `7` has the rare `3478` window
`0815953478019288`, keeps `NEIAAETTA`, adds `TIINNEF`, and already has the
Book7 phase-boundary control label.

Blocked stronger reading:
This is not a semantic payload. It does not translate `3478`, `NEIAAETTA`,
`TIINNEF`, Book `6`, or Book `7`; it also does not undo Q4's warning that Book
`7`'s internal surface order has `TIINNEF` before `NEIAAETTA`.

Interpretation: Q8 reduces one of the remaining residual blockers by converting
Book `6/7` from a vague display/phase risk into a specific transition-control
relation. A stronger translation would need a held-out contig/pair prediction
or independent in-game phrase that assigns payload without using `3478` or the
phase anchors as word glosses.

## Q9 Book6/7 Held-Out Support Audit

Latest SQLite run:
`Q9_BOOK6_7_TRANSITION_NO_HELDOUT_CONTIG_SUPPORT_KEEP_CONTROL_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q9_book6_7_heldout_support_audit_v1.py`.

Result:

- Prior transition supports retained: `3` (`Q6`, `Q7`, `Q8`).
- Held-out positive contig/overlap/literal/similarity supports: `0`.
- Weak singleton support: `1` (`Book7 -> Book6`, `NEIAAETTA` LCS only).
- Imported contig edge support: `0`.
- Max-overlap contig edge support: `0`.
- Overlap assembly prediction support: `0`.
- Literal frontier pair support: `0`.
- Residual similarity pair support: `0`.
- Promoted plaintext/lexical glosses: `0`.

Supported reading:
Q8 remains useful, but only as a local transition-control relation. The current
evidence still supports using Book `6 -> 7` as continuity-to-phase context for
future tests.

Blocked stronger reading:
Current held-out tables do not independently predict `6 -> 7` as a contig,
overlap, literal-frontier, or residual-similarity pair. The rare singleton probe
only says Book `7` has weak surface LCS to Book `6` through `NEIAAETTA`; it does
not assign payload.

Interpretation: repeat confirmation over the current contig/overlap tables is a
dead branch for Book `6/7`. The next useful evidence must be a new independent
in-game phrase, a newly imported artifact that creates a real `6/7` edge, or a
separate semantic anchor. Until then, Book `6/7`, `3478`, `NEIAAETTA`, and
`TIINNEF` stay unglossed.

## Q10 Book32/36 Display Payload Independence Audit

Latest SQLite run:
`Q10_BOOK32_36_DISPLAY_PAYLOAD_INDEPENDENCE_REJECTED_CLOSE_CONTROL_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q10_book32_36_display_payload_independence_audit_v1.py`.

Result:

- Target books: `2` (`32`, `36`).
- Display-tail hold count: `2`.
- Closed-as-control count: `2`.
- External-order separation control: `1`.
- Book-scoped BTII/NSBVN display-drift controls: `2`.
- Held-out independent payload count: `0`.
- Promoted plaintext/lexical glosses: `0`.

Supported reading:
Books `32/36` are usable as display/control evidence for the formula/display
family. Q6 separates them in the external corpus (`Livro 46` and `Livro 53`),
so there is no physical/order pair argument. Existing tail masking leaves no
independent payload, and the BTII/NSBVN drift gates are explicitly book-scoped.

Blocked stronger reading:
Current evidence does not support translating Book `32` or Book `36` as prose.
It also does not promote `BENNA`, `BTII`, `NSBVN`, `FNAAST`, or the shared tail
as semantic payload in these books.

Interpretation: the current-table route for `32/36` is exhausted. They should
not consume another confirmation lane unless a new external artifact, in-game
phrase, or mechanically different payload boundary appears.

## Q11 Residual Frontier Retriage After Q9/Q10

Latest SQLite run:
`Q11_CURRENT_TABLE_FRONTIER_EXHAUSTED_NEED_NEW_INGAME_OR_EXTERNAL_ANCHORS_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q11_residual_frontier_retriage_after_q9_q10_v1.py`.

Result:

- Remaining residual rows inspected: `5`.
- Rows still listed as actionable by the older residual requirements script: `4`.
- Current-table routes exhausted by Q9/Q10: `4`.
- Local SQLite rerun candidates after retriage: `0`.
- Rows requiring new in-game or external evidence: `5`.
- Promoted plaintext/lexical glosses: `0`.

Retriage:

- Books `6/7`: keep as Q8 transition controls, but Q9 blocks current
  contig/overlap/literal/similarity reruns.
- Book `14`: keep held until new R02/LTAST phase evidence beats the failed weak
  boundary gate.
- Books `32/36`: keep as Q10 display controls, but do not rerun the same
  display-tail/drift/concordance route.

Interpretation: the next frontier is not another local confirmation pass over
the same SQLite evidence. The next useful work is new evidence acquisition:
in-game phrase anchors, exact external captures of in-game text, Mathemagic as
operator/selector evidence, or a newly imported artifact that changes the
evidence graph.

## Q12 Bonelord Tome 3478/486486 Anchor Probe

Latest SQLite run:
`Q12_BONELORD_TOME_ADDS_INGAME_3478_486486_COLOCATION_ANCHOR_NO_COMPONENT_GLOSS`.

Materialized by:
`scripts/sqlite_human_q12_bonelord_tome_3478_486486_anchor_probe_v1.py`.

Web/source evidence checked:

- `https://tibia.fandom.com/wiki/Bonelord_Tome`
- `https://www.tibiawiki.com.br/wiki/Bonelord_Tome`

Result:

- Source pages cross-checked: `2`.
- Exact anchor entries registered: `3`.
- 3478/486486 co-location anchor: `1`.
- Prior `486486` in-game anchor reused: `1`.
- Q8 transition-control compatibility: `1`.
- Q9 no-component-gloss control: `1`.
- Promoted plaintext/lexical glosses: `0`.

Supported reading:
The Bonelord Tome is a useful in-game/fansite-item anchor for prioritising the
`3478/486486` route. It co-locates the known Knightmare `3478 ... 345` phrase
with a `486486` answer/attention line and Bonelord/TibiaSecrets knowledge
framing. This strengthens the idea that `3478` and `486486` should be tested as
phrase/name/formula anchors, not as isolated word values.

Blocked stronger reading:
The item does not translate `3478`, `486486`, Book `6`, Book `7`, or the
Knightmare phrase. It also does not give a book decoder. The source should be
verified in-client or via official item data before any stronger promotion.

Interpretation: Q12 is the first post-Q11 new-evidence improvement. It does not
solve a gloss, but it gives a better human route: compare all external
`3478/486486` phrase-level material against row0 projections and keep component
glosses blocked.

## Q13 Bonelord Tome Source Ladder And Projection

Latest SQLite run:
`Q13_BONELORD_TOME_SOURCE_LADDER_SUPPORTS_ROUTE_NEEDS_CLIENT_VERIFICATION_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q13_bonelord_tome_source_ladder_projection_v1.py`.

Source ladder checked:

- `https://www.tibia.com/`: no direct official `Bonelord Tome` sound source was
  found in the current web search.
- `https://tibiasecrets.com/bonelord_tome`: fansite history/context for the
  item concept and its 469/lore motivation.
- `https://tibia.fandom.com/wiki/Bonelord_Tome`: secondary item page listing
  `3478...` and `486486...` sounds.
- `https://www.tibiawiki.com.br/wiki/Bonelord_Tome`: second secondary item page
  listing the same sounds and official TibiaSecrets fansite-item context.
- `https://tibia.fandom.com/wiki/Fansite_Appreciation_Day_2022`: event context
  listing `TibiaSecrets | Bonelord Tome`.

Result:

- Source ladder entries: `5`.
- Direct official/client sound source count: `0`.
- Secondary sound-source count: `2`.
- Fansite history/context source count: `1`.
- Event context source count: `1`.
- Knightmare `3478...` row0 projection: out-of-book corpus (`1`).
- `486486` entity quarantine support: `1`.
- Client/official-data verification still required: `1`.
- Promoted plaintext/lexical glosses: `0`.

Supported reading:
Bonelord Tome is strong enough to prioritise a `3478/486486` route, because the
source ladder confirms item context and repeated secondary sound attestation.
The local projection also keeps the Knightmare phrase outside the book corpus,
while `486486` remains an entity/identifier quarantine.

Blocked stronger reading:
The item sounds are not yet verified from a direct client/official data source.
This blocks promotion from "source route" to "primary attested phrase". It also
blocks any component gloss for `3478`, `486486`, the Knightmare phrase, or the
Hellgate books.

Interpretation: Q13 turns Q12 into an actionable evidence ladder. The next
useful step is not decoding from the tome; it is verifying the tome sounds
directly in-client or via official item data, then using that verified phrase
context only at phrase/name/formula level.

## Q14 Bonelord Tome Verification Target

Latest SQLite run:
`Q14_BONELORD_TOME_CLIENT_SOUND_VERIFICATION_TARGET_REGISTERED_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q14_register_bonelord_tome_verification_target_v1.py`.

Result:

- Previous external semantic open-target run: `2`.
- New external semantic open-target run: `3`.
- Previous target count: `6`.
- New target count: `7`.
- High-priority target count: `4`.
- Promoted plaintext/lexical glosses: `0`.

New high-priority target:
`BONELORD_TOME_CLIENT_SOUNDS`.

Required evidence:
Direct in-client capture, official item data, or trusted client-data extraction
showing Bonelord Tome sounds with the `3478...` phrase and `486486` line.

Acceptance gate:
Even if verified, the target only upgrades the phrase/name/formula source
status. It does not promote component gloss or book prose without explicit
meaning.

## Q15 Local Client Asset Gap For Bonelord Tome

Latest SQLite run:
`Q15_LOCAL_CLIENT_ASSETS_CANNOT_VERIFY_BONELORD_TOME_NEED_MODERN_CLIENT_DATA_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q15_local_client_asset_gap_for_bonelord_tome_v1.py`.

Result:

- Local client artifacts inspected under `tmp/tibia_clients`: `33`.
- Old/pre-Bonelord-Tome client artifacts: `28`.
- Modern client candidates: `0`.
- Existing old-client probe contexts: `3`.
- Bonelord Tome verification possible from current local assets: `0`.
- Promoted plaintext/lexical glosses: `0`.

Interpretation:
The existing local client assets are useful for historical/font/old-client
checks, but they cannot verify a 2021 Bonelord Tome item. Q14 therefore remains
open: the project needs a direct in-client capture, official item data, or
trusted modern client-data extraction.

## Q16 Poll 2020 Primary Context Access Audit

Latest SQLite run:
`Q16_POLL_2020_PRIMARY_CONTEXT_AUDIT_REQUIRES_MANUAL_REVIEW`.

Materialized by:
`scripts/sqlite_human_q16_poll2020_primary_context_access_audit_v1.py`.

Result:

- Official Tibia URL variants fetched: `4`.
- Official fetch successes: `4`.
- Official pages containing the exact `663 902073 7223 67538 467 80097`
  sequence and question: `0`.
- Wayback CDX access: `1`.
- Community/context sources retained: `3`.
- Promoted plaintext/lexical glosses: `0`.

Interpretation:
The current Tibia pages respond, but the poll content is not present in the
returned HTML. CDX found snapshots, so Q16 required manual follow-up instead of
closing the target.

## Q17 Poll 2020 Wayback Snapshot Content Audit

Latest SQLite run:
`Q17_POLL_2020_WAYBACK_SNAPSHOTS_NO_CONTENT_TARGET_REMAINS_OPEN_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q17_poll2020_wayback_snapshot_content_audit_v1.py`.

Result:

- Snapshots fetched: `3`.
- Snapshot fetch successes: `3`.
- Snapshots containing exact option C sequence: `0`.
- Snapshots containing the poll question text: `0`.
- Primary context resolved: `0`.
- Promoted plaintext/lexical glosses: `0`.

Interpretation:
The current Wayback route for `questionaireid=1009` does not recover the poll
content. `POLL_2020_OPTION_C` remains an open target requiring another primary
or archived route. Community copies can guide the search, but they still cannot
serve as the acceptance gate.

## Q18 Elder Bonelord Sound Binding Audit

Latest SQLite run:
`Q18_ELDER_BONELORD_SOUNDS_ATTESTED_NO_SEMANTIC_BINDING_KEEP_NPC_QUARANTINE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q18_elder_bonelord_sound_binding_audit_v1.py`.

Sources checked:

- `https://tibia.fandom.com/wiki/Elder_Bonelord`
- `https://www.tibiawiki.com.br/wiki/Elder_Bonelord`
- `https://www.tibia-wiki.net/wiki/Elder_Bonelord`
- `https://www.tibiaqa.com/25041/is-avar-tar-lying-about-his-stories`

Result:

- Source count: `4`.
- Numeric sound attestation count: `4`.
- Sources placing numeric sounds in the same creature-voice context as English
  sounds: `2`.
- Explicit semantic binding count: `0`.
- Existing NPC phrase quarantine count: `2`.
- Rosetta/book promotion allowed count: `0`.
- Promoted plaintext/lexical glosses: `0`.

Supported reading:
The Elder Bonelord sequences `659978 54764` and `653768764` are reliable
external/in-game speech holdouts. They should remain in the human route layer as
Bonelord speech/register evidence.

Blocked stronger reading:
The checked sources list the numeric and English creature sounds together, but
they do not explicitly state that `653768764` means "look at you" or that
`659978 54764` means "let me see you". Therefore the existing `RDW-*` wordcode
anchors remain NPC-only/quarantined and cannot be promoted into Hellgate book
glosses.

Interpretation:
Q18 blocks a common contamination path. Elder Bonelord sounds can guide
register/style comparison, but the next accepted step would require a primary or
explicit source binding the numeric shout to an English phrase.

## Q19 Tibia.org Avar Variant Wayback Confirmation

Latest SQLite run:
`Q19_TIBIA_ORG_AVAR_VARIANT_PRIMARY_ARCHIVE_CONFIRMED_MICRO_ANCHOR_ONLY_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q19_tibia_org_avar_variant_wayback_confirmation_v1.py`.

Primary/archive source:
`https://web.archive.org/web/20200915225804id_/http://www.tibia.org/`.

Result:

- Current `http://tibia.org/` sequence hit count: `0`.
- Wayback exact `62792068657272657261` hit count: `1`.
- Wayback full Avar variant hit count: `1`.
- Existing `NARCISSIST` micro-anchor count: `1`.
- Explicit meaning attested count: `0`.
- Promoted plaintext/lexical glosses: `0`.
- `external_semantic_open_targets` advanced from run `3` to run `4`.

Backlog status change:
`TIBIA_ORG_AVAR_VARIANT` is no longer `OPEN_ARCHIVE_ACCESS_BLOCKED`. It is now
`PRIMARY_ARCHIVE_SEQUENCE_CONFIRMED_NO_EXPLICIT_MEANING`.

Supported reading:
The hidden Tibia.org/Wayback HTML comment is real source evidence for the Avar
Tar variant sequence. This strengthens the already recorded provisional
`NARCISSIST` micro-anchor and gives the human route a better primary phrase
context.

Blocked stronger reading:
The source confirms the sequence, not the meaning. It still does not promote the
full Avar phrase, the `NARCISSIST`/`NARCISSISM` choice as a final gloss, or any
Hellgate book prose.

Interpretation:
Q19 is a genuine evidence upgrade. The next useful test is phrase-level: compare
the archived Avar variant against the original Avar Tar poem and route it as a
micro-anchor/phrase scaffold, while still requiring explicit meaning or a strong
independent semantic bridge for promotion.

## Q20 Avar Variant Slot Micro-Anchor Audit

Latest SQLite run:
`Q20_AVAR_VARIANT_SLOT_REPLACEMENT_CONFIRMS_PRIMARY_NARCISSIST_MICROANCHOR_NO_BOOK_GLOSS`.

Materialized by:
`scripts/sqlite_human_q20_avar_variant_slot_microanchor_audit_v1.py`.

Result:

- Q19 source run used: `1`.
- Replacement slot index: `11`.
- Unchanged word count: `19`.
- Original Avar slot decode: `VAIN`.
- Tibia.org variant slot decode: `NARCISSIST`.
- Primary archived sequence confirmation: `1`.
- External micro-anchor count: `1`.
- Book promotion allowed: `0`.
- Promoted plaintext/lexical glosses: `0`.

Supported reading:
The original Avar Tar poem and the archived Tibia.org variant differ in exactly
one word slot. Under the current row0 projection, the original slot decodes as
`VAIN`, while the archived replacement decodes as `NARCISSIST`. This is now a
strong phrase-slot micro-anchor with primary archived sequence support.

Blocked stronger reading:
This still does not translate the whole Avar poem, decide between broader
`NARCISSIST`/`NARCISSISM` semantics in running prose, or promote any Hellgate
book text. It is external phrase scaffolding only.

Interpretation:
Q20 gives the human route a concrete, falsifiable anchor: phrase-slot
replacement. Future semantic hypotheses should explain why an in-game/external
variant would replace `VAIN` with `NARCISSIST` at the same slot, without forcing
that explanation into the book corpus.

## Q21 Avar Tar Narcissist Lore Plausibility

Latest SQLite run:
`Q21_AVAR_TAR_NARCISSIST_LORE_PLAUSIBLE_CHARACTER_SLOT_NO_BOOK_GLOSS`.

Materialized by:
`scripts/sqlite_human_q21_avar_tar_narcissist_lore_plausibility_v1.py`.

Sources used:

- `https://tibia.fandom.com/wiki/Avar_Tar/Transcripts`
- `https://tibiasecrets.com/Avar-Tar`
- `https://www.tibiaqa.com/25041/is-avar-tar-lying-about-his-stories`

Result:

- Q20 source run used: `1`.
- Lore/transcript source count: `3`.
- Self-aggrandizing context source count: `3`.
- Bonelord-language context source count: `3`.
- Explicit semantic binding count: `0`.
- Character-slot plausibility count: `1`.
- Book promotion allowed: `0`.
- Promoted plaintext/lexical glosses: `0`.

Supported reading:
The Q20 slot delta (`VAIN -> NARCISSIST`) is contextually plausible as an Avar
Tar character/register signal. Multiple transcript sources present Avar Tar as a
boastful heroic persona, and the same NPC is the in-game anchor for the numeric
poem. This makes the replacement meaningful as a human hypothesis: the external
variant may be pointing at Avar Tar's vanity/narcissism.

Blocked stronger reading:
No checked source explicitly says the numeric replacement means
`NARCISSIST`, and no source binds the full Avar poem to English prose. Q21 does
not promote `NARCISSIST` as a book lexeme and does not translate any Hellgate
book.

Interpretation:
This is the first useful "human shadow" move after the strict local frontier
closed: use a real source-backed persona clue to explain why a slot replacement
would be intentional. The next search should look for other in-game/editorial
variants where a 469 phrase is modified in a semantically themed context, then
test those variants as scoped shadow anchors before any canonical promotion.

## Q22 Cross-Quest Human Shadow Route Prioritization

Latest SQLite run:
`Q22_CROSS_QUEST_HUMAN_SHADOW_ROUTES_PRIORITIZED_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q22_cross_quest_shadow_route_prioritization_v1.py`.

Source runs used:

- Q21 Avar/persona run: `1`.
- In-game anchor corpus run: `1`.
- Human Mathemagic synthesis run: `1`.

Result:

- Prioritized route count: `6`.
- Active route count: `4`.
- Source-verified route count: `4`.
- Direct gloss route count: `0`.
- Canonical promotion allowed: `0`.

Prioritized routes:

| Priority | Route | Status | Use |
| --- | --- | --- | --- |
| 1 | `EDITORIAL_VARIANT_SEMANTIC_SLOT_ROUTE` | `ACTIVE_SOURCE_SEARCH` | search old official/fansite/client variants where one 469 slot changes in a themed context |
| 2 | `AVAR_PERSONA_REGISTER_ROUTE` | `ACTIVE_SHADOW_CONTEXT` | treat Avar as persona/register context, not book dictionary |
| 3 | `MATHEMAGIC_OPERATOR_SELECTOR_ROUTE` | `ACTIVE_OPERATOR_TEST` | use `1/13/49/94` as selectors/operators only |
| 4 | `GREAT_CALCULATOR_COMPILED_CORPUS_ROUTE` | `ACTIVE_STRUCTURAL_MODEL` | test Hellgate as compiled formulas/spines/fragments rather than one linear prose corpus |
| 5 | `MINOTAUR_MAGE_TRUTH_BRIDGE_ROUTE` | `NEEDS_TRANSCRIPT_AUDIT` | import exact A Prisoner/Riddler transcript rows before using Mintwallin as a Bonelord bridge |
| 6 | `BONELORD_TOME_CLIENT_SOUND_ROUTE` | `BLOCKED_ON_CLIENT_OR_OFFICIAL_DATA` | verify 2021 item sounds in client/official data before stronger claims |

Supported reading:
Mathemagica and related quests are now active methodology inputs, but only as
operators, selectors, source-prioritization signals, or corpus-structure
constraints. The highest-yield human route is no longer generic prose drafting;
it is exact variant hunting plus themed slot contrast.

Blocked stronger reading:
No Q22 route is allowed to promote plaintext. A route can become stronger only
if it brings exact sequence provenance, contrastive mechanics, and reduced
contradiction against held-out material.

Interpretation:
This gives the translation effort a practical human search program:
find source-backed variants first, use Mathemagica to rank or constrain tests,
and use Great Calculator lore to stop forcing the Hellgate books into one
continuous sentence model.

## Q23 Recent GitHub German/MHG Candidate Triage

Latest SQLite run:
`Q23_RECENT_GITHUB_GERMAN_CANDIDATE_AUDIT_ONLY_NO_PROMOTION`.

Materialized by:
`scripts/sqlite_human_q23_recent_github_candidate_solution_triage_v1.py`.

External claim audited:
`https://github.com/arturoornelasb/tibia-bonelord-469-cipher`.

Why this was audited:
A recent Reddit/GitHub discussion claims a German/MHG homophonic solution for
the 70 Hellgate books. This is a potentially useful external hypothesis, but it
must pass the project gates before influencing any human reading.

Result:

- Raw GitHub artifact fetches: `4/4`.
- Candidate mapping code count: `98`.
- Candidate book count: `70`.
- Candidate mapping unique letters: `20`.
- README claimed letter count: `22`.
- Self-disclaimer / overfit / anchor-gap signals: `4`.
- In-game anchor pass count: `0`.
- External phrase bridge pass count: `0`.
- Claimed proper-noun hits on checked 469 lore pages: `0`.
- Canonical promotion allowed: `0`.

Anchor controls:

| Anchor | Candidate output | Gate result |
| --- | --- | --- |
| `486486` | `NTM` | does not preserve A Wrinkled Bonelord name anchor |
| `1` | not pair-decodable | does not preserve `Tibia=1` anchor |
| `0` | not pair-decodable | does not preserve zero taboo anchor |
| Avar original slot `63378129` | `DETE` | does not preserve Q20 `VAIN` slot |
| Avar variant slot `62792068657272657261` | `BOFRIRRIRU` | does not preserve Q20 `NARCISSIST` slot |
| Knightmare `3478...` phrase | `LTENWEETLAED` | no accepted phrase bridge |
| Chayenne reply | not pair-decodable | no accepted phrase bridge |

Supported reading:
The external repository is worth keeping as an audit-only adversarial
hypothesis because it has a concrete mapping, a full 70-book corpus, and an
explicit claim that can be tested mechanically.

Blocked stronger reading:
It cannot be accepted as a human translation layer now. It has no bridge to the
strict in-game anchors used here, no accepted external phrase bridge, no local
hits for its strongest proper nouns on the checked 469 lore pages, and its own
documentation flags unconfirmed intent, overfit risk, and a separate NPC/book
cipher-system gap.

Interpretation:
Q23 is a useful containment result: new external solution claims should enter as
quarantined benchmarks, not as prose. The next useful action is to import the
candidate mapping into a shadow-only benchmark against local contigs, row0
invariants, exact external phrase anchors, and source-linked lore nouns.

## Q24 External Candidate Containment

Latest SQLite run:
`Q24_EXTERNAL_GERMAN_CANDIDATE_CONTAINED_AS_AUDIT_ONLY_LABEL_FIX_REQUIRED_NO_PROMOTION`.

Materialized by:
`scripts/sqlite_human_q24_external_candidate_containment_v1.py`.

Result:

- Existing imported external candidate run: `1`.
- Candidate book rows: `70`.
- Candidate contig rows: `6`.
- Candidate-local rows using `PROMOTE...` wording: `70`.
- Completion audit run checked: `10`.
- Canonical promoted gloss count: `0`.
- Canonical contamination detected: `0`.
- Label-fix required: `1`.

Interpretation:
The German/MHG candidate was already present locally as benchmark material, but
its local table labels used unsafe `PROMOTE...` wording. Q24 confirms this did
not contaminate the canonical completion state, while requiring future reads to
avoid those labels.

## Q25 External Candidate Safe Audit Projection

Latest SQLite run:
`Q25_EXTERNAL_GERMAN_CANDIDATE_SAFE_AUDIT_PROJECTION_READY_NO_PROMOTION`.

Materialized by:
`scripts/sqlite_human_q25_external_candidate_audit_safe_projection_v1.py`.

Result:

- Projected safe book rows: `70`.
- Projected safe contig rows: `6`.
- Unsafe source `PROMOTE...` labels contained: `70`.
- Safe `AUDIT_ONLY` labels materialized: `76`.
- Canonical promotion allowed: `0`.

Safe tables for future use:

- `human_q25_external_candidate_audit_safe_projection_v1_books`
- `human_q25_external_candidate_audit_safe_projection_v1_contigs`

Interpretation:
Future experiments should read the external German/MHG candidate through Q25,
not directly through `canonical_candidate_books`. This keeps the candidate useful
as an adversarial benchmark while preventing accidental promotion of its prose.

## Q26 Mathemagic Transcript Bridge Import

Latest SQLite run:
`Q26_MATHEMAGIC_TRANSCRIPT_BRIDGE_IMPORTED_OPERATOR_ONLY_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q26_mathemagic_transcript_bridge_import_v1.py`.

Sources used:

- `https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts`
- `https://tibia.fandom.com/wiki/A_Prisoner/Transcripts`
- `https://tibia.fandom.com/wiki/The_Paradox_Tower_Quest/Spoiler`
- `https://www.tibiawiki.com.br/wiki/Wyrdin`

Result:

- Transcript items imported: `5`.
- Bridge edges imported: `4`.
- Direct Bonelord -> Mathemagic method link: `1`.
- Minotaur/Mintwallin bridge source count: `1`.
- Mathemagic operator outputs attested: `4` (`1`, `13`, `49`, `94`).
- Direct plaintext gloss count: `0`.
- Canonical promotion allowed: `0`.

Imported bridges:

| Bridge | Status | Use |
| --- | --- | --- |
| `awb-language-to-operator-set` | `LIVE_OPERATOR_BRIDGE` | Wrinkled Bonelord justifies testing mathemagic as operator machinery |
| `awb-minotaur-to-prisoner` | `LIVE_CONTEXT_BRIDGE` | minotaur mages -> Mintwallin/A Prisoner as plausible bridge |
| `riddler-to-prisoner-quest-gate` | `QUEST_GATE_CONFIRMED` | Paradox Tower binds Riddler's `1+1` gate to A Prisoner's number |
| `wyrdin-madman-to-prisoner` | `CONTEXT_ONLY_BRIDGE` | Wyrdin gives source-backed "madman" context, not translation |

Supported reading:
Mathemagica is now transcript-backed as an operator/selector route. The four
numbers `1/13/49/94` should be tested only where they improve held-out
structure, route ranking, or contradiction reduction.

Blocked stronger reading:
No transcript says Mathemagica is a dictionary. No transcript translates a
Hellgate book sentence. No Q26 item promotes plaintext.

## Q27 Mathemagic Operator Queue Reconcile

Latest SQLite run:
`Q27_MATHEMAGIC_OPERATOR_QUEUE_RECONCILED_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q27_mathemagic_operator_queue_reconcile_v1.py`.

Source runs used:

- Q26 transcript bridge run: `1`.
- Mathemagic operational decision run: `1`.

Result:

- Transcript-backed operators reconciled: `4`.
- Live local operators: `1`.
- Weak audit selectors: `1`.
- Dead/blocked operators: `1`.
- Untested context-only operators: `1`.
- Plaintext allowed: `0`.
- Canonical promotion allowed: `0`.

Operator queue:

| Operator | Status | Allowed scope |
| --- | --- | --- |
| `1` | `CONTEXT_ONLY_UNTESTED_AS_SELECTOR` | world/name/formula context; never universal plaintext |
| `13` | `LIVE_LOCAL_OPERATOR_ONLY` | C86/C68 local delta and secondary audit selector |
| `49` | `DEAD_FOR_GENERAL_SELECTOR_PROMOTION_AUDIT_ONLY` | narrow audit note only; no general selector |
| `94` | `WEAK_AUDIT_SELECTOR_ONLY` | `94->24` audit selector pending independent Book24 structure |

Interpretation:
Q27 converts Mathemagica from a broad inspiration into a small controlled queue.
The only live mechanical operator is `13`, and even that is local. This prevents
the exact transcript evidence from reopening previously failed numerology while
preserving a source-backed route for future held-out tests.

## Q28 External Candidate Contig Gate Benchmark

Latest SQLite run:
`Q28_EXTERNAL_GERMAN_CANDIDATE_STRUCTURAL_AUDIT_ONLY_SEMANTIC_GATE_FAILED`.

Materialized by:
`scripts/sqlite_human_q28_external_candidate_contig_gate_benchmark_v1.py`.

Source runs used:

- Q25 safe candidate projection run: `1`.
- Q23 external candidate triage run: `2`.
- Q24 containment run: `1`.
- Completion audit run: `12`.

Result:

- Candidate book rows: `70`.
- Candidate contig rows: `6`.
- Candidate contigs matching local exact `contig_max_overlap`: `6/6`.
- Average candidate coverage: `92.371%`.
- Candidate books with coverage >= `95%`: `38`.
- Candidate books with coverage = `100%`: `5`.
- Candidate books with coverage < `85%`: `10`.
- Semantic in-game anchor passes: `0`.
- External phrase bridge passes: `0`.
- Canonical promoted glosses: `0`.
- Structural audit use allowed: `1`.
- Semantic translation use allowed: `0`.

Supported reading:
The German/MHG candidate can be used as adversarial structural material. Its
six imported contig orders agree with local exact contig reconstruction, so it
may generate continuity questions, contradiction checks, or source-search
targets.

Blocked stronger reading:
The candidate still cannot be used as accepted human translation. It fails the
semantic anchor gate and the external phrase bridge gate, and the project
completion audit still reports zero promoted glosses.

Interpretation:
Q28 separates the only useful part of the external candidate from the unsafe
part. The contig/continuity shape is worth exploiting as a benchmark; the German
prose and English glosses remain quarantined.

## Q29 External Candidate Lore Term Search Audit

Latest SQLite run:
`Q29_EXTERNAL_CANDIDATE_LORE_TERMS_UNANCHORED_KEEP_AUDIT_ONLY`.

Materialized by:
`scripts/sqlite_human_q29_external_candidate_lore_term_search_audit_v1.py`.

Source runs used:

- Q28 external candidate contig gate benchmark run: `1`.

Terms checked:

| Term | Candidate claim | Status |
| --- | --- | --- |
| `SALZBERG` | King/Speaker-King Salzberg | `CANDIDATE_TERM_UNANCHORED_IN_CURRENT_SOURCE_SEARCH` |
| `ORANGENSTRASSE` | Orange Street / Orangenstrasse | `CANDIDATE_TERM_UNANCHORED_IN_CURRENT_SOURCE_SEARCH` |
| `WEICHSTEIN` | Soft Stone / Weichstein | `CANDIDATE_TERM_UNANCHORED_IN_CURRENT_SOURCE_SEARCH` |
| `GOTTDIENER` | God's Servant / Gottdiener | `CANDIDATE_TERM_UNANCHORED_IN_CURRENT_SOURCE_SEARCH` |
| `SCHARDT` | Schardt place/name | `CANDIDATE_TERM_UNANCHORED_IN_CURRENT_SOURCE_SEARCH` |
| `THENAEUT` | Unsolved proper noun in candidate | `CANDIDATE_TERM_UNANCHORED_IN_CURRENT_SOURCE_SEARCH` |
| `LGTNELGZ` | Unsolved proper noun in candidate | `CANDIDATE_TERM_UNANCHORED_IN_CURRENT_SOURCE_SEARCH` |

Result:

- Candidate lore terms checked: `7`.
- Local source-table hits: `0`.
- Broad web relevant Tibia lore hits: `0`.
- Source anchor passes: `0`.
- Candidate lore bridge passes: `0`.
- Canonical promotion allowed: `0`.

Supported reading:
The German/MHG candidate remains useful only as a structural/adversarial object.
Its strongest names and lore-like nouns do not currently anchor to the local
source corpus, Q26 transcript bridge, or broad Tibia web-search observations.

Blocked stronger reading:
No checked candidate proper noun can be used as an in-game anchor. Any future
reopening must provide an exact book/NPC/quest source, or a clear cognate with
traceable provenance, before the term can leave `AUDIT_ONLY`.

## Q30 Great Calculator Compiled-Corpus Spine Map

Latest SQLite run:
`Q30_GREAT_CALCULATOR_COMPILED_CORPUS_MODEL_READY_AS_HUMAN_SHADOW_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q30_great_calculator_compiled_corpus_spine_map_v1.py`.

Source runs used:

- Q22 cross-quest route prioritization run: `1`.
- Q28 external candidate contig benchmark run: `1`.
- Q29 external candidate lore-term audit run: `1`.
- Human translation atlas v6 run: `1`.
- Contig max-overlap run: `1`.
- Contig structural narrative run: `1`.
- Completion audit v5 run: `13`.

Result:

- Book-level human shadow rows classified: `70/70`.
- Contig-supported books: `14`.
- Contig source-search packets: `6`.
- Compiled-corpus strata: `9`.
- External candidate structural use allowed: `1`.
- External candidate semantic use allowed: `0`.
- Canonical promoted glosses: `0`.
- Canonical promotion allowed: `0`.

Compiled-corpus strata:

| Stratum | Books |
| --- | ---: |
| `PAYLOAD_CONTEXT_CORRIDOR` | `24` |
| `FORMULA_HANDOFF_PACKET` | `11` |
| `BRANCH_PHASE_CONTROL_PACKET` | `10` |
| `SLOT_CLASSIFIER_PACKET` | `10` |
| `PAIR_TEMPLATE_ALIGNMENT_PACKET` | `5` |
| `FAMILY_SPINE_PACKET` | `4` |
| `RESIDUAL_COMPILED_FRAGMENT_PACKET` | `3` |
| `COMPOSITE_SLOT_FORMULA_PACKET` | `2` |
| `DISPLAY_BOUNDARY_AUDIT_PACKET` | `1` |

Contig packets now usable as source-search spines:

| Contig | Books | Human structural route |
| --- | --- | --- |
| `0` | `51->53` | NAESE slot window plus R02 bridge as two-book slot/bridge pair |
| `1` | `58->35->67->2` | formula/display head -> C86/VNCTIIN payload/context -> NAESE slot |
| `2` | `29->65` | VINVIN branch with R20/VAETRFEVAST context and longer R20/R02 connector |
| `3` | `52->62` | C86/VINVIN branch payload pair, with Book `62` as stronger endpoint |
| `4` | `13->38` | O23/FNAAST endpoint window with scoped O23 context |
| `5` | `47->40` | BENNA/IAVNALLBEE template into BENNA formula bridge |

Supported reading:
The Great Calculator anchor can now be operationalized as a compiled-corpus
model. The Hellgate books should be translated first as functional packets,
spines, branches, handoffs, and source-search questions rather than as one
continuous prose document.

Blocked stronger reading:
The Great Calculator book still does not translate any 469 sentence. Q30
therefore promotes a human-shadow working model only, not plaintext, not German
candidate semantics, and not canonical glossary entries.

## Q31 Bonelord Tome Provenance Bridge

Latest SQLite run:
`Q31_BONELORD_TOME_PROVENANCE_STRENGTHENS_486486_QUESTION_ORACLE_FRAME_NO_COMPONENT_GLOSS`.

Materialized by:
`scripts/sqlite_human_q31_bonelord_tome_provenance_bridge_v1.py`.

Source runs used:

- Q12 Bonelord Tome 3478/486486 anchor probe run: latest.
- Q30 Great Calculator compiled-corpus spine map run: `1`.

Web/source records imported:

| Source | Use | Gate |
| --- | --- | --- |
| `https://tibia.fandom.com/wiki/Bonelord_Tome` | final item page co-locating `3478...` and `486486...` sounds | secondary item page |
| `https://www.tibiawiki.com.br/wiki/Bonelord_Tome` | independent item-page corroboration and official fansite-item note | secondary item page |
| `https://meta.tibiaqa.com/208/fansite-item-design-contest` | original Bonelord Tome design provenance with `486486` question/answer motif | design provenance |
| `https://www.tibiasecrets.com/article166` | calculation/Great Calculator research context | community research context |

Result:

- Source records: `4`.
- Final item-page sources: `2`.
- Design provenance sources: `1`.
- Exact `3478...` final-item sources: `2`.
- `486486` question/oracle-frame sources: `3`.
- Client or official data extraction sources: `0`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Supported reading:
Bonelord Tome strengthens a phrase-level frame: `486486` can be treated as a
question/answer/attention anchor in Tome contexts. The final item pages
co-locate the Knightmare-style `3478...` phrase with a `486486` answers line,
and the original item concept already framed `486486` as the place to ask.

Blocked stronger reading:
This does not translate `486486`, `3478`, or any component of the Tome phrase.
Because the sources are secondary item pages plus design provenance, not direct
client extraction, the route remains phrase-level and `NO_COMPONENT_GLOSS`.

## Q32 Contig 1 Source Bridge Probe

Latest SQLite run:
`Q32_CONTIG1_SOURCE_BRIDGE_SUPPORTS_FORMULA_CONTEXT_SLOT_HUMAN_SHADOW_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q32_contig1_source_bridge_probe_v1.py`.

Source runs used:

- Q30 Great Calculator compiled-corpus spine map run: `1`.
- Q31 Bonelord Tome provenance bridge run: `1`.
- Completion audit v5 run: latest at execution.

Target:

| Contig | Books | Q30 structure |
| --- | --- | --- |
| `1` | `58->35->67->2` | formula/display head -> C86/VNCTIIN payload/context -> NAESE slot |

Web/source bridges imported:

| Bridge | Source | Supported phase | Strength |
| --- | --- | --- | --- |
| `BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS` | `https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29` | formula/display and mathemagical frame | `STRONG_CONTEXT_BRIDGE` |
| `BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY` | `https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29` | formula handoff and ritual/operation register | `MODERATE_CONTEXT_BRIDGE` |
| `THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD` | `https://www.tibiawiki.com.br/wiki/The_Bonelord_Threat_I_%28Book%29` | command/control context | `MODERATE_CONTEXT_BRIDGE` |
| `THREAT_II_RESEARCH_EXPERIMENTS` | `https://tibia.fandom.com/wiki/The_Bonelord_Threat_II_%28Book%29` | research/experiment handoff | `MODERATE_CONTEXT_BRIDGE` |
| `THREAT_III_MIND_BODY_SOUL_EXPERIMENTS` | `https://www.tibiawiki.com.br/wiki/The_Bonelord_Threat_III_%28Book%29` | experimental transformation register | `MODERATE_CONTEXT_BRIDGE` |

Result:

- Source bridges: `5`.
- Strong context bridges: `1`.
- Moderate context bridges: `4`.
- Exact sequence bridge count: `0`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Human functional version:

> A source-backed functional reading of contig `58->35->67->2`: a
> mathemagical formula/display head hands off into a Bonelord research/control
> context, then narrows into a slot/payload classifier. This is a
> ritual/experimental packet, not a sentence-level translation.

Supported reading:
This is the first contig-level human version that is both source-anchored and
mechanically tied to Q30. It gives the user a plausible human reading route
without pretending to know the underlying words.

Blocked stronger reading:
No Q32 source gives exact sequence meaning. Therefore `BENNA`, `C86`, `C68`,
`VNCTIIN`, `NAESE`, `LTAST`, `TTNVVN`, and the four books remain
`NO_COMPONENT_GLOSS`.

## Q33 Branch Formula Source Bridge Probe

Latest SQLite run:
`Q33_BRANCH_FORMULA_SOURCE_BRIDGE_SUPPORTS_CONTIG2_3_HUMAN_SHADOW_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q33_branch_formula_source_bridge_probe_v1.py`.

Source runs used:

- Q30 Great Calculator compiled-corpus spine map run: `1`.
- Q32 Contig 1 source bridge probe run: `1`.
- Completion audit v5 run: latest at execution.

Targets:

| Contig | Books | Q30 structure | Human functional version |
| --- | --- | --- | --- |
| `2` | `29->65` | VINVIN branch with R20/VAETRFEVAST context; second book adds long R20/R02 connector | A branch/phase packet where a VINVIN-covered R20 context extends into a longer R20/R02 phase connector. It behaves like a formula variant being carried to a phase endpoint, not like a standalone sentence. |
| `3` | `52->62` | C86/VINVIN branch payload pair; Book `62` is the stronger variant-chain endpoint | A branch payload pair where two C86-opened VINVIN/R20 lines form a controlled variant chain, with the second book acting as the stronger endpoint. It reads as a selector/branch endpoint packet under the Bonelord complex-formula model, not as lexical prose. |

Web/source bridges imported:

| Bridge | Source | Use | Strength |
| --- | --- | --- | --- |
| `AWB_COMPLEX_FORMULA_SUBJECTIVE_VIEWER` | `https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts` | branch, variant-chain, endpoint behavior | `STRONG_FORMULA_VARIANT_BRIDGE` |
| `AWB_LANGUAGE_MATHEMAGIC_PROCESSING` | `https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts` | operator/selector processing rather than direct prose | `STRONG_METHOD_BRIDGE` |
| `AWB_NUMBERS_LIFE_DEATH` | `https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts` | numeric branch control with life/death research context | `MODERATE_CONTEXT_BRIDGE` |
| `BEWARE_BLINKING_CODE_VARIABLE_UNIT` | `https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29` | variable unit size and branch ambiguity | `MODERATE_UNIT_BRIDGE` |
| `THREAT_II_RESEARCH_EXPERIMENTS` | `https://tibia.fandom.com/wiki/The_Bonelord_Threat_II_%28Book%29` | variant-chain as experimental/control sequence | `MODERATE_CONTEXT_BRIDGE` |

Result:

- Target contigs: `2`.
- Target books: `4`.
- Source bridges: `5`.
- Strong bridges: `2`.
- Moderate bridges: `3`.
- Human functional versions: `2`.
- Exact sequence bridge count: `0`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Supported reading:
Q33 gives two more contig-level human versions. The Wrinkled Bonelord's own
language lines now support reading branch/variant packets as formula behavior
that can change by viewer/selector, rather than forcing them into plain prose.

Blocked stronger reading:
No Q33 source says these contigs encode the race name. `VINVIN`, `R20`, `C86`,
`O23`, and the book texts are still branch/endpoint evidence only.

## Q34 Remaining Contig Functional Versions

Latest SQLite run:
`Q34_ALL_Q30_CONTIGS_HAVE_SOURCE_ANCHORED_HUMAN_FUNCTIONAL_VERSIONS_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q34_remaining_contig_functional_versions_v1.py`.

Source runs used:

- Q30 Great Calculator compiled-corpus spine map run: `1`.
- Q32 Contig 1 source bridge probe run: `1`.
- Q33 Branch formula source bridge probe run: `1`.
- Completion audit v5 run: latest at execution.

Targets:

| Contig | Books | Human functional version | Confidence |
| --- | --- | --- | --- |
| `0` | `51->53` | A two-book slot/bridge pair: both books repeat a NAESE/C68 slot window with an R02 phase bridge. It behaves like a repeated classifier or response-slot template, not a translated sentence. | `MODERATE_STRONG_FUNCTIONAL_PAIR` |
| `4` | `13->38` | A scoped endpoint packet: Book `13` enters an O23/FNAAST endpoint branch and Book `38` preserves the direct endpoint payload. It is a terminal/closure window that must stay quarantined from global O23 meaning. | `WEAK_MODERATE_SCOPED_ENDPOINT` |
| `5` | `47->40` | A formula-template handoff pair: Book `47` provides BENNA/IAVNALLBEE template context and Book `40` carries that into a BENNA formula bridge with LTAST boundary. It is a ritual/mathematical formula handoff packet, not prose. | `MODERATE_FORMULA_TEMPLATE_PAIR` |

Result:

- Target contigs: `3`.
- Target books: `6`.
- Source bridges: `5`.
- Human functional versions: `3`.
- Weak/scoped endpoint versions: `1`.
- Exact sequence bridge count: `0`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.
- All Q30 exact contigs have a human version: `1`.

Supported reading:
Together, Q32, Q33, and Q34 give all six exact Q30 contigs a source-anchored
human functional version. This is the first clean contour of a human translation
layer for the most structurally reliable book groups.

Blocked stronger reading:
Q34 still does not assign words. Contig `4` remains the weakest because
O23/FNAAST has endpoint structure but no exact external meaning.

## Q35 Contig Human Shadow Atlas

Latest SQLite run:
`Q35_CONTIG_HUMAN_SHADOW_ATLAS_READY_6_OF_6_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q35_contig_shadow_atlas_v1.py`.

Source runs used:

- Q30 Great Calculator compiled-corpus spine map run: `1`.
- Q32 Contig 1 source bridge probe run: `1`.
- Q33 Branch formula source bridge probe run: `1`.
- Q34 Remaining contig functional versions run: `1`.
- Completion audit v5 run: latest at execution.

Result:

- Exact Q30 contigs: `6`.
- Atlas contigs with human functional version: `6`.
- Source-anchored contigs: `6`.
- Weak/scoped contigs: `1`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Operational atlas:

| Contig | Books | Human shadow use |
| --- | --- | --- |
| `0` | `51->53` | repeated slot/bridge pair |
| `1` | `58->35->67->2` | formula/display -> research/control context -> slot/payload classifier |
| `2` | `29->65` | branch/phase packet carried to endpoint |
| `3` | `52->62` | controlled branch payload pair with stronger endpoint |
| `4` | `13->38` | scoped endpoint packet, weak/quarantined |
| `5` | `47->40` | formula-template handoff pair |

Supported reading:
The strongest structural material now has a single operational human shadow
atlas. This is the first reusable translation surface where the project can
produce plausible human versions while keeping strict no-gloss boundaries.

Blocked stronger reading:
Q35 is not a solved plaintext atlas. It is a source-search and human-shadow
translation queue. It must not be used to promote component meanings unless a
future exact source or contrastive test supplies that missing evidence.

## Q36 Book/Contig Shadow Integration

Latest SQLite run:
`Q36_BOOK_CONTIG_SHADOW_INTEGRATION_READY_NEXT_FRONTIER_SELECTED_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q36_book_contig_shadow_integration_v1.py`.

Source runs used:

- Q30 Great Calculator compiled-corpus spine map run: `1`.
- Q35 Contig human shadow atlas run: `1`.
- Completion audit v5 run: latest at execution.

Result:

- Book rows integrated: `70`.
- Books with exact contig shadow context: `14`.
- Books without exact contig shadow context: `56`.
- High-priority non-contig books: `47`.
- Weak/scoped contig books: `2`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Supported reading:
The contig atlas is now usable at book level. For the 14 books inside exact
contigs, the human version should be inherited from the contig packet. The
remaining 56 books should be handled by family/pair/source-bridge probes rather
than isolated sentence drafts.

Blocked stronger reading:
The 14 covered books are not translated canonically; they only have a stronger
human-shadow context. The 56 non-contig books remain the next frontier.

## Q37 Non-Contig Frontier Selection

Latest SQLite run:
`Q37_NONCONTIG_FRONTIER_SELECTION_READY_6_FAMILIES_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q37_noncontig_frontier_selection_v1.py`.

Source runs used:

- Q36 Book/contig shadow integration run: `1`.
- Completion audit v5 run: latest at execution.

Result:

- Selected frontier families: `6`.
- Selected non-contig books: `20`.
- Contig-shadow books kept separate: `14`.
- Total non-contig books remaining: `56`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Selected priorities:

| Priority | Frontier | Books | Next probe |
| ---: | --- | --- | --- |
| `1` | `BOOK30_FAMILY_SPINE_PACKET` | `12/21/26/30` | Consolidate existing Book30-family shadow material into one non-contig family atlas entry |
| `2` | `VNCTIIN_TIINNEF_PHASE_TRIO` | `19/31/57` | Compare VNCTIIN/TIINNEF phase context with Book7 controls, without 3478 gloss |
| `3` | `C86_VINVIN_BRANCH_TRIO` | `3/17/44` | Test whether Q33 branch/variant bridge generalizes outside exact contigs |
| `4` | `BTII_NSBVN_ATFNAAST_DISPLAY_TRIO` | `11/32/43` | Stabilize repeated display/formula drift as display-only |
| `5` | `NAESE_C68_SLOT_VARIANT_TRIO` | `22/28/48` | Extend slot classifier model through controlled variants |
| `6` | `CHAYENNE_REGISTER_FRAME_SET` | `8/37/63/66` | Unify external-register frame behavior while keeping Chayenne quarantined |

Supported reading:
The next work should not attack all 56 non-contig books at once. It should
advance through small recurrent families where the source bridge and internal
contrast are strongest.

Blocked stronger reading:
Q37 is a selection queue, not a translation. It explicitly blocks standalone
sentence drafts from non-contig books.

## Q38 Book30 Family Non-Contig Atlas

Latest SQLite run:
`Q38_BOOK30_FAMILY_NONCONTIG_ATLAS_READY_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q38_book30_family_noncontig_atlas_v1.py`.

Source runs used:

- Q37 Non-contig frontier selection run: `1`.
- Existing Book30 family shadow probe run: latest.
- Completion audit v5 run: latest at execution.

Result:

- Target books: `4` (`12/21/26/30`).
- Source bridges: `3`.
- Components shared by all books: `1`.
- Shared spine: `VNSBLFSINNAI`.
- Partial components: `9`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Human family version:

> Book30-family human shadow: a compiled formula-spine family built around
> shared `VNSBLFSINNAI`. Books `12` and `21` are long-tail witnesses with
> `TAESESTIEN`, Book `26` is a branch-prefixed long-tail witness without
> `TAESESTIEN`, and Book `30` is a `TAESESTIEN` alternate-tail witness. This is
> a family/spine reading, not prose.

Book roles:

| Book | Role |
| --- | --- |
| `12` | compact long-tail spine witness with `TAESESTIEN` |
| `21` | long-tail spine witness with bridge/tail extension |
| `26` | branch-prefixed long-tail witness without `TAESESTIEN` |
| `30` | `TAESESTIEN` alternate-tail family witness |

Supported reading:
This is the first non-contig family promoted into the human-shadow atlas layer.
It extends the Q35 contig atlas method to a recurrent family that has no exact
contig edge but has a strict shared-spine invariant.

Blocked stronger reading:
No component in the Book30 family has lexical meaning. Even `VNSBLFSINNAI` is
only a family spine, not a translated word.

## Q39 VNCTIIN/TIINNEF Phase Trio Atlas

Latest SQLite run:
`Q39_VNCTIIN_TIINNEF_PHASE_TRIO_ATLAS_READY_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q39_vnctiin_tiinnef_phase_trio_atlas_v1.py`.

Source runs used:

- Q37 Non-contig frontier selection run: `1`.
- Existing Book7 phase shadow probe run: latest.
- Q8 Book6/7 3478 phase-path transition probe run: latest.
- Completion audit v5 run: latest at execution.

Target:

| Family | Books | Controls |
| --- | --- | --- |
| `VNCTIIN_TIINNEF_PHASE_TRIO` | `19/31/57` | Book `6` continuity-only control; Book `7` continuity-to-phase bridge |

Source bridges:

| Bridge | Source | Use |
| --- | --- | --- |
| `AWB_LANGUAGE_MATHEMAGIC_PROCESSING` | `https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts` | mathemagic/processing frame |
| `AWB_COMPLEX_FORMULA_SUBJECTIVE_VIEWER` | `https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts` | formula/viewer/selector behavior |
| `BEWARE_VARIABLE_BLINK_UNIT` | `https://tibia.fandom.com/wiki/Beware_of_the_Bonelords_%28Book%29` | variable unit size; language plus mathematics |
| `BOOK7_PHASE_SHADOW_BRIDGE` | local SQLite probe | Book7 as local bridge/control only |

Result:

- Target books: `3`.
- Control books: `2`.
- Source bridges: `4`.
- Phase-context controls: `3`.
- Bridge controls: `1`.
- Continuity-only controls: `1`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Human family version:

> VNCTIIN/TIINNEF phase-context trio: Books `19`, `31`, and `57` carry
> `TIINNEF` inside a `VNCTIIN/C68` context frame. Compared with Book `6` as
> continuity-only control and Book `7` as continuity-to-phase bridge, the trio
> behaves as held-out phase-context evidence. It should be read as
> phase/context machinery under mathemagic, not as plaintext.

Supported reading:
Q39 turns Q37 priority `2` into a usable non-contig family atlas entry. It
strengthens the Book7 phase bridge by adding three held-out context witnesses
without using `3478` as a semantic key.

Blocked stronger reading:
No Q39 source translates `VNCTIIN`, `TIINNEF`, `C68`, `NEIAAETTA`, `3478`, or
any of Books `6/7/19/31/57`.

## Q40 C86/VINVIN Branch Trio Atlas

Latest SQLite run:
`Q40_C86_VINVIN_BRANCH_TRIO_ATLAS_READY_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q40_c86_vinvin_branch_trio_atlas_v1.py`.

Source runs used:

- Q37 Non-contig frontier selection run: `1`.
- Q33 Branch formula source bridge probe run: `1`.
- Completion audit v5 run: latest at execution.

Target:

| Family | Books | Exact-contig analogues |
| --- | --- | --- |
| `C86_VINVIN_BRANCH_TRIO` | `3/17/44` | Q33 contigs `29->65` and `52->62` |

Result:

- Target books: `3`.
- Exact-contig analogues: `2`.
- Source bridges: `6`.
- Branch-context books: `3`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Human family version:

> C86/VINVIN non-contig branch trio: Books `3`, `17`, and `44` repeat a
> C86-opened VINVIN/VTLR/R20 branch shape outside the exact contigs. By analogy
> with Q33's exact branch packets, this trio should be read as non-contig
> selector/branch payload evidence under the complex-formula model, not as
> lexical prose.

Supported reading:
Q40 extends a proven exact-contig branch model to a non-contig family. This
helps separate C86/VINVIN branch payloads from VNCTIIN/TIINNEF phase-context
books before any future prose attempt.

Blocked stronger reading:
No Q40 evidence translates `C86`, `VINVIN`, `VTLR`, `R20`, `O23`, or any target
book.

## Q41 Display Drift Trio Atlas

Latest SQLite run:
`Q41_DISPLAY_DRIFT_TRIO_ATLAS_READY_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q41_display_drift_trio_atlas_v1.py`.

Source runs used:

- Q37 Non-contig frontier selection run: `1`.
- Existing BTII display-drift gate run: latest.
- Q10 Book32/36 display-payload independence audit run: latest.
- Completion audit v5 run: latest at execution.

Target:

| Family | Books | Role |
| --- | --- | --- |
| `BTII_NSBVN_ATFNAAST_DISPLAY_TRIO` | `11/32/43` | display/formula drift control, not payload |

Result:

- Target books: `3`.
- Source bridges: `4`.
- Display-drift rows: `3`.
- Residual-blocked context books: `2` (`11/32`).
- Display-only books: `1` (`43`).
- Lexical gloss allowed: `0`.
- Family-wide promotion allowed: `0`.
- Canonical promotion allowed: `0`.

Human family version:

> BTII/NSBVN/ATFNAAST display-drift trio: Books `11`, `32`, and `43` repeat a
> book-scoped display/formula drift marker. Books `11` and `32` still carry
> residual-blocked context; Book `43` is display-only. The trio should stabilize
> the display layer and prevent false prose, not translate payload.

Supported reading:
Q41 gives the project an explicit negative-control family. These books should
be used to reject over-readable formula/display outputs before they contaminate
the human translation layer.

Blocked stronger reading:
No Q41 evidence translates `BTII`, `NSBVN`, `ATFNAAST`, or any target book.

## Q42 Non-Contig Frontier Coverage Audit

Latest SQLite run:
`Q42_NONCONTIG_FRONTIER_COVERAGE_AUDIT_4_OF_6_READY_2_PENDING_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q42_noncontig_frontier_coverage_audit_v1.py`.

Source runs used:

- Q37 Non-contig frontier selection run: `1`.
- Q38/Q39/Q40/Q41 atlas runs.
- Completion audit v5 run: latest at execution.

Result:

- Q37 frontier families: `6`.
- Atlas-ready frontier families: `4`.
- Pending frontier families: `2`.
- Q37 selected non-contig books: `20`.
- Atlas-ready selected books: `13`.
- Pending selected books: `7`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Coverage:

| Frontier | Books | Status |
| --- | --- | --- |
| `BOOK30_FAMILY_SPINE_PACKET` | `12/21/26/30` | `ATLAS_READY_NO_GLOSS` |
| `VNCTIIN_TIINNEF_PHASE_TRIO` | `19/31/57` | `ATLAS_READY_NO_GLOSS` |
| `C86_VINVIN_BRANCH_TRIO` | `3/17/44` | `ATLAS_READY_NO_GLOSS` |
| `BTII_NSBVN_ATFNAAST_DISPLAY_TRIO` | `11/32/43` | `ATLAS_READY_NO_GLOSS` |
| `NAESE_C68_SLOT_VARIANT_TRIO` | `22/28/48` | `PENDING_FRONTIER` |
| `CHAYENNE_REGISTER_FRAME_SET` | `8/37/63/66` | `PENDING_FRONTIER` |

Supported reading:
The non-contig frontier is now narrowed to two remaining families. The next
best move is `NAESE_C68_SLOT_VARIANT_TRIO`, because it extends slot-classifier
behavior already present in contigs and Q30.

Blocked stronger reading:
Q42 is only a coverage audit. It does not promote meanings or mark the
translation solved.

## Q43 NAESE/C68 Slot Variant Trio Atlas

Latest SQLite run:
`Q43_NAESE_C68_SLOT_VARIANT_TRIO_ATLAS_READY_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q43_naese_c68_slot_variant_trio_atlas_v1.py`.

Source runs used:

- Q37 Non-contig frontier selection run: `1`.
- Q35 Contig human shadow atlas run: `1`.
- Existing `c68_fatct_slot_items` run: latest.
- Existing `naese_slot_core_v1_items` run: latest.
- Completion audit v5 run: latest at execution.

Target:

| Family | Books | Exact-contig analogues |
| --- | --- | --- |
| `NAESE_C68_SLOT_VARIANT_TRIO` | `22/28/48` | Q35 contigs `0` and `1` |

Result:

- Target books: `3`.
- Source bridges: `5`.
- Exact-contig analogues: `2`.
- C68 canonical surface supports: `2`.
- NAESE ordered-core books: `1`.
- Variant windows: `2`.
- Edge support count: `0`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Human family version:

> NAESE/C68 slot-variant trio: Book `22` is the ordered canonical slot witness,
> while Books `28` and `48` are controlled variant windows around the same
> `FATC68T` slot frame. The trio should be read as classifier/slot machinery
> under mathemagic and variable-unit language, not as a phrase translation.

Supported reading:
Q43 turns the fifth Q37 frontier into a usable atlas entry. It keeps the useful
slot/classifier behavior while explicitly preserving the split between ordered
core and variants.

Blocked stronger reading:
No Q43 evidence translates `NAESE`, `C68`, `FATCT`, `IVIFAST`, "slot", or any
target book.

## Q44 Chayenne Register-Frame Atlas

Latest SQLite run:
`Q44_CHAYENNE_REGISTER_FRAME_ATLAS_READY_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q44_chayenne_register_frame_atlas_v1.py`.

Source runs used:

- Q37 Non-contig frontier selection run: `1`.
- Q36 Book-contig integration run: `1`.
- Chayenne shape-shadow probe run: `1`.
- Chayenne branch-shadow run: `1`.
- Q2 Chayenne explicit gloss audit run: `1`.
- Package 8 Chayenne branch falsification run: `1`.
- In-game anchor corpus run: latest.
- Completion audit v5 run: latest at execution.

Target:

| Family | Books | Shared block | Branch classes |
| --- | --- | --- | --- |
| `CHAYENNE_REGISTER_FRAME_SET` | `8/37/63/66` | `AEFIEIEFIIVFAEATVAT` | `VNCTIIN`, `LTAST->VNCTIIN`, residual audit, `BENNA/LTAST` |

Result:

- Target books: `4`.
- Source bridges: `6`.
- Branch classes: `4`.
- Exact external-shape books: `4`.
- Strong branch books: `3`.
- Audit-held branch books: `1`.
- Q2 exact sequence attestations: `4`.
- Q2 explicit gloss count: `0`.
- Package 8 functional labels: `1`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Human family version:

> Chayenne register-frame set: Books `8`, `37`, `63`, and `66` carry the same
> external Chayenne 469 shape frame through distinct internal contexts. Read the
> family as register/context reuse anchored by in-game mathemagic and Great
> Calculator corpus lore, with Book `63` held as an audit/residual witness, not
> as a dictionary or Hellgate prose.

Supported reading:
Q44 converts the last Q37 frontier into an atlas entry by using Chayenne as
source-quarantined external frame evidence. It is useful because the same block
appears across different internal branches; that weakens a single-sentence
translation and strengthens the register/frame interpretation.

Blocked stronger reading:
No Q44 evidence translates Chayenne's reply, the shared block
`AEFIEIEFIIVFAEATVAT`, any component token, Book `63`, or the four target books
as English prose.

## Q45 Non-Contig Frontier Coverage Complete Audit

Latest SQLite run:
`Q45_NONCONTIG_FRONTIER_COVERAGE_COMPLETE_6_OF_6_READY_20_OF_20_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q45_noncontig_frontier_coverage_complete_audit_v1.py`.

Result:

- Q37 frontier families: `6`.
- Atlas-ready frontier families: `6`.
- Pending frontier families: `0`.
- Q37 selected books: `20`.
- Atlas-ready selected books: `20`.
- Pending selected books: `0`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Covered Q37 families:

| Priority | Family | Books | Atlas status |
| --- | --- | --- | --- |
| `1` | `BOOK30_FAMILY_SPINE_PACKET` | `12/21/26/30` | `ATLAS_READY_NO_GLOSS` |
| `2` | `VNCTIIN_TIINNEF_PHASE_TRIO` | `19/31/57` | `ATLAS_READY_NO_GLOSS` |
| `3` | `C86_VINVIN_BRANCH_TRIO` | `3/17/44` | `ATLAS_READY_NO_GLOSS` |
| `4` | `BTII_NSBVN_ATFNAAST_DISPLAY_TRIO` | `11/32/43` | `ATLAS_READY_NO_GLOSS` |
| `5` | `NAESE_C68_SLOT_VARIANT_TRIO` | `22/28/48` | `ATLAS_READY_NO_GLOSS` |
| `6` | `CHAYENNE_REGISTER_FRAME_SET` | `8/37/63/66` | `ATLAS_READY_NO_GLOSS` |

Interpretation:
Q45 closes the first full non-contig frontier batch. We now have controlled
human-shadow comparators for all six selected non-contig families. This is a
better search surface for plausible translation work, but it is not a solved
canonical decode.

Next synthesis pass:
Use the six atlas families as comparators to draft a controlled human reading
layer by book family, then test whether any repeated function can survive a
stricter promotion gate.

## Q46 Family Synthesis Hypothesis Queue

Latest SQLite run:
`Q46_HUMAN_FAMILY_SYNTHESIS_HYPOTHESIS_QUEUE_READY_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q46_family_synthesis_hypothesis_queue_v1.py`.

Result:

- Atlas families synthesized: `6`.
- Hypothesis lanes created: `6`.
- Source-quarantined lanes: `1`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

New hypothesis lanes:

| Priority | Hypothesis | Role | Next probe |
| --- | --- | --- | --- |
| `1` | `H1_COMPILED_FORMULA_SPINE_AS_DOCUMENT_STRUCTURE` | compiled formula-spine witness | Compare `VNSBLFSINNAI` and `TAESESTIEN` tail behavior against non-target high-priority packets |
| `2` | `H2_PHASE_CONTEXT_BEFORE_SLOT_CLASSIFICATION` | phase-context machinery | Join Q39 phase-context books with Q43 `NAESE/C68` slot books through shared `C68/VNCTIIN` neighborhoods |
| `3` | `H3_BRANCH_SELECTOR_PAYLOAD_CHAIN` | selector/branch payload machinery | Contrast `C86/VINVIN` books against Chayenne and `NAESE` families where `C86/C68` sits near frame boundaries |
| `4` | `H4_DISPLAY_DRIFT_MASK_BEFORE_PROSE` | display/formula drift mask | Apply display-only masks to residual books, then re-rank remaining human-readable surfaces |
| `5` | `H5_SLOT_CLASSIFIER_VARIANT_CONTROL` | slot/classifier variant machinery | Use Book `22` as ordered-core control and Books `28/48` as variant windows against `C68`-near residuals |
| `6` | `H6_EXTERNAL_REGISTER_FRAME_HOLDOUT` | external register-frame holdout | Use Chayenne-frame books as holdouts for branch/register behavior and keep Book `63` as residual audit control |

Immediate next route:
Start with `H2_PHASE_CONTEXT_BEFORE_SLOT_CLASSIFICATION`. It is the best
candidate for a human-readable mechanism because it links two independently
controlled families: phase/context machinery from Q39 and slot/classifier
machinery from Q43. If the join improves held-out placement without creating
component gloss, it becomes a stronger candidate for a later promotion package.

## Q47 Phase-Slot C68 Window Join

Latest SQLite run:
`Q47_PHASE_SLOT_C68_WINDOW_JOIN_READY_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q47_phase_slot_c68_window_join_v1.py`.

Question:
Does `C68` separate Q39 phase-context books from Q43 slot/classifier books by
local window?

Result:

- Phase-context books tested: `3` (`19/31/57`).
- Slot/classifier books tested: `3` (`22/28/48`).
- `C68` observations: `9`.
- Phase `TIIN...` windows: `6`.
- Slot `TIVV...` windows: `3`.
- Ambiguous windows: `0`.
- Group predictions correct: `6/6`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Book-level result:

| Book | Expected role | `C68` count | Dominant window | Prediction |
| --- | --- | ---: | --- | --- |
| `19` | phase/context | `1` | `PHASE_TIIN_WINDOW` | `GROUP_PREDICTED` |
| `31` | phase/context | `2` | `PHASE_TIIN_WINDOW` | `GROUP_PREDICTED` |
| `57` | phase/context | `3` | `PHASE_TIIN_WINDOW` | `GROUP_PREDICTED` |
| `22` | slot/classifier | `1` | `SLOT_TIVV_WINDOW` | `GROUP_PREDICTED` |
| `28` | slot/classifier | `1` | `SLOT_TIVV_WINDOW` | `GROUP_PREDICTED` |
| `48` | slot/classifier | `1` | `SLOT_TIVV_WINDOW` | `GROUP_PREDICTED` |

Human mechanism:

> C68 phase-slot hinge: in the Q39 phase-context books, `C68` opens
> `TIIN`-style windows; in the Q43 slot/classifier books, `C68` opens
> `TIVV`-style `FATCT/IVIFAST` windows. This supports a human mechanism where
> `C68` marks a transition surface whose right window distinguishes
> phase/context from slot/classifier behavior, without giving `C68` a word
> meaning.

Why this matters:
Q47 is the first post-Q45 synthesis result that converts two independent atlas
families into one testable mechanism. It gives the human route a stronger
grammar-like handle: not "C68 means X", but "the right side of C68 selects a
phase window or a slot window".

## Q48 C68 Held-Out Window Taxonomy

Latest SQLite run:
`Q48_C68_HELDOUT_WINDOW_TAXONOMY_READY_HINGE_EXTENDS_WITH_EXTRA_CLASSES_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q48_c68_heldout_window_taxonomy_v1.py`.

Question:
Does the Q47 `C68` phase-slot hinge survive outside the six discovery books?

Result:

- Total books with `C68`: `23`.
- Total `C68` observations: `30`.
- Q47 discovery observations: `9`.
- Held-out observations: `21`.
- Held-out phase `TIIN...` windows: `10`.
- Held-out slot `TIVV...` windows: `6`.
- Held-out observations matching the Q47 hinge: `16/21`.
- Held-out extra classes: `5/21`.
- Held-out `TAVT` boundary windows: `1`.
- Held-out `E`-exit windows: `2`.
- Held-out terminal windows: `2`.
- Component gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Held-out taxonomy:

| Class | Count | Use |
| --- | ---: | --- |
| `PHASE_TIIN_WINDOW` | `10` | extends Q47 phase/context hinge |
| `SLOT_TIVV_WINDOW` | `6` | extends Q47 slot/classifier hinge |
| `TAVT_BOUNDARY_WINDOW` | `1` | quarantine as boundary/continuation subclass |
| `E_EXIT_WINDOW` | `2` | quarantine as exit/sidecar subclass |
| `TERMINAL_C68_WINDOW` | `2` | quarantine as terminal/truncated subclass |

Human mechanism update:

> C68 held-out window taxonomy: the Q47 phase-slot hinge extends to held-out
> `C68` windows when the right side is `TIIN` or `TIVV`, but not every `C68`
> occurrence belongs to that two-class hinge. `TAVT`, `E`-exit, and terminal
> windows must be treated as quarantined transition subclasses, so `C68` remains
> a typed transition surface rather than a word.

Why this matters:
Q48 prevents two opposite errors. It rejects the weak claim that Q47 was only
overfit to six books, because `16` held-out observations reuse the same two
windows. It also rejects the overreach that all `C68` can be forced into the
phase/slot hinge, because five held-outs need separate subclass treatment.

Next route:
Audit the extra `C68` subclasses separately, starting with `TAVT` boundary and
`E`-exit windows, before attempting any broader prose synthesis.

## Q49 C68 Extra-Subclass Quarantine

Latest SQLite run:
`Q49_C68_EXTRA_SUBCLASSES_QUARANTINED_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q49_c68_extra_subclass_quarantine_v1.py`.

Question:
Can the five Q48 extra `C68` classes be explained without forcing them into the
phase-slot hinge?

Result:

- Target books: `3` (`23/42/56`).
- Extra observations: `5`.
- Extra subclasses: `3`.
- Prior `C68_UNCLASSIFIED_CONTEXT` count: `5`.
- Prior held/audit count: `5`.
- Promoted extra subclasses: `0`.
- Prose gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Subclass map:

| Book | Q48 class | Q49 subclass | Human use |
| --- | --- | --- | --- |
| `23` | `TERMINAL_C68_WINDOW` | `C68_TERMINAL_SUBCLASS` | mixed phase-plus-terminal composition; terminal remains evidence limit |
| `42` | `TAVT_BOUNDARY_WINDOW` | `C68_TAVT_BOUNDARY_SUBCLASS` | boundary/continuation audit evidence |
| `56` | `E_EXIT_WINDOW` | `C68_E_EXIT_SUBCLASS` | exit/sidecar audit evidence |
| `56` | `E_EXIT_WINDOW` | `C68_E_EXIT_SUBCLASS` | second exit/sidecar audit evidence |
| `56` | `TERMINAL_C68_WINDOW` | `C68_TERMINAL_SUBCLASS` | terminal/truncation evidence |

Human mechanism update:

> C68 extra-subclass quarantine: the Q48 extra windows are not failures of the
> phase-slot hinge and not new prose. Book `42` supplies a `TAVT` boundary
> subclass, Book `56` supplies `E`-exit plus terminal subclasses, and Book `23`
> supplies a mixed phase-plus-terminal composition. All remain audit-only until
> a separate source bridge explains their placement.

Why this matters:
Q49 keeps the human route honest. It lets the Q47/Q48 hinge survive where it
actually repeats, while preventing the remaining `C68` material from being
absorbed into a too-broad "C68 means X" story.

## Q50 C68 Book Synthesis

Latest SQLite run:
`Q50_C68_BOOK_SYNTHESIS_READY_FUNCTIONAL_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q50_c68_book_synthesis_v1.py`.

Question:
Can Q47-Q49 produce usable human functional versions for all books with `C68`?

Result:

- Target books with `C68`: `23`.
- Profile classes: `6`.
- Hinge-only books: `19`.
- Mixed hinge-chain books: `1`.
- Quarantined-profile books: `3`.
- Readable functional versions: `23/23`.
- Prose gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Profile distribution:

| C68 profile | Books |
| --- | ---: |
| `C68_PHASE_CONTEXT_ONLY` | `11` |
| `C68_SLOT_CLASSIFIER_ONLY` | `8` |
| `C68_MIXED_PHASE_SLOT_CHAIN` | `1` |
| `C68_PHASE_TERMINAL_COMPOSITION` | `1` |
| `C68_TAVT_BOUNDARY_AUDIT` | `1` |
| `C68_E_EXIT_TERMINAL_AUDIT` | `1` |

Human synthesis rule:
Every `C68` book now receives a profile-specific functional reading:

- phase/context books: `C68` as `TIIN`-style transition surface;
- slot/classifier books: `C68` as `TIVV`-style transition surface;
- mixed book: bridge witness between phase/context and slot/classifier;
- quarantine books: boundary, exit, or terminal subclass only.

Example functional readings:

| Book | Profile | Functional reading |
| --- | --- | --- |
| `2` | `C68_MIXED_PHASE_SLOT_CHAIN` | C86 payload opens into VNCTIIN/C68 context and then NAESE/C68 slot material; this is a chained transition witness, not sentence prose |
| `8` | `C68_PHASE_CONTEXT_ONLY` | Chayenne external frame sits in a clean VNCTIIN context; `C68` is a `TIIN`-style phase/context transition |
| `22` | `C68_SLOT_CLASSIFIER_ONLY` | canonical NAESE/C68/FATCT slot-classifier line; `C68` is a `TIVV`-style slot/classifier transition |
| `42` | `C68_TAVT_BOUNDARY_AUDIT` | weak/hybrid NAESE-adjacent line; `C68` opens a `TAVT` boundary subclass and stays audit-only |
| `56` | `C68_E_EXIT_TERMINAL_AUDIT` | clean component/control line; `C68` appears in `E`-exit and terminal subclasses, not prose |

Why this matters:
Q50 is the first family-wide human synthesis layer that covers every occurrence
of a recurring operator family across the corpus. It does not solve plaintext,
but it gives a repeatable translation method: classify the typed transition
first, then draft a functional reading by profile.

## Q51 C86 Window Taxonomy

Latest SQLite run:
`Q51_C86_WINDOW_TAXONOMY_READY_10_FUNCTIONAL_7_AUDIT_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q51_c86_window_taxonomy_v1.py`.

Question:
Can all `C86` books be separated into functional branch selectors and audit
payloads?

Result:

- Books with `C86`: `17`.
- Window classes: `7`.
- Ready functional books: `10`.
- Audit/surface books: `7`.
- `EBFAI` branch windows: `6`.
- `EVIEFIIN` context windows: `6`.
- Other audit windows: `5`.
- Gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Mechanism:

> C86 window taxonomy: `C86` has two reusable functional payload windows,
> `EBFAI` into `VINVIN/VTLR` branch mechanics and `EVIEFIIN` into
> `VN/C68/TIIN` context mechanics. Other `C86` windows remain audit/surface
> payloads and must not be promoted without edge support.

Why this matters:
Q51 prevents `C86` from becoming a vague "branch" label. It separates the two
edge-supported functions from the seven audit-only surfaces, so later human
readings can be specific without inventing prose.

## Q52 C86 Book Synthesis

Latest SQLite run:
`Q52_C86_BOOK_SYNTHESIS_READY_FUNCTIONAL_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q52_c86_book_synthesis_v1.py`.

Question:
Can Q51 produce usable human functional versions for all `C86` books?

Result:

- Target books with `C86`: `17`.
- Profile classes: `9`.
- Ready functional books: `10`.
- Audit/surface books: `7`.
- Readable functional versions: `17/17`.
- Prose gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Profile distribution:

| C86 profile | Books |
| --- | ---: |
| `C86_READY_VINVIN_VTLR_BRANCH` | `5` |
| `C86_READY_VN_C68_TIIN_CONTEXT` | `5` |
| `C86_EBFAI_SURFACE_AUDIT` | `1` |
| `C86_EVIEFIIN_SURFACE_AUDIT` | `1` |
| `C86_ETIE_RESIDUAL_AUDIT` | `1` |
| `C86_EILTAEN_LOCAL_AUDIT` | `1` |
| `C86_EEN_C68_WEAK_AUDIT` | `1` |
| `C86_F_EXIT_AUDIT` | `1` |
| `C86_TERMINAL_AUDIT` | `1` |

Example functional readings:

| Book | Profile | Functional reading |
| --- | --- | --- |
| `2` | `C86_READY_VN_C68_TIIN_CONTEXT` | `C86` opens an `EVIEFIIN` branch into `VN/C68/TIIN` context mechanics; use as context payload selector |
| `3` | `C86_READY_VINVIN_VTLR_BRANCH` | `C86` opens an `EBFAI` branch into `VINVIN/VTLR/R20` mechanics; use as branch payload selector |
| `4` | `C86_EBFAI_SURFACE_AUDIT` | `EBFAI` branch surface exists but lacks enough edge support; keep as surface/audit witness |
| `18` | `C86_TERMINAL_AUDIT` | terminal/truncated `C86`; evidence limit, not a translated ending |
| `57` | `C86_EEN_C68_WEAK_AUDIT` | weak `EEN-C68` sidecar surface; use only as negative/weak control for `C86->C68` routing |

Why this matters:
Q52 gives a second full recurring-family synthesis after Q50. We now have a
replicable method across two operator families:

1. classify local window;
2. check edge/gate support;
3. write a human functional version only for the supported role;
4. quarantine unsupported surfaces instead of turning them into prose.

## Q53 C86/C68 Chain Synthesis

Latest SQLite run:
`Q53_C86_C68_CHAIN_SYNTHESIS_READY_5_SUPPORTED_4_CONTROLS_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q53_c86_c68_chain_synthesis_v1.py`.

Question:
Can `C86` and `C68` syntheses combine into a longer human-readable chain?

Result:

- Books with both `C86` and `C68`: `9`.
- Supported chain books: `5`.
- Mixed context-to-slot chain books: `1`.
- Audit/control books: `4`.
- Readable chain versions: `9/9`.
- Prose gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Chain profile distribution:

| Chain profile | Books |
| --- | ---: |
| `SUPPORTED_CONTEXT_CHAIN` | `4` |
| `SUPPORTED_CONTEXT_TO_SLOT_CHAIN` | `1` |
| `C86_AUDIT_WITH_C68_HINGE_CONTROL` | `3` |
| `DUAL_AUDIT_CONTROL` | `1` |

Book-level chain readings:

| Book | Chain profile | Functional reading |
| --- | --- | --- |
| `2` | `SUPPORTED_CONTEXT_TO_SLOT_CHAIN` | `C86` opens `EVIEFIIN` context selector into `VN/C68/TIIN`, then `C68` bridges phase/context into slot/classifier |
| `10` | `SUPPORTED_CONTEXT_CHAIN` | `C86` opens `EVIEFIIN` context selector; `C68` stays in `TIIN` phase/context window |
| `27` | `SUPPORTED_CONTEXT_CHAIN` | `C86` opens `EVIEFIIN` context selector; `C68` stays in `TIIN` phase/context window |
| `35` | `SUPPORTED_CONTEXT_CHAIN` | formula/concordance body hands off into supported `C86 -> C68` context routing |
| `67` | `SUPPORTED_CONTEXT_CHAIN` | supported `C86 -> C68` context routing and bridge control for the `67->2` edge |
| `5` | `C86_AUDIT_WITH_C68_HINGE_CONTROL` | `C68` slot hinge is usable, but `C86` is audit-only; do not promote chain |
| `31` | `C86_AUDIT_WITH_C68_HINGE_CONTROL` | `C68` phase hinge is usable, but `C86` is local/audit-only |
| `57` | `C86_AUDIT_WITH_C68_HINGE_CONTROL` | `C68` phase hinge is usable, but `C86` is weak sidecar audit |
| `42` | `DUAL_AUDIT_CONTROL` | both `C86` and `C68` are audit-only; negative control against forced chaining |

Human mechanism:

> C86/C68 chain synthesis: `C86` can open an `EVIEFIIN` context selector into
> `VN/C68/TIIN`, and `C68` then determines whether the chain stays
> phase/context or continues toward slot/classifier. Books without `C86` edge
> support remain controls, even when their `C68` side has a usable hinge.

Why this matters:
Q53 is the first chain-level synthesis. It links two independently validated
operator-family layers and starts to look like a grammar path rather than a
single-token interpretation. The best current backbone is Book `2`, with
Books `10/27/35/67` as context-routing supports and Books `5/31/42/57` as
controls.

## Q54 Supported Chain Phrase Layer

Latest SQLite run:
`Q54_SUPPORTED_CHAIN_PHRASE_LAYER_READY_5_CANDIDATES_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q54_supported_chain_phrase_layer_v1.py`.

Question:
Can the Q53 supported `C86/C68` chains become phrase-level human candidates?

Result:

- Target books: `5` (`2/10/27/35/67`).
- Phrase candidates: `5`.
- Exact contig-shadow books: `3` (`2/35/67`).
- Edge-confirmed books: `2` (`2/67`).
- Strong phrase candidates: `3`.
- Moderate held-out candidates: `2`.
- Prose gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Phrase candidates:

| Book | Confidence | Functional phrase candidate |
| --- | --- | --- |
| `2` | `STRONG_CHAIN_SLOT_EDGE` | The selected context is handed into the classifier slot. |
| `67` | `STRONG_CHAIN_HANDOFF_EDGE` | The context handoff prepares the classifier slot. |
| `35` | `STRONG_CONTIG_CONTEXT_ROUTE` | The formula body hands context toward the classifier path. |
| `10` | `MODERATE_HELDOUT_CONTEXT_ROUTE` | The formula hands off into context routing. |
| `27` | `MODERATE_HELDOUT_CONTEXT_ROUTE` | The payload corridor holds the selected context open. |

Layer reading:

> Supported C86/C68 phrase layer: the strongest current human backbone reads as
> formula/context routing into a classifier slot. Book `2` is the
> context-to-slot phrase, Book `67` is the handoff into it, Book `35` is the
> contig-supported formula-to-context route, and Books `10/27` are held-out
> route variants.

Why this matters:
Q54 is the first deliberately phrase-like layer in this run. It is still not
canonical plaintext and does not assign lexical meanings to `C86`, `C68`,
`NAESE`, or any component. The value is that the human route now has a short,
testable backbone that can be compared against source/lore parallels and
contradiction tests.

## Q55 Q54 Source Parallel Audit

Latest SQLite run:
`Q55_Q54_SOURCE_PARALLEL_AUDIT_READY_8_SOURCES_5_PHRASES_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q55_source_parallel_audit_q54_v1.py`.

Question:
Can the Q54 phrase candidates be anchored in in-game source parallels without
turning into invented prose?

Result:

- Target books: `5` (`2/10/27/35/67`).
- Source parallels: `8`.
- Phrase-source links: `29`.
- Source-parallel ready phrases: `5`.
- Method/corpus anchors: `2`.
- Quest operator anchors: `1`.
- Lore/register anchors: `5`.
- Direct gloss count: `0`.
- Prose gloss allowed: `0`.
- Canonical promotion allowed: `0`.

Source classes:

| Source class | Sources | Use |
| --- | --- | --- |
| Method/corpus | `AWB_469_LANGUAGE_MATHEMAGIC`, `GREAT_CALCULATOR_GATHER_LANGUAGE` | 469 is constrained as mathemagical/operator processing and assembled language material. |
| Quest operator | `PARADOX_1_PLUS_1_KEYS` | Mathemagic can behave as a context-selected operator, not a fixed dictionary value. |
| Language/math | `BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS` | Bonelord language is both language and mathematics, with numeric books. |
| Ritual/research/control | `BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY`, `THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD`, `THREAT_II_RESEARCH_EXPERIMENTS`, `THREAT_III_MIND_BODY_SOUL_EXPERIMENTS` | Formula, handoff, payload, and slot routes should stay in ritual, command/control, research, experiment, and transformation registers. |

Book-level source-parallel status:

| Book | Status | Functional phrase candidate |
| --- | --- | --- |
| `2` | `SOURCE_PARALLEL_READY_MULTI_ANCHOR_NO_GLOSS` | The selected context is handed into the classifier slot. |
| `10` | `SOURCE_PARALLEL_READY_MULTI_ANCHOR_NO_GLOSS` | The formula hands off into context routing. |
| `27` | `SOURCE_PARALLEL_READY_MULTI_ANCHOR_NO_GLOSS` | The payload corridor holds the selected context open. |
| `35` | `SOURCE_PARALLEL_READY_MULTI_ANCHOR_NO_GLOSS` | The formula body hands context toward the classifier path. |
| `67` | `SOURCE_PARALLEL_READY_MULTI_ANCHOR_NO_GLOSS` | The context handoff prepares the classifier slot. |

Layer reading:

> Q54 source-parallel route: the five phrase candidates are supported as
> mathemagical, compiled, ritual, research, control, and transformation-register
> routes. The support constrains register and route shape only; it does not
> translate any component or sentence.

Why this matters:
Q55 converts the Q54 phrase layer from "plausible wording" into a source-linked
human shadow route. It gives us a defensible way to keep working with readable
phrases while preserving the hard firewall: source parallels are register and
method support, not dictionary evidence.

## Q56 Source-Linked Contrast Queue

Latest SQLite run:
`Q56_SOURCE_LINKED_CONTRAST_QUEUE_READY_6_TESTS_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q56_source_linked_contrast_queue_v1.py`.

Question:
How can the Q55 source-linked phrase readings be tested without turning them
into invented prose?

Result:

- Contrast tests: `6`.
- High-priority tests: `3`.
- Medium-priority tests: `2`.
- Hard-gate tests: `1`.
- Target books: `5` (`2/10/27/35/67`).
- Control books: `11`.
- Source links across tests: `37`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Contrast queue:

| Test | Priority | Targets | Controls | Purpose |
| --- | --- | --- | --- | --- |
| `Q56_T01_CONTEXT_TO_SLOT_CLASSIFIER` | `HIGH` | `2` | `5/42` | Test whether Book `2` needs both supported `C86` context and mixed `C68` phase-slot hinge before saying context-to-classifier slot. |
| `Q56_T02_67_TO_2_HANDOFF_EDGE` | `HIGH` | `67/2` | `27/35/42` | Test whether Book `67` is the immediate handoff into Book `2`, not a standalone payload sentence. |
| `Q56_T03_FORMULA_TO_CONTEXT_CONTIG` | `HIGH` | `35` | `10/31/57/5` | Test whether Book `35` is specifically formula-to-context route, not generic phase/context prose. |
| `Q56_T04_FORMULA_HANDOFF_HELDOUT` | `MEDIUM` | `10` | `35/31/57` | Test whether Book `10` can keep moderate formula-handoff wording without the exact Book `35` contig edge. |
| `Q56_T05_PAYLOAD_CONTEXT_HOLD` | `MEDIUM` | `27` | `67/2/57/42` | Test whether Book `27` holds payload/context open without becoming direct command/dead/soul/necromancy gloss. |
| `Q56_T06_SOURCE_OVERREACH_FIREWALL` | `HARD_GATE` | `2/10/27/35/67` | `5/31/42/57/23/56` | Re-run the firewall after future phrase synthesis so source parallels remain method/register only. |

Layer reading:

> Q56 contrast queue: Q54/Q55 phrase candidates are now expressed as six
> falsifiable tests over target books, controls, quarantine controls, and
> source-register links. Passing these tests can strengthen human shadow
> wording, but cannot promote a canonical translation.

Why this matters:
Q56 gives the human translation route a proper next-step method. Instead of
asking whether a phrase "sounds right", each phrase now has a concrete target,
controls, acceptance signal, and falsification signal. This is the safest way
to advance plausible translation while preserving the anti-overreach rules.

## Q57 High-Priority Contrast Execution

Latest SQLite run:
`Q57_HIGH_PRIORITY_CONTRASTS_ACCEPT_3_SHADOW_PHRASES_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q57_execute_high_priority_contrasts_v1.py`.

Question:
Do the three high-priority Q56 contrasts survive their controls?

Result:

- Executed tests: `3`.
- Accepted human-shadow tests: `3`.
- Demoted human-shadow tests: `0`.
- Blocked human-shadow tests: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Accepted high-priority readings:

| Test | Result | Strengthened human-shadow phrase | Remaining risk |
| --- | --- | --- | --- |
| `Q56_T01_CONTEXT_TO_SLOT_CLASSIFIER` | `ACCEPT_SHADOW_CONTRAST_NO_GLOSS` | Book `2` may keep the human-shadow wording context-to-classifier slot. | `classifier` remains a functional slot label, not a lexical word. |
| `Q56_T02_67_TO_2_HANDOFF_EDGE` | `ACCEPT_SHADOW_CONTRAST_NO_GLOSS` | Books `67->2` may keep the human-shadow handoff-into-slot wording. | The phrase names a transition role only; it does not translate either book as a sentence. |
| `Q56_T03_FORMULA_TO_CONTEXT_CONTIG` | `ACCEPT_SHADOW_CONTRAST_NO_GLOSS` | Book `35` may keep the human-shadow formula-body-to-context-route wording. | `BENNA` is still not promoted as a word. |

Layer reading:

> Q57 high-priority execution accepts the Book `2` context-to-slot phrase, the
> `67->2` handoff edge phrase, and the Book `35` formula-to-context phrase as
> strengthened human-shadow readings. This remains a contrast result only, with
> no component gloss or canonical plaintext.

Why this matters:
Q57 is the first step where phrase-like readings survive explicit controls
rather than only being proposed. It strengthens the three best pieces of the
human route: upstream formula body (`35`), handoff edge (`67->2`), and
context-to-slot target (`2`).

## Q58 Remaining Contrasts And Firewall

Latest SQLite run:
`Q58_REMAINING_CONTRASTS_AND_FIREWALL_ACCEPT_3_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q58_execute_remaining_contrasts_firewall_v1.py`.

Question:
Do the remaining Q56 contrasts and the source-overreach hard gate pass after
Q57?

Result:

- Executed tests: `3`.
- Accepted medium human-shadow tests: `2`.
- Accepted firewall tests: `1`.
- Demoted human-shadow tests: `0`.
- Blocked human-shadow tests: `0`.
- Completed Q56 queue items: `6/6`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Accepted remaining readings:

| Test | Result | Strengthened human-shadow phrase | Remaining risk |
| --- | --- | --- | --- |
| `Q56_T04_FORMULA_HANDOFF_HELDOUT` | `ACCEPT_MODERATE_SHADOW_CONTRAST_NO_GLOSS` | Book `10` may keep moderate human-shadow formula-handoff wording. | Exact `35->67->2` continuity is not present for Book `10`. |
| `Q56_T05_PAYLOAD_CONTEXT_HOLD` | `ACCEPT_MODERATE_SHADOW_CONTRAST_NO_GLOSS` | Book `27` may keep moderate human-shadow payload/context-hold wording. | Held-context wording is not command, dead, soul, or necromancy plaintext. |
| `Q56_T06_SOURCE_OVERREACH_FIREWALL` | `ACCEPT_FIREWALL_NO_GLOSS` | The Q54/Q55/Q56/Q57 human route remains source-constrained shadow translation only. | The route is stronger as human shadow, but cannot be reported as solved canonical translation. |

Layer reading:

> Q58 completes the Q56 execution queue: Book `10` and Book `27` keep moderate
> human-shadow readings, and the source-overreach firewall passes. The Q54/Q55
> phrase route is now fully tested as shadow translation, not canonical
> plaintext.

Why this matters:
Q58 closes the first source-linked phrase route. All five Q54 phrase candidates
now have source anchors, explicit controls, and pass/fail status. The route is
usable for human translation work, but it is still fenced off from the canonical
decode layer.

## Q59 Consolidated Shadow Backbone

Latest SQLite run:
`Q59_CONSOLIDATED_SHADOW_BACKBONE_READY_5_PHRASES_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q59_consolidated_shadow_backbone_v1.py`.

Question:
What is the consolidated tested human route after Q54-Q58?

Result:

- Phrase books: `5`.
- Primary backbone steps: `3`.
- Heldout variants: `2`.
- Accepted human-shadow phrases: `5`.
- Accepted firewall tests: `1`.
- Source anchors: `8`.
- Completed Q56 queue items: `6/6`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Consolidated human-shadow backbone:

| Book | Class | Confidence | Plausible human version | Residual risk |
| --- | --- | --- | --- | --- |
| `35` | `PRIMARY_BACKBONE` | `STRONG_SHADOW` | O corpo da formula encaminha o contexto para o caminho classificador. | `BENNA`/formula-body remains functional only. |
| `67` | `PRIMARY_BACKBONE` | `STRONG_SHADOW` | A passagem de contexto prepara o slot classificador. | Edge role only; Book `67` is not a standalone translated sentence. |
| `2` | `PRIMARY_BACKBONE` | `STRONG_SHADOW` | O contexto selecionado entra no slot classificador. | `classifier/slot` remains functional, not lexical. |
| `10` | `HELDOUT_VARIANT` | `MODERATE_SHADOW` | A formula faz a passagem para o roteamento de contexto. | Exact `35->67->2` continuity is absent. |
| `27` | `HELDOUT_VARIANT` | `MODERATE_SHADOW` | O corredor de carga mantem aberto o contexto selecionado. | Not command, dead, soul, necromancy, or transformation plaintext. |

Consolidated route:

> Rota humana testada: a formula encaminha o contexto, a passagem prepara o slot
> classificador, e o contexto selecionado entra no slot. Book `10` fica como
> variante moderada de formula->contexto; Book `27` fica como variante moderada
> de corredor payload/contexto.

Promotion blockers:

| Risk | Meaning |
| --- | --- |
| `Q59_RISK_FUNCTIONAL_LABELS_NOT_WORDS` | `formula`, `context`, `payload`, `handoff`, `slot`, and `classifier` are route labels, not decoded words. |
| `Q59_RISK_SOURCE_REGISTER_NOT_DICTIONARY` | Mathemagic, ritual, research, control, and transformation sources constrain register only; they do not give a dictionary. |
| `Q59_RISK_CANONICAL_UNSOLVED` | The human-shadow atlas has `70/70` coverage, but no promoted gloss exists. |

Why this matters:
Q59 is the first compact human-readable translation route that is fully backed
by the Q54-Q58 evidence chain. It is useful for reasoning and source search,
but it deliberately remains a shadow backbone rather than a solved translation.

## Q60 Component Role Promotion Queue

Latest SQLite run:
`Q60_COMPONENT_ROLE_PROMOTION_QUEUE_READY_5_TARGETS_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q60_component_role_promotion_queue_v1.py`.

Question:
Which Q59 functional labels can become the next component-role promotion
targets?

Result:

- Role candidates: `5`.
- Strong role candidates: `4`.
- Moderate role candidates: `1`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Promotion target queue:

| Candidate | Strength | Functional label | Component family | Status |
| --- | --- | --- | --- | --- |
| `Q60_C01_C68_NAESE_SLOT_CLASSIFIER_ROLE` | `STRONG_ROLE_READY` | `slot_classifier` | `C68_NAESE_SLOT` | `ROLE_PROMOTION_CANDIDATE_LEXICAL_BLOCKED` |
| `Q60_C02_C86_VNCTIIN_CONTEXT_ROUTE_ROLE` | `STRONG_ROLE_READY` | `context_route` | `C86_VNCTIIN_CONTEXT` | `ROLE_PROMOTION_CANDIDATE_LEXICAL_BLOCKED` |
| `Q60_C03_BENNA_FORMULA_HANDOFF_ROLE` | `STRONG_ROLE_READY` | `formula_handoff` | `BENNA_FORMULA` | `ROLE_PROMOTION_CANDIDATE_LEXICAL_BLOCKED` |
| `Q60_C04_EDGE_67_2_HANDOFF_ROLE` | `STRONG_EDGE_READY` | `handoff_edge` | `EDGE_67_2` | `PHRASE_EDGE_PROMOTION_CANDIDATE_LEXICAL_BLOCKED` |
| `Q60_C05_PAYLOAD_CONTEXT_HOLD_ROLE` | `MODERATE_ROLE_READY` | `payload_context_hold` | `PAYLOAD_CONTEXT_HELDOUT` | `HELDOUT_ROLE_CANDIDATE_LEXICAL_BLOCKED` |

Layer reading:

> Q60 converts the tested Q59 shadow backbone into five component-role
> promotion targets. All are role-ready targets for future contrast work, but
> lexical promotion remains blocked.

Why this matters:
Q60 is the bridge from plausible phrase route to actual translation work. It
identifies the exact component-role families that should be attacked next,
while preventing the common mistake of treating a role label as a solved word.

## Q61 C68/NAESE Slot Role Minimal Pairs

Latest SQLite run:
`Q61_C68_NAESE_SLOT_ROLE_MINIMAL_PAIRS_ACCEPT_FUNCTIONAL_ROLE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q61_c68_naese_slot_role_minimal_pairs_v1.py`.

Question:
Can `C68/NAESE slot-classifier` be accepted as a functional role through
minimal pairs?

Result:

- Target books: `2` and `5`.
- Control books: `31`, `57`, and `42`.
- Canonical Q43 slot witnesses: `3` (`22/28/48`).
- Minimal pairs: `6`.
- Passing pairs: `6`.
- Functional role accepted: `1`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Book verdicts:

| Book | Class | Window/profile | Verdict |
| --- | --- | --- | --- |
| `2` | `TARGET_SLOT_ROLE` | `PHASE_TIIN_WINDOW` + `C68_MIXED_PHASE_SLOT_CHAIN` | mixed context-to-slot target supports the role. |
| `5` | `TARGET_SLOT_ROLE` | `SLOT_TIVV_WINDOW` + `C68_SLOT_CLASSIFIER_ONLY` | slot-only witness supports `C68/NAESE` role, but not a full chain. |
| `31` | `PHASE_CONTEXT_CONTROL` | `PHASE_TIIN_WINDOW` + `C68_PHASE_CONTEXT_ONLY` | phase/context control blocks slot reading. |
| `57` | `PHASE_CONTEXT_CONTROL` | `PHASE_TIIN_WINDOW` + `C68_PHASE_CONTEXT_ONLY` | phase/context control blocks slot reading. |
| `42` | `BOUNDARY_AUDIT_CONTROL` | `TAVT_BOUNDARY_WINDOW` + `C68_TAVT_BOUNDARY_AUDIT` | boundary audit control blocks slot reading. |

Layer reading:

> C68/NAESE slot-classifier role: minimal pairs separate slot/classifier
> windows from phase/context and boundary controls. The role is functionally
> accepted for shadow work, but no C68 or NAESE word meaning is promoted.

Why this matters:
Q61 is the first Q60 target to move from "role candidate" to "accepted
functional role". It gives the human route a stronger internal mechanism for
the Book `2` classifier-slot phrase while preserving the lexical firewall.

## Q62 C86/VNCTIIN Context Route Ready-Vs-Audit

Latest SQLite run:
`Q62_C86_VNCTIIN_CONTEXT_ROUTE_READY_AUDIT_ACCEPT_FUNCTIONAL_ROLE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q62_c86_vnctiin_context_route_ready_audit_v1.py`.

Question:
Can `C86/VNCTIIN context-route` be accepted as a functional role through
ready-vs-audit contrasts?

Result:

- Target books: `5` (`2/10/27/35/67`).
- Control books: `4` (`5/31/42/57`).
- Ready targets: `5`.
- Audit controls: `4`.
- EVIEFIIN surface-audit controls: `1` (`42`).
- Contrasts: `5`.
- Passing contrasts: `5`.
- Functional role accepted: `1`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Book verdicts:

| Book | Class | C86 branch | Verdict |
| --- | --- | --- | --- |
| `2` | `READY_CONTEXT_ROUTE_TARGET` | `C86_BRANCH_EVIEFIIN_TO_VN_C68_TIIN` | ready context-route target. |
| `10` | `READY_CONTEXT_ROUTE_TARGET` | `C86_BRANCH_EVIEFIIN_TO_VN_C68_TIIN` | ready context-route target. |
| `27` | `READY_CONTEXT_ROUTE_TARGET` | `C86_BRANCH_EVIEFIIN_TO_VN_C68_TIIN` | ready context-route target. |
| `35` | `READY_CONTEXT_ROUTE_TARGET` | `C86_BRANCH_EVIEFIIN_TO_VN_C68_TIIN` | ready context-route target. |
| `67` | `READY_CONTEXT_ROUTE_TARGET` | `C86_BRANCH_EVIEFIIN_TO_VN_C68_TIIN` | ready context-route target. |
| `5` | `AUDIT_SURFACE_CONTROL` | `C86_BRANCH_ETIEIVIE_PAYLOAD` | audit surface blocks promotion. |
| `31` | `AUDIT_SURFACE_CONTROL` | `C86_BRANCH_EILTAEN_PAYLOAD` | audit surface blocks promotion. |
| `42` | `EVIEFIIN_SURFACE_AUDIT_CONTROL` | `C86_BRANCH_EVIEFIIN_PAYLOAD` | EVIEFIIN-looking surface blocks forced promotion. |
| `57` | `AUDIT_SURFACE_CONTROL` | `C86_BRANCH_EEN_C68_TIIN_PAYLOAD` | weak audit surface blocks promotion. |

Layer reading:

> C86/VNCTIIN context-route role: ready books share
> `EVIEFIIN->VN/C68/TIIN` context routing, while audit controls remain residual,
> local, weak, or surface-only. The role is functionally accepted for shadow
> work, but no C86 or VNCTIIN word meaning is promoted.

Why this matters:
Q62 strengthens the internal mechanism behind the Q59 context route. The key
control is Book `42`: it has an EVIEFIIN-looking surface but fails the ready
branch gate, so the role is not being promoted from visual resemblance alone.

## Q63 BENNA Formula Handoff Directional Contrast

Latest SQLite run:
`Q63_BENNA_FORMULA_HANDOFF_DIRECTIONAL_CONTRAST_ACCEPT_FUNCTIONAL_ROLE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q63_benna_formula_handoff_directional_contrast_v1.py`.

Question:
Can `BENNA formula-handoff` be accepted as a functional role through directional
contrasts?

Result:

- Target books: `2` (`35/10`).
- Control books: `3` (`5/31/57`).
- Clean formula targets: `2`.
- Residual/template controls: `1` (`5`).
- Non-formula controls: `2` (`31/57`).
- Support edges: `3` (`58->35`, `69->35`, `47->35`).
- Contrasts: `5`.
- Passing contrasts: `5`.
- Functional role accepted: `1`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Book verdicts:

| Book | Class | BENNA bridge/role | Verdict |
| --- | --- | --- | --- |
| `35` | `PRIMARY_FORMULA_HANDOFF_TARGET` | `BENNA_FORMULA_BRIDGE_CLEAN_WITH_TAIL_NO_GLOSS` + `HANDOFF_CONTEXT_ALIVE` | primary formula-handoff target. |
| `10` | `HELDOUT_FORMULA_HANDOFF_TARGET` | `BENNA_FORMULA_BRIDGE_CLEAN_WITH_TAIL_NO_GLOSS` + `HANDOFF_CONTEXT_ALIVE` | moderate heldout formula-handoff target. |
| `5` | `RESIDUAL_SLOT_TO_FORMULA_CONTROL` | `BENNA_VARIANT_OR_RESIDUAL_FORMULA_AUDIT_ONLY` + `TEMPLATE_HEAD_ALIVE` | residual/template control blocks forced handoff promotion. |
| `31` | `NON_FORMULA_PHASE_CONTEXT_CONTROL` | no BENNA bridge/role row | non-formula phase control blocks promotion. |
| `57` | `NON_FORMULA_PHASE_CONTEXT_CONTROL` | no BENNA bridge/role row | non-formula phase control blocks promotion. |

Layer reading:

> BENNA formula-handoff role: Books `35` and `10` carry clean BENNA formula
> bridge with handoff-context role, while Book `5` is residual/template
> slot-to-formula control and Books `31/57` are non-formula phase controls. The
> role is functionally accepted for shadow work, but no BENNA word meaning is
> promoted.

Why this matters:
Q63 prevents the obvious overreach. It does not say "BENNA means formula".
Instead, it accepts a directional role only where clean formula bridge,
handoff-context propagation, and supported context routing line up. Book `5`
proves that BENNA-like material alone is not enough.

## Q64 Edge 67->2 Handoff Role Contrast

Latest SQLite run:
`Q64_EDGE_67_2_HANDOFF_ROLE_ACCEPT_FUNCTIONAL_EDGE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q64_edge_67_2_handoff_role_contrast_v1.py`.

Question:
Can the `67->2` edge be accepted as a functional handoff role?

Result:

- Target books: `2` (`67/2`).
- Control books: `3` (`27/35/42`).
- Exact path books: `3` (`35/67/2`).
- Accepted edge count: `1`.
- Contrasts: `5`.
- Passing contrasts: `5`.
- Functional edge accepted: `1`.
- Phrase path accepted: `1`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Book verdicts:

| Book | Class | Edge/contig status | Verdict |
| --- | --- | --- | --- |
| `67` | `HANDOFF_EDGE_TARGET` | `EDGE_CONFIRMED` + `EXACT_CONTIG_SHADOW_AVAILABLE` | handoff edge target supports role. |
| `2` | `SLOT_TARGET` | `EDGE_CONFIRMED` + `EXACT_CONTIG_SHADOW_AVAILABLE` | slot target receives handoff. |
| `35` | `UPSTREAM_FORMULA_CONTROL` | no direct edge + exact contig | upstream formula route, not edge target. |
| `27` | `HELDOUT_CONTEXT_CONTROL` | no direct edge + no exact contig | heldout context route blocks edge replication. |
| `42` | `BOUNDARY_AUDIT_CONTROL` | no Q54 edge + no exact contig | boundary audit blocks edge replication. |

Layer reading:

> `67->2` handoff edge role: exact contig evidence and accepted edge status
> support Book `67` as the handoff into Book `2`'s slot target. Books `27`,
> `35`, and `42` do not reproduce the same continuity. This is an edge/phrase
> path role only, not sentence plaintext.

Why this matters:
Q64 turns the strongest phrase transition in the current human route into a
tested functional edge. It also proves the boundary of the claim: Book `35` is
upstream formula, Book `27` is heldout context, and Book `42` is audit-only, so
the `67->2` role is not being applied everywhere context appears.

## Q65 Payload Context Hold Heldout Role

Latest SQLite run:
`Q65_PAYLOAD_CONTEXT_HOLD_HELDOUT_ROLE_ACCEPT_MODERATE_OPEN_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q65_payload_context_hold_heldout_role_v1.py`.

Question:
Can Book `27` payload/context hold be accepted as a heldout functional role?

Result:

- Target book: `1` (`27`).
- Control books: `4` (`67/2/57/42`).
- Ready context target count: `1`.
- Missing edge count: `1`.
- Slot/handoff controls: `2` (`67/2`).
- Audit controls: `2` (`57/42`).
- Source safeguards: `4`.
- Contrasts: `5`.
- Passing contrasts: `5`.
- Heldout role accepted: `1`.
- Stop/continue resolved count: `0`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Book verdicts:

| Book | Class | Route/edge status | Verdict |
| --- | --- | --- | --- |
| `27` | `HELDOUT_PAYLOAD_CONTEXT_TARGET` | ready `C86/VNCTIIN` context route + no direct edge | moderate payload/context-hold role accepted. |
| `67` | `HANDOFF_EDGE_CONTROL` | ready route + edge confirmed | blocks reading Book `27` as the handoff edge. |
| `2` | `SLOT_TARGET_CONTROL` | ready route + slot target | blocks reading Book `27` as the slot target. |
| `57` | `WEAK_AUDIT_CONTROL` | weak C86/C68 audit | blocks weak-audit overreach. |
| `42` | `BOUNDARY_AUDIT_CONTROL` | EVIEFIIN surface/boundary audit | blocks boundary/surface overreach. |

Source firewall:

| Source family | Blocked overreach |
| --- | --- |
| Paradox mathemagic | no `1/13/49/94` dictionary or solved key. |
| Threat I | no `C86/VNCTIIN = command/dead/eye/necromancy`. |
| Threat II | research lore is not a dictionary key. |
| Threat III | no `NAESE/C68 = soul/mind/body/undead/monster` mapping. |

Layer reading:

> Book `27` payload/context-hold role: Book `27` is a ready C86/VNCTIIN context
> route without the observed `67->2` edge or Book `2` slot target. It is
> accepted as a moderate heldout role, while stop-vs-missing-edge remains
> unresolved and source-register overreach remains blocked.

Why this matters:
Q65 completes the Q60 role queue without pretending the weakest phrase is
stronger than it is. Book `27` is useful as a heldout context route, but it is
not proof of an ending, command, necromantic sentence, or transformation gloss.

## Q66 Component Role Ledger

Latest SQLite run:
`Q66_COMPONENT_ROLE_LEDGER_READY_5_ROLES_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q66_component_role_ledger_v1.py`.

Question:
What did Q60-Q65 actually establish?

Result:

- Role targets: `5`.
- Functional roles accepted: `5`.
- Strong functional roles: `4`.
- Moderate heldout roles: `1`.
- Open risks tracked: `4`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Ledger:

| Role | Evidence | Strength | Functional reading | Residual risk |
| --- | --- | --- | --- | --- |
| `C68_NAESE_SLOT` | Q61 | `STRONG_FUNCTIONAL_ROLE_ACCEPTED` | C68/NAESE can function as slot/classifier transition where local route evidence supplies slot context. | slot/classifier labels are not Bonelord word meanings. |
| `C86_VNCTIIN_CONTEXT` | Q62 | `STRONG_FUNCTIONAL_ROLE_ACCEPTED` | C86/VNCTIIN can function as context-route in ready `EVIEFIIN->VN/C68/TIIN` route books. | context/payload/route are register labels, not dictionary glosses. |
| `BENNA_FORMULA` | Q63 | `STRONG_FUNCTIONAL_ROLE_ACCEPTED` | BENNA formula body can hand off into context routing where clean formula and handoff evidence align. | Book `5` proves BENNA-like material alone is not enough. |
| `EDGE_67_2` | Q64 | `STRONG_EDGE_ROLE_ACCEPTED` | `67->2` works as context handoff into Book `2` slot target. | edge/path role only, not sentence plaintext. |
| `PAYLOAD_CONTEXT_HELDOUT` | Q65 | `MODERATE_HELDOUT_ROLE_ACCEPTED_OPEN` | Book `27` stays as a payload/context-hold heldout. | stop-vs-missing-edge remains unresolved. |

Risk ledger:

| Risk | Status | Consequence |
| --- | --- | --- |
| `FUNCTIONAL_LABELS_NOT_WORDS` | `OPEN` | accepted roles support shadow phrasing, not word meanings. |
| `SOURCE_REGISTER_NOT_DICTIONARY` | `OPEN_CONTROLLED` | Mathemagic, Great Calculator, and threat lore constrain register but do not decode words alone. |
| `BOOK27_STOP_CONTINUE_OPEN` | `OPEN` | Book `27` does not prove an endpoint or a missing continuation. |
| `CANONICAL_TRANSLATION_UNSOLVED` | `OPEN` | no canonical plaintext has been promoted. |

Layer reading:

> Five Q60 targets now have tested functional roles for human shadow work. The
> slot, route, formula-handoff, and `67->2` edge roles are strong; Book `27`
> payload/context hold is moderate and open. None are lexical word meanings,
> and no canonical plaintext is promoted.

Why this matters:
Q66 gives the project a stable translation-facing ledger. The human layer can
now speak in roles without pretending those roles are decoded words, and future
source searches can target the exact blockers: lexical evidence, source
firewall, and Book `27` stop-vs-continuation.

## Q67 Lexical Anchor Probe Queue

Latest SQLite run:
`Q67_LEXICAL_ANCHOR_PROBE_QUEUE_READY_6_PROBES_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q67_lexical_anchor_probe_queue_v1.py`.

Question:
What should be tested next to move from functional roles toward lexical
translation?

Result:

- Q66 roles covered: `5`.
- Source families covered: `8`.
- Probe count: `6`.
- High-priority probes: `4`.
- Hard-gate probes: `1`.
- Exact-sequence-required probes: `6`.
- No-dictionary-firewall probes: `6`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Probe queue:

| Probe | Role | Priority | Purpose |
| --- | --- | --- | --- |
| `Q67_P01_C68_NAESE_SLOT_EXACT_SOURCE` | `C68_NAESE_SLOT` | `HIGH` | Search for exact source/mechanic evidence that separates slot/classifier from phase/context controls. |
| `Q67_P02_C86_VNCTIIN_CONTEXT_COMMAND_CONTROL` | `C86_VNCTIIN_CONTEXT` | `HIGH` | Test command/control/research lore without converting it into a C86/VNCTIIN dictionary. |
| `Q67_P03_BENNA_FORMULA_MATHEMAGIC_OPERATOR` | `BENNA_FORMULA` | `HIGH` | Ask whether Mathemagica or numeric Bonelord-language sources provide a repeatable operator model for BENNA handoff. |
| `Q67_P04_EDGE_67_2_PHRASE_PATH_CONTINUITY` | `EDGE_67_2` | `MEDIUM` | Test whether in-game corpus/packet sources can explain `35->67->2` as a phrase path. |
| `Q67_P05_BOOK27_STOP_VS_CONTINUATION` | `PAYLOAD_CONTEXT_HELDOUT` | `HIGH` | Decide whether Book `27` stops in payload/context or only lacks the observed `67->2` continuation. |
| `Q67_P06_GLOBAL_SOURCE_FIREWALL_NEGATIVE_CONTROL` | all Q66 roles | `HARD_GATE` | Reject any candidate that uses lore as a hidden dictionary gloss instead of exact sequence evidence. |

Source families retained as search targets and guardrails:

- `AWB_469_LANGUAGE_MATHEMAGIC`
- `BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS`
- `BEWARE_UNSPEAKABLE_RITUALS_UNDEAD_ARMY`
- `GREAT_CALCULATOR_GATHER_LANGUAGE`
- `PARADOX_1_PLUS_1_KEYS`
- `THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD`
- `THREAT_II_RESEARCH_EXPERIMENTS`
- `THREAT_III_MIND_BODY_SOUL_EXPERIMENTS`

Layer reading:

> Q67 does not translate new words. It turns the Q66 role ledger into six
> source-anchored lexical probes. Every probe requires exact sequence,
> provenance, positive controls, failed controls, and contradiction audit before
> any lexical or canonical promotion.

Why this matters:
The next progress frontier is now explicit. We can search online/in-game
material aggressively, including Mathemagica and related Bonelord quests, while
blocking the failure mode that has repeatedly produced plausible but unsupported
prose.

## Q68 BENNA Mathemagic Operator Check

Latest SQLite run:
`Q68_BENNA_MATHEMAGIC_OPERATOR_CHECK_METHOD_SUPPORT_NO_LEXICAL_PROMOTION`.

Materialized by:
`scripts/sqlite_human_q68_benna_mathemagic_operator_check_v1.py`.

Question:
Can Mathemagica promote BENNA formula-handoff into a lexical/operator rule?

Result:

- Q67 probe executed: `Q67_P03_BENNA_FORMULA_MATHEMAGIC_OPERATOR`.
- Source checks: `3`.
- Operator/method support sources: `3`.
- Exact BENNA sequence sources: `0`.
- Repeatable operator rules found: `0`.
- Control-prediction rules found: `0`.
- Firewall pass count: `1`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Source check:

| Source | Method/operator value | BENNA lexical value |
| --- | --- | --- |
| `AWB_469_LANGUAGE_MATHEMAGIC` | strong support for mathemagic/numbers/formula mode. | no exact BENNA sequence or BENNA meaning. |
| `BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS` | strong support for language plus mathematics and numeric books. | no exact BENNA sequence or BENNA meaning. |
| `PARADOX_1_PLUS_1_KEYS` | strong support for quest-side mathemagic operator context. | no BENNA rule; Paradox keys stay contained. |

Tests:

| Test | Status |
| --- | --- |
| `Q68_T01_EXACT_BENNA_SEQUENCE` | `FAILS_LEXICAL_PROMOTION_REQUIREMENT` |
| `Q68_T02_REPEATABLE_OPERATOR_RULE` | `FAILS_OPERATOR_PROMOTION_REQUIREMENT` |
| `Q68_T03_PARADOX_KEY_CONTAINMENT` | `PASSES_FIREWALL_NO_DICTIONARY` |
| `Q68_T04_BOOK5_NEGATIVE_CONTROL` | `FAILS_CONTROL_PREDICTION_REQUIREMENT` |

Layer reading:

> Mathemagica is strong method/operator pressure for BENNA formula-handoff
> searches, but it does not promote BENNA. No checked source provides an exact
> BENNA sequence, no repeatable operator predicts Book `35/10` against
> Book `5/31/57` controls, and Paradox `1+1` values remain quest mechanics
> rather than a dictionary.

Why this matters:
This is negative progress, but it is useful. It preserves Mathemagica as a
serious route for future search while shutting down the tempting shortcut
`mathemagic -> BENNA meaning`. The next high-value probe should either find an
exact BENNA-bearing source relation or move to Book `27` stop-vs-continuation.

## Q69 Book27 Stop-Vs-Continuation Source Check

Latest SQLite run:
`Q69_BOOK27_STOP_CONTINUE_SOURCE_CHECK_REMAINS_OPEN_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q69_book27_stop_continue_source_check_v1.py`.

Question:
Does Book `27` stop in payload/context hold, or does it lack the observed
`67->2` continuation?

Result:

- Q67 probe executed: `Q67_P05_BOOK27_STOP_VS_CONTINUATION`.
- Source checks: `3`.
- Register-support sources: `3`.
- Exact Book `27` sequence sources: `0`.
- Stop resolved count: `0`.
- Continuation resolved count: `0`.
- Firewall pass count: `1`.
- Heldout status preserved count: `1`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Source check:

| Source | Register value | Stop/continuation value |
| --- | --- | --- |
| `THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD` | command/control/dead-minion register. | no exact Book `27` stop or continuation evidence. |
| `THREAT_II_RESEARCH_EXPERIMENTS` | research/experiment register. | no exact Book `27` stop or continuation evidence. |
| `THREAT_III_MIND_BODY_SOUL_EXPERIMENTS` | transformation/payload register. | no exact Book `27` stop or continuation evidence. |

Tests:

| Test | Status |
| --- | --- |
| `Q69_T01_EXACT_BOOK27_SEQUENCE` | `FAILS_STOP_CONTINUE_RESOLUTION_REQUIREMENT` |
| `Q69_T02_STOP_ENDPOINT_SUPPORT` | `FAILS_STOP_ENDPOINT_REQUIREMENT` |
| `Q69_T03_MISSING_CONTINUATION_SUPPORT` | `FAILS_CONTINUATION_REQUIREMENT` |
| `Q69_T04_THREAT_REGISTER_FIREWALL` | `PASSES_FIREWALL_NO_DICTIONARY` |
| `Q69_T05_Q65_HELDOUT_STATUS_PRESERVED` | `PASSES_HELDOUT_STATUS_PRESERVED` |

Layer reading:

> Threat I/II/III are useful register pressure for Book `27`, but they do not
> decide whether Book `27` is an endpoint or merely lacks the observed `67->2`
> edge. Book `27` remains a moderate payload/context heldout with stop-vs-
> continuation unresolved.

Why this matters:
Q69 prevents a common overreach: using command, necromancy, research, soul/body,
or monster lore to force a translation of Book `27`. The next productive route
is no longer broad source register; it is sequence-neighbor search around
Book `27` and possible missing edges.

## Q70 Book27 Sequence-Neighbor Scan

Latest SQLite run:
`Q70_BOOK27_SEQUENCE_NEIGHBOR_SCAN_FINDS_27_TO_67_CANDIDATE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q70_book27_sequence_neighbor_scan_v1.py`.

Question:
Does row0 sequence-neighbor evidence favor Book `27` endpoint or missing
continuation?

Result:

- Target book: `27`.
- Scanned books: `70`.
- Outgoing overlap candidates: `15`.
- Incoming overlap candidates: `0`.
- Top outgoing candidate: `27->67`.
- Top outgoing overlap: `34` tokens.
- Accepted edge minimum overlap: `34` tokens.
- Outgoing candidates at or above accepted-edge minimum: `1`.
- Imported contig edge count for `27->67`: `0`.
- Continuation candidate count: `1`.
- Endpoint support count: `0`.
- Stop/continue resolved count: `0`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Top outgoing candidates:

| Rank | Edge | Overlap | Status |
| --- | --- | --- | --- |
| `1` | `27->67` | `34` tokens | continuation candidate, unconfirmed. |
| `2` | `27->2` | `18` tokens | weak overlap control. |
| `3` | `27->19` | `17` tokens | weak overlap control. |
| `4` | `27->13` | `9` tokens | weak overlap control. |
| `5` | `27->57` | `9` tokens | weak overlap control. |

Control comparison:

| Edge | Overlap | Imported contig edge |
| --- | --- | --- |
| `58->35` | `68` tokens | yes |
| `35->67` | `36` tokens | yes |
| `67->2` | `34` tokens | yes |
| `27->67` | `34` tokens | no |
| `27->2` | `18` tokens | no |

Layer reading:

> Book `27` has a strong unconfirmed continuation candidate: its best outgoing
> row0 suffix-prefix overlap is `27->67` with `34` tokens, equal to the accepted
> `67->2` control-edge overlap. Because `27->67` is not an imported contig edge
> and no source resolves it, it is not promoted; but endpoint readings of Book
> `27` are now mechanically weaker.

Why this matters:
Q70 is the first new structural idea after the source checks: Book `27` may be
a pre-edge or truncated route into the already strong `67->2` path. The next
step should be a confirmation gate for `27->67` against false-overlap
backgrounds and contig controls.

## Q71 Book27->67 False-Overlap Gate

Latest SQLite run:
`Q71_27_TO_67_FALSE_OVERLAP_GATE_STRONG_LOCAL_GLOBAL_UNCONFIRMED_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q71_book27_to_67_false_overlap_gate_v1.py`.

Question:
Does global overlap background confirm or weaken the `27->67` continuation
candidate?

Result:

- Global directed pairs checked: `4830`.
- Positive-overlap pairs: `732`.
- Strong threshold: `34` tokens.
- Strong-overlap pairs: `14`.
- Strong imported contig edges: `7`.
- Strong non-imported pairs: `7`.
- Stronger non-imported pairs than `27->67`: `6`.
- `27->67` global rank: `13`.
- `27->67` non-imported rank: `7`.
- `27->67` local outgoing rank from Book `27`: `1`.
- False-overlap risk count: `1`.
- Continuation confirmed count: `0`.
- Continuation candidate count: `1`.
- Lexical-ready candidates: `0`.
- Canonical promotion allowed: `0`.

Top background:

| Rank | Pair | Overlap | Imported? | Class |
| --- | --- | --- | --- | --- |
| `1` | `51->53` | `121` | yes | imported contig edge. |
| `2` | `58->35` | `68` | yes | imported contig edge. |
| `3` | `29->65` | `63` | yes | imported contig edge. |
| `4` | `58->0` | `62` | no | strong non-imported background. |
| `5` | `52->62` | `60` | yes | imported contig edge. |
| `6` | `13->38` | `56` | yes | imported contig edge. |
| `7` | `44->62` | `56` | no | strong non-imported background. |
| `8` | `45->53` | `53` | no | strong non-imported background. |
| `9` | `69->35` | `50` | no | strong non-imported background. |
| `10` | `51->48` | `48` | no | strong non-imported background. |
| `11` | `69->0` | `44` | no | strong non-imported background. |
| `12` | `35->67` | `36` | yes | imported contig edge. |
| `13` | `27->67` | `34` | no | target continuation candidate. |
| `14` | `67->2` | `34` | yes | imported contig edge. |

Tests:

| Test | Status |
| --- | --- |
| `Q71_T01_TARGET_LOCAL_RANK` | `PASSES_LOCAL_CONTINUATION_SIGNAL` |
| `Q71_T02_ACCEPTED_EDGE_THRESHOLD` | `PASSES_ACCEPTED_EDGE_THRESHOLD` |
| `Q71_T03_GLOBAL_FALSE_OVERLAP_BACKGROUND` | `FAILS_GLOBAL_CONFIRMATION_HAS_FALSE_OVERLAP_RISK` |
| `Q71_T04_IMPORTED_CONTIG_REQUIREMENT` | `FAILS_IMPORTED_CONTIG_REQUIREMENT` |
| `Q71_T05_NO_GLOSS_FIREWALL` | `PASSES_NO_GLOSS_FIREWALL` |

Layer reading:

> `27->67` is Book `27`'s strongest local continuation signal and meets the
> accepted edge threshold, but it fails global confirmation because stronger
> non-imported overlaps exist. Keep it as a strong unconfirmed continuation
> candidate, not a confirmed edge, contig, or translation.

Why this matters:
Q71 keeps the method honest. The new Book `27` idea survives local checks, but
the global background proves that overlap alone is not enough. The next step is
to classify stronger non-imported overlaps so we can tell missing contigs from
ordinary false-overlap background.

## Q72 Strong Non-Imported Overlap Triage

Latest SQLite run:
`Q72_STRONG_NONIMPORTED_OVERLAP_TRIAGE_27_TO_67_ONLY_LIVE_CANDIDATE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q72_strong_nonimported_overlap_triage_v1.py`.

Question:
Are the stronger non-imported overlaps missing contigs or false-overlap
background?

Result:

- Strong non-imported pairs triaged: `7`.
- Target pairs: `1`.
- Known local/variant background pairs: `6`.
- Imported-to-noncontig background pairs: `2`.
- Noncontig-to-imported background pairs: `3`.
- Live missing-edge candidates: `1`.
- Confirmed missing edges: `0`.
- Target candidate status: `LIVE_UNCONFIRMED_CANDIDATE_NO_GLOSS`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Triage:

| Rank | Pair | Overlap | Triage |
| --- | --- | --- | --- |
| `1` | `58->0` | `62` | imported-to-noncontig variant background. |
| `2` | `44->62` | `56` | noncontig-to-imported variant background. |
| `3` | `45->53` | `53` | noncontig-to-imported variant background. |
| `4` | `69->35` | `50` | known local formula control to imported background. |
| `5` | `51->48` | `48` | imported-to-noncontig variant background. |
| `6` | `69->0` | `44` | noncontig-to-noncontig background. |
| `7` | `27->67` | `34` | target strong local continuation candidate. |

Layer reading:

> The six stronger non-imported overlaps are explainable as background,
> variant, or known local-control overlaps under existing Q36/atlas statuses.
> `27->67` remains the only live missing-edge candidate, but it is still
> unconfirmed and carries no gloss.

Why this matters:
Q72 upgrades the usefulness of `27->67` without overstating it. The global
false-overlap objection is partly contained, but confirmation still requires a
focused edge gate. The next step is to test `27->67` as a possible missing edge
against imported contig controls and local family constraints.

## Q73 Book27->67 Confirmation Gate

Latest SQLite run:
`Q73_27_TO_67_STRUCTURAL_MISSING_EDGE_CANDIDATE_STRENGTHENED_UNCONFIRMED_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q73_book27_to_67_confirmation_gate_v1.py`.

Question:
Can `27->67` be strengthened after Q72 triage?

Result:

- Target edge: `27->67`.
- Target overlap: `34` tokens.
- Local rank pass: `1`.
- Accepted-threshold pass: `1`.
- Same bridge pass: `1`.
- Same stratum pass: `1`.
- Prefix compatibility with imported `35->67`: `1`.
- Q72 background contained count: `1`.
- Source resolution count: `0`.
- Imported contig confirmation count: `0`.
- Structural candidate strengthened count: `1`.
- Confirmed edge count: `0`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Tests:

| Test | Status |
| --- | --- |
| `Q73_T01_LOCAL_RANK_AND_THRESHOLD` | `PASSES_LOCAL_RANK_AND_THRESHOLD` |
| `Q73_T02_SAME_BRIDGE_AND_STRATUM` | `PASSES_SAME_BRIDGE_AND_STRATUM` |
| `Q73_T03_PREFIX_COMPATIBILITY_WITH_35_TO_67` | `PASSES_PREFIX_COMPATIBILITY` |
| `Q73_T04_BACKGROUND_CONTAINED_BY_Q72` | `PASSES_BACKGROUND_CONTAINED` |
| `Q73_T05_IMPORTED_OR_SOURCE_CONFIRMATION` | `FAILS_CONFIRMATION_REQUIREMENT_REMAINS_CANDIDATE` |
| `Q73_T06_NO_GLOSS_FIREWALL` | `PASSES_NO_GLOSS_FIREWALL` |

Layer reading:

> `27->67` is strengthened from a live candidate to a structural missing-edge
> candidate. It is Book `27`'s top outgoing overlap, meets the accepted edge
> threshold, shares the same payload/context bridge and stratum with Book `67`,
> and is prefix-compatible with the imported `35->67` edge. It is still not a
> confirmed edge because no imported contig or exact source resolution exists.

Why this matters:
Book `27` is no longer just a heldout phrase. It now has a concrete structural
route into the strongest existing path (`67->2`), which gives the human
translation layer a better hypothesis: Book `27` may be a truncated/pre-edge
payload-context route, not an endpoint. This remains shadow-only and cannot be
reported as canonical translation.

## Q74 Book27->67 External Exact Search Audit

Latest SQLite run:
`Q74_27_TO_67_EXTERNAL_EXACT_SEARCH_NO_EXTERNAL_CONFIRMATION_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q74_book27_to_67_external_exact_search_audit_v1.py`.

Question:
Does exact online/local source search confirm `27->67` externally?

Result:

- Web exact queries: `4`.
- Web exact external hits: `0`.
- Local search terms: `4`.
- Local match paths: `4`.
- Internal-only matches: `4`.
- Local external support count: `0`.
- External sequence confirmation count: `0`.
- Source resolution count: `0`.
- Candidate status preserved count: `1`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Web queries:

| Query | Status |
| --- | --- |
| `"LFSENSTAEFIEIEFIIVFATFTFNLIBEITEITAILBETFTE" Tibia` | no exact external hit. |
| `"ITEITAILBETFTE" "CEVIEFIINI" Tibia` | no exact external hit. |
| `"VNCTIIN" "TAILBETFTE" "Tibia"` | no exact external hit. |
| `"CEVIEFIINI" "VNCTIIN" "NAESE"` | no exact external hit. |

Local exact matches:

| Path | Class | Status |
| --- | --- | --- |
| `data/exports/functional_row0/functional_row0_contigs.jsonl` | internal export | not external support. |
| `data/exports/functional_row0/functional_row0_books.jsonl` | internal export | not external support. |
| `data/exports/functional_row0/functional_row0_contigs.txt` | internal export | not external support. |
| `scripts/sqlite_tailbetfte_suffix_frame_gate.py` | internal script | not external support. |

Layer reading:

> Exact external search did not confirm `27->67` or the key Book `27/67`
> sequence terms. Local exact matches are internal exports/scripts only. Q73's
> structural candidate status is preserved, but there is still no source
> resolution, gloss, or canonical promotion.

Why this matters:
Q74 blocks a subtle circularity risk: internal exports can help operationally,
but they are not independent source evidence. The `27->67` route remains useful
for human-shadow structure, yet any future promotion still needs an external
source/provenance hit or a stronger internal contig-reconstruction proof.

## Q75 C68/NAESE Exact Source Check

Latest SQLite run:
`Q75_C68_NAESE_EXACT_SOURCE_CHECK_NO_EXACT_GLOSS_FUNCTIONAL_ROLE_ONLY`.

Materialized by:
`scripts/sqlite_human_q75_c68_naese_exact_source_check_v1.py`.

Question:
Is there exact source support for C68/NAESE slot meaning?

Result:

- Q67 probe executed: `Q67_P01_C68_NAESE_SLOT_EXACT_SOURCE`.
- Web exact queries: `4`.
- Exact slot web hits: `0`.
- Source checks: `3`.
- Register-support sources: `2`.
- External method source count: `1`.
- Exact C68/NAESE sequence sources: `0`.
- Slot mechanical value count: `0`.
- Firewall pass count: `3`.
- Functional role preserved count: `1`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Web queries:

| Query | Status |
| --- | --- |
| `"NAESE" "Tibia" "Bonelord"` | no exact slot hit. |
| `"IVIFAST" "Tibia"` | no exact slot hit. |
| `"FATCT" "Tibia" "Bonelord"` | no exact slot hit. |
| `"NAESESTIENFATCT"` | no exact slot hit. |

Source check:

| Source | Value | Result |
| --- | --- | --- |
| `THREAT_III_MIND_BODY_SOUL_EXPERIMENTS` | transformation/payload register. | no exact C68/NAESE sequence or lexical support. |
| `PARADOX_1_PLUS_1_KEYS` | mathemagic/operator selector context. | no slot mechanical value or C68/NAESE dictionary. |
| `S2WARD_469_SEQUENCE_METHOD` | external method pressure for sequence assembly. | useful method reference, not canonical in-game anchor. |

Tests:

| Test | Status |
| --- | --- |
| `Q75_T01_EXACT_NAESE_C68_WEB_HIT` | `FAILS_EXACT_SOURCE_REQUIREMENT` |
| `Q75_T02_THREAT_III_REGISTER_FIREWALL` | `PASSES_REGISTER_FIREWALL_NO_DICTIONARY` |
| `Q75_T03_PARADOX_KEY_FIREWALL` | `PASSES_MATHEMAGIC_FIREWALL_NO_DICTIONARY` |
| `Q75_T04_EXTERNAL_METHOD_NOT_CANONICAL_ANCHOR` | `PASSES_EXTERNAL_METHOD_CONTAINMENT` |
| `Q75_T05_Q61_FUNCTIONAL_ROLE_PRESERVED` | `PASSES_FUNCTIONAL_ROLE_PRESERVED_NO_GLOSS` |

Layer reading:

> C68/NAESE keeps its Q61 role as a functional slot/classifier layer only. No
> checked source provides an exact C68/NAESE sequence, slot value, or word
> meaning. Threat III and Paradox constrain search register; s2ward/469 helps
> with method, not canonical anchoring.

Why this matters:
This closes another tempting overreach. We can use C68/NAESE as a human shadow
slot role, but not as a translated word such as soul, body, key, slot, or
classifier. The next lexical progress still requires exact sequence evidence.

## Q76 C86/VNCTIIN Command-Control Check

Latest SQLite run:
`Q76_C86_VNCTIIN_COMMAND_CONTROL_CHECK_REGISTER_SUPPORT_NO_EXACT_GLOSS`.

Materialized by:
`scripts/sqlite_human_q76_c86_vnctiin_command_control_check_v1.py`.

Question:
Is there exact source support for C86/VNCTIIN command/control or research
meaning?

Result:

- Q67 probe executed: `Q67_P02_C86_VNCTIIN_CONTEXT_COMMAND_CONTROL`.
- Web exact queries: `4`.
- Exact context web hits: `0`.
- Source checks: `2`.
- Register-support sources: `2`.
- Exact C86/VNCTIIN sequence sources: `0`.
- Context-route mechanical value count: `0`.
- Firewall pass count: `3`.
- Functional role preserved count: `1`.
- Q62 ready targets: `5`.
- Q62 audit controls: `4`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Web queries:

| Query | Status |
| --- | --- |
| `"VNCTIIN" "Tibia"` | no exact context hit. |
| `"CEVIEFIINI" "Tibia"` | no exact context hit. |
| `"EVIEFIIN" "Tibia" "Bonelord"` | no exact context hit. |
| `"C86" "VNCTIIN" "Bonelord"` | no exact context hit. |

Source check:

| Source | Value | Result |
| --- | --- | --- |
| `THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD` | command/control/necromancy register. | no exact C86/VNCTIIN sequence or lexical support. |
| `THREAT_II_RESEARCH_EXPERIMENTS` | research/experiment register. | no context-route mechanical value or lexical support. |

Tests:

| Test | Status |
| --- | --- |
| `Q76_T01_EXACT_C86_VNCTIIN_WEB_HIT` | `FAILS_EXACT_SOURCE_REQUIREMENT` |
| `Q76_T02_THREAT_I_COMMAND_FIREWALL` | `PASSES_COMMAND_FIREWALL_NO_DICTIONARY` |
| `Q76_T03_THREAT_II_RESEARCH_FIREWALL` | `PASSES_RESEARCH_FIREWALL_NO_DICTIONARY` |
| `Q76_T04_Q62_READY_VS_AUDIT_PRESERVED` | `PASSES_FUNCTIONAL_ROLE_PRESERVED_NO_GLOSS` |
| `Q76_T05_SURFACE_AUDIT_CONTROLS_BLOCK_OVERREACH` | `PASSES_AUDIT_CONTROL_FIREWALL` |

Layer reading:

> C86/VNCTIIN keeps its Q62 role as a functional context-route layer only.
> Threat I and II strongly support command/control/research register, but no
> checked source provides an exact C86/VNCTIIN sequence, context-route value, or
> word meaning.

Why this matters:
This completes the high-priority Q67 lexical-source probes for BENNA,
Book `27`, C68/NAESE, and C86/VNCTIIN. The current human method can now use
these roles coherently, but every one remains a shadow role until exact source
or contig confirmation appears.

## Decision

The path forward is no longer "wait for exact gloss or do nothing". The project
should operate with two explicit layers:

- Canonical decode layer: strict, structural, no unsupported prose.
- Human shadow layer: plausible, readable, source-anchored, falsifiable, and
  clearly marked as not promoted.

This gives us a practical way to search for meaning while preserving the rigor
that prevented false solved states.

## Q77 High-Priority Probe Synthesis

Latest SQLite run:
`Q77_HIGH_PRIORITY_PROBE_SYNTHESIS_READY_4_EXECUTED_1_STRUCTURAL_FRONTIER_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q77_high_priority_probe_synthesis_v1.py`.

Question:
What did the high-priority Q67 lexical-anchor probes actually establish?

Result:

- Q67 high-priority probes: `4`.
- Executed high-priority probes: `4`.
- Exact source successes: `0`.
- Lexical-ready candidates: `0`.
- Direct glosses: `0`.
- Canonical promotions allowed: `0`.
- Strengthened structural candidates: `1`.
- Confirmed edges: `0`.
- Open high-value frontier: `1`.
- Closed no-gloss probes: `3`.

Synthesis:

| Probe | Outcome | Operational status |
| --- | --- | --- |
| `BENNA_MATHEMAGIC` | Mathemagica gives method/operator pressure only. | closed no-gloss; reopen only with exact BENNA sequence or predictive operator rule. |
| `BOOK27_TO_67` | `27->67` is a strengthened structural missing-edge candidate. | open high-value structural frontier; still unconfirmed and no-gloss. |
| `C68_NAESE_SLOT` | C68/NAESE remains a functional slot/classifier role only. | closed no-gloss; reject lexical readings without exact sequence support. |
| `C86_VNCTIIN_CONTEXT` | C86/VNCTIIN remains a functional context-route role only. | closed no-gloss; Threat I/II constrain register, not meaning. |

Next frontier:

| Frontier | Priority | Gate |
| --- | --- | --- |
| `27_TO_67_CONTIG_RECONSTRUCTION` | high | confirm only through independent contig reconstruction or exact source/provenance. |
| `EDGE_67_2_SOURCE_CONTINUITY` | medium | require source-backed continuity rule or exact phrase parallel. |
| `GLOBAL_SOURCE_FIREWALL` | hard gate | require exact source, exact sequence, provenance, passed/failed controls, and contradiction audit before any promotion. |

Layer reading:

> All four high-priority lexical probes are now executed. None produced a
> source-backed word meaning. The only positive movement is structural:
> Book `27` should stay in the human-shadow search as a possible continuation
> into `67->2`, not as a translated sentence and not as a canonical edge.

Why this matters:
Q77 closes the current high-priority lexical-source batch without pretending
the absence of glosses is failure. It preserves the useful human method:
functional roles can guide plausible readings, but promotion still requires an
exact in-game anchor or a stronger structural proof.

## Q78 Edge 67->2 Source Continuity

Latest SQLite run:
`Q78_EDGE_67_2_SOURCE_CONTINUITY_METHOD_SUPPORT_NO_EXACT_PHRASE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q78_edge_67_2_source_continuity_v1.py`.

Question:
Does any in-game source explain a compiled or gathered-language packet that
would make `35->67->2` a phrase path rather than only a structural contig?

Result:

- Q67 probe executed: `Q67_P04_EDGE_67_2_PHRASE_PATH_CONTINUITY`.
- Local phrase-path accept count: `1`.
- Q64 passing contrasts: `5`.
- Q64 control edge failures: `3`.
- Source checks: `2`.
- Source method-support checks: `2`.
- Exact edge-source hits: `0`.
- Exact phrase parallels: `0`.
- Web exact hits: `0`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Source checks:

| Source | Value | Result |
| --- | --- | --- |
| `GREAT_CALCULATOR_GATHER_LANGUAGE` | supports assembled/compiled Bonelord-language material as corpus structure. | method support only; no Book67, Book2, `67->2`, or exact phrase meaning. |
| `BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS` | supports numeric/mathematical language and numeric books as search register. | method support only; no `67->2`, `35->67->2`, or exact plaintext relation. |

Exact web queries:

| Query | Status |
| --- | --- |
| `"67->2" "Bonelord"` | no exact edge hit. |
| `"Book 67" "Book 2" "469" "Tibia"` | no exact edge hit. |
| `"CEVIEFIINI" "VNCTIIN"` | no exact sequence hit. |
| `"Tibia" "35->67->2"` | no exact path hit. |

Control gate:

| Book | Role | Edge condition |
| --- | --- | --- |
| `67` | handoff edge inside `35->67->2`. | passes target edge condition. |
| `2` | slot/classifier target receiving handoff. | passes receiver edge condition. |
| `35` | upstream formula/context route. | fails same edge condition; not the handoff target. |
| `27` | heldout payload/context control. | fails same edge condition. |
| `42` | boundary/audit control. | fails same edge condition. |

Layer reading:

> `35->67->2` is now source-compatible as a human-shadow packet path:
> formula/context route, handoff edge, and slot/classifier target. The in-game
> source layer supports a gathered, numeric, mathematical language model, but
> still does not supply a phrase translation for the edge.

Why this matters:
Q78 upgrades the practical human reading route without breaking the firewall.
We can use `35->67->2` as the main readable packet spine and test `27->67`
against it, but any sentence-level reading remains provisional until an exact
source relation or independent contig proof appears.

## Q79 Global Source Firewall

Latest SQLite run:
`Q79_GLOBAL_SOURCE_FIREWALL_PASS_BLOCKS_ALL_PROMOTIONS_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q79_global_source_firewall_v1.py`.

Question:
Does a candidate use source lore as register only, or does it smuggle in a
dictionary gloss?

Result:

- Q67 hard-gate probe executed: `Q67_P06_GLOBAL_SOURCE_FIREWALL_NEGATIVE_CONTROL`.
- Firewall candidates checked: `5`.
- Candidates blocked from promotion: `5`.
- Exact source-sequence count: `0`.
- Exact meaning-relation count: `0`.
- Allowed shadow candidates: `5`.
- Firewall tests: `5`.
- Passing firewall tests: `4`.
- Failing promotion-requirement tests: `1`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Candidate firewall:

| Candidate | Allowed layer | Firewall result |
| --- | --- | --- |
| `BENNA_MATHEMAGIC` | shadow method only. | block canonical promotion; method only. |
| `BOOK27_STOP_CONTINUE` | shadow structural candidate only. | block canonical promotion; unconfirmed edge. |
| `C68_NAESE_SLOT` | shadow functional role only. | block canonical promotion; no dictionary. |
| `C86_VNCTIIN_CONTEXT` | shadow functional role only. | block canonical promotion; no dictionary. |
| `EDGE_67_2_PATH` | shadow packet path only. | block sentence translation; no exact phrase. |

Firewall tests:

| Test | Status |
| --- | --- |
| `Q79_T01_EXACT_SOURCE_SEQUENCE_REQUIREMENT` | fails for all candidates, blocking promotion. |
| `Q79_T02_REGISTER_NOT_DICTIONARY` | passes firewall. |
| `Q79_T03_STRUCTURAL_NOT_PLAINTEXT` | passes firewall. |
| `Q79_T04_CONTROL_FAILURES_REQUIRED` | passes firewall. |
| `Q79_T05_COMPLETION_AUDIT_PROMOTED_GLOSS_ZERO` | passes firewall. |

Layer reading:

> The current human-readable route is usable as a search and explanation layer:
> method, structure, function, and packet path. It is not a source-backed
> plaintext translation. The promotion gate remains exact sequence plus exact
> source relation plus controls plus contradiction audit.

Why this matters:
Q79 closes the Q67 queue without losing the new progress. We now have a clean
human translation workspace: `35->67->2` is the main readable packet spine,
`27->67` is the strongest heldout continuation candidate, and every lexical
claim remains blocked until the project finds an exact in-game anchor.

## Q80 Packet Shadow Versions

Latest SQLite run:
`Q80_PACKET_SHADOW_VERSIONS_READY_PRIMARY_35_67_2_HELDOUT_27_67_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q80_packet_shadow_versions_v1.py`.

Question:
What human-readable versions can be used after Q77-Q79 without violating the
source firewall?

Result:

- Packet versions: `2`.
- Accepted primary packets: `1`.
- Conditional heldout packets: `1`.
- Source anchors carried forward: `8`.
- Exact source-sequence count: `0`.
- Exact meaning-relation count: `0`.
- Confirmed edge-extension count: `0`.
- Lexical-ready candidates: `0`.
- Direct gloss count: `0`.
- Canonical promotion allowed: `0`.

Primary packet:

| Packet | Status | Human-shadow version |
| --- | --- | --- |
| `35->67->2` | accepted as human-shadow packet, not canonical. | `O corpo da formula encaminha o contexto; a passagem prepara o slot classificador; o contexto selecionado entra no slot classificador.` |

Heldout extension:

| Packet | Status | Human-shadow version |
| --- | --- | --- |
| `27->67->2` | conditional heldout extension, unconfirmed. | `Se 27->67 for confirmado, o corredor de carga mantem aberto o contexto selecionado antes da passagem preparar o slot classificador e o contexto selecionado entrar nesse slot.` |

Book-role mapping:

| Book | Role | Reading status |
| --- | --- | --- |
| `35` | primary upstream formula/context route. | formula routes context; no BENNA gloss. |
| `67` | primary handoff edge. | handoff prepares classifier slot; not standalone sentence. |
| `2` | primary context-to-slot target. | selected context enters classifier slot; no C68/NAESE gloss. |
| `27` | heldout payload/context hold. | only a conditional continuation candidate; no command/dead/soul/ritual gloss. |

Layer reading:

> The current human-readable translation layer can now state a controlled
> packet-level version: `35->67->2` behaves like a formula-to-context-to-slot
> packet. `27->67->2` is useful as a hypothesis only if the missing edge is
> later confirmed. Neither packet is plaintext, dictionary, or canonical.

Why this matters:
Q80 converts the structural work into a usable human-facing translation
artifact while preserving all gates. This is the first clean packet version
after the high-priority lexical probes: it gives a readable version to reason
with, but keeps exact-source discovery as the promotion requirement.

## Q81 Controlled Human Shadow Export

Latest SQLite run:
`Q81_CONTROLLED_HUMAN_SHADOW_EXPORT_READY_70_BOOKS_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q81_controlled_shadow_export_v1.py`.

Export artifacts:

- `tmp/human_shadow_exports/q81_controlled_human_shadow_export_v1.md`.
- `tmp/human_shadow_exports/q81_controlled_human_shadow_export_v1.json`.

Question:
Can the complete atlas be exported as a controlled human-shadow translation
artifact?

Result:

- Exported books: `70`.
- Readable rows: `70`.
- Anchored rows: `70`.
- Contradiction audit `PASS` rows: `70`.
- `NOT_PROMOTED` rows: `70`.
- Promoted glosses: `0`.
- Primary packet books: `3`.
- Heldout packet books: `3`.

Export status:

| Artifact | Use | Gate |
| --- | --- | --- |
| Markdown export | human review and reading pass over all 70 books. | not canonical plaintext. |
| JSON export | machine-readable review, sorting, and future source-search queues. | no gloss promotion. |
| SQLite rows | operational trace for every exported book. | each row preserves anchors, blocked claims, falsifier, audit status, and packet tags. |

Layer reading:

> The project now has a full controlled human-shadow translation export. Every
> book has a plausible reading and anchor metadata, and every row remains
> explicitly `NOT_PROMOTED`. This is a review/search artifact, not a solved
> dictionary or canonical translation.

Why this matters:
Q81 turns the 70/70 atlas into an inspectable artifact that can be reviewed by
humans and used for the next source-search cycle. It makes the current
translation state usable without lowering the promotion bar.

## Q82 Exact Source Target Queue

Latest SQLite run:
`Q82_EXACT_SOURCE_TARGET_QUEUE_READY_8_FAMILIES_15_BOOKS_NO_PROMOTION`.

Materialized by:
`scripts/sqlite_human_q82_exact_source_target_queue_v1.py`.

Question:
Which human-shadow families should be searched next for exact in-game source
evidence?

Result:

- Promotion-review books: `15`.
- Target families: `8`.
- Critical targets: `2`.
- High targets: `2`.
- Medium targets: `3`.
- External-frame risk targets: `1`.
- Exact source hits: `0`.
- Canonical promotion allowed: `0`.

Target queue:

| Target | Priority | Books | Search question |
| --- | --- | --- | --- |
| `BENNA_C86_VNCTIIN_FORMULA_HANDOFF` | critical | `2` | Can a source prove BENNA formula handoff into C86/VNCTIIN context rather than only structural routing? |
| `C86_VNCTIIN_PAYLOAD_CORRIDOR` | critical | `3` | Can any in-game source bind C86/VNCTIIN-bearing sequences to a specific payload/context meaning? |
| `NAESE_BENNA_COMPOSITE` | high | `2` | Can any exact source distinguish NAESE/C68 slot material flowing into BENNA formula body? |
| `R02_NAESE_SLOT_BRIDGE` | high | `2` | Can any source bind R02 phase bridge into NAESE/C68 slot mechanics? |
| `BOOK49_MATH49_REGISTER` | medium | `1` | Can the self-contained Book49 repeat shape be tied to a real in-game 49/math operator? |
| `BOOK54_PAIR_LOCAL_SPINE` | medium | `1` | Can the Book54 local-pair spine be confirmed outside its local alignment with Book20? |
| `BOOK7_PHASE_MATHEMAGIC` | medium | `1` | Can Mathemagica or Paradox prove the Book7 phase continuation/handoff rule? |
| `CHAYENNE_FRAME_REGISTER` | medium external-frame risk | `3` | Can Chayenne-frame books be anchored inside game relationships rather than external register shape only? |

Acceptance gate:

> Accept only if an in-game or official/primary source gives the exact
> sequence, its provenance, a meaning or mechanically forced value, and failed
> controls. Reject register-only lore, external-only shape matches, and any
> plausible prose that lacks exact sequence-plus-meaning evidence.

Why this matters:
Q82 turns the complete human-shadow export into a concrete source-search
program. The next work should not browse randomly; it should execute the two
critical targets first because they are the only families likely to move the
Q80 packet from readable shadow toward a promotable package.

## Q83 BENNA/C86 Exact Source Audit

Latest SQLite run:
`Q83_BENNA_C86_EXACT_SOURCE_AUDIT_METHOD_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q83_benna_c86_exact_source_audit_v1.py`.

Question:
Can a source prove BENNA formula handoff into C86/VNCTIIN context rather than
only structural routing?

Result:

- Q82 target executed: `Q82_T01_BENNA_C86_VNCTIIN_FORMULA_HANDOFF`.
- Target books: `2` (`10`, `35`).
- Web queries: `8`.
- Web exact target hits: `0`.
- Official exact target hits: `0`.
- Source checks: `5`.
- Method/register support sources: `5`.
- Exact source-sequence count: `0`.
- Exact meaning-relation count: `0`.
- Lexical-ready candidates: `0`.
- Canonical promotion allowed: `0`.

Source checks:

| Source | Result | Blocked inference |
| --- | --- | --- |
| `AWB_469_LANGUAGE_MATHEMAGIC` | method support only. | no BENNA/LTAST/TAILBETFTE/VNCTIIN handoff meaning. |
| `BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS` | register support only. | no BENNA formula body, C86/VNCTIIN, or handoff semantics. |
| `HONEMINAS_FORMULA_PARALLEL` | formula-mode support only. | no mechanical or lore link to the target sequence. |
| `PARADOX_1_PLUS_1_KEYS` | operator-mode support only. | no exact sequence relation or predictive rule. |
| `TIBIAWIKI_BR_469_SYNTHESIS` | secondary synthesis support only. | no solid translation claim for the target sequence. |

Tests:

| Test | Status |
| --- | --- |
| `Q83_T01_WEB_EXACT_SEQUENCE` | fails exact-source requirement. |
| `Q83_T02_SOURCE_METHOD_FIREWALL` | passes method-support-only firewall. |
| `Q83_T03_BOOK10_35_STRUCTURAL_STATUS` | preserve shadow handoff only. |
| `Q83_T04_PROMOTION_FIREWALL` | passes promotion block. |

Layer reading:

> Books `10/35` still form a strong BENNA/LTAST formula handoff into
> C86/VNCTIIN context, but this remains a structural/method reading. No checked
> source gives the exact target sequence or a source-provided meaning relation.

Why this matters:
Q83 prevents the strongest formula-handoff candidate from being promoted too
early. The next critical target is now `C86_VNCTIIN_PAYLOAD_CORRIDOR`; if that
also fails exact-source search, the Q80 packet remains useful only as human
shadow.

## Q84 C86/VNCTIIN Exact Source Audit

Latest SQLite run:
`Q84_C86_VNCTIIN_EXACT_SOURCE_AUDIT_REGISTER_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q84_c86_vnctiin_exact_source_audit_v1.py`.

Question:
Can any in-game source bind C86/VNCTIIN-bearing sequences to a specific
payload/context meaning?

Result:

- Q82 target executed: `Q82_T02_C86_VNCTIIN_PAYLOAD_CORRIDOR`.
- Target books: `3` (`2`, `27`, `67`).
- Web queries: `8`.
- Web exact target hits: `0`.
- Official exact target hits: `0`.
- Source checks: `5`.
- Register-support sources: `5`.
- Exact source-sequence count: `0`.
- Exact meaning-relation count: `0`.
- Context-route mechanical value count: `0`.
- Lexical-ready candidates: `0`.
- Canonical promotion allowed: `0`.

Source checks:

| Source | Result | Blocked inference |
| --- | --- | --- |
| `THREAT_I_EYESTALK_MAGIC_COMMAND_DEAD` | command/register support only. | no C86/VNCTIIN, CEVIEFIINI, TAILBETFTE, or payload/context value. |
| `THREAT_II_RESEARCH_EXPERIMENTS` | research/register support only. | no C86/VNCTIIN sequence support or context-route value. |
| `THREAT_III_MIND_BODY_SOUL_EXPERIMENTS` | transformation/register support only. | no mapping from C86/VNCTIIN, NAESE, or TAILBETFTE to soul/body/command semantics. |
| `AWB_469_LANGUAGE_MATHEMAGIC` | method support only. | no identification of C86/VNCTIIN or Book `2/27/67` corridor. |
| `BEWARE_LANGUAGE_MATH_NUMERIC_BOOKS` | language/register support only. | no exact C86/VNCTIIN sequence or meaning. |

Tests:

| Test | Status |
| --- | --- |
| `Q84_T01_WEB_EXACT_SEQUENCE` | fails exact-source requirement. |
| `Q84_T02_THREAT_REGISTER_FIREWALL` | passes register-support-only firewall. |
| `Q84_T03_Q76_PRIOR_RESULT_PRESERVED` | preserves Q76 no-exact-gloss result. |
| `Q84_T04_PROMOTION_FIREWALL` | passes promotion block. |

Layer reading:

> Books `2/27/67` keep the C86/VNCTIIN payload-corridor reading as a strong
> human-shadow structure. Threat I/II/III strengthen the surrounding command,
> research, and transformation register, but no checked source gives the exact
> sequence or a source-provided meaning relation.

Why this matters:
Q84 closes the second critical Q82 target. Together Q83 and Q84 show that the
Q80 packet has enough support to guide human reading, but not enough to leave
the shadow layer. The next useful step is to synthesize the impact of both
critical failures before moving to high-priority NAESE/BENNA or R02/NAESE
targets.

## Q85 Critical Source Audit Synthesis

Latest SQLite run:
`Q85_CRITICAL_SOURCE_AUDIT_SYNTHESIS_Q80_SHADOW_STABLE_PROMOTION_BLOCKED`.

Materialized by:
`scripts/sqlite_human_q85_critical_source_audit_synthesis_v1.py`.

Question:
What is the impact of Q83/Q84 on the Q80 packet and next translation route?

Result:

- Critical Q82 targets: `2`.
- Audited critical targets: `2`.
- Critical exact-source hits: `0`.
- Critical exact meaning relations: `0`.
- Q80 shadow packets preserved: `2`.
- Q80 packet promotions allowed: `0`.
- Next high-priority targets: `2`.
- Canonical promotion allowed: `0`.

Impact:

| Item | Status | Next action |
| --- | --- | --- |
| `BENNA_C86_VNCTIIN_FORMULA_HANDOFF` | keep structural/method shadow; block promotion. | reopen only with new exact BENNA/LTAST/TAILBETFTE/VNCTIIN source or predictive operator rule. |
| `C86_VNCTIIN_PAYLOAD_CORRIDOR` | keep register-supported payload corridor shadow; block promotion. | reopen only with exact CEVIEFIINI/VNCTIIN/TAILBETFTE/NAESE source relation or mechanical value. |
| `Q80_PACKET` | stable as readable shadow; canonical promotion blocked. | use for human review/search; execute Q82 high targets next. |

Next targets:

| Target | Priority | Reason |
| --- | --- | --- |
| `Q82_T03_NAESE_BENNA_COMPOSITE` | high | may test slot material flowing into BENNA formula independently of failed packet promotion. |
| `Q82_T04_R02_NAESE_SLOT_BRIDGE` | high | may provide an alternate phase-to-slot bridge that does not depend on C86/VNCTIIN promotion. |
| `Q82_T07_BOOK7_PHASE_MATHEMAGIC` | medium | preserves Mathemagica as an operator-discovery route after BENNA/C86 exact-source failure. |

Layer reading:

> The Q80 packet is stable enough to guide human review, but Q83/Q84 prove that
> its two critical promotion routes currently lack exact-source evidence. It
> should remain a readable shadow packet while the search shifts to NAESE/BENNA
> and R02/NAESE alternatives.

Why this matters:
This prevents another loop over the same negative searches. The method now has
a clear branch: keep the best human packet as working interpretation, and look
for exact-source leverage in the high-priority slot/phase families.

## Q86 NAESE/BENNA Exact Source Audit

Latest SQLite run:
`Q86_NAESE_BENNA_EXACT_SOURCE_AUDIT_METHOD_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q86_naese_benna_exact_source_audit_v1.py`.

Question:
Can the high-priority `NAESE/BENNA` composite in books `5/9` be anchored to an
exact in-game or source-backed meaning?

Result:

- Q82 target executed: `Q82_T03_NAESE_BENNA_COMPOSITE`.
- Target books: `2` (`5`, `9`).
- Web queries: `8`.
- Web exact target hits: `0`.
- Official exact target hits: `0`.
- Source checks: `5`.
- Method-support sources: `5`.
- Exact source-sequence count: `0`.
- Exact meaning-relation count: `0`.
- Slot mechanical value count: `0`.
- BENNA operator-rule count: `0`.
- Lexical-ready candidates: `0`.
- Canonical promotion allowed: `0`.

Book-level human shadows:

| Book | Reading | Status |
| --- | --- | --- |
| `5` | NAESE/C68 slot material flows into a BENNA formula body. | preserve as composite shadow only. |
| `9` | NAESE/C68 slot window feeds a BENNA formula/concordance body and continues into an LTAST boundary tail. | preserve as composite shadow only. |

Source checks:

| Source | Result | Blocked inference |
| --- | --- | --- |
| `Q75_C68_NAESE_SOURCE_CHECK` | NAESE slot functional only, no exact gloss. | no exact C68/NAESE sequence, slot value, or lexical support. |
| `Q68_BENNA_MATHEMAGIC_SOURCE_CHECK` | BENNA method support only, no exact gloss. | no exact BENNA sequence, operator rule, or lexical support. |
| `AWB_469_LANGUAGE_MATHEMAGIC` | method support only. | no NAESE/BENNA composite flow or meaning relation. |
| `HONEMINAS_FORMULA_PARALLEL` | formula mode support only. | no link from Honeminas formula to the NAESE/BENNA composite. |
| `THREAT_III_MIND_BODY_SOUL_EXPERIMENTS` | transformation register support only. | no map from NAESE/C68/BENNA to soul, mind, body, monster, or formula semantics. |

Tests:

| Test | Status |
| --- | --- |
| `Q86_T01_WEB_EXACT_SEQUENCE` | fails exact-source requirement. |
| `Q86_T02_PRIOR_NAESE_AND_BENNA_FIREWALL` | preserves Q75/Q68 no-exact-gloss results. |
| `Q86_T03_COMPOSITE_STATUS` | preserves composite shadow only. |
| `Q86_T04_PROMOTION_FIREWALL` | passes promotion block. |

Layer reading:

> Books `5/9` form a useful human-shadow route where slot material appears to
> feed formulaic BENNA material, but every checked source remains register or
> method support. No checked source gives the exact composite sequence plus
> source-provided meaning.

Why this matters:
Q86 keeps the user-requested human/plausible translation route alive while
preventing an invented word-level gloss. The next high-priority route is now
`Q82_T04_R02_NAESE_SLOT_BRIDGE`, because it may give an alternate phase-to-slot
bridge independent of the blocked BENNA/C86 promotions.

## Q87 R02/NAESE Exact Source Audit

Latest SQLite run:
`Q87_R02_NAESE_EXACT_SOURCE_AUDIT_STRUCTURAL_BRIDGE_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q87_r02_naese_exact_source_audit_v1.py`.

Question:
Can the high-priority `R02/NAESE` bridge in books `51/53` be anchored to an
exact in-game or source-backed meaning?

Result:

- Q82 target executed: `Q82_T04_R02_NAESE_SLOT_BRIDGE`.
- Target books: `2` (`51`, `53`).
- Local control books: `3` (`14`, `45`, `46`).
- Web queries: `8`.
- Web exact target hits: `0`.
- Official exact target hits: `0`.
- Source checks: `7`.
- Method-support sources: `7`.
- Exact source-sequence count: `0`.
- Exact meaning-relation count: `0`.
- Structural bridge passes: `2`.
- Slot functional accepts: `1`.
- Lexical-ready candidates: `0`.
- Canonical promotion allowed: `0`.

Book-level human shadows:

| Book | Reading | Status |
| --- | --- | --- |
| `51` | R02/TRVEIIVNTBB bridge carries into the NAESE/C68 slot frame. | preserve as phase-to-slot shadow only. |
| `53` | R02/TRVEIIVNTBB bridge carries into the NAESE/C68 slot frame. | preserve as phase-to-slot shadow only. |

Local controls:

| Book | Control | Status |
| --- | --- | --- |
| `14` | weak R02 boundary-audit fragment touching VNA/LTAST-like material. | not clean slot proof. |
| `45` | R02/R20 context connector adjacent to slot mechanics. | not clean slot proof. |
| `46` | R02/R20 context connector adjacent to slot mechanics. | not clean slot proof. |

Source checks:

| Source | Result | Blocked inference |
| --- | --- | --- |
| `R02_NAESE_SLOT_BRIDGE_PRIOR_GATE` | structural bridge pass, no prose. | no R02, TRVEIIVNTBB, or NAESE word meaning. |
| `Q61_C68_NAESE_MINIMAL_PAIRS` | functional slot role accepted, no gloss. | no C68, NAESE, slot, or classifier word gloss. |
| `Q75_C68_NAESE_EXACT_SOURCE_CHECK` | no exact C68/NAESE gloss. | no soul, mind, body, undead, monster, key, slot, or classifier word mapping. |
| `HUMAN_R20_R02_PHASE_BRIDGE` | phase bridges ready, no gloss. | no collapse of phase, slot, VINVIN branch, and micro-context into one prose meaning. |
| `AWB_469_LANGUAGE_MATHEMAGIC` | method support only. | no ANIVVENINTEIN, TRVEIIVNTBB, R02, or NAESE meaning. |
| `THREAT_I_COMMAND_REGISTER` | command/register support only. | no exact R02/NAESE sequence or phase-to-slot meaning. |
| `THREAT_III_TRANSFORMATION_REGISTER` | transformation/register support only. | no R02/TRVEIIVNTBB/NAESE mapping to soul, mind, body, monster, or formula semantics. |

Tests:

| Test | Status |
| --- | --- |
| `Q87_T01_WEB_EXACT_SEQUENCE` | fails exact-source requirement. |
| `Q87_T02_PRIOR_BRIDGE_GATE` | preserves structural bridge only. |
| `Q87_T03_SLOT_MINIMAL_PAIRS` | preserves functional slot role without gloss. |
| `Q87_T04_LOCAL_CONTROLS` | preserves controls. |
| `Q87_T05_PROMOTION_FIREWALL` | passes promotion block. |

Layer reading:

> Books `51/53` are now the strongest controlled human-shadow bridge from R02
> phase material into the NAESE/C68 slot frame. The source audit still blocks
> any word-level translation of R02, TRVEIIVNTBB, NAESE, C68, FATCT, IVIFAST,
> slot, or bridge.

Why this matters:
Q87 gives the human translator a better route than Q86: the `R02/NAESE` pair is
not just plausible, it passes local structural controls. The limitation is also
clear: it is a strong phase-to-slot shadow, not a canonical translation. With
both high-priority targets closed, the next useful route is the medium
`Q82_T07_BOOK7_PHASE_MATHEMAGIC` target, because Mathemagica may expose an
operator pattern rather than a direct word gloss.

## Q88 Book7 Phase/Mathemagica Exact Source Audit

Latest SQLite run:
`Q88_BOOK7_PHASE_MATHEMAGIC_EXACT_SOURCE_AUDIT_OPERATOR_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q88_book7_phase_mathemagic_exact_source_audit_v1.py`.

Question:
Can Mathemagica or Paradox prove the `Book7` phase continuation/handoff rule as
an exact source-backed meaning?

Result:

- Q82 target executed: `Q82_T07_BOOK7_PHASE_MATHEMAGIC`.
- Target books: `1` (`7`).
- Web queries: `8`.
- Web exact target hits: `0`.
- Official exact target hits: `0`.
- Source checks: `10`.
- Method-support sources: `10`.
- Exact source-sequence count: `0`.
- Exact meaning-relation count: `0`.
- Book7 bridge support count: `9`.
- Held direction count: `2`.
- Transition signal count: `1`.
- Heldout positive count: `0`.
- Mathemagica operator output count: `4`.
- Live-local operator count: `1`.
- Exact 3478 phrase source count: `2`.
- Client/official data source count: `0`.
- Lexical-ready candidates: `0`.
- Canonical promotion allowed: `0`.

Book-level human shadow:

| Book | Reading | Status |
| --- | --- | --- |
| `7` | Phase-continuity line carrying a sequence through a local phase anchor. | preserve as Book7/Mathemagica shadow only. |

Source checks:

| Source | Result | Blocked inference |
| --- | --- | --- |
| `Q4_BOOK7_PHASE_DIRECTION` | phase bridge confirmed, direction held, no gloss. | no Book7 sentence or component gloss. |
| `Q8_BOOK6_7_3478_TRANSITION` | phase path supported, no payload gloss. | no 3478, NEIAAETTA, TIINNEF, Book6, or Book7 payload translation. |
| `Q9_HELDOUT_SUPPORT_AUDIT` | no heldout contig support; keep control. | no independent contig/overlap/literal/similarity support for a sentence reading. |
| `Q26_MATHEMAGIC_TRANSCRIPT_BRIDGE` | operator-only, no gloss. | Mathemagica is not a plaintext dictionary. |
| `Q27_MATHEMAGIC_OPERATOR_QUEUE` | operators reconciled, no gloss. | no operator becomes a plaintext word or Book7 gloss. |
| `HUMAN_MATHEMAGIC_SYNTHESIS` | operators, not plaintext. | no accepted human gloss from Mathemagica alone. |
| `Q31_BONELORD_TOME_3478_486486` | question/oracle frame, no component gloss. | no component gloss for 3478, 486486, or Book7 phase components. |
| `AWB_469_LANGUAGE_MATHEMAGIC` | method support only. | no TIINNEF, NEIAAETTA, 3478, or Book7 meaning. |
| `PARADOX_MATHEMAGIC_OPERATOR_KEYS` | operator-key support only. | 1/13/49/94-style keys are not a Book7 dictionary. |
| `TIBIASECRETS_HELLGATE_AVERAGE_ROUTE` | external method pressure only. | external method pressure cannot promote a Book7 gloss. |

Tests:

| Test | Status |
| --- | --- |
| `Q88_T01_WEB_EXACT_SEQUENCE` | fails exact-source requirement. |
| `Q88_T02_BOOK7_LOCAL_BRIDGE` | preserves local bridge, direction held. |
| `Q88_T03_MATHEMAGIC_OPERATOR_MODE` | preserves operator mode, no dictionary. |
| `Q88_T04_3478_FRAME` | preserves 3478/oracle frame, no component gloss. |
| `Q88_T05_PROMOTION_FIREWALL` | passes promotion block. |

Layer reading:

> Book `7` remains a strong human-shadow line for phase continuity and
> operator-guided search. Mathemagica and 3478/486486 make the route worth using
> for future probes, but they still do not provide an exact Book7 phrase meaning
> or a forced plaintext value.

Why this matters:
Q88 turns Mathemagica into a productive search engine rather than a dead end:
use it to rank operator and selector experiments, not to invent a word list. The
best current human routes are now separated: `R02/NAESE` as the strongest local
phase-to-slot bridge, `Book7/Mathemagica` as operator search machinery, and
`Q80` as a stable but non-promoted packet shadow.

## Q89 Human Route Synthesis After Q86-Q88

Latest SQLite run:
`Q89_HUMAN_ROUTE_SYNTHESIS_READY_NEXT_BOOK49_MATH49_NO_CANONICAL_GLOSS`.

Materialized by:
`scripts/sqlite_human_q89_route_synthesis_after_q86_q88_v1.py`.

Question:
After Q86-Q88, what are the best human translation routes, and what should be
tested next?

Result:

- Route count: `5`.
- Alive route count: `3`.
- Next action count: `4`.
- Promoted gloss count: `0`.
- Top route: `Q89_R01_R02_NAESE_PHASE_SLOT_BRIDGE`.
- Next exact-source target: `Q82_T05_BOOK49_MATH49_REGISTER`.

Current route ranking:

| Rank | Route | Books | Status | Human use |
| --- | --- | --- | --- | --- |
| `1` | `R02_NAESE_PHASE_SLOT_BRIDGE` | `51/53` | alive primary human route. | R02/TRVEIIVNTBB phase material carries into the NAESE/C68 slot frame. |
| `2` | `BOOK7_MATHEMAGIC_OPERATOR_ROUTE` | `7` | alive operator-discovery route. | Book7 carries phase continuity through a local phase anchor; Mathemagica guides selector/operator tests. |
| `3` | `Q80_CONTROLLED_PACKET_SHADOW` | `35/67/2` | alive readable packet shadow. | Formula routes context; handoff prepares classifier slot; selected context enters that slot. |
| `4` | `NAESE_BENNA_COMPOSITE` | `5/9` | held composite shadow. | NAESE/C68 slot material appears to flow into BENNA formula material. |
| `5` | `REMAINING_MEDIUM_TARGETS` | `49/54/8/37/66` | next frontier. | Book49/math49, Book54 local pair/spine, and Chayenne/register frame remain controlled next probes. |

Next actions:

| Priority | Action | Target | Expected failure mode |
| --- | --- | --- | --- |
| `1` | `BOOK49_MATH49_EXACT_SOURCE_AUDIT` | `Q82_T05_BOOK49_MATH49_REGISTER` | 49 becomes a tempting Paradox/Mathemagica key without predicting local book behavior. |
| `2` | `BOOK54_PAIR_LOCAL_SPINE_AUDIT` | `Q82_T06_BOOK54_PAIR_LOCAL_SPINE` | local similarity reads like prose but fails controls outside the pair. |
| `3` | `CHAYENNE_FRAME_REGISTER_AUDIT` | `Q82_T08_CHAYENNE_FRAME_REGISTER` | external naming/shape match contaminates in-game evidence. |
| `4` | `HUMAN_ROUTE_EXPORT` | `HUMAN_ROUTE_ATLAS` | readable prose hides which claims are only shadow. |

Layer reading:

> The best human translation path is no longer a single attempted prose decode.
> It is a ranked route map: `R02/NAESE` is the strongest local phase-to-slot
> bridge; `Book7/Mathemagica` is the best operator-search route; `Q80` remains
> the most readable packet; `NAESE/BENNA` is held until a predictive rule or
> exact source appears.

Why this matters:
Q89 turns the last audit batch into a practical translation strategy. We now
have plausible human versions that are useful for reading and hypothesis
selection, while the promotion gate remains intact. The next concrete move is
Book49/math49, because it is the best chance to connect Paradox/49/94 operator
logic to an in-game book route without inventing a dictionary.

## Q90 Book49/Math49 Exact Source Audit

Latest SQLite run:
`Q90_BOOK49_MATH49_EXACT_SOURCE_AUDIT_OPERATOR_PRESSURE_NO_EXACT_BOOK49_GLOSS`.

Materialized by:
`scripts/sqlite_human_q90_book49_math49_exact_source_audit_v1.py`.

Question:
Can the self-contained `Book49` repeat shape be tied to a real in-game
`49`/Mathemagica operator strongly enough to promote a meaning?

Result:

- Q82 target executed: `Q82_T05_BOOK49_MATH49_REGISTER`.
- Target books: `1` (`49`).
- Web queries: `8`.
- Web exact Book49 sequence hits: `0`.
- Official exact target hits: `0`.
- Source checks: `14`.
- Mathemagica `49` source count: `2`.
- Exact Book49 sequence count: `0`.
- Exact meaning-relation count: `0`.
- Self-containment support count: `1`.
- Repeat rank: `1`.
- `+49` selector-audit count: `1`.
- `+49` holdout pass count: `0`.
- `49/94` control-block count: `1`.
- Calibration context count: `0`.
- Operator-reset context count: `0`.
- Lexical-ready candidates: `0`.
- Canonical promotion allowed: `0`.

Book-level human shadow:

| Book | Reading | Status |
| --- | --- | --- |
| `49` | Closed repeat/register formula that appears to bind or repeat itself. | preserve as repeat/register shadow only. |

Source checks:

| Source | Result | Blocked inference |
| --- | --- | --- |
| `A_PRISONER_MATHEMAGICS_TRANSCRIPT` | in-game transcript includes `1 + 1 = 49`. | no Book49, IAEN/NEEN, repeat-register, or 469 book meaning. |
| `BOOK49_SELFCONTAINMENT_GATE` | self-contained repeat formula audit-safe. | no word, sentence, spell, chant, calibration, or reset gloss. |
| `BOOK49_REPEAT_SHADOW` | repeat shadow supported, no gloss. | repeat rank does not make prose or a 49 dictionary key. |
| `BOOK49_RESIDUAL_NEGATIVE` | residual audit only, no gloss. | O32/NEEI/residual components stay audit-only. |
| `Q3_BOOK49_REGISTER_FUNCTION` | calibration/reset not supported. | no calibration or operator-reset context. |
| `MATHEMAGIC_PLUS49_WIDE_FRONTIER` | `+49` selector audit only. | no Book49 meaning. |
| `MATHEMAGIC_PLUS49_RANK13_HOLDOUT` | `+49` fails holdout. | no general decoding key or prose rule. |
| `MATHEMAGIC_49_94_WINDOW` | controls tie or beat. | no Book49 operator meaning. |
| `MATHEMAGIC_BOOK_MOD70_SENTINEL` | audit-only O32 guardrail. | no mod70 selector promotion. |
| `Q26_MATHEMAGIC_TRANSCRIPT_BRIDGE` | operator-only, no gloss. | no plaintext dictionary or Book49 phrase translation. |
| `Q27_MATHEMAGIC_OPERATOR_QUEUE` | operators reconciled, no gloss. | no operator word or Book49 gloss. |
| `PARADOX_TOWER_QUEST_SPOILER` | quest context support only. | no Book49 source or forced value. |
| `S2WARD_GREAT_CALCULATOR_CORPUS` | external corpus/method support only. | no in-game Book49 meaning anchor. |
| `TIBIASECRETS_HELLGATE_AVERAGE_ROUTE` | external numeric method pressure only. | no IAEN/NEEN promotion. |

Tests:

| Test | Status |
| --- | --- |
| `Q90_T01_WEB_EXACT_BOOK49_SEQUENCE` | fails exact-source requirement. |
| `Q90_T02_49_MATHEMAGIC_SOURCE` | supports operator pressure only. |
| `Q90_T03_INTERNAL_REPEAT_GATE` | preserves repeat/register shadow. |
| `Q90_T04_PLUS49_CONTROLS` | fails promotion controls. |
| `Q90_T05_CALIBRATION_RESET_GATE` | fails calibration/reset promotion. |
| `Q90_T06_PROMOTION_FIREWALL` | passes promotion block. |

Layer reading:

> Book `49` is a legitimate repeat/register witness, and `49` is a legitimate
> Mathemagica output. Q90 shows that those two facts are still not joined by an
> exact in-game source, a forced value, or a predictive `+49/mod70` rule. The
> correct human version is therefore "closed repeat/register formula", not
> "49-key translation".

Why this matters:
Q90 closes the most tempting medium target without losing the useful part of the
hypothesis. `49` remains valuable as operator pressure, but Book49 cannot be
promoted until a new source gives IAEN/NEEN sequence meaning or a heldout
`+49/mod70` test beats controls. The next Q82 target is
`Q82_T06_BOOK54_PAIR_LOCAL_SPINE`.

## Q91 Book54 Local-Pair Spine Exact Source Audit

Latest SQLite run:
`Q91_BOOK54_PAIR_LOCAL_SPINE_EXACT_SOURCE_AUDIT_LOCAL_PAIR_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q91_book54_pair_local_spine_exact_source_audit_v1.py`.

Question:
Can the `Book54` local-pair spine be confirmed outside its local alignment with
Book `20`?

Result:

- Q82 target executed: `Q82_T06_BOOK54_PAIR_LOCAL_SPINE`.
- Target books: `1` (`54`).
- Web queries: `6`.
- Web exact target hits: `0`.
- Official exact target hits: `0`.
- Source checks: `8`.
- Exact source-sequence count: `0`.
- Exact meaning-relation count: `0`.
- Shared block length: `25`.
- LCS ratio against shorter row: `0.8621`.
- Same-library count: `2`.
- Physical adjacency count: `0`.
- Independent pair-convention count: `0`.
- Promoted functional label count: `1`.
- Lexical-ready candidates: `0`.
- Canonical promotion allowed: `0`.

Book-level human shadow:

| Book | Reading | Status |
| --- | --- | --- |
| `54` | Shorter Book20/54 local-pair member with shared `LTFNTFEIFAIFAINIIETNEEIVN` spine and its own `ALN` tail. | preserve as local-pair spine shadow only. |

Source checks:

| Source | Result | Blocked inference |
| --- | --- | --- |
| `BOOK54_PAIR_SHADOW` | shared core with own tail, no gloss. | shared block, prefix, and tail are not lexical words or prose. |
| `BOOK20_54_LOCAL_PAIR_CONTEXT` | same library, not physically adjacent. | no independent in-game pair convention. |
| `PKG5_BOOK54_LOCAL_PAIR_FALSIFICATION` | functional local-pair label, no gloss. | plaintext and shared-block word glosses stay blocked. |
| `ZERO_PAIR_LOCAL_CONTEXT_GATE` | local context ready, no gloss. | zero-boundary/local-pair context cannot import semantic value. |
| `GREAT_CALCULATOR_COMPILED_CORPUS_SPINES` | compiled-corpus spine model support. | method compatibility is not exact Book54 meaning. |
| `RESIDUAL_LOCAL_PAIR_BRIDGE` | local-pair residual support, no gloss. | local pair/template controls are not independent prose. |
| `TIBIASECRETS_HELLGATE_AVERAGE_ROUTE` | external numeric method pressure only. | no Book54/shared-spine promotion. |
| `S2WARD_469_CORPUS` | external corpus structure support only. | external comparison is not in-game meaning. |

Tests:

| Test | Status |
| --- | --- |
| `Q91_T01_WEB_EXACT_BOOK54_SEQUENCE` | fails exact-source requirement. |
| `Q91_T02_LOCAL_PAIR_MECHANICS` | preserves functional pair label. |
| `Q91_T03_LOCATION_CONTEXT` | same-library only, not adjacent. |
| `Q91_T04_ZERO_PAIR_CONTEXT` | preserves context with no semantic import. |
| `Q91_T05_PROMOTION_FIREWALL` | passes promotion block. |

Layer reading:

> Book `54` is a strong local-pair/shared-spine witness with Book `20`; it is
> not just a random ending fragment. The current human wording can safely say
> "shorter local-pair member with own tail", but there is no exact source or
> independent in-game pair convention to turn the shared block into a meaning.

Why this matters:
Q91 preserves a useful human reading while closing the stronger promotion path.
The remaining Q82 target is `Q82_T08_CHAYENNE_FRAME_REGISTER`, which must be
handled with an external-frame firewall because its risk is contamination from
non-game naming/shape matches.

## Q92 Chayenne Frame Register Exact Source Audit

Latest SQLite run:
`Q92_CHAYENNE_FRAME_REGISTER_EXACT_SOURCE_AUDIT_EXTERNAL_FRAME_SUPPORT_NO_EXACT_BOOK_GLOSS`.

Materialized by:
`scripts/sqlite_human_q92_chayenne_frame_register_exact_source_audit_v1.py`.

Question:
Can the Chayenne-frame books be anchored inside game relationships rather than
external register shape only?

Result:

- Q82 target executed: `Q82_T08_CHAYENNE_FRAME_REGISTER`.
- Target books: `3` (`8/37/66`).
- Web queries: `8`.
- Web primary Chayenne hits: `1`.
- Web exact Book8/37/66 sequence hits: `0`.
- Official exact target hits: `0`.
- Source checks: `12`.
- Exact Chayenne sequence attestations already registered by Q2: `4`.
- Q44 frame books: `4` (`8/37/63/66`).
- External-shape accepted books: `4`.
- Target branch books: `3`.
- Audit-held books: `1` (`63`).
- Exact book-sequence count: `0`.
- Exact meaning-relation count: `0`.
- Explicit gloss count: `0`.
- Functional label count: `1`.
- Component gloss allowed: `0`.
- Lexical-ready candidates: `0`.
- Canonical promotion allowed: `0`.

Book-level human shadow:

| Book | Reading | Status |
| --- | --- | --- |
| `8` | Clean VNCTIIN-context branch carrying the Chayenne external frame as register/context material. | preserve as Chayenne frame branch, no plaintext. |
| `37` | LTAST/TTNVVN boundary-handoff branch leading into the same Chayenne frame and then VNCTIIN context. | preserve as Chayenne frame branch, no plaintext. |
| `66` | BENNA/LTAST formula branch carrying the same external frame. | preserve as Chayenne frame branch, no plaintext. |

Source checks:

| Source | Result | Blocked inference |
| --- | --- | --- |
| `PORTALTIBIA_CHAYENNE_2009_PRIMARY` | primary interview exact reply, no gloss. | primary provenance is not an in-game book gloss. |
| `TIBIAWIKI_469_CHAYENNE_CONTEXT` | Chayenne/Knightmare/Avar/context index. | no Chayenne reply or Book8/37/66 translation. |
| `A_WRINKLED_BONELORD_TRANSCRIPT` | in-game language/mathemagic method anchor. | no Chayenne frame or target-book mapping. |
| `AVAR_TAR_TRANSCRIPT` | in-game spoken 469-adjacent holdout. | no exact target relation or meaning. |
| `CHAYENNE_EXTERNAL_SHAPE_GATE` | `AEFIEIEFIIVFAEATVAT` frame confirmed. | explicit meaning and lexical gloss blocked. |
| `Q2_CHAYENNE_EXPLICIT_GLOSS_AUDIT` | exact sequence attested, frame only. | no plaintext promotion. |
| `Q44_CHAYENNE_REGISTER_FRAME_ATLAS` | register-frame atlas ready, no gloss. | no shared-block gloss or fixed sentence. |
| `PKG8_CHAYENNE_FUNCTIONAL_FALSIFICATION` | branch label promoted, no plaintext. | no component gloss or Book63 promotion. |
| `CHAYENNE_PRIMARY_SOURCE_SEARCH` | sources attest sequence, no explicit gloss. | community/context speculation cannot promote plaintext. |
| `CHAYENNE_EXACT_NEAR_CONTRAST` | structure promoted, no prose. | near/exact contrast blocks lexical prose. |
| `CHAYENNE_ROLE_BRIDGE_GATE` | context and handoff bridge, no plaintext. | mixed role support is structural only. |
| `CHAYENNE_TOPOLOGY_PROBE` | topology ready, no gloss. | multi-branch topology blocks one fixed sentence. |

Tests:

| Test | Status |
| --- | --- |
| `Q92_T01_WEB_EXACT_BOOK_SEQUENCES` | fails exact-book source requirement. |
| `Q92_T02_PRIMARY_CHAYENNE_REPLY` | preserves external provenance only. |
| `Q92_T03_INGAME_CONTEXT_ANCHORS` | preserves method context, no target gloss. |
| `Q92_T04_BRANCH_TOPOLOGY` | preserves register-frame label. |
| `Q92_T05_EXTERNAL_FRAME_FIREWALL` | blocks external shape to plaintext. |
| `Q92_T06_PROMOTION_FIREWALL` | passes promotion block. |

Layer reading:

> Books `8/37/66` form a valid Chayenne-frame/register branch set: `8` is the
> clean VNCTIIN context branch, `37` is the LTAST-to-VNCTIIN handoff, and `66`
> is the BENNA/LTAST formula branch carrying the same external frame. The
> Chayenne interview is strong external provenance, but no checked source gives
> an exact Book8/37/66 sequence plus meaning, so no plaintext is promotable.

Why this matters:
Q92 closes the last queued Q82 medium target without discarding its useful
signal. Chayenne should remain a source-quarantined frame/register witness and
not a phrase dictionary. The next route should export the Q90/Q91/Q92 blockers
into the human route atlas, then rank fresh non-Q82 exact-source routes.

## Q93 Human Route Atlas After Q90-Q92

Latest SQLite run:
`Q93_ROUTE_ATLAS_AFTER_Q90_Q92_READY_70_BOOKS_8_Q82_TARGETS_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q93_route_atlas_after_q90_q92_v1.py`.

Exports:

- `tmp/human_shadow_exports/q93_human_route_atlas_after_q90_q92_v1.md`
- `tmp/human_shadow_exports/q93_human_route_atlas_after_q90_q92_v1.json`

Question:
Can the flat Q81 70-book human shadow be converted into a route atlas after
Q90-Q92, with every book grouped by route, status, allowed reading, blocked
gloss, and next exact-source target?

Result:

- Exported books: `70`.
- Route groups: `32`.
- Q82 exact-source targets audited: `8/8`.
- Closed Q82 targets: `8`.
- Alive route groups: `4`.
- Closed medium route groups: `3`.
- Next action count: `5`.
- Promoted gloss count: `0`.
- Promotion status across exported books: `NOT_PROMOTED`.

Route-status distribution:

| Status | Groups | Books |
| --- | ---: | ---: |
| `ALIVE_PRIMARY_HUMAN_ROUTE` | `1` | `2` |
| `ALIVE_OPERATOR_DISCOVERY_ROUTE` | `1` | `1` |
| `ALIVE_PACKET_SHADOW_COMPONENT` | `2` | `5` |
| `HELD_COMPOSITE_SHADOW` | `1` | `2` |
| `CLOSED_MEDIUM_NO_GLOSS` | `2` | `2` |
| `CLOSED_MEDIUM_EXTERNAL_FRAME_NO_GLOSS` | `1` | `4` |
| `NEXT_IDEA_CORPUS_ROUTE` | `2` | `4` |
| `NEXT_IDEA_ENDPOINT_ROUTE` | `2` | `3` |
| `ATLAS_SHADOW_GROUP_NO_CURRENT_SOURCE_TARGET` | `20` | `47` |

Next route actions:

| Priority | Action | Books | Gate |
| --- | --- | --- | --- |
| `1` | `Q93_A01_R02_NEGATIVE_CONTROL_SOURCE_LADDER` | `51/53/45/46/14` | `51/53` must predict slot-bridge behavior better than `45/46/14` before prose. |
| `2` | `Q93_A02_BOOK7_OPERATOR_HELDOUT_SELECTOR_BENCHMARK` | `7/6/19/31/57/49` | A `3478/1/13/49/94` selector must beat controls on heldout books. |
| `3` | `Q93_A03_Q80_PACKET_SOURCE_AS_PACKET` | `35/67/2/27/10` | Search for packet-level source relation, not isolated component promotion. |
| `4` | `Q93_A04_BOOK30_GREAT_CALCULATOR_CORPUS_ROUTE` | `12/21/26/30` | Corpus/gathering relation must predict spine behavior and block endpoint import. |
| `5` | `Q93_A05_O23_ENDPOINT_SOUND_OR_DIALOG_ANCHOR` | `13/38/56` | Only exact in-game dialogue/book/sound relation may attach endpoint meaning. |

Layer reading:

> The human translation layer is now organized by route rather than by a flat
> list of 70 plausible readings. All Q82 exact-source targets have been audited,
> the medium routes are closed without gloss, and the next work shifts toward
> controlled route tests: R02/NAESE negatives, Book7/Mathemagica heldout
> selectors, Q80 as a packet-level source problem, Book30/Great Calculator as a
> corpus/gathering route, and O23 endpoint anchors.

Why this matters:
Q93 makes the current translation status more usable for human reasoning. It
prevents closed medium targets from being reopened by intuition alone, while
keeping the live paths visible. The project is still not solved: the completion
audit remains at `promoted_gloss_count=0`, so every route is still shadow,
operator, packet, corpus, or endpoint evidence rather than accepted plaintext.

## Q94 R02/NAESE Negative-Control Source Ladder

Latest SQLite run:
`Q94_R02_NAESE_NEGATIVE_CONTROL_SOURCE_LADDER_SPECIFIC_BRIDGE_WITH_BOOK46_WARNING_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q94_r02_naese_negative_control_source_ladder_v1.py`.

Question:
Does the strongest human route, `R02/NAESE`, survive local negative controls
before any phrase-level prose is attempted?

Result:

- Q93 action executed: `Q93_A01_R02_NEGATIVE_CONTROL_SOURCE_LADDER`.
- Positive books: `2` (`51/53`).
- Control books: `3` (`14/45/46`).
- Web queries: `8`.
- Web exact target hits: `0`.
- Official exact hits: `0`.
- Source checks: `8`.
- Exact source-sequence count: `0`.
- Exact meaning-relation count: `0`.
- Positive slot-bridge pass count: `2`.
- Control slot-bridge pass count: `0`.
- Control context-connector count: `1` (`46`).
- Control no-slot count: `2` (`14/45`).
- Boundary control count: `1` (`14`).
- Overbroad warning count: `1` (`46`).
- Specificity pass count: `1`.
- Lexical-ready candidates: `0`.
- Canonical promotion allowed: `0`.

Book ladder:

| Book | Role | Result | Human use |
| --- | --- | --- | --- |
| `51` | positive | ordered-core R02 slot bridge pass. | positive R02/NAESE phase-to-slot witness. |
| `53` | positive | ordered-core R02 slot bridge pass. | positive R02/NAESE phase-to-slot witness. |
| `14` | control | boundary/audit reject. | weak R02/LTAST boundary control, no slot proof. |
| `45` | control | prefix/no-slot reject. | R02/R20 prefix/context connector without NAESE/C68 continuation. |
| `46` | near-control | context-connector warning. | has NAESE/C68 material, but as connector support, not ordered-core bridge. |

Source checks:

| Source | Result | Blocked inference |
| --- | --- | --- |
| `Q87_R02_NAESE_EXACT_SOURCE_AUDIT` | structural bridge support, no exact source. | no R02/NAESE/C68 word gloss. |
| `R02_NAESE_SLOT_BRIDGE_GATE` | `2/2` positives pass. | structural pass is not sentence translation. |
| `R20_R02_NAESE_PHASE_GATE` | R02 specific with R20 warnings. | no global R/R20 meaning. |
| `BOOK45_R02_PREFIX_CONTROL` | R02 prefix control, no NAESE/C68. | prefix overlap is not a slot bridge. |
| `R02_LTAST_BOUNDARY_GATE` | boundary structural gate, no gloss. | Book14 is not R02/LTAST translation. |
| `Q81_CONTROLLED_SHADOW_EXPORT` | all five books remain `NOT_PROMOTED`. | readable shadow is not plaintext. |
| `Q93_ROUTE_ATLAS` | R02 ladder selected as next primary route. | priority does not weaken exact-source gates. |
| `AWB_LANGUAGE_MATHEMAGIC` | method anchor only. | no R02/NAESE sequence meaning. |

Tests:

| Test | Status |
| --- | --- |
| `Q94_T01_WEB_EXACT_SOURCE` | fails exact-source requirement. |
| `Q94_T02_POSITIVE_SPECIFICITY` | positives pass slot bridge. |
| `Q94_T03_CONTROL_REJECTION` | controls reject with Book46 warning. |
| `Q94_T04_OVERBROAD_RISK` | Book46 warning held. |
| `Q94_T05_PROMOTION_FIREWALL` | promotion blocked. |

Layer reading:

> Books `51/53` remain the strongest local human route: they carry the
> R02/TRVEIIVNTBB phase bridge into the NAESE/C68 slot frame. Books `14/45`
> reject the overbroad reading, while Book `46` is the important warning: it
> touches NAESE/C68 as a context connector, not as the ordered-core bridge. This
> keeps the route alive but blocks phrase-level prose.

Why this matters:
Q94 strengthens the human translation method by requiring local specificity.
The next step should not be a sentence translation of `R02` or `NAESE`; it
should be the Book7/Mathemagica heldout selector benchmark from Q93, because
operator prediction is the next plausible way to force value without inventing a
dictionary.

## Q95 Book7/Mathemagica Heldout Selector Benchmark

Latest SQLite run:
`Q95_BOOK7_OPERATOR_HELDOUT_SELECTOR_BENCHMARK_LOCAL_PHASE_SUPPORTED_NO_OPERATOR_HELDOUT_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q95_book7_operator_heldout_selector_benchmark_v1.py`.

Question:
Can `Book7/Mathemagica` use `3478` or the `1/13/49/94` outputs to predict
heldout books before any semantic claim?

Result:

- Q93 action executed: `Q93_A02_BOOK7_OPERATOR_HELDOUT_SELECTOR_BENCHMARK`.
- Target/control books: `6` (`7/6/19/31/57/49`).
- Phase positive books: `1` (`7`).
- Continuity controls: `1` (`6`).
- Phase-context controls: `3` (`19/31/57`).
- Repeat/register operator controls: `1` (`49`).
- Web queries: `8`.
- Web exact Book7 hits: `0`.
- Official exact target hits: `0`.
- Source checks: `14`.
- Exact source-sequence count: `0`.
- Exact meaning-relation count: `0`.
- Operator candidates: `4` (`1/13/49/94`).
- Operator source outputs: `4`.
- Live local operator count: `1` (`13`, outside Book7).
- Book7 operator-heldout pass count: `0`.
- Book7 local transition signal count: `1`.
- Book6/7 independent heldout count: `0`.
- Delta13 non-Book7 heldout pass count: `5`.
- `+49` holdout pass count: `0`.
- `49/94` window control-block count: `1`.
- Protected controls: `2` (`6/49`).
- Lexical-ready candidates: `0`.
- Canonical promotion allowed: `0`.

Book benchmark:

| Book | Role | Result | Human use |
| --- | --- | --- | --- |
| `7` | phase positive | local phase bridge supported, no operator heldout. | keep as Book7 phase-control route. |
| `6` | continuity control | continuity-only, no phase gloss. | protects Book7 from being reduced to NEIAAETTA continuity. |
| `19/31/57` | phase-context controls | VNCTIIN+TIINNEF phase context, no operator pass. | controls for TIINNEF in VNCTIIN context. |
| `49` | repeat/register operator control | repeat/register, `+49` blocked. | prevents 49/94 numerology from being promoted. |

Operator benchmark:

| Operator | Status | Scope | Block |
| --- | --- | --- | --- |
| `1` | context-only, no Book7 pass. | source output only. | cannot decode Book7 or controls. |
| `13` | live local outside Book7. | C86/C68 local operator only. | cannot be imported into Book7 phase material. |
| `49` | blocked general selector, audit-only. | narrow audit only. | cannot decode Book7 or Book49. |
| `94` | weak audit only, window blocked. | weak audit only. | cannot force Book7 value. |

Source checks:

| Source | Result | Blocked inference |
| --- | --- | --- |
| `Q88_BOOK7_MATHEMAGIC_AUDIT` | operator support, no exact source. | no exact Book7 meaning or forced value. |
| `BOOK7_PHASE_SHADOW` | bridge supported, no gloss. | no TIINNEF/NEIAAETTA definitions. |
| `Q4_BOOK7_PHASE_DIRECTION` | direction held, no gloss. | no internal direction or prose. |
| `Q8_BOOK6_7_3478_TRANSITION` | phase path supported, no payload gloss. | no 3478/Book6/Book7 payload words. |
| `Q9_BOOK6_7_HELDOUT_SUPPORT` | no independent heldout support. | Book6/7 remains local control. |
| `Q26_MATHEMAGIC_TRANSCRIPT_BRIDGE` | operator-only, no gloss. | Mathemagica is not a dictionary. |
| `Q27_MATHEMAGIC_OPERATOR_QUEUE` | only `13` live locally. | no operator is a Book7 gloss. |
| `MATHEMAGIC_OPERATIONAL_DECISION` | local operators only. | no general selector for Book7. |
| `DELTA13_HELDOUT` | C86/C68 operator stable. | not a Book7-family pass. |
| `PLUS49_RANK13_HOLDOUT` | `+49` fails holdout. | no Book7/Book49 selector. |
| `MATHEMAGIC_49_94_WINDOW` | controls tie or beat. | no forced Book7 value. |
| `A_PRISONER_TRANSCRIPT` | in-game Mathemagica outputs. | no Book7/Hellgate book meaning. |
| `A_WRINKLED_BONELORD_TRANSCRIPT` | in-game method anchor. | no TIINNEF/NEIAAETTA/Book7 gloss. |
| `TIBIAWIKI_469_MATHEMAGIC_CONTEXT` | Mathemagica context with warning. | context does not solve plaintext. |

Tests:

| Test | Status |
| --- | --- |
| `Q95_T01_WEB_EXACT_BOOK7` | fails exact-source requirement. |
| `Q95_T02_BOOK7_LOCAL_PHASE` | preserves Book7 phase control. |
| `Q95_T03_OPERATOR_HELDOUT_TARGET` | fails Book7 operator heldout. |
| `Q95_T04_DELTA13_SCOPE` | preserves delta13 outside Book7. |
| `Q95_T05_49_94_PLUS49_CONTROLS` | blocks `49/94` and `+49` promotion. |
| `Q95_T06_PROMOTION_FIREWALL` | promotion blocked. |

Layer reading:

> Book `7` remains useful, but not because it can be translated as a sentence.
> It is a phase-control bridge against Book `6` and the VNCTIIN/TIINNEF controls
> `19/31/57`. Mathemagica is still useful as operator-search machinery, but
> Q95 shows that `1/13/49/94` does not currently force Book7 value. The only
> strong operator, `13`, belongs to the C86/C68 route, not Book7.

Why this matters:
Q95 prevents the most tempting operator overreach. The project keeps the useful
part of Mathemagica while removing it as a Book7 dictionary path. The next
action should be Q93's packet-level source search: `Q93_A03_Q80_PACKET_SOURCE_AS_PACKET`.

## Q96 Q80 Packet Source-As-Packet Audit

Latest SQLite run:
`Q96_Q80_PACKET_SOURCE_AS_PACKET_AUDIT_PACKET_PATH_SUPPORT_NO_EXACT_SOURCE_NO_GLOSS`.

Materialized by:
`scripts/sqlite_human_q96_q80_packet_source_as_packet_audit_v1.py`.

Question:
Can the Q80 packet become stronger if `35/67/2` and heldout `27/67/2` are
audited as one packet-level source relation rather than separate components?

Result:

- Q93 action executed: `Q93_A03_Q80_PACKET_SOURCE_AS_PACKET`.
- Packet books: `5` (`35/67/2/27/10`).
- Primary path books: `3` (`35/67/2`).
- Heldout path books: `3` (`27/67/2`).
- Sibling formula controls: `2` (`10/35`).
- Web queries: `10`.
- Web exact packet hits: `0`.
- Official exact target hits: `0`.
- Source checks: `13`.
- Exact source-sequence count: `0`.
- Exact meaning-relation count: `0`.
- Q80 packet versions: `2`.
- Accepted primary packet count: `1`.
- Conditional heldout packet count: `1`.
- Component exact-source hit count: `0`.
- Packet-level exact-source hit count: `0`.
- Packet method-support count: `2`.
- Structural edge candidate count: `1`.
- Confirmed edge count: `0`.
- Source resolution count: `0`.
- Firewall-blocked candidate count: `5`.
- Lexical-ready candidates: `0`.
- Canonical promotion allowed: `0`.

Packet book roles:

| Book | Role | Result | Human use |
| --- | --- | --- | --- |
| `35` | primary formula-handoff start. | primary packet component, shadow only. | formula routes context. |
| `67` | primary/heldout handoff. | local edge component, shadow only. | handoff into payload/context path. |
| `2` | payload/context entry. | payload context entry, shadow only. | selected context enters slot frame. |
| `27` | heldout extension start. | structural missing-edge candidate, unconfirmed. | conditional heldout extension. |
| `10` | sibling formula-handoff control. | formula-handoff control, shadow only. | checks 35 against sibling formula behavior. |

Source checks:

| Source | Result | Blocked inference |
| --- | --- | --- |
| `Q80_PACKET_SHADOW` | primary `35->67->2`, heldout `27->67->2`, no gloss. | zero exact source and zero promotions. |
| `Q83_BENNA_C86_SOURCE_AUDIT` | method support, no exact source. | formula handoff cannot become plaintext. |
| `Q84_C86_VNCTIIN_SOURCE_AUDIT` | register support, no exact source. | payload corridor cannot become plaintext. |
| `Q85_CRITICAL_SYNTHESIS` | Q80 stable, promotion blocked. | packet readability cannot override failed components. |
| `Q73_27_TO_67_STRUCTURAL_EDGE` | strengthened structural missing edge. | no confirmed edge or sentence. |
| `Q74_27_TO_67_EXTERNAL_SEARCH` | no external confirmation. | internal matches are not independent source support. |
| `Q78_67_2_SOURCE_CONTINUITY` | method support, no exact phrase. | no Book67/Book2 sentence. |
| `Q79_GLOBAL_SOURCE_FIREWALL` | blocks all promotions. | no packet candidate is plaintext. |
| `YOU_CANNOT_EVEN_IMAGINE_BOOK` | Great Calculator assembly anchor. | corpus lore does not identify packet meaning. |
| `BEWARE_OF_THE_BONELORDS_BOOK` | language plus mathematics anchor. | general math/language lore does not translate `35/67/2`. |
| `TIBIASECRETS_HELLGATE_AVERAGES` | external arithmetic pressure. | not an in-game exact packet meaning. |
| `S2WARD_469_CORPUS` | external corpus alignment support. | no source-backed plaintext. |
| `A_WRINKLED_BONELORD_TRANSCRIPT` | method anchor only. | no exact packet meaning. |

Tests:

| Test | Status |
| --- | --- |
| `Q96_T01_WEB_EXACT_PACKET` | fails exact-source requirement. |
| `Q96_T02_COMPONENT_AUDITS` | components block promotion. |
| `Q96_T03_PACKET_LEVEL_REASSESSMENT` | preserves packet shadow only. |
| `Q96_T04_HELDOUT_EDGE` | `27->67` structural but unconfirmed. |
| `Q96_T05_SOURCE_FIREWALL` | passes global firewall. |
| `Q96_T06_PROMOTION_FIREWALL` | promotion blocked. |

Layer reading:

> The packet reading is still the best human prose-like route: `35` routes
> formula context, `67` carries the handoff, and `2` enters the payload/context
> slot. The heldout route `27->67->2` remains conditionally useful, and `10/35`
> checks formula-handoff behavior. But auditing the route as a packet does not
> create exact source evidence; it stays a controlled shadow.

Why this matters:
Q96 keeps the useful packet intuition but removes it as a shortcut to plaintext.
The next action should move to Q93's corpus/gathering route:
`Q93_A04_BOOK30_GREAT_CALCULATOR_CORPUS_ROUTE`.
