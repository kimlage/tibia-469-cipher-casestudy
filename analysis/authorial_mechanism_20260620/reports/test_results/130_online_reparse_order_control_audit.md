# 130. Online Reparse Order Control Audit

Classification: `numeric_online_reparse_survives_order_controls`
Translation delta: `NONE`

## Purpose

Audit 129 lowered the charged full-corpus bound by using a deterministic
online parser in numeric book order. This audit tests whether that gain
is tied to a compact/canonical order or whether arbitrary book
permutations obtain similar raw compression.

## Result

- Numeric online bound: `8343.062` bits
- Best raw order: `numeric` at `8343.062` bits (`+0.000` vs numeric)
- Best charged order: `numeric` at `8343.062` bits (`+0.000` vs numeric)
- Random raw <= numeric: `0/6`
- Random charged <= numeric: `0/6`
- Arbitrary-order descriptor cost: `332.453` bits

## Named Orders

| Order | Raw bits | Raw delta | Descriptor | Charged delta | Roundtrip |
|---|---:|---:|---:|---:|---:|
| `numeric` | `8343.062` | `+0.000` | `0.000` | `+0.000` | `70/70` |
| `reverse_numeric` | `8924.889` | `+581.827` | `1.000` | `+582.827` | `70/70` |
| `evens_then_odds` | `8721.037` | `+377.975` | `2.000` | `+379.975` | `70/70` |
| `odds_then_evens` | `8606.334` | `+263.272` | `2.000` | `+265.272` | `70/70` |
| `length_ascending` | `8956.031` | `+612.969` | `332.453` | `+945.423` | `70/70` |

## Random Controls

- Raw min/mean/max: `8531.646` / `8675.318` / `8779.192` bits
- Raw stdev: `75.267` bits
- Empirical `p(random raw <= numeric)`: `0.0000`
- Empirical `p(random charged <= numeric)`: `0.0000`

## Lowest Raw Rows

| Rank | Order | Family | Raw bits | Raw delta | Charged delta |
|---:|---|---|---:|---:|---:|
| 1 | `numeric` | `canonical` | `8343.062` | `+0.000` | `+0.000` |
| 2 | `random_04` | `random_permutation_control` | `8531.646` | `+188.584` | `+521.038` |
| 3 | `odds_then_evens` | `simple_control` | `8606.334` | `+263.272` | `+265.272` |
| 4 | `random_00` | `random_permutation_control` | `8659.005` | `+315.943` | `+648.396` |
| 5 | `random_05` | `random_permutation_control` | `8673.001` | `+329.939` | `+662.392` |
| 6 | `random_02` | `random_permutation_control` | `8687.494` | `+344.432` | `+676.885` |
| 7 | `evens_then_odds` | `simple_control` | `8721.037` | `+377.975` | `+379.975` |
| 8 | `random_03` | `random_permutation_control` | `8721.571` | `+378.509` | `+710.962` |

## Interpretation

Numeric order remains the best raw and charged order among the tested
named and random controls. This supports the online reparse as a
compact mechanical recipe rather than arbitrary order overfitting.

## Boundary

- No plaintext or translation is introduced.
- Row0/table origin is unchanged.
- Arbitrary order search is not promoted as a new bound.
