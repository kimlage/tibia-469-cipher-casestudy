# Leave-One-Book-Out Book-Bounded Source Audit

Classification: `book_bounded_singleton_holdout_predictive`
Translation delta: `NONE`

## Purpose

Audit 14 exposed that some singleton copies crossed artificial source-book
boundaries in the concatenated complement inventory. This audit reparses
each singleton while forbidding copy sources from crossing source-book
boundaries. Current-prefix copies are still legal if they stay inside the
already-emitted current prefix.

## Summary

- Books checked: `70`.
- Roundtrip books: `70/70`.
- Beats raw digits: `70/70`.
- Mean book-bounded gain vs raw: `464.898` bits.
- Min book-bounded gain vs raw: `96.055` bits.
- Mean book-bounded minus unbounded: `4.409` bits.
- Max book-bounded minus unbounded: `21.552` bits.
- Failure books: `[]`.

## Weakest Books

| Book | Length | Book-bounded gain vs raw |
|---:|---:|---:|
| `25` | `35` | `96.055` |
| `49` | `115` | `124.657` |
| `39` | `59` | `154.073` |
| `54` | `57` | `154.609` |
| `20` | `63` | `169.644` |
| `7` | `106` | `175.129` |
| `34` | `123` | `231.581` |
| `18` | `93` | `262.908` |
| `4` | `140` | `265.301` |
| `67` | `98` | `283.568` |

## Highest Boundary Penalties

| Book | Penalty vs unbounded | Book-bounded gain vs raw |
|---:|---:|---:|
| `42` | `21.552` | `479.069` |
| `67` | `20.794` | `283.568` |
| `59` | `20.337` | `823.333` |
| `8` | `19.447` | `473.355` |
| `27` | `19.228` | `370.718` |
| `17` | `18.990` | `809.586` |
| `58` | `18.917` | `842.924` |
| `43` | `18.897` | `429.455` |
| `31` | `18.695` | `643.584` |
| `3` | `18.377` | `423.367` |

## Decision

- The singleton holdout is retested under book-bounded copy-source constraints.
- The item-level signal does not depend on source-book boundary crossings to beat raw digit coding.
- No plaintext, translation, row0-origin change, or case reopening is introduced.
