# Active Residual Target-Max Resegmentation Gate

Classification: `active_residual_targetmax_resegmentation_saturated_no_improvements`
Translation delta: `NONE`

## Purpose

Gate 61 shows that 19 active copy lengths still stop before their
encoder target-max extension. This gate tests whether any remaining
local extend-and-trim rewrite improves the active formula under the
same exact component scorer used by the promoted target-max gates.

## Summary

- Current total bits: `8156.049986`.
- Exact scorer reproduction: `8156.049986`.
- Active exceptions tested: `19`.
- Candidate rows: `38`.
- Valid candidates: `34`.
- Invalid candidates: `4`.
- Improving candidates: `0`.
- Error histogram: `{'literal_forces_copy': 4}`.

## Best Valid Residual Candidate

- Book/op/mode: `54` / `0` / `preserve_next_mode`.
- Slack: `2`.
- Candidate total bits: `8156.050149`.
- Candidate gain bits: `-0.000163`.
- Component deltas: `{'literal_bits_no_payload': 0.0, 'literal_payload_bits': 0.0, 'item_type_bits': 0.0, 'copy_source_bits': -0.9998369744007505, 'copy_length_bits': 0.9999999999997726}`.

## Decision

- Interpretation: Every remaining active target-max exception was tested with the same local trim modes used by the promoted target-max gates. No exact valid candidate improves the active bound. The best valid residual rewrite is still worse by 0.000163 bits, so this local residual target-max resegmentation frontier is saturated.
- Current compression bound remains `8156.049986` bits.
- The residual local target-max resegmentation frontier is saturated under this exact scorer.
- Further progress requires a nonlocal joint parser rather than another local extend-and-trim rule.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- No new formula is emitted.
