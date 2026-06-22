# Target Digit Boundary Island Gate

Classification: `target_digit_boundary_island_code_rejected`
Translation delta: `NONE`

## Purpose

Test whether high-surprisal boundary candidates should be encoded as
contiguous islands plus offsets rather than as a flat candidate set.

## Summary

- Books/candidates/actual cutpoints: `60` / `9507` / `201`.
- Policies tested: `23`.
- Best island policy: `right_ge:4`.
- Baseline full cutpoint atlas bits: `1570.073`.
- Island correction bits after policy charge: `941.005`.
- Island saving after policy charge: `629.068` bits.
- Same-policy threshold saving: `645.694` bits.
- Island delta vs same-policy threshold: `16.625` bits.
- Random island saving p95 after policy charge: `489.157` bits.
- TP/FP/FN: `94` / `841` / `107`.
- Predicted boundaries/correction events: `935` / `948`.
- Islands/occupied/multi-hit: `782` / `94` / `0`.
- Precision/recall: `0.100535` / `0.467662`.
- Exact books: `0/60`.
- Prefix-selected positive test-saving cells: `5/5`.
- Prefix-selected island-beats-threshold cells: `2/5`.

## Comparison To Threshold Gate

- Threshold gate best policy: `right_ge:4`.
- Threshold gate saving after policy charge: `645.694` bits.
- Best island saving delta vs threshold gate: `-16.625` bits.
- Best island correction delta vs threshold gate: `16.625` bits.

The island model is structurally informative but not a better code.
The best policy's occupied islands are all single-hit, but there are still
too many islands and outside misses for this to replace the flat threshold
candidate-set correction code.

## Top Island Policies

| Policy | Island saving | Delta vs same-policy threshold | Islands | Occupied | FN | Exact books |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `right_ge:4` | `629.068` | `16.625` | `782` | `94` | `107` | `0` |
| `rank_top:0.1` | `625.853` | `12.288` | `799` | `85` | `116` | `0` |
| `rank_top:0.05` | `621.496` | `0.471` | `400` | `61` | `140` | `0` |
| `right_ge:4.5` | `621.436` | `9.427` | `451` | `74` | `127` | `0` |
| `rank_top:0.08` | `619.723` | `6.218` | `638` | `74` | `127` | `0` |
| `rank_top:0.15` | `613.264` | `26.202` | `1164` | `101` | `99` | `0` |
| `right_ge:3.5` | `606.105` | `25.392` | `1152` | `104` | `95` | `0` |
| `right_ge:5.5` | `604.046` | `-2.809` | `152` | `50` | `151` | `8` |

## Decision

- Island code promoted: `False`.
- Endpoint generator promoted: `False`.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
