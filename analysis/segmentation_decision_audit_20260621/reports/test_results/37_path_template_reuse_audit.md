# Path Template Reuse Audit

Classification: `path_template_reuse_hypothesis_rejected`
Translation delta: `NONE`

## Purpose

Gate 37 tests the next structural path/state hypothesis after branch-choice
weak signals were closed. It asks whether the remaining first-drift corrections
can be selected by reusing multi-operation stable templates already seen in
exact parser books under the same observable state key.

This is not a compression sweep and does not search row0 or plaintext.

## Summary

- Active classifier: `if_peak_len_le5_then_skip_to_next_peak_ge5`.
- Exact parser books: `50`.
- Residual parser books: `10`.
- Widths tested: `[1, 2, 3]`.
- Best template width: `1`.
- Best deterministic residual matches:
  `0/10`.
- Best library keys: `115`.
- Ambiguous keys at best width: `22`.
- Prequential cells with residuals and at least one deterministic residual
  match:
  `0/4`.
- Shuffle control `p_ge_observed`: `1.0000`.
- Promotes parser rule: `False`.

## Width Scoreboard

| width | library keys | ambiguous keys | deterministic residual matches | residuals | shuffle mean | p_ge_observed |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 115 | 22 | 0 | 10 | 0.000 | 1.0000 |
| 2 | 115 | 28 | 0 | 10 | 0.000 | 1.0000 |
| 3 | 115 | 29 | 0 | 10 | 0.000 | 1.0000 |

## Prequential Rows For Best Width

| cutoff | train exact books | test residuals | covered keys | deterministic keys | template matches |
| --- | --- | --- | --- | --- | --- |
| 20 | 8 | 8 | 1 | 0 | 0 |
| 30 | 15 | 5 | 1 | 0 | 0 |
| 40 | 23 | 3 | 1 | 0 | 0 |
| 50 | 32 | 2 | 1 | 0 | 0 |
| 60 | 40 | 0 | 0 | 0 | 0 |

## Residual Rows For Best Width

| book | op | drift class | support | deterministic key | match | active shape | stable shape |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | 0 | literal_understop | 0 | False | False | ('literal', 27) | ('literal', 39) |
| 16 | 9 | copy_started_inside_stable_literal | 0 | False | False | ('copy', 8) | ('literal', 1) |
| 20 | 2 | internal_copy_missed_as_literal | 0 | False | False | ('literal', 3) | ('copy', 10) |
| 21 | 0 | book_start_copy_missed_as_literal | 0 | False | False | ('literal', 7) | ('copy', 9) |
| 26 | 0 | book_start_copy_missed_as_literal | 0 | False | False | ('literal', 1) | ('copy', 11) |
| 34 | 7 | internal_copy_missed_as_literal | 0 | False | False | ('literal', 5) | ('copy', 5) |
| 39 | 0 | book_start_copy_missed_as_literal | 0 | False | False | ('literal', 7) | ('copy', 5) |
| 45 | 1 | internal_copy_missed_as_literal | 0 | False | False | ('literal', 1) | ('copy', 8) |
| 55 | 2 | copy_length_drift_same_source | 8 | False | False | ('copy', 45) | ('copy', 44) |
| 57 | 2 | literal_understop | 0 | False | False | ('literal', 17) | ('literal', 28) |

## Decision

Path-template reuse is not promoted. Under the tested observable state key and
exact source-free operation lengths, the exact-book template library does not
provide a deterministic reusable path template for the residual first-drift
corrections. This falsifies a simple "reuse a seen multi-op path shape"
explanation for the remaining branch decisions.

The next blocker remains a richer path/state mechanism or a source-free target
digit account.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
