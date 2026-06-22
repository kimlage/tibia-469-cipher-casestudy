# Final Target Chunk Signature Audit

Status: `analysis_only`
Classification: `TARGET_CHUNK_SIGNATURE_GENERATOR_REJECTED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

After rejecting an exact target-chunk dictionary, can the missing
target-stream be reduced to a compact coarse-signature layer rather
than exact copied/literal payload?

## Result

- Operation chunks: `261` (`208` copy, `53` literal).
- Target-stream digits: `9567`.
- Exact unique chunks from the dictionary audit: `256/261` (`0.981`).
- Best non-payload signature family: `kind_x_book_mod10_x_length_bucket`.
- Best non-payload signatures/singletons/selector bits: `85` / `22` / `495.649`.
- Least-unique payload family: `kind_x_length_bucket_x_digit_sum_mod10` with `90` signatures and `489.978` selector bits.
- Most-exact payload family: `kind_x_length_bucket_x_first2_last2` with `251` singleton rows over `256` signatures.

The non-payload signatures are too coarse: they reduce labels only by
leaving the exact target digits unresolved. Payload-derived signatures
become specific, but that specificity comes from first/last digits,
checksums, support sets, or histograms already read from the target
chunk. Same-length random controls show no promotable special structure.

## Decision

- No target-chunk signature generator is promoted.
- The target-stream blocker remains open.
- This is a falsification of a shallow latent-signature shortcut, not a new compression result.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Target chunk signature gate](test_results/01_target_chunk_signature_gate.md)
