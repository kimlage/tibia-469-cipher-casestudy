# Target-Max Resegmentation Second-Pass Gate

Classification: `targetmax_resegmentation_second_pass_improves_bound`
Translation delta: `NONE`

## Purpose

Gate 53 promoted one target-max resegmentation under the exact
component scorer. This gate retests the remaining compatible local
target-max rewrites against that promoted formula and emits a new
formula only if exact scoring and roundtrip validation still improve
the bound.

## Summary

- Current formula bits: `8158.766094`.
- Current exact scorer bits: `8158.766094`.
- Stale exceptions skipped: `1`.
- Candidates tested: `44`.
- Valid candidates: `40`.
- Improving candidates: `4`.
- Candidate bits: `8157.065654`.
- Candidate gain: `+1.700440` bits.
- Candidate: book `2`, op `9`, mode `preserve_next_mode`, slack `1`.
- Component deltas: `{'literal_bits_no_payload': 0.0, 'literal_payload_bits': -2.2479275134437557, 'item_type_bits': 0.0, 'copy_source_bits': 0.0, 'copy_length_bits': 0.5474877953020041}`.
- Inventory: `{'literal_runs': 87, 'literal_digits': 856, 'copy_items': 261, 'copied_digits': 10407}`.

## Promoted Formula

- [sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_second_pass_formula_469.json](../../../authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_second_pass_formula_469.json)

## Candidate Table

| Book | Op | Mode | Next | Slack | Errors | Gain | Total |
|---:|---:|---|---|---:|---:|---:|---:|
| `2` | `9` | `preserve_next_mode` | `literal` | `1` | `0` | `+1.700440` | `8157.065654` |
| `2` | `9` | `literalize_next_remainder` | `literal` | `1` | `0` | `+1.700440` | `8157.065654` |
| `10` | `0` | `preserve_next_mode` | `copy` | `72` | `0` | `-2.739092` | `8161.505186` |
| `10` | `0` | `literalize_next_remainder` | `copy` | `72` | `0` | `-519.403261` | `8678.169355` |
| `13` | `4` | `preserve_next_mode` | `copy` | `1` | `0` | `-2.060405` | `8160.826499` |
| `13` | `4` | `literalize_next_remainder` | `copy` | `1` | `2` | `NA` | `NA` |
| `13` | `8` | `preserve_next_mode` | `copy` | `1` | `0` | `-0.548086` | `8159.314180` |
| `13` | `8` | `literalize_next_remainder` | `copy` | `1` | `0` | `-124.725323` | `8283.491417` |
| `14` | `3` | `preserve_next_mode` | `copy` | `1` | `0` | `-1.200122` | `8159.966216` |
| `14` | `3` | `literalize_next_remainder` | `copy` | `1` | `2` | `NA` | `NA` |
| `17` | `7` | `preserve_next_mode` | `literal` | `1` | `0` | `-0.736966` | `8159.503060` |
| `17` | `7` | `literalize_next_remainder` | `literal` | `1` | `0` | `-0.736966` | `8159.503060` |
| `20` | `2` | `preserve_next_mode` | `copy` | `1` | `0` | `-3.482260` | `8162.248354` |
| `20` | `2` | `literalize_next_remainder` | `copy` | `1` | `0` | `-6.029863` | `8164.795957` |
| `20` | `5` | `preserve_next_mode` | `copy` | `1` | `0` | `-1.807355` | `8160.573449` |
| `20` | `5` | `literalize_next_remainder` | `copy` | `1` | `0` | `-6.770011` | `8165.536105` |
| `21` | `1` | `preserve_next_mode` | `copy` | `2` | `0` | `-1.000789` | `8159.766884` |
| `21` | `1` | `literalize_next_remainder` | `copy` | `2` | `0` | `-70.920544` | `8229.686638` |
| `23` | `8` | `preserve_next_mode` | `copy` | `1` | `0` | `-0.873820` | `8159.639914` |
| `23` | `8` | `literalize_next_remainder` | `copy` | `1` | `2` | `NA` | `NA` |
| `24` | `0` | `preserve_next_mode` | `copy` | `1` | `0` | `-0.585319` | `8159.351413` |
| `24` | `0` | `literalize_next_remainder` | `copy` | `1` | `0` | `-144.543506` | `8303.309600` |
| `28` | `1` | `preserve_next_mode` | `copy` | `1` | `0` | `-3.239260` | `8162.005354` |
| `28` | `1` | `literalize_next_remainder` | `copy` | `1` | `0` | `-15.549000` | `8174.315094` |
| `28` | `2` | `preserve_next_mode` | `copy` | `1` | `0` | `-2.438005` | `8161.204099` |
| `28` | `2` | `literalize_next_remainder` | `copy` | `1` | `0` | `-34.329491` | `8193.095585` |
| `30` | `3` | `preserve_next_mode` | `copy` | `1` | `0` | `-0.577440` | `8159.343534` |
| `30` | `3` | `literalize_next_remainder` | `copy` | `1` | `0` | `-94.589431` | `8253.355525` |
| `34` | `4` | `preserve_next_mode` | `copy` | `1` | `0` | `-2.060157` | `8160.826251` |
| `34` | `4` | `literalize_next_remainder` | `copy` | `1` | `0` | `-22.301989` | `8181.068083` |
| `46` | `1` | `preserve_next_mode` | `copy` | `3` | `0` | `-0.000581` | `8158.766675` |
| `46` | `1` | `literalize_next_remainder` | `copy` | `3` | `0` | `-273.703389` | `8432.469483` |
| `51` | `0` | `preserve_next_mode` | `copy` | `7` | `0` | `+0.015456` | `8158.750638` |
| `51` | `0` | `literalize_next_remainder` | `copy` | `7` | `0` | `-329.195615` | `8487.961709` |
| `54` | `0` | `preserve_next_mode` | `copy` | `2` | `0` | `-0.000163` | `8158.766257` |
| `54` | `0` | `literalize_next_remainder` | `copy` | `2` | `0` | `-6.550596` | `8165.316691` |
| `56` | `5` | `preserve_next_mode` | `copy` | `1` | `0` | `-0.555325` | `8159.321419` |
| `56` | `5` | `literalize_next_remainder` | `copy` | `1` | `0` | `-169.370758` | `8328.136852` |
| `56` | `8` | `preserve_next_mode` | `copy` | `1` | `0` | `+0.999844` | `8157.766250` |
| `56` | `8` | `literalize_next_remainder` | `copy` | `1` | `0` | `-37.764218` | `8196.530312` |
| `61` | `0` | `preserve_next_mode` | `copy` | `10` | `0` | `-3.586362` | `8162.352456` |
| `61` | `0` | `literalize_next_remainder` | `copy` | `10` | `0` | `-53.164441` | `8211.930535` |
| `65` | `0` | `preserve_next_mode` | `copy` | `13` | `0` | `-1.596470` | `8160.362564` |
| `65` | `0` | `literalize_next_remainder` | `copy` | `13` | `2` | `NA` | `NA` |

## Interpretation

This is a compression-bound update only. The exact scorer validates a
second local target-max resegmentation after the gate-53 formula. It
does not derive the 10x10 row0 table, identify plaintext, or reopen
semantic interpretation.

## Boundary

- Compression bound changes only after exact scorer reproduction and roundtrip validation.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
