# Current Formula Dependency Scoreboard

Classification: `current_formula_dependencies_mapped_no_new_bound`
Translation delta: `NONE`

## Purpose

This audit re-counts the dependencies of the current local-source-bound
formula and maps each retained declaration to the gate that explains why
it is not yet derived. It does not change the compression bound.

## Current Formula

- Formula: `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_formula_469.json`.
- Formula classification: `full_corpus_source_substitution_fourth_pass_improves_bound`.
- Current local-source bound: `8160.825608` bits.
- Roundtrip: `70/70` books.
- Ops: `348` total, `87` literal, `261` copy.
- Literal digits: `857` (`0.076090`).
- Copied digits: `10406` (`0.923910`).

## Dependency Ledger

| Dependency | Units | Coverage | Status | Mainline priority |
|---|---:|---|---|---|
| `row0_table` | `99` | 99 ordered codes / 55 unordered pair rows | `exogenous_substrate` | `external_or_provenance` |
| `copy_source` | `261` | 10406 copied digits | `encoder_canonical_decoder_declared` | `structural_parser` |
| `copy_length` | `261` | 10406 copied digits | `partly_decodable_declared_exceptions_retained` | `structural_parser` |
| `literal_payload` | `87` | 857 literal digits | `mostly_forced_payload_model_retained` | `downstream_of_structural_parser` |
| `item_type_stream` | `265` | item/copy-literal shape stream | `learned_stream_retained_not_compact_op_type_field` | `parser_sequence_later` |

## Blockers

### row0_table

- Blocker: No primary CipSoft/source artifact or paid row0-origin formula.
- Next testable unlock: Primary source, fixed external source, or paid holdout-capable row0 algorithm.
- Evidence: `{'parallel_verdict': 'row0_origin_exogenous_under_current_evidence', 'paid_anchor_decision': 'explicit_paid_anchor_model_does_not_beat_lookup', 'all_anchors_explicit_pair_label_net_bits': -11.851749041416053}`

### copy_source

- Blocker: Earliest-source regularity depends on future target text; state-free and distance replacements lose.
- Next testable unlock: Joint source/length parser with decoder-known state, not same-chunk local substitution.
- Evidence: `{'earliest_source_hits': 261, 'copy_items': 261, 'ambiguous_source_candidate_ops': 138, 'distance_replacement_penalty_bits': 25.551406147975285, 'state_free_penalty_bits': 15.186017251789963, 'local_source_frontier_saturated': True}`

### copy_length

- Blocker: High-coverage target-max is encoder-only; decoder model still carries 201 exceptions.
- Next testable unlock: Decoder-computable length rule or joint source/length objective that pays its exceptions.
- Evidence: `{'decoder_default_count': 60, 'decoder_exception_count': 201, 'encoder_target_max_match_count': 238, 'encoder_target_max_decodable': False, 'midpoint_prefix_frozen_win_count': 5}`

### literal_payload

- Blocker: Most literals are forced by copy unavailability; remaining simplifications and repairs are worse.
- Next testable unlock: Only a new source/length representation can plausibly absorb the small optional literal frontier.
- Evidence: `{'forced_literal_digits': 760, 'optional_literal_digits': 97, 'best_cross_op_delta_bits': 0.02743357555300463, 'active_literal_payload_bits': 2613.660822752486, 'order1_full_delta_bits': 95.96760019306384, 'best_modal_default_delta_bits': 38.04883314088829}`

### item_type_stream

- Blocker: Compact op type is derivable, but the learned item-type sequence remains part of the score.
- Next testable unlock: Only revisit if a full parser derives operation sequence under holdout.
- Evidence: `{'item_type_stream_bits': 212.01191674175735, 'removed_type_fields': 348, 'score_delta_bits_after_type_derivation': 0.0}`

## Decision

- Compression bound is unchanged at `8160.825608` bits.
- Local same-chunk source substitution is already saturated.
- The next mainline mechanical work should be a structural decoder-known source/length parser or objective.
- Literal payload and item-type work are downstream unless that structural parser changes available copy choices.
- Row0 remains exogenous and requires primary provenance or a paid origin formula.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- No row0-origin formula is promoted.
- No new book-generation formula is emitted.
