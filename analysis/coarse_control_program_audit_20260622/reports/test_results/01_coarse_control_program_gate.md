# Coarse Control Program Gate

Classification: `coarse_control_program_candidate`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether the coarse `type:length_bucket` control stream can be encoded or generated from target-free sequential state after granting per-book operation count. This follows the length factor audit: exact length is no longer treated as one symbol.

## Model Summary

| Model | Features | Bits | Saving | Random p95 | Top1 Hits | Status |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `book_length` | `book_length_bucket` | `1649.534` | `117.852` | `128.346` | `59/493` | `REJECTED_COARSE_CONTROL_PROGRAM` |
| `count_x_pos` | `op_count_bucket+op_pos_bucket_online` | `1606.355` | `161.032` | `67.278` | `90/493` | `PROMOTED_COARSE_CONTROL_PROGRAM_CANDIDATE` |
| `global` | `global` | `1601.356` | `166.030` | `166.030` | `65/493` | `REJECTED_COARSE_CONTROL_PROGRAM` |
| `op_count` | `op_count_bucket` | `1512.974` | `254.413` | `116.843` | `88/493` | `PROMOTED_COARSE_CONTROL_PROGRAM_CANDIDATE` |
| `op_pos` | `op_pos_bucket_online` | `1580.987` | `186.400` | `125.420` | `92/493` | `PROMOTED_COARSE_CONTROL_PROGRAM_CANDIDATE` |
| `phase_x_pos` | `book_phase+op_pos_bucket_online` | `1613.516` | `153.870` | `161.260` | `66/493` | `REJECTED_COARSE_CONTROL_PROGRAM` |
| `prev_symbol` | `prev_symbol` | `1593.616` | `173.771` | `92.044` | `92/493` | `PROMOTED_COARSE_CONTROL_PROGRAM_CANDIDATE` |
| `prev_x_pos` | `prev_symbol+op_pos_bucket_online` | `1641.950` | `125.436` | `81.726` | `78/493` | `PROMOTED_COARSE_CONTROL_PROGRAM_CANDIDATE` |
| `prev_x_remaining_ops` | `prev_symbol+remaining_ops_bucket` | `1658.368` | `109.018` | `56.610` | `83/493` | `PROMOTED_COARSE_CONTROL_PROGRAM_CANDIDATE` |
| `remaining_ops` | `remaining_ops_bucket` | `1560.473` | `206.914` | `162.895` | `81/493` | `PROMOTED_COARSE_CONTROL_PROGRAM_CANDIDATE` |

## Best Model

- Best model: `op_count`.
- Best model bits: `1512.974`.
- Saving vs uniform coarse control: `254.413`.
- Random p95 saving: `116.843`.
- Promoted models: `['prev_symbol', 'op_pos', 'remaining_ops', 'op_count', 'prev_x_pos', 'prev_x_remaining_ops', 'count_x_pos']`.
- Generator-promoted models: `['prev_symbol', 'op_pos', 'remaining_ops', 'op_count', 'prev_x_pos', 'prev_x_remaining_ops', 'count_x_pos']`.

## Generation Check For Best Model

| Cutoff | Test Books | Greedy Exact | Beam20 Exact | Beam20 Nontrivial | Greedy Prefix Ops |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `50` | `0` | `16` | `4` | `7` |
| `30` | `40` | `3` | `13` | `3` | `9` |
| `40` | `30` | `6` | `13` | `4` | `10` |
| `50` | `20` | `5` | `10` | `3` | `7` |
| `60` | `10` | `3` | `8` | `3` | `4` |

## Decision

A coarse control program candidate is promoted: the stream beats controls and generates at least one nontrivial held-out coarse sequence in beam.

`row0`, translation, plaintext, and the compression bound remain unchanged.

## Remaining External Fields

- `type:length_bucket` control stream, unless covered only as a codec clue
- within-bucket length residual innovation tape
- literal innovation tape payload and schedule
- copy-hint rank stream
- seed books `0..9`
- `row0`
