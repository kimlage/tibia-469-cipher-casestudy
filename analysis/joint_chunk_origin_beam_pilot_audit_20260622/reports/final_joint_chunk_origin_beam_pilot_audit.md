# Final Joint Chunk-Origin Beam Pilot Audit

Status: `analysis_only`
Classification: `WEAK_JOINT_CHUNK_ORIGIN_BEAM_CLUE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can the selected joint chunk-origin route already reduce the executable copy/source tape when exact copy length is replaced by only the coarse length bucket?

## Result

The selected bucket chunk-origin policy is `long_freq_recent`. It costs `2649.756` rank bits across `208` copy ops, versus `1873.768` bits for the exact-length copy hint and `2550.594` raw source-address bits.

It saves `507.351` bits against uniform bucket-candidate ranks and beats the full random p05 control (`2827.207`), but it is `775.988` bits worse than the exact-length hint and has only `5/208` top-80 hits.

## Decision

`joint_chunk_origin_beam_pilot` remains open as a representation route, but this first bucket-level copy pilot is not an executable generator. The current blocker is the lack of a target-free length/chunk prior sharp enough to replace exact length plus copy hint. Row0, plaintext, translation, and compression_bound are unchanged.

## Reproducible Artifacts

- [01_bucket_chunk_origin_beam_pilot.py](../scripts/01_bucket_chunk_origin_beam_pilot.py)
- [01_bucket_chunk_origin_beam_pilot.json](test_results/01_bucket_chunk_origin_beam_pilot.json)
- [01_bucket_chunk_origin_beam_pilot.md](test_results/01_bucket_chunk_origin_beam_pilot.md)
