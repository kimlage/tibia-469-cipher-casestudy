# 128. Prequential Recipe Reparse Train-Set Controls

Classification: `recipe_reparse_predictive_not_numeric_prefix_specific`
Translation delta: `NONE`

## Purpose

Audits 126-127 show that deterministic frozen-count reparsing has a real
suffix signal above content controls. This audit asks a different question:
is the signal specific to numeric prefix -> future suffix, or do random
same-size training inventories provide equal or better source material?

This first control is intentionally focused on cutoff `50`, where the
test suffix is still 20 books but the random-inventory DP controls are
cheap enough to run repeatedly. The observed row uses train books
`0..49` and tests `50..69`. Controls sample random same-size train sets,
reparse the remaining books in numeric order, and keep the same parser
and frozen component-count contract.

## Result

| Cutoff | Observed gain | Random mean gain | Random max gain | p(random >= observed) |
|---:|---:|---:|---:|---:|
| `50` | `10441.679` | `9473.486` | `10489.489` | `0.1538` |

## Interpretation

This audit separates copy/reference predictability from numeric-order
specificity. If random train inventories match or exceed the numeric
prefix, the mechanism remains predictive but not evidence for numeric
book order as an authorial generation order.

This remains analysis-only. It does not lower `compression_bound`,
derive `row0`, translate the books, or promote an authorial method.
