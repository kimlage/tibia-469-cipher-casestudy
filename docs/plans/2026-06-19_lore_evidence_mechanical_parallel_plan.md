---
title: "469 lore-driven evidence and mechanical hypothesis plan"
date: 2026-06-19
status: ready_to_execute
scope: evidence_search_and_mechanism_only
translation_delta: NONE
---

# 469 Lore-Driven Evidence and Mechanical Hypothesis Plan

This plan searches for **new evidence** and **new mechanical attempts inspired
by lore** without reopening free-form translation. Lore is used as a hypothesis
generator; promotion still requires source evidence, preregistered tests,
holdouts, controls, and MDL discipline.

## Operating Rule

Every candidate must be classified before analysis:

| Class | Meaning | Can move semantic verdict? |
|---|---|---|
| `official_gt` | CipSoft/in-game number-to-text, book-to-text, or symbol table | yes |
| `official_unglossed_numeric` | official/in-game number without meaning | no |
| `mechanism_lore` | lore suggesting how the artifact was made/rendered | no |
| `external_holdout` | external string usable for compatibility testing | no |
| `negative_control` | source that should not be covered by real 469 machinery | no |
| `watchlist_only` | official-adjacent source to monitor | no |
| `rejected` | fan solution, numerology, or unsupported claim | no |

No source may be promoted to translation unless it supplies official
number-to-plaintext, book-to-plaintext, or symbol-to-meaning evidence.

## Success Criteria

The objective is successful if one of these happens:

1. A new `official_gt` source is found and archived with source URL, date,
   screenshot/text evidence, and exact numeric/text alignment.
2. A new mechanical formula explains row0, render/orientation, or tape assembly
   below lookup cost and beats controls.
3. A source family is closed with an evidence-backed negative result, reducing
   future search space.

## Source Lanes by Community / Language

Each lane should search official sources first, then promoted/recognized
fansites, then archived community material. A non-English source is acceptable
only if the original text, translation, and source status are preserved.

| Lane | Languages / communities | Primary targets | Notes |
|---|---|---|---|
| `EN-international` | English / global official community | Tibia.com, official news, official forum archives, TibiaWiki EN, promoted fansites, Chayenne/YTC context | Main canonical lane for source status and cross-language reconciliation. |
| `PT-BR` | Brazilian / Portuguese community | TibiaWiki BR, TibiaBR-style fansites, Brazilian forum archives, Secret Library pages | Treat as P0 because `74032 45331` was confirmed through TibiaWiki BR. |
| `PL` | Polish community | Polish promoted fansites, old forum threads, event transcriptions | Important because Tibia has a large Polish community and many historical fansites. |
| `ES` | Spanish / LATAM community | Spanish fansites, old forum posts, translated quest/lore archives | Search for event/NPC transcription drift and old 469 summaries. |
| `DE` | German community | German fansites, old official/community archives | High risk because prior German/MHG solution was falsified; use only for source discovery, not linguistic promotion. |
| `Other-official/fansite` | Any other language with official/promoted Tibia community evidence | promoted fansite lists, official fansite programme references, archived fansite pages | Include only when source status is verifiable. |

For every lane, record:

```text
source_name
language
country/community
source_status: official | promoted_fansite | fansite | forum | unknown
url
archive_url
retrieval_date
raw_quote_or_transcription
translation_to_en_or_pt
numeric_strings
speaker/source
evidence_class
recommended_test
promotion_gate
```

## Lore-Inspired Mechanical Fronts

| Lore inspiration | Mechanical hypothesis | Test target | Required controls |
|---|---|---|---|
| Great Calculator / assemble | Books were assembled from pre-rendered numeric components | tape/module/literal formula, residual gaps | MDL vs current tape formula, held-out books, Avar Tar |
| Demona / Honeminas formula | Formula numbers act as selector/indexer, not plaintext | row0 placement, tape order, residual selection | digit-multiset controls, random same-length numbers, source-holdout |
| Tridiag / incomplete formula | Diagonal/E layer may be a partial worksheet rule | E cells, diagonal, 33/66, blockers | E-label shuffles, geometry-stratified controls |
| Donina / red light / controller | Render/priority layer controls what is visible | zero omission, 19/91, 39/93, orientation | book holdout, pair holdout, render feature ablation |
| Magic Web / gates / destination | Gate/destination numbers select paths or modules | module order, tape spans, source/destination endpoints | endpoint holdout, bridge holdout, random gate vectors |
| Subjective viewer | Viewer changes orientation/render, not meaning | ab/ba, upper/lower mirror, 6/9, zero | pair holdout, ordered-code shuffle |
| Eyes/blink language | Eye count defines arity/channel count | K5, 5x2, alternate arities, source classifier | digit-label shuffles, 4/6/7/10-eye controls |
| Secret Library `74032 45331` | External unglossed numeric anchor | external classifier, substring/LCS/module compatibility | same-length random controls |
| Chayenne | External copy/module compatibility | module-copy holdout | Avar Tar and YTC controls |
| Paradox / mirror books | Style/control for fake hidden text | false-positive calibration | non-469 gibberish controls |
| Spirit Grounds / Gate Keeper | Weird language + gate is not enough | negative-control classifier | must remain no-promotion unless numeric official GT appears |
| Evil Mastermind fake dictionaries | In-lore warning against overfit dictionaries | process guard | reject dictionary-like claims without source GT |
| Dreadeye / difficulty | Communication may be alien/multilayered | source-class context | no direct formula promotion |
| First Dragon memoir hooks | Future official source may reveal new text | watchlist | official-source gate only |

## Execution Phases

### Phase 1 — Source Discovery

- Search each language/community lane for `469`, `Bonelord`, `Beholder`,
  `Bonelord language`, `469 language`, `Secret Library`, `Demona`,
  `Honeminas`, `Magic Web`, `A Wrinkled Bonelord`, `Evil Eye`, `Elder
  Bonelord`, `First Dragon`, and equivalent local-language terms.
- Preserve original snippets and translations.
- Do not trust fan claims; extract only source leads and numeric strings.
- Flag every source as official, promoted fansite, community, archive, or
  unknown.

### Phase 2 — Evidence Registry

- Build a table of all found sources.
- Deduplicate cross-language copies.
- Split primary source from translation/summary.
- Extract all numeric strings of length >= 3.
- Mark each source as `official_gt`, `official_unglossed_numeric`,
  `mechanism_lore`, `external_holdout`, `negative_control`, `watchlist_only`,
  or `rejected`.

### Phase 3 — Hypothesis Generation

- For every `mechanism_lore` source, write exactly one testable hypothesis.
- State the dependent variable before running anything:
  - row0 label prediction
  - row0 anomaly prediction
  - render/orientation prediction
  - tape/module/literal compression
  - external string classification
  - source-class discrimination
- Define stop rules before testing.

### Phase 4 — Mechanical Tests

- Run only tests that target a named open axis:
  - matrix origin
  - assembly origin
  - render/orientation
  - external truth/classifier
- Compare against current baseline:
  - `mechanical_origin_model_v1`
  - `tape_based_formula_469.json`
  - row0 pair table
  - existing K5/5x2 rejection
  - existing E/zero/render audits
- Use controls:
  - inventory-preserving label shuffle
  - digit-label shuffle
  - source-number same-length random controls
  - Avar Tar negative control
  - YTC/Secret Library as external unknown/anchor controls
  - book holdout and pair holdout when possible

### Phase 5 — Integration

- Promote only three result types:
  - `official_gt_found`
  - `mechanical_formula_improved`
  - `source_family_closed_negative`
- Do not promote:
  - short overlaps
  - post-hoc lore matches
  - high hit count with high rule cost
  - fan translations
  - any plaintext without official evidence

## Parallel Codex Prompts

Use these as independent Codex tasks. Each task should be read-only unless you
explicitly decide to integrate evidence after review.

### Prompt 1 — EN / International Source Lane

```text
Work in /Users/sargam/Documents/Developer/tibia-469-cipher-casestudy.
Goal: search English/international official and promoted-fansite sources for new 469/Bonelord evidence.
Do not edit files. Build a source table in your response.

Search targets: Tibia.com, official news/forums if accessible, TibiaWiki EN, promoted fansites, archived community pages.
Keywords: 469, Bonelord language, Beholder language, A Wrinkled Bonelord, Secret Library, Demona, Honeminas, Magic Web, Evil Eye, Elder Bonelord, First Dragon.

For each source, classify as official_gt, official_unglossed_numeric, mechanism_lore, external_holdout, negative_control, watchlist_only, or rejected.
Extract numeric strings and propose one mechanical test only if the source is mechanism_lore or stronger.
Do not propose plaintext unless the source itself gives number-to-text or book-to-text ground truth.
```

### Prompt 2 — PT-BR Source Lane

```text
Work in /Users/sargam/Documents/Developer/tibia-469-cipher-casestudy.
Goal: search Portuguese/Brazilian Tibia sources for new 469/Bonelord evidence.
Do not edit files. Build a source table in your response.

Prioritize TibiaWiki BR, Brazilian fansites, archived forum posts, Secret Library pages, update pages, and in-game book/NPC transcriptions.
Keywords: 469, Bonelord, Beholder, linguagem Bonelord, biblioteca, Secret Library, Demona, Honeminas, Magic Web, A Wrinkled Bonelord, Evil Eye, Elder Bonelord, First Dragon.

Treat PT-BR as P0 because 74032 45331 was source-confirmed there.
For every source, preserve original Portuguese text, English/PT summary, numeric strings, source status, and classification.
No fan translation can be promoted without official/in-game ground truth.
```

### Prompt 3 — PL Source Lane

```text
Work in /Users/sargam/Documents/Developer/tibia-469-cipher-casestudy.
Goal: search Polish Tibia community/fansite sources for 469/Bonelord evidence.
Do not edit files. Build a source table in your response.

Prioritize promoted/recognized fansites, old Polish forum archives, quest/lore transcriptions, NPC transcripts, and update summaries.
Search Polish and English terms: 469, Bonelord, Beholder, język Bonelordów, biblioteka, Sekretna Biblioteka, Demona, Honeminas, Magic Web.

Extract numeric strings, translate relevant snippets, classify evidence, and propose mechanical tests only for mechanism_lore or stronger sources.
```

### Prompt 4 — ES Source Lane

```text
Work in /Users/sargam/Documents/Developer/tibia-469-cipher-casestudy.
Goal: search Spanish/LATAM Tibia sources for 469/Bonelord evidence.
Do not edit files. Build a source table in your response.

Prioritize Spanish fansites, old forum archives, quest/lore pages, NPC transcripts, and update/event pages.
Keywords: 469, Bonelord, Beholder, idioma Bonelord, lenguaje Bonelord, biblioteca, Secret Library, Demona, Honeminas, Magic Web, Evil Eye, Elder Bonelord.

Preserve original text and translation. Classify sources by evidence gate. No plaintext promotion without official number-to-text evidence.
```

### Prompt 5 — DE Source Lane

```text
Work in /Users/sargam/Documents/Developer/tibia-469-cipher-casestudy.
Goal: search German Tibia sources for source evidence only, not for German-language decoding.
Do not edit files. Build a source table in your response.

Prioritize official/promoted fansites, old forum archives, quest/lore pages, and NPC/book transcripts.
Keywords: 469, Bonelord, Beholder, Bonelord Sprache, Beholder Sprache, Bibliothek, Geheime Bibliothek, Demona, Honeminas, Magic Web.

Important: prior German/MHG solution routes are falsified. Use this lane only to find primary source leads, numeric strings, or official/in-game evidence. Do not promote German readings.
```

### Prompt 6 — Other-Language / Official Fansite Lane

```text
Work in /Users/sargam/Documents/Developer/tibia-469-cipher-casestudy.
Goal: identify any other official/promoted Tibia community language lanes that may contain 469/Bonelord evidence.
Do not edit files. Build a source table in your response.

Start by finding current and historical official/promoted fansite lists. For each language/community found, search only high-trust sources first.
Extract source status, language, numeric strings, original text, translation, and evidence class.
Reject unsupported fan claims. Promote only official/in-game ground truth or mechanism-lore leads.
```

### Prompt 7 — Lore-to-Mechanism Hypothesis Compiler

```text
Work in /Users/sargam/Documents/Developer/tibia-469-cipher-casestudy.
Goal: compile lore sources into new mechanical hypotheses, not translations.
Do not edit files. Use local reports as baseline.

For each lore family, produce: inspiration, mechanical hypothesis, target variable, required input data, expected output, controls, stop rule.
Families: Great Calculator/assemble, Demona/Honeminas, Tridiag, Donina/red light, Magic Web/gates, subjective viewer, eyes/blink, Secret Library, Chayenne, Paradox, Spirit Grounds, Evil Mastermind, Dreadeye, First Dragon.

Reject any hypothesis that cannot name a test target among: row0 placement, render/orientation, tape/module assembly, residual compression, external-string classification, source-class discrimination.
```

### Prompt 8 — Formula-Origin Attack Plan

```text
Work in /Users/sargam/Documents/Developer/tibia-469-cipher-casestudy.
Goal: design the next formula-origin tests inspired by lore, using current rejected/accepted reports as constraints.
Do not edit files. Produce a ranked test plan.

Allowed axes: row0 pair-cell placement, tape/module/literal assembly, render/orientation exceptions, E/zero/diagonal bridge, 6<->9 quotient.
Required: explain what existing reports already reject, what new input would make the test non-duplicative, what controls are mandatory, and what result would count as progress.

Do not include semantic translation attempts.
```

## Consolidation Prompt

Run this after the parallel lanes return:

```text
Work in /Users/sargam/Documents/Developer/tibia-469-cipher-casestudy.
Goal: consolidate parallel source-lane results into a single evidence registry and next-test shortlist.

Inputs: outputs from EN, PT-BR, PL, ES, DE, other-language, lore-hypothesis, and formula-origin tasks.
Deduplicate sources, preserve original language snippets, classify every source, extract numeric strings, and rank candidates.

Output:
1. official_gt candidates, if any;
2. mechanism_lore candidates with tests;
3. external_holdout / numeric_anchor candidates;
4. rejected fan claims;
5. top 5 next mechanical tests;
6. stop/no-go list.

Do not promote plaintext unless official source evidence proves it.
```

## Final Decision Gate

After consolidation, continue only if at least one condition is true:

- There is a new official/in-game source.
- There is a new external numeric string with reliable provenance.
- There is a new lore-derived mechanical hypothesis that is not already covered
  by existing reports and has clear controls.
- There is a credible way to reduce current formula complexity below the
  `mechanical_origin_model_v1` baseline.

Otherwise, record the result as a negative evidence-search pass and keep the
case closed.

---

# Knightmare / D&D / Source-Inspiration Extension

This extension incorporates the operational glossary and source-inspiration
plan from:

```text
/Users/sargam/Downloads/469_source_inspiration_glossary_knightmare_dnd_codex_plan_2026-06-19.md
```

It expands the execution objective from "find new sources" to:

```text
build a testable source-inspiration library for Knightmare, D&D/Beholder,
quest mechanisms, numeric identity anchors, and 469 mechanism hypotheses.
```

It still does **not** create translation, book-decoder, symbol-letter mapping,
or code-word claims without official CipSoft/in-game ground truth.

## Evidence Confidence Levels

| Level | Use |
|---|---|
| `CONFIRMED_SOURCE` | Primary/in-game/transcript/wiki source with direct text. |
| `AUTHORIAL_DIRECT` | Knightmare speaks about his own work or authorship. |
| `AUTHORIAL_ASSOCIATED` | Quest/area/theme mentioned by Knightmare or strongly associated with his design style. |
| `MECHANISM_CORPUS` | Quest/lore used as mechanical comparandum without authorship claim. |
| `DND_PARALLEL` | Public D&D Beholder mechanism used as candidate inspiration. |
| `PAREIDOLIA_RISK` | Numerology or similarity without source/control. |

## Base Source Corpus

| Source | Source status | Useful facts | 469 use |
|---|---|---|---|
| Knightmare profile | `AUTHORIAL_ASSOCIATED` | Arndt Bednarzik; Content Team; game content designer; former gamemaster/map developer/quest designer | Authorial pattern corpus for puzzles, cities, quests, NPCs, libraries, and meta-jokes. |
| Knightmare NPC transcript | `AUTHORIAL_DIRECT` / `CONFIRMED_SOURCE` | "world-builder, god, sage, storyteller"; background creation; old NPC spellcasting by keywords; Excalibug language gate; sound `3478 67 90871 97664 3466 0 345!`; dice 1..99 | Phrase-layer as keyword/trigger; Excalibug route; numeric identity anchors; 99-code analogy. |
| D&D Beholder | `DND_PARALLEL` | Central eye, eyestalks, eye rays, variants, product identity | 10 channels/digits, central-eye zero/suppression, viewer identity, Beholder -> Bonelord rename context. |
| Tibia Beholder -> Bonelord | `CONFIRMED_SOURCE` / historical context | Rename indicates D&D/product-identity pressure | Supports Beholder substrate, not decoding. |
| `3478` / Bonelord (Nostalgia) | `CONFIRMED_SOURCE` | `3478` as Bonelord/Nostalgia identity anchor; event creature; old Beholder relation | Numeric identity anchor, not automatically a word key. |
| A Wrinkled Bonelord | `CONFIRMED_SOURCE` | `486486`; `1` = Tibia; `0` taboo; enough eyes to blink 469; subjective viewer; minotaur mages close to truth | Identity anchors, zero taboo, eye/blink arity, render/view transform, watchlist formula route. |
| Bonelord Tome | `MECHANISM_CORPUS` / meta-lore | Weight `46.90`; sounds with `3478`, `486486`, eyes, TibiaSecrets | High-value lore anchor, not translation GT. |
| Beware of the Bonelords | `CONFIRMED_SOURCE` | Blinking code with each eye; blink may mean syllable/letter/word; language + mathematics | Variable granularity: phrase-layer word-code, book-layer symbol/code, mechanical lookup origin. |

## Knightmare Quest / Mechanism Corpus

This is not an authorship claim for every quest. It is a mechanical-comparandum
library. Each source must retain its confidence level.

| Quest / area | Mechanisms to extract | Candidate 469 crosswalk | Planned audit |
|---|---|---|---|
| Thais | NPC rewriting, base city, historical memory | source-layer rewriting / NPC keyword conventions | `knightmare_design_corpus.yaml` |
| Kazordoon | mountain city, hidden culture, dwarven culture | hidden/cultural encoding, city-as-container | `quest_mechanism_ontology.yaml` |
| Carlin | NPC/culture/history construction | NPC/culture as data layer | `quest_mechanism_ontology.yaml` |
| Ab'Dendriel | black pyramid relocation, dragon cemetery | relocation/recombination motifs | `quest_mechanism_ontology.yaml` |
| Venore | draft reuse, swamp/pyramid | source reuse and recombination | `quest_mechanism_ontology.yaml` |
| Edron | compact premium multi-level area | compact multi-layer design | `quest_mechanism_ontology.yaml` |
| Liberty Bay | discarded magic version, mythology recombination | source inspiration vs actual origin | `source_attribution_confidence.md` |
| Port Hope | ape theme, perceived King Kong coincidence | inspiration perception controls | `source_attribution_confidence.md` |
| Ankrahmun | desert/pyramid/necromancy context | Serpentine/Demona/Pyramid overlap | `serpentine_partial_quest_mechanism_audit.py` |
| Darashia | landmass, transport limits, hints | access/hint/transport constraints | `quest_gate_mechanism_ontology.py` |
| Svargrond | partial authorship, boss/ice dragon context | authorship confidence controls | `source_attribution_confidence.md` |
| Yalahar | quarters, mechanisms, factions, advanced decay | pair-table blocks, module/tape components, source/literal spans | `yalahar_quarter_block_model.py` |
| Farmine/Zao | staged unlock, foreign base, lizard context | progression / source classifier / constructed-language comparandum | `zao_lizard_speech_control.py` |
| Rookgaard | tutorial/safe haven/challenge calibration | gated learning / basic puzzle controls | `quest_mechanism_ontology.yaml` |
| Pits of Inferno | key 3700, blood/oil, vocation gates, thrones, maze, ritual order | 7 vs 10 vs 14 layers, module order, symbol order, role gates | `poi_throne_order_motif_test.py` |
| Dreamer's Challenge | factions, dream realm, teleports, Nightmare/Bones duality | phrase/book split, shared B/E/A then divergence, viewer identity | `dreamer_duality_layer_split_test.py` |
| The Inquisition | mission chain, boss sequence, PoI dependency, purifier/banish | module dependency graph, containment chains, residual chains | `inquisition_dependency_chain_audit.py` |
| Children of the Revolution / Zao | altered speech, staged tasks, military/faction progress | constructed-language control, source classifier | `zao_lizard_speech_control.py` |
| Secret Library | books as entities, knowledge theft, external numeric anchor | book-as-object model, `74032 45331` classifier | `secret_library_numeric_anchor_classifier.py` |
| Paradox Tower | paradox arithmetic, Riddler, entrance puzzle, mirror/viewer logic | render/motif controls, not plaintext | `paradox_arithmetic_operator_registry.py` |
| Serpentine Tower | forcefield, partial/unfinished mechanism, papers, tower/pyramid | partial mechanisms and source-status controls | `serpentine_partial_quest_mechanism_audit.py` |

## Operational Mechanism Glossary

| Term | Definition | 469 use | Status |
|---|---|---|---|
| `Beholder` | D&D multi-eyed creature; old Bonelord substrate | visual/mechanical inspiration substrate | source-inspiration only |
| `Bonelord` | Tibia post-rename creature | final Tibia lore layer | source-inspiration only |
| `3478` | Bonelord/Nostalgia; phrase token; formula overlap | numeric identity anchor | not a plaintext key |
| `486486` | A Wrinkled Bonelord's name | identity/formula anchor | not a plaintext key |
| `central eye` | central/suppressive Beholder channel | zero / `*` / omission candidate | planned |
| `eyestalk` | peripheral eye channel | digit/channel candidate | planned |
| `eye ray` | eye action/channel | homophone/channel candidate | planned |
| `10 eye rays / d10 channel` | D&D-style 10-channel Beholder mapping | digits `0..9`, homophone inventory, pair table | not yet tested enough |
| `central eye / anti-magic cone` | separate suppressive central-eye effect | `0` taboo, `00 -> *`, leading-zero omission, mask symbol | zero tested, D&D framing open |
| `subjective viewer` | observer changes formula/name | render transform: ab/ba, 19/91, 39/93, 6/9, zero | partially tested |
| `numeric identity anchors` | numbers as names/entities | `3478`, `486486`, `1`, `0`, identity graph motifs | open as source-integrated audit |
| `NPC keyword` | spoken keyword triggers script/action | phrase-layer as trigger, not sentence | open |
| `Excalibug` | secret Knightmare would discuss in Bonelord language | possible language-gated route | open; no plaintext promotion |
| `keys / levers / doors / forcefields` | quest access mechanics | strings as recipes/gates/selectors | open ontology |
| `dream/faction duality` | Dreamer/Nightmare/Bones split | phrase/book layer split analogy | speculative |
| `throne / seven sins / ordered ritual` | PoI/Ruthless Seven order/gates | module/tape/symbol ordering, 7/14 relation | open |
| `city quarters / mechanism unlocks` | Yalahar city structure | pair-table blocks, module components | open |
| `book/library as entity` | Secret Library / books-as-objects | books as mechanical artifacts, not prose | partially supported |
| `random dice / 1..99` | Knightmare dice game accepts 1..99 gold; roll 6 wins 5x | 99 codes / missing code / stochastic inventory analogy | high-risk control only |
| `Great Calculator` | assembly source | module/tape assembly framing | accepted mechanism-lore |
| `Magic Web` | gates/coordinates/formulas | selector/render model | direct seed rejected |
| `zero taboo` | `0` is obscene | zero/suppression layer | supporting clue |
| `1 = Tibia` | digit/world anchor | structural hint only | not formula |
| `Avar Tar` | false/non-469 control | negative control | keep as control |

## Inspiration Model Implementation Target

The full execution should create:

```text
analysis/inspiration_model_20260620/
  README.md
  source_registry.yaml
  dnd_beholder_mechanism_registry.yaml
  knightmare_design_corpus.yaml
  quest_mechanism_ontology.yaml
  source_inspiration_glossary.md
  source_attribution_confidence.md
  tests/
    01_build_source_corpus.py
    02_extract_quest_mechanisms.py
    03_dnd_eye_ray_d10_channel_test.py
    04_central_eye_zero_suppression_test.py
    05_subjective_viewer_render_transform_suite.py
    06_npc_keyword_trigger_mechanism_audit.py
    07_excalibug_bonelord_language_anchor_audit.py
    08_numeric_identity_key_seed_search.py
    09_yalahar_quarter_block_model.py
    10_dreamer_duality_layer_split_test.py
    11_poi_throne_order_motif_test.py
    12_library_entity_ontology_crosswalk.py
    13_authorial_source_classifier.py
  reports/
    source_corpus_report.md
    mechanism_crosswalk_report.md
    inspiration_model_leaderboard.md
    final_inspiration_model_report.md
```

## Required Registries

### `source_registry.yaml`

Required fields:

```yaml
id:
title:
source_url:
source_type:
confidence:
authorial_attribution:
relation_to_knightmare:
relation_to_469:
mechanisms:
numbers:
keywords:
risk_level:
allowed_use:
blocked_use:
```

### `dnd_beholder_mechanism_registry.yaml`

Minimum entries:

```yaml
beholder_10_eyestalks:
  mechanism: "10 peripheral eye channels"
  469_target: ["digits_0_9", "homophone_inventory", "pair_table"]
  status: "planned"

central_eye:
  mechanism: "suppression / anti-magic / central gaze"
  469_target: ["zero", "mask_symbol", "zero_omission"]
  status: "planned"

beholder_variants:
  mechanism: "entity-specific formulas / viewer variants"
  469_target: ["numeric_identity", "subjective_viewer", "source_classifier"]
  status: "planned"

xenophobia_identity:
  mechanism: "identity/self-name variation"
  469_target: ["3478", "486486", "subjective_name_formula"]
  status: "planned"
```

### `knightmare_design_corpus.yaml`

Minimum entries:

```yaml
knightmare_npc_transcript:
  mechanisms:
    - world_builder_statement
    - npc_keyword_spellcasting
    - early_runes
    - old_keys
    - city_design
    - excalibug_language_gate
    - dice_1_99
    - 3478_phrase

paradox_tower:
  mechanisms:
    - riddle_entrance
    - paradox_math
    - godhood/death
    - tower

serpentine_tower:
  mechanisms:
    - forcefield_activation
    - possible_continuation
    - ankrahmun_pyramid_context

pits_of_inferno:
  mechanisms:
    - key_3700
    - blood_access
    - oil_bridge
    - vocation_gate
    - seven_thrones
    - maze

dreamers_challenge:
  mechanisms:
    - faction_duality
    - dream_realm
    - teleport_network

yalahar:
  mechanisms:
    - city_quarters
    - mechanism_unlocks
    - decision/faction
    - decaying_advanced_race

secret_library:
  mechanisms:
    - books_as_entities
    - knowledge_theft
    - external_numeric_anchor
```

## Detailed Test Specs

### `03_dnd_eye_ray_d10_channel_test.py`

Question: does row0 or digit distribution look derived from 10 fixed channels,
as in Beholder eyestalks/eye-rays?

Features:

```text
digit index
digit frequency
first/second position bias
pair-cell symbol
homophone class size
zero omission rate
orientation ab/ba
```

Models:

```text
natural_order_0_9
D&D_order_if_supplied_as_metadata
random_permuted_eye_order
frequency_rank_order
symbol_frequency_order
```

Controls:

```text
10! digit permutations sampled
inventory-preserving label shuffles
random 10-channel ontologies
```

Accept only if it beats random digit-order controls and compresses at least one
named layer without plaintext claims.

### `04_central_eye_zero_suppression_test.py`

Question: does zero behave like a central-eye/suppression channel?

Targets:

```text
0 as obscene
00 -> *
leading zero omission
zero-context omission
mask symbol placement
0 in phrase-code as homophone for "a"
```

Models:

```text
central_eye = 0
central_eye = 1
central_eye = any digit d
central_eye = missing 39 / orphan 93 relationship
```

Controls:

```text
digit relabel
code-preserving zero shuffle
source-layer split
```

### `05_subjective_viewer_render_transform_suite.py`

Question: does the subjective viewer alter rendering/orientation?

Targets:

```text
ab/ba mirror
19/91 conflict
39 missing / 93 orphan
6<->9 quotient
zero omission
previous-code context
Bonelord Tome two-eyed line
```

Models:

```text
mirror
rotate_180
swap_6_9
upper_lower_view
left_right_eye_view
central_eye_suppression
phase_by_numeric_identity_key
```

Controls:

```text
label shuffle
digit permutation
random same-complexity transforms
```

### `06_npc_keyword_trigger_mechanism_audit.py`

Question: is the phrase-layer better modeled as keyword/spell trigger?

Sources:

```text
Knightmare phrase
The Evil Eye
Elder Bonelord
A Wrinkled Bonelord
Bonelord Tome
Avar Tar negative
```

Features:

```text
utterance context
speaker
keyword prompt
numeric string
known phrase-code segmentation
component reuse
book-layer compatibility
```

Output:

```text
phrase_layer_trigger_report.md
```

### `07_excalibug_bonelord_language_anchor_audit.py`

Question: does Knightmare's "ask me in Bonelord language" Excalibug line point
to a testable route?

Tests:

```text
search Excalibug / sword / weapon / inferior species / Knightmare in 469 corpus
test phrase-code generation possibilities
test 3478/486486/Bonelord Tome co-location with Excalibug
compare against controls
```

Blocker:

```text
No accepted Excalibug translation without official gloss.
```

### `08_numeric_identity_key_seed_search.py`

Question: do `3478` or `486486` act as mechanism seeds/selectors?

Targets:

```text
pair-table placement
symbol order
homophone fill
orientation
zero omission
module/tape order
external string classification
```

Seeds:

```text
3478
486486
486
3478468486
4864863478
74032
45331
469
```

Controls:

```text
same-length random seeds
digit-multiset matched seeds
lore decoy seeds
source-negative seeds
```

### `09_yalahar_quarter_block_model.py`

Question: does the "city in quarters/mechanisms" style explain table/module
blocks?

Targets:

```text
row/column blocks
high-block E layer
module/tape components
source/literal spans
```

### `10_dreamer_duality_layer_split_test.py`

Question: does Dreamer/Nightmare/Bones duality help explain the two 469 layers?

Targets:

```text
phrase vs book split
B/E/A shared then diverged
two-cipher separation
external strings
```

### `11_poi_throne_order_motif_test.py`

Question: do ritual/order/thrones/vocation gates explain any 469 ordering?

Targets:

```text
module order
tape slices
book order
symbol order
14 symbols vs 7 pairs
```

### `12_library_entity_ontology_crosswalk.py`

Question: does book-as-entity/object help classify 469?

Targets:

```text
70 books
Secret Library
Bonelord Tome
Beware of Bonelords
Great Calculator
module/tape formula
```

### `13_authorial_source_classifier.py`

Question: which layer does a new 469-adjacent source belong to?

Classes:

```text
book_layer_2digit
phrase_trigger
numeric_identity
formula_lore
external_numeric_anchor
copy_holdout
negative_control
quest_mechanism_comparandum
```

Inputs:

```text
Chayenne
YTC
Avar Tar
Bonelord Tome
Secret Library 74032 45331
2020 poll
Knightmare NPC phrase
A Wrinkled Bonelord lines
```

## Prioritized Inspiration Hypotheses

| ID | Hypothesis | Priority | Status | Scripts |
|---|---|---|---|---|
| `H19` | D&D Beholder eye-ray structure inspired a 10-channel digit system. | P0 | not tested | `03_dnd_eye_ray_d10_channel_test.py`, `04_central_eye_zero_suppression_test.py` |
| `H20` | `0` / `*` / omitted zero may encode central-eye or suppression channel. | P0 | zero tested, D&D framing open | `04_central_eye_zero_suppression_test.py` |
| `H21` | 469 reuses authorial mechanisms visible in Knightmare quest design: keys, levers, gates, roles, teleport networks, factions, books, riddles. | P0/P1 | not systematically tested | `02_extract_quest_mechanisms.py`, `13_authorial_source_classifier.py` |
| `H22` | Knightmare's Excalibug line is a scoped language-gated route. | P1 | not modernly tested | `07_excalibug_bonelord_language_anchor_audit.py` |
| `H23` | Dreamer/Bonelord dualities may explain why phrase-layer and book-layer share seed but diverge. | P2 | speculative | `10_dreamer_duality_layer_split_test.py` |
| `H24` | 469 books are better modeled as knowledge objects/entities than messages. | P1 | partially supported | `12_library_entity_ontology_crosswalk.py` |

## Inspiration-Model Codex Prompt

Use this prompt to execute the Knightmare/D&D extension as its own parallel
goal or subagent:

```text
Work in /Users/sargam/Documents/Developer/tibia-469-cipher-casestudy.

Execute the Knightmare / D&D / Source-Inspiration Extension in docs/plans/2026-06-19_lore_evidence_mechanical_parallel_plan.md.

Goal: build and test a source-inspiration library for Tibia 469 using Knightmare authorial/style evidence, D&D/Beholder mechanics, quest mechanism ontology, numeric identity anchors, and lore-to-mechanism hypotheses.

Hard rules:
- Do not create or promote plaintext, book translation, symbol-letter mapping, or code-word mapping.
- Promote semantic progress only with official CipSoft/in-game number-to-text, book-to-text, or symbol-to-meaning evidence.
- Lore can inspire tests, but every test needs target, controls, and stop rule.
- Compare against existing accepted/rejected 469 reports before claiming novelty.

Required outputs:
1. analysis/inspiration_model_20260620/source_registry.yaml
2. analysis/inspiration_model_20260620/dnd_beholder_mechanism_registry.yaml
3. analysis/inspiration_model_20260620/knightmare_design_corpus.yaml
4. analysis/inspiration_model_20260620/quest_mechanism_ontology.yaml
5. analysis/inspiration_model_20260620/source_inspiration_glossary.md
6. analysis/inspiration_model_20260620/source_attribution_confidence.md
7. tests for H19-H24 where feasible
8. reports/source_corpus_report.md
9. reports/mechanism_crosswalk_report.md
10. reports/inspiration_model_leaderboard.md
11. reports/final_inspiration_model_report.md

Test specs to implement or stub with explicit blockers:
- dnd_eye_ray_d10_channel_test.py
- central_eye_zero_suppression_test.py
- subjective_viewer_render_transform_suite.py
- npc_keyword_trigger_mechanism_audit.py
- excalibug_bonelord_language_anchor_audit.py
- numeric_identity_key_seed_search.py
- yalahar_quarter_block_model.py
- dreamer_duality_layer_split_test.py
- poi_throne_order_motif_test.py
- library_entity_ontology_crosswalk.py
- authorial_source_classifier.py

Final report must classify each hypothesis as:
accepted_mechanical, weak_clue, rejected_control, watchlist_only, or blocked_waiting_for_official_source.

No plaintext promotion without official ground truth.
```
