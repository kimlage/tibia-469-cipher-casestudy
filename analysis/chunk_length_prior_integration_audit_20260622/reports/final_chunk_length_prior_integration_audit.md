# Final Chunk Length-Prior Integration Audit

Status: `analysis_only`
Classification: `POSTHOC_COPY_LENGTH_PRIOR_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can a decoder-visible copy-length prior inside the coarse bucket rescue the joint chunk-origin route by paying length first and then using the same-length copy hint?

## Result

Full-fit, the best family `bucket_opcount_pos` costs `562.273` length-prior bits; combined with the `1873.768`-bit copy hint, it is `-103.509` bits relative to the current composition-index + copy-hint ledger.

That gain does not generalize: prefix holdout has `0/5` positive-saving cells and `4/5` cells beating random p05.

## Decision

The length-prior rescue is posthoc under current evidence. It does not promote an executable generator component and does not change row0, plaintext, translation, or compression_bound.

## Reproducible Artifacts

- [01_chunk_length_prior_integration_gate.py](../scripts/01_chunk_length_prior_integration_gate.py)
- [01_chunk_length_prior_integration_gate.json](test_results/01_chunk_length_prior_integration_gate.json)
- [01_chunk_length_prior_integration_gate.md](test_results/01_chunk_length_prior_integration_gate.md)
