# 146. Active Reparse State Boundary Audit

Classification: `active_reparse_requires_path_dependent_copy_source_state`
Translation delta: `NONE`

## Purpose

Audit 145 strengthened component-level prediction for the active
`8177.317` bit formula, but recipe discovery remains unproved. This
audit explains the next parser boundary: unlike the older reparse audit,
the active copy-source model is path-dependent because source cost depends
on the previous copy source plus previous copy length.

## State Boundary

- Old reparse state key: `(book_pos, previous_item)`
- Active state key required: `(book_pos, previous_item, previous_copy_source, previous_copy_length)`
- Max observed book-level state proxy multiplier: `38968.0`

## Prefix State Proxies

| Cutoff | Test books | Candidate edges | Old states | Active state proxy | Max book multiplier | Active path copy states |
|---:|---:|---:|---:|---:|---:|---:|
| `10` | `60` | `490781` | `28881` | `302879952` | `38968.0` | `203` |
| `20` | `50` | `427463` | `23925` | `256343727` | `38968.0` | `151` |
| `35` | `35` | `352774` | `17610` | `222810162` | `38968.0` | `92` |
| `50` | `20` | `227265` | `10527` | `146167728` | `35754.0` | `48` |
| `60` | `10` | `85441` | `4407` | `40909602` | `21305.0` | `18` |

## Path-Dependence Example

For one active copy row:

- Book/op: `5/9`
- Source: `0` among `889` legal sources
- True previous-copy default: `874` -> `exception`
- Alternate previous-copy default: `0` -> `default`

## Decision

- Exact active reparse is not promoted in this cycle.
- The remaining recipe externality is now localized: active source coding requires previous-copy state.
- The next useful implementation target is a pruned/cached path-dependent reparse, or a source-cost simplification that keeps the active bound without that state.
- No compression-bound, row0-origin, plaintext, or semantic claim is changed.
