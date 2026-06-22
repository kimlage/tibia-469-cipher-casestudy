# Skeleton Generation Route Review

Classification: `skeleton_generation_route_review_boundary_frontier_saturated`
Translation delta: `NONE`

## Purpose

Step back from local boundary and length probes and decide which route,
if any, still moves toward a mechanical generator for the 70 books.

## Summary

- Routes reviewed: `8`.
- Promoted generator routes: `0`.
- Promoted clue/dependency routes: `2`.
- Rejected/weak/deferred routes: `5`.
- Open blocker: `operation_skeleton`.
- Recommended next route: `joint_target_stream_parser_or_latent_state`.

The current evidence says to stop local cutpoint/length/miss-label sweeps. The only live route that still aligns with a generator is a joint target-stream/parser or explicit latent-state account that emits digits and boundaries together, rather than choosing endpoints after the target text is known.

## Route Ledger

| Route | Status | Evidence | Next action |
| --- | --- | --- | --- |
| `dependency_boundary` | `OPEN_BLOCKER` | promoted_generators=0/5; materialized_unit_floor=593; next_blocker=operation_skeleton | keep operation_skeleton as first-class blocker |
| `simple_source_free_skeleton_grammar` | `REJECTED_CONTROL` | best_exact_books=3/60; op_hits=14/261; preq_cover_all=0/5 | do not continue simple context grammar sweeps |
| `operation_length_contexts` | `REJECTED_CONTROL` | best_exact_books=9/60; rowwise_exact_lengths=52/261; preq_cover_all=0/5 | do not rerun local length Markov/context policies |
| `scaled_or_lattice_cutpoint_geometry` | `REJECTED_CONTROL` | scaling_exact_books=42/60 but record_delta=35; lattice_hits=159/201 below_random_mean_lift=-2.357; recursive_hits=11/201 | do not continue proportional grid/recursive split paths |
| `target_digit_stream` | `PROMOTED_MECHANICAL_CLUE_NOT_GENERATOR` | best_model=prev2_digits; derived60_bpd=2.108869; beats_shuffled=True; promotes_generator=False | promote only as target-stream prior; exact residual still required |
| `target_digit_boundary_candidates` | `PROMOTED_DEPENDENCY_REDUCTION_NOT_GENERATOR` | best_policy=right_ge:4; saving=645.694; tp_fp_fn=94/841/107; exact_books=0/60 | retain as pruning/coding clue only |
| `boundary_residual_labels` | `WEAK_OR_REJECTED` | residual_delta=69.462 but preq=4/5; transition_best=shape beats_random_p95=False | stop treating miss labels as the next generator route |
| `downstream_after_exact_skeleton` | `DEFERRED_REJECTED_UNTIL_SKELETON_GENERATED` | literal_promoted=False; copy_source_promoted=False; both assume exact skeleton is granted | defer source/payload work until skeleton dependency falls |

## Stop Routes

- `simple_source_free_skeleton_grammar`
- `local_operation_length_context_sweeps`
- `proportional_cutpoint_grids`
- `boundary_miss_label_classification`
- `downstream_source_payload_before_skeleton`

## Decision

- Do not promote any new skeleton generator.
- Retain `prev2` target-digit and boundary threshold evidence only as mechanical clues/dependency reducers.
- Stop local boundary-miss and simple length/cutpoint rule sweeps unless a new latent state or joint target-stream parser is introduced.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
