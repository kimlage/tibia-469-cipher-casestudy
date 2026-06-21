# Prequential Optional Literal Rule Validation

Classification: `prequential_optional_literal_exception_rule_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 105 found an optional-literal exception rule on the full corpus.
This audit selects rules on prefix rows only and evaluates them on suffix
rows without retuning.

## Result

- Evaluated splits: `4`.
- Train-selected beats no-exception baseline splits: `4`.
- Fixed full-corpus rule beats no-exception baseline splits: `4`.
- Mean train-selected vs suffix-oracle error gap: `0.500`.
- Max train-selected vs suffix-oracle error gap: `1`.
- Promotes prequential rule: `False`.

## Splits

| cutoff | train/test rows | train/test exceptions | train-selected rule | train test errors | fixed-rule test errors | baseline errors | oracle errors |
|---:|---:|---:|---|---:|---:|---:|---:|
| 20 | 60/165 | 7/10 | `(length_le_5 and remaining_ge_10)` | 3 | 3 | 10 | 2 |
| 35 | 123/102 | 10/7 | `(length_le_5 and remaining_ge_24)` | 2 | 1 | 7 | 1 |
| 50 | 173/52 | 14/3 | `(length_le_5 and remaining_ge_10)` | 0 | 0 | 3 | 0 |
| 60 | 206/19 | 16/1 | `(length_le_5 and remaining_ge_10)` | 0 | 0 | 1 | 0 |

## Decision

- Prefix-selected optional-literal rules generalize partially: they beat the no-exception baseline in every tested suffix, and the fixed corpus rule does too. But train-selected rules do not match suffix-oracle rule error in every split, and the whole family still depends on target copy availability and the length atlas. The result is predictive support for the clue, not a promoted generator.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
