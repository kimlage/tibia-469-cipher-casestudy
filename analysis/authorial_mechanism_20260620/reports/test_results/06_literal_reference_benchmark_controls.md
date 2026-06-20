# Literal Reference Benchmark and Controls

Verdict: `controlled_mechanical_improvement_no_semantics`. Translation delta: `NONE`.

This benchmark compares the base module formula, the tape formula, and
the literal-reference formula under the same rough internal cost ledger.
The item overhead is held neutral between literal and reference items, so
the reported gain is the address-vs-digit payload delta only.

## Model Cost Ladder

| Model | Rough total bits | Gain vs previous | Literal digits | Roundtrip |
|---|---:|---:|---:|---:|
| `mechanical_formula_469` | `24350.7` | `0.0` | `2083` | `True` |
| `tape_based_formula_469` | `17753.5` | `6597.1` | `1976` | `True` |
| `literal_reference_formula_469` | `16586.1` | `1167.4` | `1397` | `True` |

## Real Reference Scores

| Mode | Reference items | Referenced digits | Saved bits |
|---|---:|---:|---:|
| unrestricted | `36` | `579` | `1167.4` |
| exclude components already touched by the same book | `20` | `321` | `646.3` |

## Negative Controls

| Control | Runs | Mean saved bits | Max saved bits | p(>= observed) |
|---|---:|---:|---:|---:|
| `component_digit_shuffle` | `400` | `0.0` | `0.0` | `0.0025` |
| `random_length_matched_literals` | `400` | `0.0` | `0.0` | `0.0025` |
| `shuffled_book_exclusion` | `400` | `759.6` | `1002.1` | `0.9850` |

## Boundary

The literal-reference layer is promoted only as a controlled mechanical
compression improvement. It does not explain the 10x10 pair-table
origin, does not create plaintext, and does not support any private
authorial-intent claim.
