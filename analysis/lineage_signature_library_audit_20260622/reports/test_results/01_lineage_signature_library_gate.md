# Lineage Signature Library Gate

Classification: `lineage_signature_library_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- Fallback rows after v6: `90`.
- Best signature key: `signature_kind_run_lengths`.
- Best delta vs copy-hint: `737.215` bits.
- Prefix positive splits: `0/5`.
- Mean signature run count: `2.200`.

## Full Fit

| Signature | Library | Unique | Delta |
| --- | ---: | ---: | ---: |
| `signature_kind_run_lengths` | `63` | `63` | `737.215` |
| `signature_kind_book_run_lengths` | `78` | `78` | `1018.926` |
| `signature_atom_offset_run_lengths` | `89` | `89` | `1264.285` |

## Prefix Holdout

| Cutoff | Test rows | Hits | Delta |
| ---: | ---: | ---: | ---: |
| `20` | `63` | `16` | `112.401` |
| `30` | `52` | `15` | `230.846` |
| `40` | `38` | `9` | `438.458` |
| `50` | `23` | `6` | `678.157` |
| `60` | `7` | `1` | `1024.474` |

## Control

- Observed full-fit delta: `737.215`.
- Shuffled signature p05/p50/p95 delta: `737.215` / `737.215` / `737.215`.
- Beats p05: `False`.

## Decision

`lineage_signature_library_not_promoted`: the remaining fallbacks do not share a compact paid causal-signature library.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
