# External Numeric Anchor Source Gate

Classification: `chayenne_secondary_overlap_weak_clue_not_origin`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This gate tests known external numeric strings as sources for the unified innovation tape.

| Metric | Value |
| --- | ---: |
| Innovation digits | `1962` |
| All-source copied digits | `137` |
| All-source delta vs raw | `-278.802` |
| Promotable-source copied digits | `0` |
| Promotable-source delta vs raw | `10.585` |
| Chayenne copied digits | `245` |
| Chayenne delta vs raw | `-338.627` |
| Positive holdouts | `2/3` |

## Per-Source Results

| Source | Provenance Class | Promotable | Copied Digits | Delta vs Raw |
| --- | --- | ---: | ---: | ---: |
| `chayenne` | `secondary_validation_corpus_compatible_not_origin` | `False` | `245` | `-338.627` |
| `avar_tar` | `negative_control` | `False` | `5` | `8.821` |
| `your_true_colour` | `official_primary_external` | `True` | `0` | `9.585` |
| `secret_library_74032_45331` | `confirmed_external_numeric_anchor` | `True` | `0` | `9.585` |
| `honeminas_primary_vectors` | `lore_selector_hypothesis_not_content_source` | `False` | `0` | `9.585` |

## Controls

| Control | Delta p05 | Delta p50 | Delta p95 | Copied p95 |
| --- | ---: | ---: | ---: | ---: |
| Shuffled sources | `11.143` | `11.907` | `11.907` | `6` |
| Random sources | `11.907` | `11.907` | `11.907` | `0` |

## Decision

`known external numeric anchors do not provide a promotable innovation content source; Chayenne overlap is secondary validation, not origin`

Next blocker: `innovation content origin remains external; known short external anchors are not sufficient`

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
