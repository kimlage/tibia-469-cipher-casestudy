# Source Boundary Alignment Audit

Classification: `source_boundary_block_hypothesis_rejected`
Translation delta: `NONE`

## Purpose

Gate 15 tests a block/chunk hypothesis for segmentation: copy
intervals might be chosen because they respect operation or book
boundaries already present in the source stream. This is a structural
generation hypothesis, not a compression sweep.

## Boundary Coverage

- Copy rows tested: `208`.
- Source starts on prior operation boundary: `28/208`.
- Source ends on prior operation boundary: `29/208`.
- Source starts on prior book boundary: `17/208`.
- Source ends on prior book boundary: `18/208`.
- Source interval has no internal prior operation boundary: `111/208`.
- Source interval equals one prior chunk: `0/208`.

## Candidate Controls

| Control | Expected source-end boundary hits |
|---|---:|
| Uniform over all legal candidate pairs | `6.867` |
| Uniform over global-max candidate pairs | `28.580` |
| Declared pairs | `29` |

The declared source-end boundary rate is close to the global-max
candidate control because the retained parser already chooses global
max copies. It is not an independent chunk-boundary rule.

## Source Tie Policies

| Policy | Hits | Misses |
|---|---:|---:|
| `earliest` | `207/208` | `1` |
| `end_boundary_then_earliest` | `198/208` | `10` |
| `start_boundary_then_earliest` | `199/208` | `9` |
| `both_boundaries_then_earliest` | `206/208` | `2` |
| `no_internal_boundary_then_earliest` | `167/208` | `41` |

## Decision

- Promotes source-boundary rule: `False`.
- Best boundary-aware policy: `both_boundaries_then_earliest` with `206/208` hits.
- Lift vs existing earliest-source global-max rule: `-1`.
- Source-side operation boundaries do not explain copy chunking. Only a small minority of declared copies start or end on an available prior operation boundary, almost none equal one prior chunk, and boundary-aware global-max tie-breakers are worse than the existing earliest-source rule.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
