# Source State Dependency Gate

Classification: `source_state_dependency_retained_state_free_defaults_rejected`
Translation delta: `NONE`

## Purpose

Audit 146 localized the active deterministic-reparse blocker: the active
copy-source default depends on previous copy source and previous copy
length. Audit 147 tested state-free decoder-computable defaults. This gate
checks whether those results remove the source-state dependency after the
canonicality/decodability boundary is applied.

## Summary

- Old reparse state key: `(book_pos, previous_item)`.
- Active required state key: `(book_pos, previous_item, previous_copy_source, previous_copy_length)`.
- Exact active reparse implemented upstream: `False`.
- Max book state-proxy multiplier: `38968.0`.
- Best state-free default: `state_free_back_current_length`.
- Best state-free stream penalty: `15.186` bits.
- Best state-free total penalty: `15.186` bits.
- Prefix-frozen state-free losses: `5/5`.
- Prefix-frozen gap min/mean/max: `7.652` / `14.615` / `22.840` bits.
- Canonicality removed source dependency: `False`.
- Earliest exact-chunk rule decoder-computable: `False`.

## Interpretation

The state-free candidates do not replace the active path-dependent source
default. The best candidate, `state_free_back_current_length`, is still
`15.186` bits worse on the full source stream and loses every tested
prefix-frozen split. Combined with the canonicality gate, this keeps the
source ledger as a real decoder dependency rather than a removable
tie-break note.

## Boundary

- No compression bound is promoted.
- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0/table origin remains exogenous.
