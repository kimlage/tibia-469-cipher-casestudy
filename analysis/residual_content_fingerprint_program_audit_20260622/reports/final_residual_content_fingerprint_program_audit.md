# Final Residual Content-Fingerprint Program Audit

Status: `analysis_only`
Classification: `residual_content_fingerprint_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This audit tests whether the remaining v6 fallback copy choices can be selected by a small paid fingerprint of the copied content. Exact length is treated as already paid by the executable ledger; the fingerprint filters same-length prior chunks, and any remaining ambiguity is paid as a rank.

The tested set is the `90` v6 fallback copy events. The best policy is `prefix_1`, with `0` unique content selections and delta `245.804` bits versus the existing copy-hint tape.

Prefix support is `0/5` positive splits; family support is `0` positive splits. Random-content controls have p05/p50/p95 deltas `241.635` / `248.687` / `255.289`; observed beats p05 is `False`.

## Decision

`residual_content_fingerprint_program_not_promoted`.

A paid content fingerprint is not currently a smaller executable content-selection program than the v6 copy-hint tape. This keeps the blocker at residual content origin/selection rather than source-address format.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.

## Reproducible Artifacts

- [01_residual_content_fingerprint_program_gate.py](../scripts/01_residual_content_fingerprint_program_gate.py)
- [01_residual_content_fingerprint_program_gate.json](test_results/01_residual_content_fingerprint_program_gate.json)
- [01_residual_content_fingerprint_program_gate.md](test_results/01_residual_content_fingerprint_program_gate.md)
