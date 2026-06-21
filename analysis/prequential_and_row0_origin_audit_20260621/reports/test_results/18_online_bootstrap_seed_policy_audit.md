# Online Bootstrap Seed Policy Audit

Classification: `explicit_raw_seed_closes_online_bootstrap_failure`
Translation delta: `NONE`

## Purpose

Audit 17 showed one local failure in the previous-books-only online
frontier: book `0`, before any previous-book inventory exists. This audit
tests whether that is a seed/bootstrap accounting issue rather than a
failure of the later sequential generation rule.

## Book 0

- Raw uniform cost: `478.358` bits.
- Online parsed cost: `488.857` bits.
- Online minus raw: `10.499` bits.
- Online inventory: `128` literal digits, `16` copied digits, `3` copy items.

## Policies

| Policy | Status | Book 0 charge | Stream gain vs raw | Wins/ties | Failures | Admissibility |
|---|---|---:|---:|---:|---|---|
| `online_book0_parser` | `baseline_has_cold_start_failure` | `488.857` | `29383.262` | `69/70` | `[0]` | `admissible_baseline` |
| `raw_book0_seed_then_online` | `one_explicit_seed_closes_local_failure` | `478.358` | `29393.761` | `70/70` | `[]` | `admissible_as_explicit_seed_policy_not_authorial_proof` |
| `externally_given_book0_seed` | `mechanical_generator_seed_only_not_compression_bound` | `0.000` | `29872.118` | `70/70` | `[]` | `not_admissible_as_compression_bound_without_external_attestation` |

## Decision

- A single explicit raw seed for book `0` closes the only local raw-coding failure in the previous-books-only frontier.
- Books `1-69` are unchanged and still beat raw under book-bounded previous-book sources.
- This is a bootstrap accounting improvement, not a new compression-bound promotion, row0 derivation, plaintext claim, or case reopening.
