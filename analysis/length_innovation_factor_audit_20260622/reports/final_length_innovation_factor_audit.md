# Final Length Innovation Factor Audit

Status: `analysis_only`
Classification: `length_innovation_factorization_clue_residual_external`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

After the exact `type:length` state program failed, this audit asks whether the length dependency has the wrong representation. It factors each exact length into a coarse `type:length_bucket` stream plus a within-bucket residual innovation tape.

This is a mechanical representation audit only. It does not test plaintext, translation, fan glosses, semantics, or row0 origin.

## Factorization Result

- Rows: `261`.
- Independent `op_type + exact_length`: `1855.639` bits.
- `type:length_bucket` stream: `775.003` bits.
- Uniform within-bucket residual tape: `966.638` bits.
- Factorized total: `1741.641` bits.
- Saving from factorization: `113.998` bits.

The factorization is useful because it reduces the declared exact-length dependency after paying the coarse stream. It is not a generator because it still pays the residual tape.

## Residual Codec Result

- Best residual feature: `type_bucket`.
- Best residual bits over prefix/suffix cutoffs: `2063.071`.
- Saving vs uniform residual: `-117.997` bits.
- Shuffled-control p95 saving: `-171.115` bits.
- Top1 residual hits: `53/493`.
- Promoted residual features: `[]`.

No residual codec is promoted. The best feature, `type_bucket`, is only weak relative to bad same-bucket residual controls and remains worse than uniform within-bucket residual declaration.

## Decision

- `length_innovation_factorization_clue_residual_external`.
- Exact length should now be tracked as two dependencies: coarse `type:length_bucket` control and a fine within-bucket residual tape.
- The fine residual tape is the unresolved length-innovation blocker.
- `row0`, translation, plaintext, and the compression bound remain unchanged.

## Remaining External Fields

- `type:length_bucket` control stream
- within-bucket length residual innovation tape
- literal innovation tape payload and schedule
- copy-hint rank stream
- seed books `0..9`
- `row0`

## Reproducible Artifacts

- [01_length_innovation_factor_gate.py](../scripts/01_length_innovation_factor_gate.py)
- [01_length_innovation_factor_gate.json](test_results/01_length_innovation_factor_gate.json)
- [01_length_innovation_factor_gate.md](test_results/01_length_innovation_factor_gate.md)
- [02_compile_final_length_innovation_factor_audit.py](../scripts/02_compile_final_length_innovation_factor_audit.py)
