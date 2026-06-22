# Final Markov Chunk-Content Prior Audit

Status: `analysis_only`
Classification: `MARKOV_CHUNK_CONTENT_PRIOR_REJECTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Does the prefix-trained `prev2` digit-content prior help choose same-length copy chunks, turning the strongest digit clue into a chunk-origin selector?

## Result

No. Across the five prefix holdouts, content-first Markov policies beat the frequency/recency copy-hint baseline in `0/5` cells. Aggregate best content-first Markov cost is `4244.687` bits versus `3998.858` for frequency/recency (`245.829` bits). Using Markov only as a tie-breaker also gives no improvement.

## Decision

`prev2` remains a target-digit/boundary clue, not a copy chunk-origin program. The next blocker is still a richer latent/nonlocal state that links length, chunk content, and copy availability. Row0, plaintext, translation, and compression_bound are unchanged.

## Reproducible Artifacts

- [01_markov_chunk_content_prior_gate.py](../scripts/01_markov_chunk_content_prior_gate.py)
- [01_markov_chunk_content_prior_gate.json](test_results/01_markov_chunk_content_prior_gate.json)
- [01_markov_chunk_content_prior_gate.md](test_results/01_markov_chunk_content_prior_gate.md)
