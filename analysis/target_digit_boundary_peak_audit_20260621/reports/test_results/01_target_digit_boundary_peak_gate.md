# Target Digit Boundary Peak Gate

Classification: `target_digit_boundary_peak_suppression_weak_not_promoted`
Translation delta: `NONE`

## Purpose

Test whether internal cutpoints are better modeled as local peaks or
non-maximum-suppressed rank peaks in the `prev2` right-surprisal stream,
without granting op-count.

## Summary

- Books/candidates/actual cutpoints: `60` / `9507` / `201`.
- Policies tested: `360`.
- Best peak policy: `nms_rank:top=0.05:gap=3`.
- Baseline full cutpoint atlas bits: `1570.073`.
- Correction bits after policy charge: `954.126`.
- Saving after policy charge: `615.947` bits.
- Random saving p95 before policy charge: `475.241` bits.
- TP/FP/FN: `57` / `360` / `144`.
- Predicted boundaries/correction events: `417` / `504`.
- Precision/recall: `0.136691` / `0.283582`.
- Exact books: `0/60`.
- Prefix-selected positive test-saving cells: `5/5`.

## Comparison To Threshold Gate

- Prior threshold policy: `right_ge:4`.
- Saving delta vs threshold: `-29.746` bits.
- Correction-event delta vs threshold: `-444`.
- False-positive delta vs threshold: `-481`.
- False-negative delta vs threshold: `37`.

Peak suppression removes many false positives but misses more real
cutpoints. It is a useful diagnostic, not a better dependency code.

## Top Full-Fit Peak Policies

| Policy | Saving | TP | FP | FN | Exact books |
| --- | ---: | ---: | ---: | ---: | ---: |
| `nms_rank:top=0.05:gap=3` | `615.947` | `57` | `360` | `144` | `0` |
| `nms_rank:top=0.05:gap=4` | `605.769` | `54` | `337` | `147` | `0` |
| `nms_rank:top=0.05:gap=2` | `604.120` | `56` | `376` | `145` | `0` |
| `nms_rank:top=0.05:gap=6` | `603.078` | `52` | `305` | `149` | `0` |
| `nms_rank:top=0.05:gap=8` | `602.901` | `50` | `280` | `151` | `0` |
| `nms_rank:top=0.05:gap=5` | `602.122` | `52` | `315` | `149` | `0` |
| `nms_rank:top=0.08:gap=3` | `601.751` | `62` | `566` | `139` | `0` |
| `nms_rank:top=0.1:gap=3` | `601.665` | `68` | `693` | `133` | `0` |

## Decision

- Peak replacement promoted: `False`.
- Endpoint generator promoted: `False`.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
