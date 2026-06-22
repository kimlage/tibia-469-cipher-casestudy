# Length Control Tape Gate

Classification: `length_control_tape_predictive_clue_not_cutpoint_replacement`
Translation delta: `NONE`

## Purpose

Test whether the unresolved internal operation-start frontier can be
reframed as a smaller length-control tape. If book lengths and the
sequence of operation lengths are granted, internal starts are generated
by cumulative sum. This gate asks whether that length stream has
prefix-holdout structure, and whether it is strong enough to replace
fixed-op-count cutpoint declaration.

## Summary

- Canonical ops: `261`.
- Internal operation starts: `201`.
- Unique lengths: `89`.
- Raw composition bits with fixed op counts, all books: `1137.308`.
- Cutoffs tested: `[20, 30, 40, 50, 60]`.
- Random shuffle trials per cutoff: `500`.
- Best paid feature modes: `{'type': 1, 'book_start_x_type': 3, 'global': 1}`.
- Type-granted best cutoffs: `4/5`.
- Beats shuffled paid p95 cutoffs: `4/5`.
- Beats fixed-op-count composition cutoffs: `0/5`.
- Promotes predictive length-control clue: `True`.
- Promotes cutpoint replacement: `False`.

This gate treats the operation lengths as a possible control tape: if book lengths and length stream are granted, internal starts follow by cumulative sum. It asks whether that stream has prefix-holdout structure beyond shuffled controls, and separately whether the paid model beats a uniform fixed-op-count cutpoint composition.

## Prefix-Holdout Rows

| Cutoff | Train/Test Ops | Best Paid Feature | Type Grant | Paid Saving vs Global | Shuffle Paid p95 | Paid Saving vs Composition | Beats Shuffle | Beats Composition |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `79/182` | `type` | `True` | `28.347` | `0.000` | `-373.838` | `True` | `False` |
| `30` | `121/140` | `book_start_x_type` | `True` | `31.446` | `0.000` | `-302.294` | `True` | `False` |
| `40` | `166/95` | `book_start_x_type` | `True` | `16.566` | `0.000` | `-233.425` | `True` | `False` |
| `50` | `205/56` | `book_start_x_type` | `True` | `6.290` | `0.000` | `-158.469` | `True` | `False` |
| `60` | `241/20` | `global` | `False` | `0.000` | `0.000` | `-86.616` | `False` | `False` |

## Decision

- The length stream has real predictive structure in prefix holdout after a simple context cost.
- The strongest paid contexts usually require the operation type stream, so this is not source-free skeleton generation.
- The paid length model does not beat fixed-op-count uniform cutpoint composition in any cutoff.
- Therefore this promotes only a control-tape clue, not a replacement for the internal start atlas.
- Row0, plaintext, translation, and compression bound remain unchanged.
