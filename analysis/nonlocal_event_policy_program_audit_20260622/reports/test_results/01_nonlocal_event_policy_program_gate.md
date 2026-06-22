# Nonlocal Event Policy Program Gate

Classification: `nonlocal_event_policy_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

This gate tests replay events as a joint sequence, not as separate source/length/literal subcodecs.

| Stream | Events | Alphabet | Splits | Positive | Shuffle p95 wins | Beam exact hits | Total Saving Bits |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `type_length` | 62 | 14 | 3 | 0 | 0 | 0 | -15.097 |
| `type_length_sourcebucket` | 62 | 27 | 3 | 0 | 1 | 0 | -12.766 |

## Decision

`nonlocal sequence models do not generate or reduce the joint event policy stream in holdout after model cost`

No v9 reduction is integrated in this run.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
