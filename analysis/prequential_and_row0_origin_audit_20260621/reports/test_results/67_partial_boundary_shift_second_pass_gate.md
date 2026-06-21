# Partial Boundary Shift Second-Pass Gate

Classification: `partial_boundary_shift_second_pass_candidate_found`
Translation delta: `NONE`

## Purpose

After gate 66 promotes one partial boundary shift, this gate recomputes
the active target-max exception topology on the promoted formula and
exact-scores every remaining positive partial local shift.

## Summary

- Current total bits: `8155.261037`.
- Exact scorer reproduction: `8155.261037`.
- Active copy events: `261`.
- Active target-max exceptions: `19`.
- Active slack digits: `112`.
- Shift candidates tested: `223`.
- Valid candidates: `207`.
- Improving candidates: `1`.
- Candidate count by mode: `{'literalize_next_remainder': 111, 'preserve_next_mode': 111, 'trim_literal': 1}`.
- Valid count by mode: `{'literalize_next_remainder': 95, 'preserve_next_mode': 111, 'trim_literal': 1}`.
- Improving count by mode: `{'literalize_next_remainder': 0, 'preserve_next_mode': 1, 'trim_literal': 0}`.

## Best Valid Candidate

- Book/op: `46` / `1`.
- Mode: `preserve_next_mode`.
- Delta/slack: `1` / `3`.
- Candidate total bits: `8154.676268`.
- Candidate gain bits: `+0.584769`.
- Component deltas: `{'literal_bits_no_payload': 0.0, 'literal_payload_bits': 0.0, 'item_type_bits': 0.0, 'copy_source_bits': 0.0001937934102897998, 'copy_length_bits': -0.5849625007213035}`.

## Top Valid Candidates

| Book | Op | Mode | Delta | Slack | Gain bits | Total bits |
|---:|---:|---|---:|---:|---:|---:|
| `46` | `1` | `preserve_next_mode` | `1` | `3` | `+0.584769` | `8154.676268` |
| `54` | `0` | `preserve_next_mode` | `2` | `2` | `-0.000163` | `8155.261200` |
| `46` | `1` | `preserve_next_mode` | `2` | `3` | `-0.000388` | `8155.261424` |
| `46` | `1` | `preserve_next_mode` | `3` | `3` | `-0.000581` | `8155.261618` |
| `13` | `8` | `preserve_next_mode` | `1` | `1` | `-0.280706` | `8155.541743` |
| `56` | `5` | `preserve_next_mode` | `1` | `1` | `-0.555325` | `8155.816362` |
| `30` | `3` | `preserve_next_mode` | `1` | `1` | `-0.577440` | `8155.838477` |
| `24` | `0` | `preserve_next_mode` | `1` | `1` | `-0.585319` | `8155.846356` |
| `17` | `7` | `trim_literal` | `1` | `1` | `-0.836501` | `8156.097538` |
| `23` | `8` | `preserve_next_mode` | `1` | `1` | `-0.873820` | `8156.134857` |
| `54` | `0` | `preserve_next_mode` | `1` | `2` | `-1.000163` | `8156.261200` |
| `21` | `1` | `preserve_next_mode` | `1` | `2` | `-1.000395` | `8156.261432` |

## Decision

- Interpretation: A further exact-scored partial boundary shift remains after the first promotion. A separate formula gate is required before changing the bound.
- Row0 origin remains exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
