# Unstable Parser Path Decomposition Audit

Classification: `unstable_parser_paths_decomposed`
Translation delta: `NONE`

## Purpose

Gate 78 found `12` books whose exact parser paths change across frozen
cutoffs. This gate decomposes those unstable paths into source-only
changes, same-shape boundary shifts, or larger segmentation changes.

## Summary

- Unstable books decomposed: `12`.
- Class counts: `{'boundary_shift_same_shape': 9, 'segmentation_shape_change': 3}`.
- Max variants in one book: `4`.

## Worst Books

| Book | Variants | Class | Variant cutoffs |
|---:|---:|---|---|
| 65 | 4 | `boundary_shift_same_shape` | `[[10, 20], [35], [50], [60]]` |
| 21 | 2 | `boundary_shift_same_shape` | `[[10], [20]]` |
| 24 | 2 | `boundary_shift_same_shape` | `[[10], [20]]` |
| 28 | 2 | `boundary_shift_same_shape` | `[[10], [20]]` |
| 30 | 2 | `segmentation_shape_change` | `[[10], [20]]` |
| 34 | 2 | `segmentation_shape_change` | `[[10], [20]]` |
| 35 | 2 | `boundary_shift_same_shape` | `[[10, 20], [35]]` |
| 39 | 2 | `segmentation_shape_change` | `[[10, 20], [35]]` |
| 46 | 2 | `boundary_shift_same_shape` | `[[20, 35], [10]]` |
| 51 | 2 | `boundary_shift_same_shape` | `[[10, 20, 35], [50]]` |

## Decision

- The unstable parser paths are primarily boundary/segmentation choice problems rather than pure source-address swaps. This narrows the next structural task: stabilize copy boundary selection under frozen prefixes, especially book 65, instead of searching for another compression-only parameter.
- No compression-bound change is introduced.
- No corpus-wide formula promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
