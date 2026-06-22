# Final Seed Bootstrap Decision-Policy Audit

Status: `analysis_only`
Classification: `seed_bootstrap_decision_policy_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit isolates the policy missing from the failed target-free seed transducer. It stays on the true seed prefix path and tests whether small decoder-visible rules can predict the oracle surface action (`copy` vs `literal`) under prefix holdout.

The oracle surface has `473` decision rows with action counts `{'literal': 361, 'copy': 112}`. Prefix-selected visible-state rules reach mean test accuracy `0.446`. Shuffled-label controls have p95 mean accuracy `0.847`.

## Decision

`seed_bootstrap_decision_policy_not_promoted`.

This does not generate the seed stream. It only tests the decision layer on the correct prefix path; source and length selection remain external. The result should be used to decide whether a richer bootstrap policy is worth integrating into a decoder.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_seed_bootstrap_decision_policy_gate.py](../scripts/01_seed_bootstrap_decision_policy_gate.py)
- [01_seed_bootstrap_decision_policy_gate.json](test_results/01_seed_bootstrap_decision_policy_gate.json)
- [01_seed_bootstrap_decision_policy_gate.md](test_results/01_seed_bootstrap_decision_policy_gate.md)
