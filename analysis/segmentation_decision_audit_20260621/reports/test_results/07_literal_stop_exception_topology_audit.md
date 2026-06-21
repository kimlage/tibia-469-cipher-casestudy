# Literal Stop Exception Topology Audit

Classification: `literal_stop_exceptions_heterogeneous_no_rule_promoted`
Translation delta: `NONE`

## Purpose

Gate 06 left four followed-by-copy literal-stop exceptions. This audit
maps whether they form a promotable mechanical class or remain retained
exceptions.

## Exception Classes

- Online rule hits: `45/49`.
- Exception count: `4`.
- Classes: `{'book_start_understop': 1, 'microgap_zero_offset_understop': 1, 'book_start_overstop': 1, 'long_internal_understop': 1}`.

| Book | Op | Target start | Stable literal | Predicted | Error | Next copy | Class |
|---:|---:|---:|---:|---:|---:|---:|---|
| `14` | `0` | `0` | `39` | `18` | `-21` | `6` | `book_start_understop` |
| `16` | `9` | `164` | `1` | `0` | `-1` | `8` | `microgap_zero_offset_understop` |
| `34` | `0` | `0` | `4` | `10` | `6` | `6` | `book_start_overstop` |
| `57` | `2` | `69` | `28` | `11` | `-17` | `44` | `long_internal_understop` |

## Predicate Controls

| Predicate | TP | FP | Precision | Recall | Uses stable boundary |
|---|---:|---:|---:|---:|---|
| `source_free_predicted_offset_zero` | `1` | `0` | `1.000` | `0.250` | `False` |
| `source_free_predicted_copy_le8` | `3` | `9` | `0.250` | `0.750` | `False` |
| `source_free_book_start` | `2` | `11` | `0.154` | `0.500` | `False` |
| `diagnostic_predicted_before_stable` | `3` | `0` | `1.000` | `0.750` | `True` |
| `diagnostic_abs_error_ge6` | `3` | `0` | `1.000` | `0.750` | `True` |
| `diagnostic_short_next_or_long_literal` | `4` | `9` | `0.308` | `1.000` | `True` |

## Decision

- Promotes exception rule: `False`.
- The four online literal-stop misses are heterogeneous. Source-free flags such as book-start, predicted offset zero, or short predicted copy do not isolate them without false positives. Diagnostic predicates can describe the failures after seeing the stable stop, but they are not generation rules.
- The four literal-stop exceptions remain retained.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
