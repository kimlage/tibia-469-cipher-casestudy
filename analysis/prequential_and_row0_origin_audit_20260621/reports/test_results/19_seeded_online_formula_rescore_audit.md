# Seeded Online Formula Rescore Audit

Classification: `seed_policy_rejected_by_full_formula_rescore`
Translation delta: `NONE`

## Purpose

Audit 18 showed that an explicit raw seed for book `0` closes the only
per-book previous-books-only local failure. This audit asks the stricter
question: if the seed policy is converted back into actual formula recipes
and rescored under the complete active ledger, does it still improve the
current online formula?

## Summary

- Online formula: `8343.062` bits.
- Seeded online formula: `8344.041` bits.
- Seeded delta vs online: `0.979` bits.
- Book-bounded seeded formula: `8648.260` bits.
- Book-bounded seeded delta vs online: `305.198` bits.
- Promoted candidates: `[]`.

## Candidates

| Candidate | Status | Total bits | Delta vs online | Literal digits | Copied digits | Roundtrip |
|---|---|---:|---:|---:|---:|---|
| `online_reparse_formula` | `baseline_promoted_elsewhere` | `8343.062` | `0.000` | `857` | `10406` | `70/70` |
| `seeded_online_formula_rescored` | `rejected_as_full_scorer_promotion` | `8344.041` | `0.979` | `873` | `10390` | `70/70` |
| `book_bounded_seeded_online_formula_rescored` | `rejected_as_full_scorer_promotion` | `8648.260` | `305.198` | `896` | `10367` | `70/70` |

## Decision

- The raw seed remains useful bootstrap accounting, but it is not promoted as a full-formula improvement.
- The existing online formula remains the cheaper complete scored recipe.
- No plaintext, translation, row0-origin change, or case reopening is introduced.
