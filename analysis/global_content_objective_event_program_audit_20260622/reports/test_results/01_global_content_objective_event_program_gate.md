# Global Content Objective Event Program Gate

Classification: `global_content_objective_event_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This target-free decoder receives emitted prefix, remaining literal tape, and final stream length. It minimizes literal/copy event cost without scoring candidates against the target.

| Cutoff | Width | Best Prefix Digits | True Actions Survive | Exact Target In Beam | Best Len | Literal Pos |
| ---: | ---: | ---: | ---: | --- | ---: | ---: |
| 20 | 16 | 695 | 0 | `False` | 1015 | 531 |
| 20 | 64 | 695 | 0 | `False` | 1015 | 531 |
| 35 | 16 | 1053 | 0 | `False` | 1373 | 602 |
| 35 | 64 | 1053 | 0 | `False` | 1373 | 602 |
| 50 | 16 | 1300 | 0 | `False` | 1620 | 641 |
| 50 | 64 | 1300 | 0 | `False` | 1620 | 641 |

## Decision

`target-free global event objective does not keep or generate the true innovation suffix`

Exact beam splits: `0/3`; max true-action survival: `0`; best exact prefix: `1300/1962`.

No v9 reduction is integrated in this run.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
