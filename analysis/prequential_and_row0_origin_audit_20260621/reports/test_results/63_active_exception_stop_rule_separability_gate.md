# Active Exception Stop-Rule Separability Gate

Classification: `active_exception_stop_rule_not_separable_by_simple_features`
Translation delta: `NONE`

## Purpose

Gate 62 closes the local residual target-max rewrite frontier. This
gate asks whether the 19 remaining stop-before-target-max boundaries
are separable by simple single-feature or two-feature conjunction rules.
It does not emit a formula or change the compression bound.

## Summary

- Copy events: `261`.
- Target-max exceptions: `19`.
- Rules tested: `300`.
- Decoder-valid rules tested: `105`.
- Exact separators: `0`.
- Decoder-valid exact separators: `0`.

## Best Rule

- Rule: `next_type_copy & next_length_ge_20`.
- Decoder-valid: `False`.
- TP/FP/FN/TN: `11` / `53` / `8` / `189`.
- Precision/recall/F1: `0.171875` / `0.578947` / `0.265060`.

## Best Decoder-Valid Rule

- Rule: `book_lt_35 & length_le_10`.
- TP/FP/FN/TN: `8` / `55` / `11` / `187`.
- Precision/recall/F1: `0.126984` / `0.421053` / `0.195122`.

## Controls

- Permutation trials: `1000`.
- Permuted max-F1 min/median/max: `0.155340` / `0.222222` / `0.375000`.
- P(permuted max F1 >= observed): `0.160000`.
- Permuted exact separators: `0`.

## Decision

- Interpretation: The residual stop boundaries are not isolated by simple declared feature rules. The best rule uses recipe/target-adjacent features, captures only 11 of 19 exceptions, and has many false positives; the best decoder-valid rule is weaker. A nonlocal parser would need richer state than these single or pairwise feature stops.
- Current compression bound remains `8156.049986` bits.
- Copy length remains a declared dependency; simple stop rules do not derive the residual segmentation boundary.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- No new formula is emitted.
