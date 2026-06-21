# Copy Length Derivation Boundary Gate

Classification: `copy_length_partly_decodable_context_supported_dependency_retained`
Translation delta: `NONE`

## Purpose

Copy length is one of the remaining declared recipe dependencies. This
gate consolidates the default/exception compile, the midpoint context
validation, and the compact recipe dependency ledger to decide whether
copy length has become decoder-derived or remains declared.

## Summary

- Copy items: `261`.
- Active/candidate copy-length bits: `1485.689` / `1348.806`.
- Candidate gain already promoted upstream: `136.884` bits.
- Encoder target-max matches: `238/261`.
- Encoder target-max decodable: `False`.
- Decoder max-possible defaults/exceptions: `60` / `201`.
- Decoder default/exception stream bits: `1340.806`.
- Midpoint gain vs global: `13.839` bits.
- Midpoint prefix-frozen wins: `5/5`.
- P(permuted midpoint gain >= observed): `0.0033`.
- Best searched cutoff delta vs midpoint: `0.256` bits.
- Copy-length fields retained in compact recipe: `261`.
- Copied digits covered: `10406`.

## Interpretation

The copy-length model is improved but not eliminated. The high-coverage
target-max rule matches most copies, but it is encoder-only because it
depends on future target text. The decodable `decoder_max_possible`
default plus adaptive exceptions is retained, and the natural midpoint
context generalizes under prefix and permutation controls. The compact
recipe still declares copy length for all copy ops.

## Boundary

- No new compression bound is promoted by this gate.
- Copy length remains a declared dependency.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
