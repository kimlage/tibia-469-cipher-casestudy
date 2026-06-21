# Source-Length Joint Derivability Audit

Classification: `source_length_joint_derivation_partial_decoder_dependency_retained`
Translation delta: `NONE`

## Purpose

This gate tests whether the two remaining copy dependencies, source and
length, become derivable when they are evaluated as a joint pair rather
than as separate ledgers. It is an analysis-only boundary test: no new
formula is emitted and no compression bound is promoted.

## Summary

- Copy events: `261`.
- Copied digits: `10406`.
- Prior source-boundary earliest-source hits: `261/261`.
- Earliest-source hits at declared length: `251/261`.
- Non-earliest delta after source substitutions: `10`.
- Unique / ambiguous source candidates: `123` / `138`.
- Decoder max-length hits after declared source: `60/261`.
- Encoder target-max hits after declared source: `238/261`.
- Joint encoder earliest+target-max hits: `230/261`.
- Joint declared-source+decoder-max hits: `60/261`.
- Joint unique-source+decoder-max hits: `28/261`.
- Joint previous-end+decoder-max hits: `1/261`.

## Controls

- Uniform candidate expected earliest-source hits: `169.473`.
- Uniform candidate expected target-max hits: `237.300`.
- Uniform candidate expected earliest+target-max hits: `156.406`.
- Uniform legal-length expected decoder-max hits: `10.714`.
- Length permutation target-max hit summary: `{'n': 1000, 'min': 0, 'median': 7.0, 'mean': 7.287, 'max': 16}`.
- P(permuted target-max hits >= observed): `0.0000`.
- Length permutation decoder-max hit summary: `{'n': 1000, 'min': 0, 'median': 2.0, 'mean': 1.968, 'max': 8}`.
- P(permuted decoder-max hits >= observed): `0.0000`.

## Interpretation

The copy source and length regularities are coupled, but the coupling is
mostly on the encoder side. The latest source-substituted formula no
longer preserves the earlier `261/261` all-earliest source pattern:
current coverage is `251/261`. Most declared lengths are still
target-maximal after the declared source, and the joint earliest+target
max pattern covers `230/261`; neither rule is decoder-valid because both
checks require the future target text. The decoder-valid version that
keeps source declared and derives length as max-possible covers only
`60/261` events, so it does not remove the copy-length ledger. A simple
state-only previous-end joint rule covers `1/261` events.

## Boundary

- Source and length remain declared dependencies in the current formula.
- The result sharpens the structural-parser target but does not promote a new formula.
- Compression bound is unchanged.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
