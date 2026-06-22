# Book Control Header Gate

Classification: `book_control_header_rejected`
Translation delta: `NONE`

## Purpose

Test whether the transducer's remaining book-level control fields
form one useful header: operation count, literal operation count,
and innovation-tape digit consumption. A promoted result would reduce
declared book-level control before the operation-level parser runs.

## Summary

- Books: `60`.
- Header alphabet size: `29`.
- Component alphabets op/literal_ops/literal_digits: `13` / `6` / `15`.
- Cutoffs tested: `[20, 30, 40, 50, 60]`.
- Random shuffle trials per cutoff: `500`.
- Best header feature modes: `{'global': 5}`.
- Beats shuffled header p95 cutoffs: `0/5`.
- Beats separately coded field predictors: `5/5`.
- Promotes book-control header clue: `False`.
- Promotes joint header replacement: `False`.

This gate tests whether per-book control fields form one useful header for the transducer: op_count, literal_op_count, and literal_tape_digits. It compares a joint header predictor against shuffled controls and against separately coded field predictors.

## Prefix-Holdout Rows

| Cutoff | Train/Test Books | Best Header Feature | Header Saving vs Global | Shuffle p95 | Header Saving vs Separate | Beats Shuffle | Beats Separate |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `20` | `10/50` | `global` | `0.000` | `0.000` | `243.306` | `False` | `True` |
| `30` | `20/40` | `global` | `0.000` | `0.000` | `122.204` | `False` | `True` |
| `40` | `30/30` | `global` | `0.000` | `0.000` | `86.040` | `False` | `True` |
| `50` | `40/20` | `global` | `0.000` | `0.000` | `49.295` | `False` | `True` |
| `60` | `50/10` | `global` | `0.000` | `0.000` | `21.532` | `False` | `True` |

## Decision

- A joint book-control header is promoted only if it beats shuffled controls and separately coded fields.
- If it only beats shuffled controls, it is a clue about book-level control structure, not a replacement.
- This gate does not generate operation starts, copy sources, literal payload, or row0.
- Row0, plaintext, translation, and compression bound remain unchanged.
