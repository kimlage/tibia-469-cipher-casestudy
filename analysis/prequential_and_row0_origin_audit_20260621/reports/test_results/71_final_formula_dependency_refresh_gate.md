# Final Formula Dependency Refresh Gate

Classification: `final_formula_dependency_refresh_decoder_boundary_unchanged`
Translation delta: `NONE`

## Purpose

This gate refreshes the source/length dependency scoreboard on the
current `8154.676268`-bit formula after both partial-boundary promotions.
It checks whether the lower bound also changes the structural generation
blocker.

## Summary

- Final total bits: `8154.676268`.
- Copy events: `261`.
- Declared operation dependency fields: `609`.
- Encoder target-max hit delta after partial shifts: `0`.
- Declared-source + decoder-max delta: `0`.
- Unique-source + decoder-max delta: `0`.
- Previous-end + decoder-max delta: `0`.
- Decoder-valid joint rule improved: `False`.
- Structural blocker: `source_length_parser_still_required`.

## Current Counts

| Metric | Count | Delta vs gate 60 active |
|---|---:|---:|
| `earliest_source_hits_at_declared_length` | `247` | `+0` |
| `unique_source_hits_at_declared_length` | `123` | `+0` |
| `latest_source_hits_at_declared_length` | `128` | `+0` |
| `decoder_max_length_hits_after_declared_source` | `60` | `+0` |
| `encoder_target_max_length_hits_after_declared_source` | `242` | `+0` |
| `joint_encoder_earliest_target_max_hits` | `230` | `+0` |
| `joint_declared_source_decoder_max_hits` | `60` | `+0` |
| `joint_unique_source_decoder_max_hits` | `28` | `+0` |
| `joint_unique_source_target_max_hits` | `118` | `+0` |
| `joint_previous_end_decoder_max_hits` | `1` | `+0` |

## Declared Dependency Ledger

- Literal payload fields: `87`.
- Copy source fields: `261`.
- Copy length fields: `261`.
- Total retained operation dependency fields: `609`.

## Decision

- The final partial-boundary promotions improve the compression bound, but they do not change the source/length dependency scoreboard: encoder target-max coverage and every decoder-valid joint rule remain unchanged versus the gate-60 active formula. The next mechanical blocker remains a source/length parser or derivation, not another local boundary shift.
- The compression bound remains `8154.676268` bits.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
