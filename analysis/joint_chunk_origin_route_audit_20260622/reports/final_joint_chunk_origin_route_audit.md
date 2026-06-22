# Final Joint Chunk-Origin Route Audit

Status: `analysis_only`
Classification: `JOINT_CHUNK_ORIGIN_ROUTE_REQUIRED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

After the executable tape representation reached a frontier, what is the next representation change that can plausibly move toward a generative mechanism without reopening rejected local routes?

## Evidence

- Rejected routes consolidated: `3`.
- Frontier routes: `1`.
- Lower-bound-only routes: `1`.
- Next constructive gate: `joint_chunk_origin_beam_pilot`.

Exact target-chunk dictionaries and shallow chunk signatures are rejected. The executable external-tape program is useful as a ledger, but has no promoted tape reductions. Target-conditioned source collapse remains only a lower bound because it grants the missing target chunk.

## Decision

The next aligned route is `joint_chunk_origin_beam_pilot`: a representation that proposes chunk-origin hypotheses jointly with source choice, length, and literal innovation. Promotion should require nontrivial held-out exact books/ops or a paid reduction of the combined chunk/source/literal ledger, above chunk-shuffled and same-length controls.

## Reproducible Artifacts

- [01_joint_chunk_origin_route_gate.py](../scripts/01_joint_chunk_origin_route_gate.py)
- [01_joint_chunk_origin_route_gate.json](test_results/01_joint_chunk_origin_route_gate.json)
- [01_joint_chunk_origin_route_gate.md](test_results/01_joint_chunk_origin_route_gate.md)
