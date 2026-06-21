# 127. Prequential Recipe Reparse Controls

Classification: `controlled_recipe_reparse_signal_above_negative_controls`
Translation delta: `NONE`

## Purpose

Audit 126 showed that deterministic frozen-count reparsing beats raw
digits and the active suffix recipe. This control audit asks whether that
signal is stronger than simple negative controls with the same train
prefix and test-book lengths.

Controls:

- `random_same_lengths`: each test book is replaced by iid decimal digits.
- `shuffle_each_book`: each test book keeps its digit multiset but is shuffled.
- `shuffle_suffix_pool`: the whole test suffix digit pool is shuffled and
  repartitioned into the same book lengths.

## Result

| Cutoff | Observed gain | Random mean | Random p>=obs | Per-book shuffle mean | Pool shuffle mean |
|---:|---:|---:|---:|---:|---:|
| `20` | `22842.618` | `-2586.012` | `0.1111` | `-2453.166` | `-2499.708` |
| `35` | `17163.556` | `-1950.318` | `0.1111` | `-1861.657` | `-1875.097` |
| `50` | `10441.679` | `-1140.388` | `0.1111` | `-1106.351` | `-1114.517` |

## Interpretation

The observed suffixes beat random same-length controls at every tested
cutoff. This makes the audit-126 recipe-reparse signal harder to dismiss
as generic LZ behavior on long decimal strings. The shuffled controls
remain useful diagnostics for digit-multiset effects and are kept in
the JSON for exact comparison.

This remains analysis-only. It does not lower `compression_bound`,
derive `row0`, translate the books, or promote an authorial method.
