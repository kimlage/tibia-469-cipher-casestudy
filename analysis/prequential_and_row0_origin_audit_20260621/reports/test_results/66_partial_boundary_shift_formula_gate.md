# Partial Boundary Shift Formula Gate

Classification: `partial_boundary_shift_formula_improves_bound`
Translation delta: `NONE`

## Purpose

Gate 65 found an exact-scored partial boundary shift candidate. This
gate reapplies the best candidate, validates 70-book roundtrip, and
materializes a new formula only if the exact scorer improves.

## Summary

- Current total bits: `8156.049986`.
- Exact scorer reproduction: `8156.049986`.
- Candidate total bits: `8155.261037`.
- Candidate gain bits: `+0.788949`.
- Candidate: book `10`, op `0`, mode `preserve_next_mode`, delta `3` of slack `72`.
- Roundtrip errors: `0`.
- Score errors: `0`.
- Component deltas: `{'literal_bits_no_payload': 0.0, 'literal_payload_bits': 0.0, 'item_type_bits': 0.0, 'copy_source_bits': -0.9975359600484808, 'copy_length_bits': 0.2085866218112642}`.
- Output formula: `analysis/authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_formula_469.json`.

## Decision

- Compression-bound status: `promoted_8155_261037`.
- This is a mechanical formula update only.
- Row0 origin remains exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
