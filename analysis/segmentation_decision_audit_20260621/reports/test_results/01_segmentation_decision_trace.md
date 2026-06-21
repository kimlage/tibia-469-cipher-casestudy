# Segmentation Decision Trace

Classification: `segmentation_decision_trace_audit_only`
Translation delta: `NONE`

## Purpose

This trace converts the retained `(source,length)` dependency into a
per-copy decision ledger. It is analysis-only: it does not emit a
new formula and it does not alter row0, plaintext, translation, or the
compression bound.

## Summary

- Stable-projection operations traced: `262`.
- Reference skeleton operations: `261`.
- Copy decisions traced: `208`.
- Candidate pair count median: `80.000`; max: `1248.0`.
- Extra digits if extending declared source to max median: `0.000`; max: `1.0`.
- Declared length is max for `207/208` copies.
- Declared length is min for `7/208` copies.
- Declared length equals previous in-book length for `1/208` copies.
- Extending to max would change literal payload in `0` copy decisions.
- Declared boundary preserves a recurrent copy opportunity in `123` copy decisions.
- Hard-case books by candidate-pair pressure: `[10, 28, 33, 35, 37, 40, 46, 47, 48, 50, 53, 56, 57, 59, 61, 62, 63, 64, 65, 66, 67, 68, 69]`.

## Hard Cases

| Book | Op | Declared source | Declared length | Decoder max | Candidate pairs | Extend extra | Declared boundary pairs | Max boundary pairs |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `66` | `0` | `1696` | `210` | `210` | `1248` | `0` | `0` | `0` |
| `53` | `0` | `7130` | `271` | `271` | `706` | `0` | `0` | `0` |
| `65` | `1` | `9955` | `146` | `146` | `683` | `0` | `123` | `123` |
| `68` | `0` | `2869` | `143` | `143` | `668` | `0` | `0` | `0` |
| `69` | `0` | `1546` | `140` | `140` | `656` | `0` | `0` | `0` |
| `48` | `0` | `721` | `112` | `112` | `616` | `0` | `109` | `109` |
| `62` | `0` | `424` | `126` | `126` | `538` | `0` | `0` | `0` |
| `59` | `0` | `5059` | `141` | `141` | `533` | `0` | `166` | `166` |
| `59` | `2` | `42` | `79` | `79` | `521` | `0` | `0` | `0` |
| `63` | `1` | `1247` | `79` | `79` | `512` | `0` | `0` | `0` |
| `61` | `0` | `4514` | `122` | `122` | `457` | `0` | `96` | `96` |
| `10` | `1` | `0` | `276` | `276` | `442` | `0` | `0` | `0` |

## Decision

- This gate builds the required trace but promotes no segmentation rule.
- Structural hypotheses are tested in the next gate against this trace.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
