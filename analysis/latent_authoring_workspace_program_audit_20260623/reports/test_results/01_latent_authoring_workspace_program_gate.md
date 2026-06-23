# Latent Authoring Workspace Program Gate

Classification: `latent_authoring_workspace_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- Baseline v9 bits: `6917.285`.
- Workspace lower-bound bits: `2279.414`.
- Cost comparison status: `not_comparable_lower_bound_grants_coarse_and_op_positions`.
- Test events in beam: `100/493`.
- True-path books in beam: `3`.
- Exact nontrivial books without correction: `0`.

## Control Gate

- Cutoff: `40`.
- Real events in beam: `20`; control p95 `19`.
- Real true-path books in beam: `1`; control p95 `1`.
- Real program bits: `2371.442`; control p05 `2390.663`.
- Beats event-beam p95: `True`.
- Beats true-path p95: `False`.
- Beats program-bits p05: `True`.

## Decision

`Workspace candidates do not generate nontrivial books or preserve true paths above controls; lower-bound bits do not reduce v9`.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
