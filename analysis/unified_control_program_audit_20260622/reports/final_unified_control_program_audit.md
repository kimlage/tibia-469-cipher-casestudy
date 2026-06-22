# Final Unified Control Program Audit

Status: `analysis_only`
Classification: `unified_control_program_partial_coupling_not_generator`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

This audit asks whether the residual controls needed to reproduce the 70-book 469 corpus form a small, synchronized, prefix-generalizable control program, or whether the current explanation is still an operational atlas with better accounting.

It does not test plaintext, translation, fan glosses, semantics, or row0 origin. Row0 remains exogenous, and the compression bound remains separate from generation explanation.

## Inputs

- Recent latent-transducer gates: copy-state rescue, copy-candidate ranking, copy-hint lower bound, and copy-hint stream structure.
- Canonical derived-book operation skeleton used by the recent generation fronts.
- Best known copy-hint lower-bound policy from the copy-hint stream audit.

## Unified Residual Ledger

- Books covered: `60` derived books.
- Operations: `261` total, `208` copies, `53` literal runs.
- Copied digits: `9301`.
- Literal innovation tape: `266` digits, `883.633` raw uniform bits.
- Target starts derived from prior lengths: `261/261`.
- Source-address cost: `2550.594` bits.
- Same-length chunk hint cost: `2366.891` bits.
- Best known copy-hint rank cost: `1873.768` bits.
- Unique `type:length` control symbols: `10`.

The ledger makes the residual explicit: starts are downstream of the length sequence, but op type, length, literal innovation, copy hint rank, seed payload, and row0 are still declared or paid streams.

## Residual Cost Ledger

| Model | Bits | Interpretation |
| --- | ---: | --- |
| start/type/length/literal/source separated | `5289.866` | operational source-address declaration |
| start/type/length/literal/copy-hint | `4613.040` | source replaced by same-length copy hint |
| innovation tape + copy-hint + joint `type:length` stream | `3532.404` | best organized residual stream model |
| innovation tape + copy-hint + separate control streams | `3601.905` | organized residual without joint type:length |

The best organized residual model is `1757.462` bits below independent source-address declaration on the full ledger. This is a lower-bound/accounting improvement, not a generator, because it still pays the residual streams.

## Control-Tape Coupling Gate

Promoted relations: `['previous_op_to_next_control_symbol']`.

| Relation | Rows | Saving | Random p95 | Status |
| --- | ---: | ---: | ---: | --- |
| `book_phase_to_control_symbol` | `261` | `1.406` | `-0.898` | `WEAK_COUPLING_BELOW_EFFECT_GATE` |
| `joint_type_length_to_hint_or_literal_behavior` | `261` | `215.066` | `-101.399` | `AUDIT_ONLY_LEAKY_FEATURE` |
| `length_bucket_to_hint_rank_bucket` | `208` | `2.997` | `-54.234` | `WEAK_COUPLING_BELOW_EFFECT_GATE` |
| `op_type_position_to_literal_consumption` | `261` | `187.716` | `-69.498` | `AUDIT_ONLY_LEAKY_FEATURE` |
| `previous_op_to_next_control_symbol` | `261` | `47.178` | `-61.852` | `PROMOTED_COUPLING_CLUE` |

Only `previous_op_to_next_control_symbol` is promoted as a non-tautological coupling clue. The literal-consumption and joint type:length relations are kept audit-only because their features leak the field being explained. Length-bucket and book-phase effects beat weak controls but remain below the effect-size gate.

## Unified Program Holdout

- Total independent-source test bits across cutoffs: `10178.609`.
- Total best unified test bits across cutoffs: `6757.999`.
- Reduction vs independent source: `3420.610` bits.
- Exact books without atlas: `0`.
- Exact ops without atlas: `0`.
- Fields still external: `['type_length_control_stream', 'literal_innovation_tape', 'copy_hint_rank_stream', 'seed_books_0_9', 'row0']`.

The holdout result shows that organized residual streams compress the remaining controls better than independent source-address declaration, but no book or operation is generated exactly without the atlas/control streams.

## Decision

- Final classification: `unified_control_program_partial_coupling_not_generator`.
- `row0` unchanged: still exogenous under current evidence.
- `compression_bound` unchanged: this audit organizes residual generation fields and does not claim a new compression bound.
- Generative status: partial synchronization clue, not a promoted unified control program.
- Current explanation: strong mechanical parser/compressor with explicit residual streams; not a complete authorial generator.

## Remaining External Fields

- `type_length_control_stream`
- `literal_innovation_tape`
- `copy_hint_rank_stream`
- `seed_books_0_9`
- `row0`

## Next Blocker

The next real blocker is not another local source/rank selector. It is a target-free rule that generates the `type:length` control stream, the literal innovation tape schedule/payload, and copy-hint ranks jointly enough to reduce declared fields under prefix/holdout. Without that, the route remains an organized residual ledger rather than a compact generation formula.

## Reproducible Artifacts

- [01_unified_residual_control_ledger.py](../scripts/01_unified_residual_control_ledger.py)
- [01_unified_residual_control_ledger.json](test_results/01_unified_residual_control_ledger.json)
- [01_unified_residual_control_ledger.md](test_results/01_unified_residual_control_ledger.md)
- [02_unified_control_program_tests.py](../scripts/02_unified_control_program_tests.py)
- [02_unified_control_program_tests.json](test_results/02_unified_control_program_tests.json)
- [02_unified_control_program_tests.md](test_results/02_unified_control_program_tests.md)
- [03_compile_final_unified_control_program_audit.py](../scripts/03_compile_final_unified_control_program_audit.py)
