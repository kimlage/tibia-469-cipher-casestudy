# Chunk Length-Prior Integration Gate

Classification: `POSTHOC_COPY_LENGTH_PRIOR_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether a prefix-trained copy-length prior inside the granted coarse bucket can be integrated with the same-length copy hint to replace part of the external length/source ledger.

## Full-Fit Lower Bound

- Best family: `bucket_opcount_pos`.
- Full-fit length-prior bits: `562.273`.
- Copy-hint bits: `1873.768`.
- Integrated full-fit bits: `2436.040`.
- Current composition-index + copy-hint bits: `2539.550`.
- Full-fit delta vs current: `-103.509` bits.

## Prefix Holdout

| Cutoff | Selected family | Test ops | Length bits | Saving vs uniform | Beats random p05 | Integrated bits |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| `20` | `bucket_opcount_pos` | `155` | `647.085` | `-27.759` | `True` | `2081.258` |
| `30` | `bucket_opcount_pos` | `119` | `509.370` | `-17.162` | `True` | `1623.745` |
| `40` | `bucket_opcount_pos` | `80` | `349.610` | `-14.324` | `True` | `1124.562` |
| `50` | `bucket_opcount_pos` | `49` | `215.665` | `-5.308` | `True` | `707.433` |
| `60` | `bucket_opcount_pos` | `18` | `83.213` | `-5.315` | `False` | `266.802` |

## Decision

The apparent full-fit copy-length structure is not promoted. It can make the full ledger look smaller after seeing the whole corpus, but prefix-frozen contexts do not beat the uniform feasible-length code. This keeps the blocker at a target-free length/chunk state, not a posthoc length-prior table.
