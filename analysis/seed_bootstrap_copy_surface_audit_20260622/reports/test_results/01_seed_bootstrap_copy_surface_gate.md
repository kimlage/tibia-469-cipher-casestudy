# Seed Bootstrap Copy-Surface Gate

Classification: `PROMOTED_SEED_BOOTSTRAP_COPY_SURFACE_CLUE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- Seed digits: `1696`.
- Raw seed bits: `5633.990`.
- Best min_len by copied digits: `4`.
- Best observed copied/literal digits: `1335` / `361`.
- Strong vs same-multiset shuffle min_lens: `[4, 5, 6, 8, 10, 12]`.
- Order-sensitive min_lens: `[5]`.

## Copy Surface

| min_len | copied | literal | copy ops | copied fraction | shuffle p95 copied | order p95 copied |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `4` | `1335` | `361` | `112` | `0.787` | `534` | `1354` |
| `5` | `1218` | `478` | `79` | `0.718` | `119` | `1211` |
| `6` | `1129` | `567` | `60` | `0.666` | `37` | `1134` |
| `8` | `992` | `704` | `38` | `0.585` | `0` | `995` |
| `10` | `932` | `764` | `31` | `0.550` | `0` | `938` |
| `12` | `868` | `828` | `25` | `0.512` | `0` | `874` |

## Decision

`PROMOTED_SEED_BOOTSTRAP_COPY_SURFACE_CLUE`.

This is a target-conditioned surface clue, not an executable generator. It does not reduce the v6 seed payload ledger until a target-free bootstrap policy derives copy starts and copy choices.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
