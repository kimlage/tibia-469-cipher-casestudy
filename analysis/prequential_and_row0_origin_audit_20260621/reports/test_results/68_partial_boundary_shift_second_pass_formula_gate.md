# Partial Boundary Shift Second-Pass Formula Gate

Classification: `partial_boundary_shift_second_pass_formula_improves_bound`
Translation delta: `NONE`

## Purpose

Gate 67 found one further exact-scored partial shift candidate after
the first partial-boundary promotion. This gate reapplies it and
materializes a new formula only if exact scoring improves.

## Summary

- Current total bits: `8155.261037`.
- Exact scorer reproduction: `8155.261037`.
- Candidate total bits: `8154.676268`.
- Candidate gain bits: `+0.584769`.
- Candidate: book `46`, op `1`, mode `preserve_next_mode`, delta `1` of slack `3`.
- Roundtrip errors: `0`.
- Score errors: `0`.
- Component deltas: `{'literal_bits_no_payload': 0.0, 'literal_payload_bits': 0.0, 'item_type_bits': 0.0, 'copy_source_bits': 0.0001937934102897998, 'copy_length_bits': -0.5849625007213035}`.
- Output formula: `analysis/authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_second_pass_formula_469.json`.

## Decision

- Compression-bound status: `promoted_8154_676268`.
- This is a mechanical formula update only.
- Row0 origin remains exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
