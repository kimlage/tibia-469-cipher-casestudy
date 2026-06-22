# Final Nonlocal Event Policy Program Audit

Status: `analysis_only`
Classification: `nonlocal_event_policy_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit follows the live internal route from the generator decision ledger: a nonlocal event-policy program over the v9 innovation replay.
It codes the replay event sequence under train-prefix holdout and checks whether the true suffix remains in finite beams.

For the main joint stream `type_length_sourcebucket`, total saving is `-12.766` bits across `3` splits, with `0` positive splits, `1` shuffle-p95 wins, and `0` exact suffix beam hits.

## Decision

`nonlocal_event_policy_program_not_promoted`.

Nonlocal sequence models do not generate or reduce the joint event policy stream in holdout after model cost.

This does not change v9, row0, plaintext, semantics, or the compression bound.

## Reproducible Artifacts

- [01_nonlocal_event_policy_program_gate.py](../scripts/01_nonlocal_event_policy_program_gate.py)
- [01_nonlocal_event_policy_program_gate.json](test_results/01_nonlocal_event_policy_program_gate.json)
- [01_nonlocal_event_policy_program_gate.md](test_results/01_nonlocal_event_policy_program_gate.md)
