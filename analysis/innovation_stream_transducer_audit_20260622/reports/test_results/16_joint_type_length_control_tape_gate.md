# Joint Type-Length Control Tape Gate

Classification: `joint_type_length_control_tape_clue_not_skeleton_replacement`
Translation delta: `NONE`

## Purpose

Test the constructive follow-up to the length-control clue. If each
operation is encoded as a joint `type:length` symbol, then granted book
lengths and op counts let the stream generate operation starts by
cumulative sum and operation modes directly. This is tested against
shuffled pair controls and against fixed-op-count cutpoint+type
composition.

## Summary

- Canonical ops: `261`.
- Pair alphabet size: `97`.
- Type alphabet size: `2`.
- All-books cutpoint composition bits with fixed op counts: `1137.308`.
- All-books type composition bits with fixed op counts: `107.955`.
- All-books skeleton composition bits with fixed op counts: `1245.263`.
- Best paid pair feature modes: `{'book_start': 2, 'prev_type': 2, 'global': 1}`.
- Best paid type feature modes: `{'global': 5}`.
- Beats shuffled paid pair p95 cutoffs: `4/5`.
- Beats skeleton composition cutoffs: `0/5`.
- Promotes joint type-length clue: `True`.
- Promotes skeleton replacement: `False`.

This gate tests the natural follow-up to the length-control clue: encode each operation as a joint type:length control symbol, so book lengths plus the stream determine operation starts and modes. It measures prefix-holdout prediction against shuffled pair controls and against the paid cost of declaring cutpoints plus types with fixed op counts.

## Prefix-Holdout Rows

| Cutoff | Train/Test Ops | Best Paid Pair Feature | Paid Pair Saving vs Global | Shuffle p95 | Paid Pair Saving vs Skeleton | Beats Shuffle | Beats Skeleton |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `20` | `79/182` | `book_start` | `4.324` | `0.000` | `-381.790` | `True` | `False` |
| `30` | `121/140` | `prev_type` | `16.123` | `0.000` | `-296.747` | `True` | `False` |
| `40` | `166/95` | `prev_type` | `11.625` | `0.000` | `-222.888` | `True` | `False` |
| `50` | `205/56` | `book_start` | `1.993` | `0.000` | `-152.410` | `True` | `False` |
| `60` | `241/20` | `global` | `0.000` | `0.000` | `-82.978` | `False` | `False` |

## Decision

- Joint `type:length` prediction is not promoted as skeleton replacement.
- The pair stream is much more expensive than fixed-op-count cutpoint+type composition in every cutoff.
- Any surviving paid predictive signal is therefore a weak control-stream clue, not generation.
- Operation counts, copy source, literal payload, and row0 remain external.
- No plaintext, translation, semantic reading, or case reopening is introduced.
