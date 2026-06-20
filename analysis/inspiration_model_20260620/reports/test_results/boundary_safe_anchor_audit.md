# Boundary-Safe Anchor Audit

Verdict: `rejected_control`. Translation delta: `NONE`.

This replaces raw `''.join(book_strings)` anchor counting with per-book
counts and an explicit cross-boundary false-hit check.

| Anchor | Book-safe hits | Books hit | Raw concat hits | Cross-book false hits | Tape hits | Module hits |
|---|---:|---:|---:|---:|---:|---:|
| `3478` | 24 | 24 | 24 | 0 | 4 | 11 |
| `486486` | 0 | 0 | 0 | 0 | 0 | 0 |
| `486` | 0 | 0 | 0 | 0 | 0 | 0 |
| `74032` | 0 | 0 | 0 | 0 | 0 | 0 |
| `45331` | 0 | 0 | 0 | 0 | 0 | 0 |
| `43153` | 0 | 0 | 0 | 0 | 0 | 0 |
| `34784` | 0 | 0 | 0 | 0 | 0 | 0 |
| `469` | 1 | 1 | 1 | 0 | 0 | 0 |
| `99` | 112 | 58 | 112 | 0 | 22 | 45 |
| `1` | 1869 | 70 | 1869 | 0 | 349 | 758 |
| `0` | 855 | 70 | 855 | 0 | 157 | 332 |

Stop rule: boundary-safe substring presence alone is not a formula,
codebook, plaintext, or semantic promotion.
