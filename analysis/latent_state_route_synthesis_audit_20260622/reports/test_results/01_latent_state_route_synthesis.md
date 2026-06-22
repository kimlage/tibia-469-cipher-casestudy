# Latent-State Route Synthesis

Classification: `LATENT_NONLOCAL_STATE_ROUTE_REQUIRED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Consolidate the executable frontier and the first joint chunk-origin pilots so the next work does not keep reopening independent local priors.

## Route Matrix

| Route | Status | Evidence | Decision |
| --- | --- | --- | --- |
| `current_executable_tape_program` | `FRONTIER` | roundtrip=True; promoted_reductions=0; external_bits_excluding_seed=4358.858 | ledger retained, generator not promoted |
| `joint_chunk_origin_route` | `OPEN_ROUTE` | next_gate=joint_chunk_origin_beam_pilot; rejected_routes=3 | route remains aligned only if it becomes a joint state program |
| `bucket_chunk_origin_rank` | `WEAK_CLUE_NOT_EXECUTABLE` | rank_bits=2649.756; exact_hint_bits=1873.768; top80=5/208 | bucket-level candidate sets remain too broad |
| `copy_length_prior_then_hint` | `POSTHOC_NOT_PROMOTED` | full_fit_delta=-103.509; holdout_positive=0/5 | simple length context cannot be the next route |
| `prev2_content_prior_for_chunks` | `REJECTED_CONTROL` | content_first_delta=245.829; beats_freq=0/5 | prev2 remains digit/boundary clue, not chunk selector |
| `observable_stateful_control` | `REJECTED_CONTROL` | best_model=remaining_prev_bucket; delta_vs_independent=-1001.211; greedy_exact_books=0; beam20_nontrivial=0 | observable previous/remaining state is not enough |
| `unified_control_coupling` | `PARTIAL_CLUE_NOT_GENERATOR` | exact_books_without_atlas=0; exact_ops_without_atlas=0; promoted_couplings=1 | coupling clue exists but does not generate program |

## Next Gate

- Name: `latent_nonlocal_state_program_pilot`.
- Purpose: test a hidden/nonlocal state that jointly emits or keeps in beam operation control, length/chunk origin, literal innovation, and copy availability, rather than scoring those fields independently.
- Minimum success:
  - nontrivial held-out exact book or exact operation subsequence without atlas correction
  - or paid reduction of combined control+length+literal+copy-hint ledger under prefix/family holdout
  - and stronger than same-multiset, same-length, digit-shuffled, and permuted-order controls

## Decision

The next aligned work is a latent/nonlocal state program. A new gate should jointly reduce control, length/chunk origin, literal innovation, and copy availability. More isolated length, content, or source priors are closed unless embedded in that joint program.
