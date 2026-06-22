# Unified External Tape Ledger

Status: `analysis_only`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

- Derived books: `60`.
- Operations: `261` (`53` literal, `208` copy).
- Seed payload bits: `5633.990`.
- Uniform coarse-control bits: `935.675`.
- Composition-index bits: `665.782`.
- Literal-payload bits: `883.633`.
- Copy-hint rank bits: `1873.768`.
- Total external tape bits including seed: `9992.848`.

## Ledger Fields

Each row records the book/op, coarse control token, exact length, composition-index charge, literal or copy-hint tape charge, derived fields, and target-conditioned dependencies.

## Decision

This ledger is the baseline for a unified control program. Any promoted macro grammar must reduce this external tape total after paying grammar and correction costs.
