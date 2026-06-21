# Latent State Requirement Audit

Classification: `latent_state_requirement_audit_only`
Translation delta: `NONE`

## Purpose

Gate 40 asks whether the gate-39 support failure can be repaired by simple
observable latent-state splits such as book parity, book decade, operation
bucket, target half, or active operation class. If not, it quantifies the
minimum residual distinctions a true latent state would still need.

This is a requirement audit, not a promoted parser.

## Summary

- Exact parser books: `50`.
- Residual parser books: `10`.
- Families tested: `['trajectory', 'context', 'combined']`.
- Splits tested: `['none', 'book_parity', 'book_mod3', 'book_mod5', 'book_decade', 'book_half', 'op_index_parity', 'op_index_bucket', 'target_half', 'active_type', 'active_length_bucket']`.
- Score count: `33`.
- Best split: `trajectory + target_half`.
- Best deterministic matches:
  `0/10`.
- Best supported residual states:
  `4/10`.
- Best out-of-support residual states:
  `6/10`.
- Prequential cells with any deterministic match:
  `0/4`.
- Residuals needing latent resolution:
  `10`.
- Distinct stable labels needing resolution:
  `9`.
- Minimum oracle bits for distinct labels:
  `3.170`.
- Promotes parser rule: `False`.

## Top Split Scoreboard

| family | split | deterministic matches | supported | out of support | contradictions | status counts |
| --- | --- | --- | --- | --- | --- | --- |
| trajectory | book_half | 0 | 4 | 6 | 2 | {'ambiguous_excludes_stable': 2, 'ambiguous_includes_stable': 2, 'out_of_support': 6} |
| trajectory | book_parity | 0 | 4 | 6 | 2 | {'ambiguous_excludes_stable': 2, 'ambiguous_includes_stable': 2, 'out_of_support': 6} |
| trajectory | none | 0 | 4 | 6 | 2 | {'ambiguous_excludes_stable': 2, 'ambiguous_includes_stable': 2, 'out_of_support': 6} |
| trajectory | op_index_bucket | 0 | 4 | 6 | 2 | {'ambiguous_excludes_stable': 2, 'ambiguous_includes_stable': 2, 'out_of_support': 6} |
| trajectory | op_index_parity | 0 | 4 | 6 | 2 | {'ambiguous_excludes_stable': 2, 'ambiguous_includes_stable': 2, 'out_of_support': 6} |
| trajectory | target_half | 0 | 4 | 6 | 2 | {'ambiguous_excludes_stable': 2, 'ambiguous_includes_stable': 2, 'out_of_support': 6} |
| trajectory | book_mod3 | 0 | 4 | 6 | 3 | {'ambiguous_excludes_stable': 3, 'ambiguous_includes_stable': 1, 'out_of_support': 6} |
| trajectory | book_mod5 | 0 | 4 | 6 | 3 | {'ambiguous_excludes_stable': 3, 'ambiguous_includes_stable': 1, 'out_of_support': 6} |
| trajectory | active_length_bucket | 0 | 4 | 6 | 4 | {'ambiguous_excludes_stable': 3, 'deterministic_contradiction': 1, 'out_of_support': 6} |
| trajectory | active_type | 0 | 4 | 6 | 4 | {'ambiguous_excludes_stable': 4, 'out_of_support': 6} |
| trajectory | book_decade | 0 | 4 | 6 | 4 | {'ambiguous_excludes_stable': 4, 'out_of_support': 6} |
| context | active_length_bucket | 0 | 2 | 8 | 1 | {'ambiguous_includes_stable': 1, 'deterministic_contradiction': 1, 'out_of_support': 8} |
| context | active_type | 0 | 2 | 8 | 1 | {'ambiguous_includes_stable': 1, 'deterministic_contradiction': 1, 'out_of_support': 8} |
| context | none | 0 | 2 | 8 | 1 | {'ambiguous_includes_stable': 1, 'deterministic_contradiction': 1, 'out_of_support': 8} |
| context | book_half | 0 | 2 | 8 | 2 | {'ambiguous_excludes_stable': 1, 'deterministic_contradiction': 1, 'out_of_support': 8} |
| context | target_half | 0 | 2 | 8 | 2 | {'ambiguous_excludes_stable': 1, 'deterministic_contradiction': 1, 'out_of_support': 8} |
| context | book_mod3 | 0 | 1 | 9 | 0 | {'ambiguous_includes_stable': 1, 'out_of_support': 9} |
| context | book_parity | 0 | 1 | 9 | 0 | {'ambiguous_includes_stable': 1, 'out_of_support': 9} |

## Prequential Rows For Best Split

| cutoff | queries | deterministic matches | supported | status counts |
| --- | --- | --- | --- | --- |
| 20 | 8 | 0 | 3 | {'ambiguous_excludes_stable': 3, 'out_of_support': 5} |
| 30 | 5 | 0 | 1 | {'ambiguous_excludes_stable': 1, 'out_of_support': 4} |
| 40 | 3 | 0 | 0 | {'out_of_support': 3} |
| 50 | 2 | 0 | 0 | {'out_of_support': 2} |
| 60 | 0 | 0 | 0 | {} |

## Residual Rows For Best Split

| book | op | active label | stable label | support | label count | status |
| --- | --- | --- | --- | --- | --- | --- |
| 14 | 0 | ('literal', 27) | ('literal', 39) | 50 | 39 | ambiguous_excludes_stable |
| 16 | 9 | ('copy', 8) | ('literal', 1) | 0 | 0 | out_of_support |
| 20 | 2 | ('literal', 3) | ('copy', 10) | 0 | 0 | out_of_support |
| 21 | 0 | ('literal', 7) | ('copy', 9) | 50 | 39 | ambiguous_includes_stable |
| 26 | 0 | ('literal', 1) | ('copy', 11) | 50 | 39 | ambiguous_includes_stable |
| 34 | 7 | ('literal', 5) | ('copy', 5) | 0 | 0 | out_of_support |
| 39 | 0 | ('literal', 7) | ('copy', 5) | 50 | 39 | ambiguous_excludes_stable |
| 45 | 1 | ('literal', 1) | ('copy', 8) | 0 | 0 | out_of_support |
| 55 | 2 | ('copy', 45) | ('copy', 44) | 0 | 0 | out_of_support |
| 57 | 2 | ('literal', 17) | ('literal', 28) | 0 | 0 | out_of_support |

## Decision

No simple observable split promotes a parser. The best split still leaves the
residual first-drift choices without deterministic support. A real improvement
must introduce a falsifiable latent state with enough structure to predict
these distinctions, or explain the target digit stream source-free.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
