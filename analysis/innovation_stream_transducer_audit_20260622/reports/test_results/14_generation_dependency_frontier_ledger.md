# Generation Dependency Frontier Ledger

Classification: `GENERATION_FRONTIER_INTERNAL_STARTS_MAIN_BLOCKER`
Translation delta: `NONE`

## Purpose

Consolidate the post-gate dependency frontier after the innovation-stream
transducer tests. This is a bookkeeping audit, not a compression sweep.

## Summary

- Derived/seed books: `60` / `10`.
- Canonical ops/copy/literal: `261` / `208` / `53`.
- Literal tape digits: `266`.
- Book-start/internal ops: `60` / `201`.
- Book-start literal/copy modes: `13` / `47`.
- Right_ge:4 candidates/actual/nonstarts: `995` / `154` / `841`.
- Right_ge:4 missed internal starts: `107`.
- Tape structure promoted: `True`.
- Closed-loop exact books: `0`.
- Target-conditioned replay exact books: `22`.
- Internal trigger promoted: `False`.
- Book-start mode promoted: `False`.
- Next aligned route: `derive internal operation starts without target-future oracle; book-start and tape-shape clues are useful but do not yet form a generator`.

## Frontier Items

| Dependency | Status | Evidence | Remaining |
| --- | --- | --- | --- |
| `row0_table` | `external_unchanged` | All innovation-stream gates preserve row0_origin_status=unchanged_exogenous. | full row0 origin remains outside this generation route |
| `seed_books_0_9_payload` | `external_seed_material` | The innovation tape route generates only derived books 10..69 from granted seed material. | seed payload not derived here |
| `literal_innovation_tape` | `tape_shaped_clue_promoted_not_generated` | 266 literal digits; tape structure promoted, Markov bits 879.609; seed subcodec remains -180.128 bits vs raw tape. | raw tape payload and its origin/order still external |
| `tape_consumption_schedule` | `sparsity_weak_not_policy` | schedule best feature global_majority; feature delta -5.585 bits; promotes=False. | when to consume tape vs copy remains unresolved |
| `book_start_existence` | `structural_clue_retained` | right_ge:4 candidate labels recover 34/94 starts with decoder-visible book_start feature. | only the existence of a first operation is explained |
| `book_start_mode` | `rejected_policy_external` | 13/47 literal/copy starts; best non-global delta -4.000 bits. | literal/copy mode at book start remains declared |
| `internal_operation_starts` | `blocked_rejected_current_route` | 201 internal canonical ops; right_ge:4 includes 94 and misses 107; internal candidate trigger hits 0/70 even with target-conditioned copy availability. | internal op-start parser remains the main blocker |
| `target_conditioned_copy_availability` | `conditional_clue_not_closed_loop` | known-start trigger delta 48.262 bits; decoder-visible trigger delta -4.807 bits. | copy availability still relies on target future where promoted |
| `copy_source_and_length` | `external_fields_after_shape` | copy ops 208; replay source+length hits 47/208 under target-conditioned replay. | source and length fields are not generated |
| `closed_loop_generation` | `not_promoted` | sync exact books 0/60; target-conditioned replay exact books 22/60 with shuffled p95 23.0. | no closed-loop generated derived book set |

## Decision

- No generator is promoted by this ledger.
- The current main blocker is internal operation-start generation.
- Book-start existence and tape-shaped payload are useful clues, but neither derives the internal skeleton.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
