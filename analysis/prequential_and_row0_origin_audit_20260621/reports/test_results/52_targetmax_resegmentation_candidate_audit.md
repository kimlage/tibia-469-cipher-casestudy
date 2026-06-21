# Target-Max Resegmentation Candidate Audit

Classification: `targetmax_local_resegmentation_has_proxy_improvements_unpromoted`
Translation delta: `NONE`

## Purpose

Gate 51 showed that each non-target-max copy length enters one following
operation and stops inside it. This audit tests the local mechanical
rewrite: extend the copy to target-max and trim the following op.

## Summary

- Current total bits: `8160.825608`.
- Exceptions tested: `23`.
- Candidates tested: `46`.
- Valid candidates: `42`.
- Proxy-improving candidates: `5`.
- Valid by mode: `{'preserve_next_mode': 23, 'literalize_next_remainder': 19}`.
- Improving by mode: `{'preserve_next_mode': 4, 'literalize_next_remainder': 1}`.
- Best proxy delta: `-2.059513` bits.
- Best proxy total: `8158.766094` bits.
- Best candidate: book `9`, op `0`, mode `preserve_next_mode`, slack `4`.
- Best component deltas: `{'literal_bits_no_payload': 0.0, 'literal_payload_bits': 0.0, 'item_type_bits': 0.0, 'copy_source_bits': 0.0033531567469253787, 'copy_length_bits': -2.0628666430261546}`.

## Candidate Table

| Book | Op | Mode | Next | Slack | Roundtrip | Score errors | Proxy delta |
|---:|---:|---|---|---:|---|---:|---:|
| `2` | `9` | `preserve_next_mode` | `literal` | `1` | `True` | `0` | `-1.700440` |
| `2` | `9` | `literalize_next_remainder` | `literal` | `1` | `True` | `0` | `-1.700440` |
| `9` | `0` | `preserve_next_mode` | `copy` | `4` | `True` | `0` | `-2.059513` |
| `9` | `0` | `literalize_next_remainder` | `copy` | `4` | `True` | `0` | `+28.852223` |
| `10` | `0` | `preserve_next_mode` | `copy` | `72` | `True` | `0` | `+3.738464` |
| `10` | `0` | `literalize_next_remainder` | `copy` | `72` | `True` | `0` | `+519.402633` |
| `13` | `4` | `preserve_next_mode` | `copy` | `1` | `True` | `0` | `+2.060405` |
| `13` | `4` | `literalize_next_remainder` | `copy` | `1` | `True` | `2` | `NA` |
| `13` | `8` | `preserve_next_mode` | `copy` | `1` | `True` | `0` | `+0.548086` |
| `13` | `8` | `literalize_next_remainder` | `copy` | `1` | `True` | `0` | `+124.725323` |
| `14` | `3` | `preserve_next_mode` | `copy` | `1` | `True` | `0` | `+1.200122` |
| `14` | `3` | `literalize_next_remainder` | `copy` | `1` | `True` | `2` | `NA` |
| `17` | `7` | `preserve_next_mode` | `literal` | `1` | `True` | `0` | `+0.736966` |
| `17` | `7` | `literalize_next_remainder` | `literal` | `1` | `True` | `0` | `+0.736966` |
| `20` | `2` | `preserve_next_mode` | `copy` | `1` | `True` | `0` | `+3.482260` |
| `20` | `2` | `literalize_next_remainder` | `copy` | `1` | `True` | `0` | `+6.029557` |
| `20` | `5` | `preserve_next_mode` | `copy` | `1` | `True` | `0` | `+1.807355` |
| `20` | `5` | `literalize_next_remainder` | `copy` | `1` | `True` | `0` | `+6.770011` |
| `21` | `1` | `preserve_next_mode` | `copy` | `2` | `True` | `0` | `+1.000789` |
| `21` | `1` | `literalize_next_remainder` | `copy` | `2` | `True` | `0` | `+70.920544` |
| `23` | `8` | `preserve_next_mode` | `copy` | `1` | `True` | `0` | `+0.873820` |
| `23` | `8` | `literalize_next_remainder` | `copy` | `1` | `True` | `2` | `NA` |
| `24` | `0` | `preserve_next_mode` | `copy` | `1` | `True` | `0` | `+0.585319` |
| `24` | `0` | `literalize_next_remainder` | `copy` | `1` | `True` | `0` | `+144.543506` |
| `28` | `1` | `preserve_next_mode` | `copy` | `1` | `True` | `0` | `+3.239260` |
| `28` | `1` | `literalize_next_remainder` | `copy` | `1` | `True` | `0` | `+15.548876` |
| `28` | `2` | `preserve_next_mode` | `copy` | `1` | `True` | `0` | `+1.438005` |
| `28` | `2` | `literalize_next_remainder` | `copy` | `1` | `True` | `0` | `+34.329491` |
| `30` | `3` | `preserve_next_mode` | `copy` | `1` | `True` | `0` | `+0.577440` |
| `30` | `3` | `literalize_next_remainder` | `copy` | `1` | `True` | `0` | `+94.589431` |
| `34` | `4` | `preserve_next_mode` | `copy` | `1` | `True` | `0` | `+2.060157` |
| `34` | `4` | `literalize_next_remainder` | `copy` | `1` | `True` | `0` | `+22.301866` |
| `46` | `1` | `preserve_next_mode` | `copy` | `3` | `True` | `0` | `+0.000581` |
| `46` | `1` | `literalize_next_remainder` | `copy` | `3` | `True` | `0` | `+273.703389` |
| `51` | `0` | `preserve_next_mode` | `copy` | `7` | `True` | `0` | `-0.015456` |
| `51` | `0` | `literalize_next_remainder` | `copy` | `7` | `True` | `0` | `+329.195615` |
| `54` | `0` | `preserve_next_mode` | `copy` | `2` | `True` | `0` | `+0.000163` |
| `54` | `0` | `literalize_next_remainder` | `copy` | `2` | `True` | `0` | `+6.550596` |
| `56` | `5` | `preserve_next_mode` | `copy` | `1` | `True` | `0` | `+0.555325` |
| `56` | `5` | `literalize_next_remainder` | `copy` | `1` | `True` | `0` | `+169.370758` |
| `56` | `8` | `preserve_next_mode` | `copy` | `1` | `True` | `0` | `-0.999844` |
| `56` | `8` | `literalize_next_remainder` | `copy` | `1` | `True` | `0` | `+37.764218` |
| `61` | `0` | `preserve_next_mode` | `copy` | `10` | `True` | `0` | `+3.586362` |
| `61` | `0` | `literalize_next_remainder` | `copy` | `10` | `True` | `0` | `+53.164441` |
| `65` | `0` | `preserve_next_mode` | `copy` | `13` | `True` | `0` | `+1.596470` |
| `65` | `0` | `literalize_next_remainder` | `copy` | `13` | `True` | `2` | `NA` |

## Interpretation

This is not a promoted formula gate. It maps whether the local
target-max resegmentation rewrite is mechanically valid and whether
the available compatible component scorer sees a possible improvement.
A real compression-bound promotion still requires exact scoring under
the current full source-substitution ledger or a joint reparse objective.

## Boundary

- No new formula is emitted.
- Compression bound is unchanged.
- Candidate totals are proxy diagnostics, not promoted bounds.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
