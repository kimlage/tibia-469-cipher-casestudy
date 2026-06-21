# Partial Boundary Shift Saturation Gate

Classification: `partial_boundary_shift_saturated`
Translation delta: `NONE`

## Purpose

After two promoted partial-boundary shifts, this gate recomputes the
active topology and exact-scores every remaining positive partial local
shift. It exists to close the local partial-shift family.

## Summary

- Current total bits: `8154.676268`.
- Exact scorer reproduction: `8154.676268`.
- Active copy events: `261`.
- Active target-max exceptions: `19`.
- Active slack digits: `111`.
- Shift candidates tested: `221`.
- Valid candidates: `205`.
- Improving candidates: `0`.
- Candidate count by mode: `{'literalize_next_remainder': 110, 'preserve_next_mode': 110, 'trim_literal': 1}`.
- Valid count by mode: `{'literalize_next_remainder': 94, 'preserve_next_mode': 110, 'trim_literal': 1}`.
- Improving count by mode: `{'literalize_next_remainder': 0, 'preserve_next_mode': 0, 'trim_literal': 0}`.

## Best Valid Candidate

- Book/op: `54` / `0`.
- Mode: `preserve_next_mode`.
- Delta/slack: `2` / `2`.
- Candidate total bits: `8154.676431`.
- Candidate gain bits: `-0.000163`.
- Component deltas: `{'literal_bits_no_payload': 0.0, 'literal_payload_bits': 0.0, 'item_type_bits': 0.0, 'copy_source_bits': -0.9998369744007505, 'copy_length_bits': 1.0}`.

## Top Valid Candidates

| Book | Op | Mode | Delta | Slack | Gain bits | Total bits |
|---:|---:|---|---:|---:|---:|---:|
| `54` | `0` | `preserve_next_mode` | `2` | `2` | `-0.000163` | `8154.676431` |
| `13` | `8` | `preserve_next_mode` | `1` | `1` | `-0.280706` | `8154.956974` |
| `56` | `5` | `preserve_next_mode` | `1` | `1` | `-0.555325` | `8155.231593` |
| `30` | `3` | `preserve_next_mode` | `1` | `1` | `-0.577440` | `8155.253708` |
| `46` | `1` | `preserve_next_mode` | `1` | `2` | `-0.585156` | `8155.261424` |
| `24` | `0` | `preserve_next_mode` | `1` | `1` | `-0.585319` | `8155.261587` |
| `46` | `1` | `preserve_next_mode` | `2` | `2` | `-0.585350` | `8155.261618` |
| `17` | `7` | `trim_literal` | `1` | `1` | `-0.836501` | `8155.512769` |
| `23` | `8` | `preserve_next_mode` | `1` | `1` | `-0.873820` | `8155.550088` |
| `54` | `0` | `preserve_next_mode` | `1` | `2` | `-1.000163` | `8155.676431` |
| `21` | `1` | `preserve_next_mode` | `1` | `2` | `-1.000395` | `8155.676663` |
| `21` | `1` | `preserve_next_mode` | `2` | `2` | `-1.000789` | `8155.677058` |

## Decision

- Interpretation: No remaining positive partial local boundary shift improves the exact active scorer after two promotions.
- Current compression bound remains `8154.676268` bits.
- Row0 origin remains exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
