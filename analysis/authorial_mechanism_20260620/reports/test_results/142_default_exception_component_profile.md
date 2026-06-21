# 142. Default/Exception Component Profile

Classification: `default_exception_components_prefix_frozen_partial_family_holdout`
Translation delta: `NONE`

## Purpose

Audit 141 tests whether the promoted default/exception ledgers predict
held-out books after learning counts on train books. This profile
separates the compression bound, prefix-frozen evidence, and remaining
family-holdout limits by component.

## Bit Ledgers

- Compression bound with copy-source default: `8177.317` bits
- Copy-length-only default/exception bits: `8206.178` bits
- Prefix-frozen generation profile: `8177.317` bits
- Copy-source default gain vs copy-length-only profile: `28.862` bits

## Prefix Component Summary

| Component | Mode | Min gain | Mean gain | Total gain | Nonpositive splits |
|---|---|---:|---:|---:|---:|
| `copy_length` | `online` | `40.392` | `110.112` | `550.559` | `0` |
| `copy_length` | `frozen` | `40.062` | `101.006` | `505.028` | `0` |
| `copy_source` | `online` | `10.113` | `27.648` | `138.238` | `0` |
| `copy_source` | `frozen` | `9.402` | `21.784` | `108.920` | `0` |

## Decision

- Keep `8177.317` bits as `compression_bound`.
- Use `8177.317` bits as the prefix-frozen generation profile for the default/exception layer.
- Retain copy-length and copy-source default/exception as prefix-frozen explanatory evidence.
- Keep the generation claim partial because family/bookcase holdouts still have nonpositive component splits.
- `row0` and semantics are unchanged.
