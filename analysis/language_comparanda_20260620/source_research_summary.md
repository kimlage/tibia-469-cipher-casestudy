---
title: "Research summary: Tibia language comparanda and intermediate layer"
date: 2026-06-20
source_note: "/Users/sargam/Downloads/469_language_comparanda_intermediate_layer_audit_2026-06-20.md"
status: incorporated_as_controls
translation_delta: NONE
---

# Research Summary

The source note asked whether the project had assumed too quickly that 469
must map directly from digits to English/German/plaintext. The useful result is
not a translation. It is a benchmark route:

```text
469 digits -> row0 14-symbol stream -> possible script/conlang/formula layer
```

instead of only:

```text
469 digits -> English/German/plaintext
```

The strongest external comparandum is Jekhr/Deepling, because public TibiaWiki
material records an explicit written-symbol to Latin-letter/pronunciation layer
plus vocabulary and number words. That proves Tibia can contain a multi-hop
language presentation, but it does not imply that 469 is Jekhr or that row0 has
semantic content.

Other useful comparanda:

- Orcish: quest/trade language with functional NPC interaction.
- Chakoya: small dialogue-driven lexicon with uncertain community inference.
- Gharonk: library/journal language with partial vocabulary and number words.
- Elven: tiny high-flavor, low-data lexicon.
- KAPLAR: single-word phrase anchor, useful as a false-expansion control.
- Tibia spell incantations: formula/keyword morphology, not a race language.
- Caveman/Zao Mountain NPCs: watchlist only until transcripts are gathered.

The incorporated hypothesis labels are:

| ID | Hypothesis | Status |
|---|---|---|
| H25 | row0 may be an intermediate script/conlang layer | `open_mechanism_only` |
| H26 | row0 may share morphology with known Tibia conlangs | `speculative_control_only` |
| H27 | phrase layer may behave like keyword/spell formulae | `plausible_phrase_only` |
| H28 | community translations need confidence labels | `accepted_process_guard` |
| H29 | Tibia languages can encode numbers as words | `mechanism_alert_only` |
| H30 | Jekhr provides a multi-hop benchmark | `accepted_benchmark` |

All six preserve `translation_delta = NONE`.
