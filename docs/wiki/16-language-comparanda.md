---
page_id: language-comparanda
page_type: finding
context: bonelord-469
visibility: public_candidate
status: frozen
updated_at: 2026-06-20
moc_parent: README.md
source_refs:
  - analysis/language_comparanda_20260620
---

# 16. Language Comparanda

[<- Source-Inspiration Model](15-source-inspiration-model.md) . [Wiki home](README.md)

---

## Verdict

The language-comparanda pass adds a useful benchmark/control layer, not a new
translation. It records known Tibia constructed/pseudo-language material so
future claims can be tested against positive controls, uncertainty labels, and
false-positive controls.

Translation delta: `NONE`.

Round result: `BENCHMARK READY / semantic plateau unchanged`.

## Why This Was Added

The project had already tested the 70-book row0 stream heavily against direct
natural-language readings. The new question was narrower:

```text
469 digits -> row0 14-symbol stream -> possible intermediate script/conlang/formula layer
```

instead of only:

```text
469 digits -> English/German/plaintext
```

Jekhr/Deepling makes this worth preserving as a benchmark because it is a
Tibia-native example of a written-symbol layer with Latin transcription,
pronunciation, vocabulary, and number words. That does not make 469 Jekhr. It
only proves that a multi-hop script pipeline is a valid control family.

## Registry

| ID | Use |
|---|---|
| `deepling_jekhr` | primary positive control for intermediate script recovery |
| `orc_language` | functional NPC/trade keyword-language control |
| `chakoya_language` | partial dialogue lexicon and uncertainty control |
| `gharonk_language` | library-language and number-word control |
| `elven_language` | tiny lexicon reference only |
| `kaplar_minotaur` | single-anchor false-expansion control |
| `human_tibia_language` | spell/keyword formula control |
| `caveman_language` | watchlist until transcripts are gathered |
| `bonelord_469` | target corpus only, never a positive control |

All currently registered sources are community wiki/QA sources. They are useful
for building controls; they are not CipSoft-attested 469 ground truth.

## H25-H30 Classification

| ID | Hypothesis | Classification |
|---|---|---|
| H25 | row0 may be an intermediate script/conlang layer | `open_mechanism_only` |
| H26 | row0 may match a known Tibia conlang profile | `speculative_control_only` |
| H27 | phrase layer may behave like keyword/spell formulae | `plausible_phrase_only` |
| H28 | community translations need confidence labels | `accepted_process_guard` |
| H29 | Tibia languages can use non-numeric number words | `mechanism_alert_only` |
| H30 | Jekhr provides a glyph/Latin/meaning benchmark | `accepted_benchmark` |

## Reports

- [Language inventory report](../../analysis/language_comparanda_20260620/reports/language_inventory_report.md)
- [Lexicon confidence report](../../analysis/language_comparanda_20260620/reports/lexicon_confidence_report.md)
- [Intermediate script test report](../../analysis/language_comparanda_20260620/reports/intermediate_script_test_report.md)
- [Final language comparanda report](../../analysis/language_comparanda_20260620/reports/final_language_comparanda_report.md)
- [Registry audit](../../analysis/language_comparanda_20260620/reports/test_results/01_language_registry_audit.md)
- [Benchmark readiness audit](../../analysis/language_comparanda_20260620/reports/test_results/02_benchmark_readiness_audit.md)

## What Counts As Future Progress

A future language-comparanda method must first recover known controls such as
Jekhr, Orcish, Chakoya, or Gharonk under their confidence labels. It must then
show that row0 beats shuffled labels, self-anagrams, random conlang lexica, and
gibberish controls, while reducing description length. Even then, the result is
mechanism-only unless official 469 semantic ground truth appears.

No known Tibia language currently unlocks 469. The only semantic unlock remains
the same: CipSoft/in-game number-to-text, book-to-text, or symbol-to-meaning
ground truth.
