# Joint Chunk-Origin Route Gate

Classification: `JOINT_CHUNK_ORIGIN_ROUTE_REQUIRED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Select the next representation route after the executable tape ledger reached a practical frontier. This gate does not promote a formula; it prevents the next work from repeating exact chunk dictionaries, shallow signatures, or local tape codecs that have already failed.

## Route Matrix

| Route | Status | Evidence |
| --- | --- | --- |
| `exact_target_chunk_dictionary` | `REJECTED` | unique chunks 256/261; copy unique 207/208; dictionary delta 32442.167 bits |
| `coarse_target_chunk_signature` | `REJECTED` | best non-payload family kind_x_book_mod10_x_length_bucket has 85 signatures and 22 singleton rows; payload signatures rely on target digits |
| `current_external_tape_program` | `FRONTIER` | roundtrip True; promoted executable reductions 0; rejected routes 3 |
| `target_conditioned_source_collapse` | `LOWER_BOUND_ONLY` | source choice collapses after target chunk is granted, but target chunk remains the missing generator |
| `operation_boundary_chunk_reuse` | `REJECTED` | prior source-boundary alignment found no single-prior-chunk copy explanation and source starts/end rarely align to op boundaries |

## Requirements For The Next Gate

- `generate_or_keep_target_chunks_without_exact_chunk_dictionary`: prefix/family holdout must keep true chunk stream in beam above same-length/chunk-shuffled controls Failure: if exact chunks must be declared or payload signatures are used, route collapses to rejected dictionary/signature accounts
- `choose_source_and_length_jointly_after_chunk_hypothesis`: given generated chunk candidates, earliest-source collapse should reduce source tape with paid exceptions Failure: if source policy still needs future target text outside the generated chunk candidate, source remains external
- `consume_literal_innovation_as_part_of_chunk_origin`: literal/copy chunk candidates must share one innovation process and improve over separate literal payload + composition/source tapes Failure: if literal tape remains a separate payload declaration, representation has not changed enough
- `execute_decoder_without_atlas_corrections_dominating`: controller must reduce executable ledger after model, beam-rank, and correction costs Failure: if corrections exceed direct external tape declaration, it is only a predictive clue
- `survive_controls`: prefix holdout, public-bookcase family holdout, same-multiset chunk shuffle, same-length random chunks, and permuted train controls Failure: if gains vanish under controls, classify as parser/compressor artifact

## Next Constructive Gate

- Name: `joint_chunk_origin_beam_pilot`.
- Purpose: construct a beam over chunk-origin hypotheses instead of field tapes.
- Minimum success: `at least one nontrivial held-out book exact without full atlas correction; or reduction of combined chunk/source/literal external ledger after paid corrections; and stronger than same-length/chunk-shuffled controls`.

## Decision

The aligned next route is a joint chunk-origin beam pilot. It must explain chunk candidates, source choice, segmentation, and innovation together. Exact chunks, shallow signatures, current external tapes, and operation boundary block reuse are not sufficient under current evidence.
