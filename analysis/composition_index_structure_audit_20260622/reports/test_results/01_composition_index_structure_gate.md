# Composition Index Structure Gate

Classification: `COMPOSITION_INDEX_REMAINS_EXTERNAL`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

The book-level controller reduced exact within-bucket lengths to one composition index per book. This gate asks whether the true index has prefix-generalizable structure or remains external payload.

No target text, plaintext, semantics, row0 origin, or exact residuals are used to choose the coarse sequence.

## Rank Distribution

- Nontrivial books: `48`.
- Edge ranks among nontrivial books: `2`.
- Low-half ranks among nontrivial books: `24`.
- Quantile counts: `{'q00': 7, 'q01': 2, 'q02': 6, 'q03': 3, 'q04': 8, 'q05': 9, 'q06': 2, 'q07': 2, 'q08': 7, 'q09': 2}`.

## Best Prefix-Holdout Model

- Best model: `count_x_length__quantile10`.
- Best model classification: `COMPOSITION_INDEX_REMAINS_EXTERNAL`.
- Uniform composition-index bits over repeated holdouts: `1198.420`.
- Model bits: `1211.748`.
- Saving: `-13.327` bits.
- Nontrivial saving: `-13.327` bits.
- Random-rank saving mean: `-24.843` bits.
- Random-rank saving p95: `-13.273` bits.

| Cutoff | Test Books | Uniform Bits | Model Bits | Saving | Nontrivial Saving | Edge Books | Top Symbol Hits |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `50` | `450.430` | `458.061` | `-7.631` | `-7.631` | `2` | `4` |
| `30` | `40` | `350.161` | `356.149` | `-5.988` | `-5.988` | `0` | `12` |
| `40` | `30` | `227.004` | `225.862` | `1.142` | `1.142` | `0` | `12` |
| `50` | `20` | `132.752` | `133.539` | `-0.787` | `-0.787` | `0` | `8` |
| `60` | `10` | `38.074` | `38.137` | `-0.063` | `-0.063` | `0` | `6` |

## Decision

The composition-index field is not promoted. The book-length constrained composition codec remains useful, but the exact index inside that composition stays external payload under current evidence.

## Remaining External Fields

- coarse sequence corrections when the true sequence misses beam
- book-level composition index for exact residual lengths
- literal innovation tape payload and schedule
- copy-hint rank stream
- seed books `0..9`
- `row0`

## Reproducible Artifacts

- [01_composition_index_structure_gate.py](../../scripts/01_composition_index_structure_gate.py)
- [01_composition_index_structure_gate.json](01_composition_index_structure_gate.json)
