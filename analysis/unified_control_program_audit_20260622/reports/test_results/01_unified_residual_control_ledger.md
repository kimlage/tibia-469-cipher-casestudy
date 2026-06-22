# Unified Residual Control Ledger

Classification: `unified_residual_control_ledger_built`
Translation delta: `NONE`

## Summary

- Books covered: `60` derived books.
- Ops: `261` (`208` copy, `53` literal).
- Target starts derived from prior lengths: `261/261`.
- Literal tape digits/bits: `266` / `883.633`.
- Copy digits: `9301`.
- Source-address bits: `2550.594`.
- Same-length chunk hint bits: `2366.891`.
- Rank-coded copy hint bits: `1873.768`.
- Unique type:length symbols: `10`.

## Field Status

- `target_start`: derived if the prior operation lengths are known.
- `op_type`: external control stream in this ledger.
- `length`: external control stream in this ledger.
- `literal_payload`: external innovation tape.
- `copy_source_raw`: replaced analytically by a paid same-length copy hint where length is granted.
- `copy_hint_rank`: external copy-control stream; lower bound promoted, simple rank-bucket structure rejected.
- `row0`: unchanged exogenous.

## Sample Rows

| Book | Op | Start | Type | Len | External Fields | Clues | Target Dependency |
| ---: | ---: | ---: | --- | ---: | --- | --- | --- |
| `10` | `0` | `0` | `literal` | `5` | `op_type,length,literal_payload` | `innovation_tape_structure_clue_not_generator` | `literal_payload_is_target_digits` |
| `10` | `1` | `5` | `copy` | `276` | `op_type,length,copy_hint_rank` | `copy_hint_lower_bound_promoted,copy_hint_simple_structure_rejected` | `copy_hint_rank_computed_against_canonical_target_payload` |
| `11` | `0` | `0` | `literal` | `6` | `op_type,length,literal_payload` | `innovation_tape_structure_clue_not_generator` | `literal_payload_is_target_digits` |
| `11` | `1` | `6` | `copy` | `7` | `op_type,length,copy_hint_rank` | `copy_hint_lower_bound_promoted,copy_hint_simple_structure_rejected` | `copy_hint_rank_computed_against_canonical_target_payload` |
| `11` | `2` | `13` | `copy` | `29` | `op_type,length,copy_hint_rank` | `copy_hint_lower_bound_promoted,copy_hint_simple_structure_rejected` | `copy_hint_rank_computed_against_canonical_target_payload` |
| `11` | `3` | `42` | `literal` | `7` | `op_type,length,literal_payload` | `innovation_tape_structure_clue_not_generator` | `literal_payload_is_target_digits` |
| `11` | `4` | `49` | `copy` | `30` | `op_type,length,copy_hint_rank` | `copy_hint_lower_bound_promoted,copy_hint_simple_structure_rejected` | `copy_hint_rank_computed_against_canonical_target_payload` |
| `11` | `5` | `79` | `copy` | `58` | `op_type,length,copy_hint_rank` | `copy_hint_lower_bound_promoted,copy_hint_simple_structure_rejected` | `copy_hint_rank_computed_against_canonical_target_payload` |
| `12` | `0` | `0` | `literal` | `2` | `op_type,length,literal_payload` | `innovation_tape_structure_clue_not_generator` | `literal_payload_is_target_digits` |
| `12` | `1` | `2` | `copy` | `19` | `op_type,length,copy_hint_rank` | `copy_hint_lower_bound_promoted,copy_hint_simple_structure_rejected` | `copy_hint_rank_computed_against_canonical_target_payload` |
| `12` | `2` | `21` | `copy` | `12` | `op_type,length,copy_hint_rank` | `copy_hint_lower_bound_promoted,copy_hint_simple_structure_rejected` | `copy_hint_rank_computed_against_canonical_target_payload` |
| `12` | `3` | `33` | `literal` | `4` | `op_type,length,literal_payload` | `innovation_tape_structure_clue_not_generator` | `literal_payload_is_target_digits` |

## Decision

- This is a ledger of residual external program fields, not a promoted generator.
- It is the substrate for residual-cost, coupling, and holdout tests in this front.
- No plaintext, translation, row0-origin claim, or case reopening is introduced.
