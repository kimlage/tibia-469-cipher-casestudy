# Active Exception Partial Boundary Shift Gate

Classification: `active_exception_partial_boundary_shift_candidate_found`
Translation delta: `NONE`

## Purpose

Gate 62 exact-scored only the full shift to target-max for each residual
copy-length exception. This gate exact-scores every positive partial
boundary shift up to target-max inside the same two-operation local window.

## Summary

- Current total bits: `8156.049986`.
- Exact scorer reproduction: `8156.049986`.
- Exceptions tested: `19`.
- Shift candidates tested: `229`.
- Valid candidates: `213`.
- Improving candidates: `2`.
- Candidate count by mode: `{'literalize_next_remainder': 114, 'preserve_next_mode': 114, 'trim_literal': 1}`.
- Valid count by mode: `{'literalize_next_remainder': 98, 'preserve_next_mode': 114, 'trim_literal': 1}`.
- Improving count by mode: `{'literalize_next_remainder': 0, 'preserve_next_mode': 2, 'trim_literal': 0}`.

## Best Valid Candidate

- Book/op: `10` / `0`.
- Mode: `preserve_next_mode`.
- Delta/slack: `3` / `72`.
- Candidate total bits: `8155.261037`.
- Candidate gain bits: `+0.788949`.
- Component deltas: `{'literal_bits_no_payload': 0.0, 'literal_payload_bits': 0.0, 'item_type_bits': 0.0, 'copy_source_bits': -0.9975359600484808, 'copy_length_bits': 0.2085866218112642}`.

## Top Valid Candidates

| Book | Op | Mode | Delta | Slack | Gain bits | Total bits |
|---:|---:|---|---:|---:|---:|---:|
| `10` | `0` | `preserve_next_mode` | `3` | `72` | `+0.788949` | `8155.261037` |
| `46` | `1` | `preserve_next_mode` | `1` | `3` | `+0.584769` | `8155.465218` |
| `54` | `0` | `preserve_next_mode` | `2` | `2` | `-0.000163` | `8156.050149` |
| `46` | `1` | `preserve_next_mode` | `2` | `3` | `-0.000388` | `8156.050374` |
| `46` | `1` | `preserve_next_mode` | `3` | `3` | `-0.000581` | `8156.050568` |
| `10` | `0` | `preserve_next_mode` | `6` | `72` | `-0.250132` | `8156.300118` |
| `10` | `0` | `preserve_next_mode` | `5` | `72` | `-0.279060` | `8156.329046` |
| `13` | `8` | `preserve_next_mode` | `1` | `1` | `-0.363168` | `8156.413155` |
| `10` | `0` | `preserve_next_mode` | `1` | `72` | `-0.363392` | `8156.413378` |
| `56` | `5` | `preserve_next_mode` | `1` | `1` | `-0.555325` | `8156.605311` |
| `30` | `3` | `preserve_next_mode` | `1` | `1` | `-0.577440` | `8156.627426` |
| `24` | `0` | `preserve_next_mode` | `1` | `1` | `-0.585319` | `8156.635305` |

## Decision

- Interpretation: At least one partial boundary shift improves the exact active scorer. This is a candidate for formula promotion only after a separate promotion gate writes and validates a new formula.
- Current compression bound remains `8156.049986` bits.
- Copy length remains a declared dependency.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- No new formula is emitted.
