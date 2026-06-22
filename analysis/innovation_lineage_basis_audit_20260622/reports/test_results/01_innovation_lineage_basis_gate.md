# Innovation Lineage Basis Gate

Classification: `innovation_lineage_basis_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- V6 fallback rows tested: `90`.
- Lineage atoms: `63`.
- Baseline copy-hint bits: `779.571`.
- Single-atom lineage coverage: `55`.
- Total bits after declaration: `1022.251`.
- Delta vs copy-hint: `242.680`.
- Prefix positive splits: `0/5`.
- Single-atom by kind: `{'seed': 55}`.

## Prefix Holdout

| Cutoff | Rows | Coverage | Delta |
| ---: | ---: | ---: | ---: |
| `20` | `63` | `33` | `148.598` |
| `30` | `52` | `26` | `114.628` |
| `40` | `38` | `18` | `79.189` |
| `50` | `23` | `8` | `33.327` |
| `60` | `7` | `3` | `9.037` |

## Control

- Observed delta: `242.680`.
- Randomized lineage p05/p50/p95 delta: `85.693` / `106.016` / `130.492`.
- Beats p05: `False`.

## Decision

`innovation_lineage_basis_not_promoted`: innovation lineage is useful provenance, but it does not replace the remaining v6 fallback copy-hint tape.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
