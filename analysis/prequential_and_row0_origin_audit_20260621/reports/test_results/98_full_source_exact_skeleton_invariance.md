# Full Source Exact Skeleton Invariance

Classification: `source_free_skeleton_exactly_invariant`
Translation delta: `NONE`

## Purpose

Gate 95 showed source-policy invariance only for coarse operation shape.
This audit compares the exact source-free skeleton: operation type,
target start, length, and forced flag, with source addresses removed.

## Result

- Observations: `525`.
- `(cutoff, book)` cases: `175`.
- Books represented: `60`.
- Case skeleton invariance: `175/175`.
- Book skeleton invariance across cutoffs/policies: `60/60`.
- Exact source-bearing signature invariance: `48/175`.
- Canonical skeleton op count: `261`.
- Canonical skeleton copy items: `208`.
- Canonical skeleton literal runs/digits: `53` / `266`.
- Canonical skeleton copied digits: `9301`.

## Decision

- Promotes generator: `False`.
- Source fields removed from skeleton atlas: `True`.
- Source fields removed from decoder: `False`.
- Removing source addresses from the exposed-source paths yields an exact operation skeleton that is invariant across policies and cutoffs. This is a real skeleton/segmentation atlas, but it is not a decoder-side generator because literal payload and copy source choices remain external.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
