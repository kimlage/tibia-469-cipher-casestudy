# Target-Max Resegmentation Saturation Gate

Classification: `targetmax_resegmentation_saturated_with_improvements`
Translation delta: `NONE`

## Purpose

Gate 54 left the exact target-max resegmentation frontier open. This
gate greedily promotes the best exact positive candidate, rescoring
after each promotion, until no positive candidate remains.

## Summary

- Initial formula bits: `8157.065654`.
- Final formula bits: `8156.050355`.
- Total gain: `+1.015300` bits.
- Promoted passes: `2`.
- Final candidates tested: `38`.
- Final valid candidates: `34`.
- Final improving candidates: `0`.
- Final stale exceptions: `4`.
- Final inventory: `{'literal_runs': 87, 'literal_digits': 856, 'copy_items': 261, 'copied_digits': 10407}`.

## Promoted Formula

- [sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_saturated_formula_469.json](../../../authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_saturated_formula_469.json)

## Promoted Passes

| Pass | Book | Op | Mode | Next | Slack | Input bits | Output bits | Gain | Valid | Improving |
|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|
| `1` | `56` | `8` | `preserve_next_mode` | `copy` | `1` | `8157.065654` | `8156.065811` | `+0.999844` | `38` | `2` |
| `2` | `51` | `0` | `preserve_next_mode` | `copy` | `7` | `8156.065811` | `8156.050355` | `+0.015456` | `36` | `1` |

## Final Frontier

| Book | Op | Mode | Next | Slack | Errors | Gain | Total |
|---:|---:|---|---|---:|---:|---:|---:|
| `10` | `0` | `preserve_next_mode` | `copy` | `72` | `0` | `-2.661089` | `8158.711444` |
| `10` | `0` | `literalize_next_remainder` | `copy` | `72` | `0` | `-519.502796` | `8675.553151` |
| `13` | `4` | `preserve_next_mode` | `copy` | `1` | `0` | `-2.175882` | `8158.226237` |
| `13` | `4` | `literalize_next_remainder` | `copy` | `1` | `2` | `NA` | `NA` |
| `13` | `8` | `preserve_next_mode` | `copy` | `1` | `0` | `-0.363168` | `8156.413523` |
| `13` | `8` | `literalize_next_remainder` | `copy` | `1` | `0` | `-124.717944` | `8280.768299` |
| `14` | `3` | `preserve_next_mode` | `copy` | `1` | `0` | `-1.015204` | `8157.065559` |
| `14` | `3` | `literalize_next_remainder` | `copy` | `1` | `2` | `NA` | `NA` |
| `17` | `7` | `preserve_next_mode` | `literal` | `1` | `0` | `-0.736966` | `8156.787321` |
| `17` | `7` | `literalize_next_remainder` | `literal` | `1` | `0` | `-0.736966` | `8156.787321` |
| `20` | `2` | `preserve_next_mode` | `copy` | `1` | `0` | `-3.482260` | `8159.532614` |
| `20` | `2` | `literalize_next_remainder` | `copy` | `1` | `0` | `-6.029863` | `8162.080218` |
| `20` | `5` | `preserve_next_mode` | `copy` | `1` | `0` | `-1.807355` | `8157.857710` |
| `20` | `5` | `literalize_next_remainder` | `copy` | `1` | `0` | `-6.770011` | `8162.820366` |
| `21` | `1` | `preserve_next_mode` | `copy` | `2` | `0` | `-1.000789` | `8157.051144` |
| `21` | `1` | `literalize_next_remainder` | `copy` | `2` | `0` | `-70.920544` | `8226.970899` |
| `23` | `8` | `preserve_next_mode` | `copy` | `1` | `0` | `-0.873820` | `8156.924175` |
| `23` | `8` | `literalize_next_remainder` | `copy` | `1` | `2` | `NA` | `NA` |
| `24` | `0` | `preserve_next_mode` | `copy` | `1` | `0` | `-0.585319` | `8156.635674` |
| `24` | `0` | `literalize_next_remainder` | `copy` | `1` | `0` | `-144.543506` | `8300.593861` |
| `28` | `1` | `preserve_next_mode` | `copy` | `1` | `0` | `-3.054342` | `8159.104697` |
| `28` | `1` | `literalize_next_remainder` | `copy` | `1` | `0` | `-15.364082` | `8171.414437` |
| `28` | `2` | `preserve_next_mode` | `copy` | `1` | `0` | `-2.438005` | `8158.488360` |
| `28` | `2` | `literalize_next_remainder` | `copy` | `1` | `0` | `-34.329491` | `8190.379846` |
| `30` | `3` | `preserve_next_mode` | `copy` | `1` | `0` | `-0.577440` | `8156.627795` |
| `30` | `3` | `literalize_next_remainder` | `copy` | `1` | `0` | `-94.766970` | `8250.817324` |
| `34` | `4` | `preserve_next_mode` | `copy` | `1` | `0` | `-2.060157` | `8158.110512` |
| `34` | `4` | `literalize_next_remainder` | `copy` | `1` | `0` | `-22.301989` | `8178.352344` |
| `46` | `1` | `preserve_next_mode` | `copy` | `3` | `0` | `-0.000581` | `8156.050936` |
| `46` | `1` | `literalize_next_remainder` | `copy` | `3` | `0` | `-274.235109` | `8430.285464` |
| `54` | `0` | `preserve_next_mode` | `copy` | `2` | `0` | `-0.000163` | `8156.050518` |
| `54` | `0` | `literalize_next_remainder` | `copy` | `2` | `0` | `-6.550596` | `8162.600951` |
| `56` | `5` | `preserve_next_mode` | `copy` | `1` | `0` | `-0.555325` | `8156.605680` |
| `56` | `5` | `literalize_next_remainder` | `copy` | `1` | `0` | `-169.481085` | `8325.531440` |
| `61` | `0` | `preserve_next_mode` | `copy` | `10` | `0` | `-3.586362` | `8159.636717` |
| `61` | `0` | `literalize_next_remainder` | `copy` | `10` | `0` | `-53.412368` | `8209.462723` |
| `65` | `0` | `preserve_next_mode` | `copy` | `13` | `0` | `-1.596470` | `8157.646825` |
| `65` | `0` | `literalize_next_remainder` | `copy` | `13` | `2` | `NA` | `NA` |

## Interpretation

This closes the local target-max resegmentation family under the exact
greedy frontier: all positive candidates reachable by this gate are
promoted, and the final candidate table has zero positive exact gains.
The result is still a mechanical compression-bound update only.

## Boundary

- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
- Saturation is local to the greedy target-max resegmentation frontier, not proof of a final authorial method.
