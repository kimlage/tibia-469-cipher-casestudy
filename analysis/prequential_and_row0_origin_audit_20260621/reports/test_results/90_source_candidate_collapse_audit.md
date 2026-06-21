# Source Candidate Collapse Audit

Classification: `source_canonicality_candidate_collapse_artifact`
Translation delta: `NONE`

## Purpose

Gate 89 tested source tie policies, but `precompute_matches` may already
collapse candidate sources before the parser sees them. This audit checks
the helper implementation and recounts hidden same-length alternatives.

## Findings

- Candidate collapse confirmed in `precompute_matches`: `True`.
- Projection copy events: `208`.
- Earliest-target-match count: `208/208`.
- Unique-target-match count: `78/208`.
- Events with hidden alternate sources: `130/208`.
- Max hidden alternates for one event: `13`.
- Gate 89 superseded: `True`.

## Decision

- The parser helper exposes only the earliest source for each copy length. Therefore the 208/208 earliest-target-match result is induced by candidate generation, not independent source evidence. Gate 89 could not change sources because alternate same-length sources were never exposed to the heap.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
