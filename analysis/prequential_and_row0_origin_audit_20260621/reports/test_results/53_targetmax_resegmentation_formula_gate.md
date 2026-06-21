# Target-Max Resegmentation Formula Gate

Classification: `targetmax_resegmentation_formula_improves_bound`
Translation delta: `NONE`

## Purpose

Gate 52 found local target-max resegmentation proxy improvements. This
gate first proves that the exact component scorer reproduces the current
bound, then promotes the best single candidate only if roundtrip and exact
component scoring improve the formula.

## Summary

- Current formula bits: `8160.825608`.
- Current exact scorer bits: `8160.825608`.
- Candidate bits: `8158.766094`.
- Candidate gain: `+2.059513` bits.
- Candidate: book `9`, op `0`, mode `preserve_next_mode`, slack `4`.
- Roundtrip errors: `0`.
- Score errors: `0`.
- Component deltas: `{'literal_bits_no_payload': 0.0, 'literal_payload_bits': 0.0, 'item_type_bits': 0.0, 'copy_source_bits': 0.0033531567469253787, 'copy_length_bits': -2.0628666430261546}`.
- Inventory: `{'literal_runs': 87, 'literal_digits': 857, 'copy_items': 261, 'copied_digits': 10406}`.

## Promoted Formula

- [sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_formula_469.json](../../../authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_formula_469.json)

## Interpretation

This is the first promoted target-max resegmentation step. The gain comes
from copy-length coding; copy-source cost rises slightly, while literal
payload, literal structure, and item-type cost remain unchanged. The
result is mechanical only and does not affect row0 or semantics.

## Boundary

- Compression bound changes only after exact scorer reproduction and roundtrip validation.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
