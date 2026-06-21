# Generation Boundary Closure Audit

Classification: `generation_boundary_open_no_generator_promoted`
Translation delta: `NONE`

## Purpose

Consolidate the recent analysis-only generation gates into one current
boundary ledger: what is generated, what remains declared, and what the
next real blocker is.

## Summary

- Dependencies consolidated: `5`.
- Promoted generators: `0`.
- Materialized unit floor: `593`.
- Unit definition: book_order + 70 book lengths + 261 skeleton records + 208 source fields + 53 literal chunks.
- Next blocker: `operation_skeleton`.
- Compression bound: `unchanged_8154_676268`.
- Row0: `unchanged_exogenous`.

## Dependency Ledger

| Dependency | Status | Count | Best signal | Negative control |
| --- | --- | ---: | --- | --- |
| `book_order` | `canonical_retained_not_generated` | `1` | numeric survives full formula controls | prefix order-specific cutoffs = 0; frontier perfect in 10 orders including 6 random |
| `book_lengths` | `declared_residuals` | `70` | active residual ledger 1030 -> 566 bits | best source-free policy 14/70 exact; holdout cover-all 0/6 |
| `operation_skeleton` | `atlas_retained` | `261` | exact skeleton invariant across exposed-source policy/cutoff cases | best grammar 3/60 books and 14/261 ops |
| `copy_sources` | `declared_after_skeleton_and_payload` | `208` | target-aware controls hit 208/208 | best decoder-visible policy 8/208; context holdout cover-all 0/5 |
| `literal_payload` | `declared_after_skeleton` | `53` | 266 digits across 53 chunks; 103 digits are in chunks seen before | paid context +44.588 bits vs raw; holdout any-exact chunks 0/5 |

## Decision

- The current work has a robust parser/atlas boundary, not a source-free generator. The exact operation skeleton remains the first blocker; book lengths, literal payload, and copy sources remain declared dependencies even after their local gates.
- Do not count further compression micro-sweeps as progress unless they remove one of the declared dependencies above or generalize under holdout.
- The next constructive path is deriving the operation skeleton or finding a stronger target-stream account that removes the need to materialize it.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
