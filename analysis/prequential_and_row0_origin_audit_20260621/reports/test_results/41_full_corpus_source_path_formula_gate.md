# Full-Corpus Source Path Formula Gate

Classification: `full_corpus_source_path_formula_improves_bound`
Translation delta: `NONE`

## Purpose

Gate 40 showed that global source-path optimization helps under frozen
prefix counts. This gate tests whether the same structural idea can become
a full-corpus formula improvement: generate a candidate by exact DP over
same-chunk legal source choices, then rescore the candidate with the real
adaptive source default/exception stream.

## Summary

- Active total bits: `8177.317`.
- Candidate total bits: `8162.412`.
- Candidate gain: `+14.905` bits.
- Active copy-source bits: `3002.838`.
- Candidate copy-source bits: `2987.933`.
- Adaptive copy-source delta: `-14.905` bits.
- Frozen source delta used by optimizer: `-11.097` bits.
- Changed sources: `2/261`.
- Candidate legal source options considered: `637`.
- Active defaults/exceptions: `5` / `256`.
- Candidate defaults/exceptions: `7` / `254`.
- Max DP state count: `14`.
- Total DP transitions: `1737`.

## Promoted Formula

- [sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_path_optimized_formula_469.json](../../../authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_path_optimized_formula_469.json)

## Interpretation

The optimization is accepted only if the adaptive rescore improves the
full-corpus formula. The frozen-count DP is used only to propose a path;
it is not itself counted as the final score.

Segmentation and copy lengths remain fixed, so this does not solve the
complete active parser problem.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- Source choices remain explicit formula data unless derived by a future parser.
