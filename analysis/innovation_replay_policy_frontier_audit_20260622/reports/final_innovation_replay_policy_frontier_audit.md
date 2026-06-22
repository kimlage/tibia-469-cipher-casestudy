# Final Innovation Replay Policy Frontier Audit

Status: `analysis_only`
Classification: `innovation_replay_policy_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit tests the blocker left by executable v7: the unified innovation payload is now a smaller executable dependency, but its replay ledger is still target-conditioned. The gate tries simple online policies using only emitted material, total stream length, and the residual literal tape.

The best policy is `literal_only` and reaches only `242/1962` exact prefix digits. After suffix correction it is `4906.133` bits versus the v7 payload replay ledger.

Boundary diagnostics do not rescue the route: event starts hit segment boundaries in `5/62` cases, event ends in `5/62`, and copy source start+end both hit replay event boundaries in `0/39` copies.

## Decision

`innovation_replay_policy_not_promoted`.

The result keeps v7 promoted as a paid executable payload reduction, but does not turn its replay ledger into a source-free generator. The next blocker is specifically the copy/literal decision and copy source-length policy for the innovation stream.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_innovation_replay_policy_frontier_gate.py](../scripts/01_innovation_replay_policy_frontier_gate.py)
- [01_innovation_replay_policy_frontier_gate.json](test_results/01_innovation_replay_policy_frontier_gate.json)
- [01_innovation_replay_policy_frontier_gate.md](test_results/01_innovation_replay_policy_frontier_gate.md)
