# Aligned Numeric Anchor Audit

Verdict: `rejected_control`. Translation delta: `NONE`.

Exact numeric hits are projected into 2-digit row0/code space before
any interpretation. Odd-length seeds are kept as partially unpaired,
not silently promoted to valid code sequences.

| Anchor | Hits | Offset mod 2 | Status |
|---|---:|---|---|
| `3478` | 24 | `{0: 12, 1: 12}` | `structural_overlap_not_key` |
| `486486` | 0 | `{}` | `absent_or_blocked` |
| `486` | 0 | `{}` | `absent_or_blocked` |
| `74032` | 0 | `{}` | `absent_or_blocked` |
| `45331` | 0 | `{}` | `absent_or_blocked` |
| `43153` | 0 | `{}` | `absent_or_blocked` |
| `34784` | 0 | `{}` | `absent_or_blocked` |
| `469` | 1 | `{0: 1}` | `structural_overlap_not_key` |
| `99` | 112 | `{1: 57, 0: 55}` | `structural_overlap_not_key` |
| `1` | 1869 | `{1: 946, 0: 923}` | `structural_overlap_not_key` |
| `0` | 855 | `{0: 442, 1: 413}` | `structural_overlap_not_key` |

Stop rule: a seed that cannot become a boundary-aligned lower-cost
mechanical formula remains a source/lore anchor only.
