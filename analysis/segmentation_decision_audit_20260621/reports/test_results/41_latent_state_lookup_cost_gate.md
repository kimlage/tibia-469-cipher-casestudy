# Latent State Lookup Cost Gate

Classification: `latent_state_lookup_cost_audit_only`
Translation delta: `NONE`

## Purpose

Gate 41 prices the fallback hypothesis "there is a latent state" after exposed
state, nearest trajectories, templates, and simple splits fail. It asks how
expensive an explicit latent lookup would be before any candidate rule earns
the right to be called mechanical.

This is not a promoted parser and not a new compression bound.

## Summary

- Decision universe: `267`.
- First-drift residual sites: `10`.
- Full-oracle minimum correction events: `11`.
- Distinct first-drift stable labels: `9`.
- Simple split deterministic matches:
  `0`.
- First-drift lookup lower bound:
  `79.361` bits.
- First-drift lookup with per-site label dictionary:
  `90.269` bits.
- Full-parser lookup lower bound:
  `83.907` bits.
- Promotes latent lookup formula: `False`.

## Cost Ledger

| component | bits |
| --- | --- |
| site_bits_first_drift | 58.570 |
| site_bits_full_oracle_lower_bound | 63.116 |
| free_multiset_order_bits | 20.791 |
| free_dictionary_per_site_bits | 31.699 |
| first_drift_lookup_lower_bound_bits | 79.361 |
| first_drift_lookup_dictionary_bits | 90.269 |
| full_parser_lookup_lower_bound_bits | 83.907 |

## Residual Rows

| book | op | active label | stable label | status |
| --- | --- | --- | --- | --- |
| 14 | 0 | ['literal', 27] | ['literal', 39] | ambiguous_excludes_stable |
| 16 | 9 | ['copy', 8] | ['literal', 1] | out_of_support |
| 20 | 2 | ['literal', 3] | ['copy', 10] | out_of_support |
| 21 | 0 | ['literal', 7] | ['copy', 9] | ambiguous_includes_stable |
| 26 | 0 | ['literal', 1] | ['copy', 11] | ambiguous_includes_stable |
| 34 | 7 | ['literal', 5] | ['copy', 5] | out_of_support |
| 39 | 0 | ['literal', 7] | ['copy', 5] | ambiguous_excludes_stable |
| 45 | 1 | ['literal', 1] | ['copy', 8] | out_of_support |
| 55 | 2 | ['copy', 45] | ['copy', 44] | out_of_support |
| 57 | 2 | ['literal', 17] | ['literal', 28] | out_of_support |

## Decision

Latent state is not promoted by naming it. Under current evidence, a latent
state that merely selects the residual sites and labels is an explicit lookup,
with a first-drift lower bound of `79.361`
bits before any human-readable rule is charged. Because the post-repair oracle
requires at least `11` correction events,
even that is not a full parser explanation.

The next acceptable progress must provide a compact rule for this latent state,
or switch to a source-free target digit account.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
