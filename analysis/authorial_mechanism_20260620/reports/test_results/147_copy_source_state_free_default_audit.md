# 147. Copy Source State-Free Default Audit

Classification: `state_free_copy_source_defaults_rejected_active_path_state_retained`
Translation delta: `NONE`

## Purpose

Audit 146 localized the exact-reparse blocker: the active copy-source
default depends on the previous copy source and previous copy length.
This audit tests whether a decoder-computable default that is free of
that path state can replace the active default without worsening the
copy-source ledger.

## Full-Corpus Frontier

| Default rule | State-free | Stream bits | Delta vs active stream | Defaults | Replacement total |
|---|---:|---:|---:|---:|---:|
| `active_previous_source_plus_length` | `false` | `2990.838` | `0.000` | `5/261` | `8177.317` |
| `state_free_back_current_length` | `true` | `3006.024` | `15.186` | `3/261` | `8192.503` |
| `state_free_previous_book_start` | `true` | `3014.841` | `24.003` | `1/261` | `8201.320` |
| `state_free_zero_source` | `true` | `3018.179` | `27.340` | `1/261` | `8204.657` |
| `state_free_current_book_start` | `true` | `3020.071` | `29.233` | `0/261` | `8206.550` |
| `state_free_previous_book_same_offset` | `true` | `3020.089` | `29.250` | `0/261` | `8206.567` |
| `state_free_midpoint_source` | `true` | `3020.090` | `29.252` | `0/261` | `8206.568` |
| `state_free_latest_legal_source` | `true` | `3020.091` | `29.253` | `0/261` | `8206.569` |
| `state_free_back_double_length` | `true` | `3022.249` | `31.411` | `1/261` | `8208.728` |

- Active source stream bits: `2990.838`
- Best state-free default: `state_free_back_current_length`
- Best state-free stream penalty: `15.186` bits
- Best state-free total penalty: `15.186` bits

## Prefix Future-Suffix Check

| Split | Test events | Active frozen bits | Best state-free frozen bits | Gap |
|---|---:|---:|---:|---:|
| `prefix_10_future_suffix` | `204` | `2470.698` | `2485.800` | `15.103` |
| `prefix_20_future_suffix` | `152` | `1889.260` | `1912.100` | `22.840` |
| `prefix_35_future_suffix` | `93` | `1173.755` | `1193.558` | `19.802` |
| `prefix_50_future_suffix` | `48` | `623.858` | `631.510` | `7.652` |
| `prefix_60_future_suffix` | `18` | `229.692` | `237.371` | `7.680` |

Best state-free frozen gap summary:
`{'n': 5, 'min': 7.6518848233965855, 'mean': 14.615207376816631, 'max': 22.839645662357952}`

## Interpretation

The tested state-free defaults are decodable from current emitted length,
book position, current copy length, and public book-length context. None
matches the active previous-source-plus-length default. The best
state-free candidate still carries a positive stream and total penalty,
so it does not remove the path-dependent source state identified by
audit 146.

## Decision

- Compression bound unchanged.
- Active path-dependent copy-source default retained.
- Exact reparse still requires previous-copy source/length state or a different source model.
- Row0 origin, plaintext, and semantic status unchanged.
