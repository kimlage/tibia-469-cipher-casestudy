# V5 External Dependency Frontier Synthesis

Classification: `V5_EXTERNAL_DEPENDENCY_FRONTIER_SYNTHESIS`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Frontier

- Promoted frontier: `executable_v5_source_endpoint_memory`.
- V5 external bits excluding seed: `4097.333`.
- V5 external bits including seed: `9731.323`.

## Largest Non-Seed Blocker Components

| Component | Bits |
| --- | ---: |
| `copy_fallback_hint_bits` | `891.118` |
| `literal_payload_bits` | `883.633` |
| `residual_composition_bits` | `439.959` |

## Largest Non-Seed Paid Components

| Component | Bits |
| --- | ---: |
| `copy_fallback_hint_bits` | `891.118` |
| `literal_payload_bits` | `883.633` |
| `online_x64_coarse_bits` | `876.412` |
| `residual_composition_bits` | `439.959` |
| `representation_declaration_bits` | `1.585` |

## Route Ledger

| Route | Status | Evidence |
| --- | --- | --- |
| `executable_v5_source_endpoint_memory` | `promoted` | external excluding seed 4109.138 -> 4097.333; robust=True |
| `v5_endpoint_priority_cascade` | `weak_fullfit_only_not_promoted` | full-fit delta -13.526; prefix positive 2/5 |
| `near_source_mark_offset` | `rejected_lower_bound_only` | offset-only delta -760.558; paid source delta 153.030 |
| `source_mark_identity_stream` | `rejected_exact_stream` | best valid global_delta_rank_plus_offset delta 105.634; invalid bucket lower bound -435.248 |
| `literal_payload_generation` | `closed_not_promoted` | source-free literal payload generator rejected; prefix/holdout exact chunks 0/5 |
| `literal_reference_subcodec` | `closed_not_promoted` | prior-reference recurrence loses after mode/source cost |
| `shared_literal_length_tape` | `weak_clue_not_promoted` | literal tape retained only as weak shared-innovation clue |

## Next Route

`joint_content_origin_program`: A future constructive route must jointly model exact copy-origin mark identity and literal innovation payload as content-origin choices. Local endpoint priority, local offsets, exact rank-delta streams, and literal reference subcodecs are closed under current evidence.

Promotion requires:
- reduce copy_fallback_hint_bits or literal_payload_bits after paying exact identity/payload costs
- survive prefix/suffix holdout or shuffled/source-mark controls
- remain executable with 70/70 roundtrip and no target-content oracle

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
