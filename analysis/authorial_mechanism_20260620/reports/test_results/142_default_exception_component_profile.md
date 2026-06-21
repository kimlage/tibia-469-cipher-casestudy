# 142. Default/Exception Component Profile

Classification: `copy_length_default_exception_frozen_profile_source_default_compression_only`
Translation delta: `NONE`

## Purpose

Audit 141 showed that the promoted default/exception ledgers are
online-predictive but frozen-unstable. This profile separates the
compression bound from the frozen-prefix generation explanation by
component.

## Bit Ledgers

- Compression bound with copy-source default: `8177.317` bits
- Frozen-prefix generation profile: `8206.178` bits
- Copy-source default full-corpus gain retained only in compression bound: `28.862` bits

## Prefix Component Summary

| Component | Mode | Min gain | Mean gain | Total gain | Nonpositive splits |
|---|---|---:|---:|---:|---:|
| `copy_length` | `online` | `37.679` | `101.579` | `507.893` | `0` |
| `copy_length` | `frozen` | `38.937` | `79.306` | `396.529` | `0` |
| `copy_source` | `online` | `2.986` | `21.066` | `105.328` | `0` |
| `copy_source` | `frozen` | `-140.801` | `-64.418` | `-322.091` | `5` |

## Decision

- Keep `8177.317` bits as `compression_bound`.
- Use `8206.178` bits as the frozen-prefix generation-explanation profile for the default/exception layer.
- Retain copy-length default/exception as frozen-prefix explanatory evidence.
- Treat copy-source default/exception as compression-bound-only until a train-frozen source model beats legal uniform.
- `row0` and semantics are unchanged.
