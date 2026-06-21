# Copy Source Ledger

Classification: `copy_source_ledger_audit_only`
Translation delta: `NONE`

## Purpose

Grant the exact source-free skeleton and literal payload, then map the
remaining copy-source dependency.

## Summary

- Copy events: `208`.
- Total matching sources under oracle target chunks: `597`.
- Matching sources min/median/max: `1` / `2` / `14`.
- Single-source events: `78`.
- Multi-source events: `130`.
- Canonical earliest/latest matching events: `200` / `85`.
- Canonical previous-source events: `0`.
- Canonical previous-end events: `7`.
- Source ending at previous end events: `0`.
- Oracle rank bits among matching sources: `232.902`.
- Raw absolute source bits: `2550.594`.

## Decision

- This ledger grants the exact skeleton and literal payload, then maps the remaining copy-source dependency. Matching-source counts are diagnostic controls; using them to choose a source is target-aware.
- No copy-source generator is promoted by this ledger.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
