# Final V5 Endpoint-Cascade Stability Audit

Status: `analysis_only`
Classification: `WEAK_V5_ENDPOINT_CASCADE_FULLFIT_ONLY`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit tested whether the obvious post-v5 extension, adding start-only endpoint use through a deterministic endpoint cascade, should replace v5.

The best policy is `end_then_start`. Full-fit residual falls from v5 `3220.921` to `3205.395` before declaration. After charging `2.000` bits for the policy family, the full-fit delta is `-13.526` bits.

Promotion fails because prefix selection is unstable: only `2/5` suffix splits improve, with aggregate delta `12.679`. The result is therefore a full-fit weak clue, not executable v6.

## Decision

`WEAK_V5_ENDPOINT_CASCADE_FULLFIT_ONLY`.

Executable v5 remains the promoted program frontier. The next useful route should not be another endpoint-priority selector unless it adds a new source of marks or clears prefix holdout.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_v5_endpoint_cascade_stability_gate.py](../scripts/01_v5_endpoint_cascade_stability_gate.py)
- [01_v5_endpoint_cascade_stability_gate.json](test_results/01_v5_endpoint_cascade_stability_gate.json)
- [01_v5_endpoint_cascade_stability_gate.md](test_results/01_v5_endpoint_cascade_stability_gate.md)
