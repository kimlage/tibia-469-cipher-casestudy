# Copy State Rescue Diagnostic

Classification: `copy_state_control_blocker_mapped`
Translation delta: `NONE`

## Purpose

Diagnose the copy-span failure exposed by the closed-loop rescue surface
audit. This does not promote a generator; it separates missing copy
inventory from low-rank copy-state/control failure.

## Event Summary

- Rescue events traced: `1732`.
- Copy-surface rescue events: `1721`.
- Last-kind counts: `{'copy': 16, 'literal': 1716}`.
- Copy-surface last-kind counts: `{'copy': 16, 'literal': 1705}`.
- Copy-surface true-copy event fraction: `0.009297`.
- Copy-surface true-literal event fraction: `0.990703`.
- Mean copy-surface rescue rank bits: `12.360`.
- Mean copy-surface last emitted length: `1.065`.

## Canonical Copy Prefix Coverage

- Copy ops tested: `32`.
- Copy digits tested: `1240`.
- Source-match ops: `32` (`1.000000`).
- Ops with any inventory prefix: `32`.
- Ops with any pruned prefix: `0`.
- Ops with full length allowed: `12`.
- Ops with full inventory chunk: `12`.
- Ops with full pruned chunk: `0`.
- Inventory prefix digit fraction: `0.857258`.
- Pruned prefix digit fraction: `0.000000`.
- Mean inventory/pruned prefix fraction: `0.907349` / `0.000000`.

This diagnostic asks whether copy-span rescue failures are mostly missing inventory or low-rank control. It uses canonical copy spans only for post-hoc labeling and coverage accounting, not for decoding.

## Cutoff Rows

| Cutoff | Books | Events | Copy Events | Copy Last-Kind | Copy Ops | Any Pruned Prefix | Pruned Prefix Digits |
| ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `20` | `[20, 45, 69]` | `288` | `287` | `{'copy': 2, 'literal': 285}` | `11` | `0` | `0.000` |
| `30` | `[30, 50, 69]` | `349` | `349` | `{'copy': 4, 'literal': 345}` | `7` | `0` | `0.000` |
| `40` | `[40, 55, 69]` | `347` | `342` | `{'copy': 4, 'literal': 338}` | `7` | `0` | `0.000` |
| `50` | `[50, 60, 69]` | `356` | `355` | `{'copy': 4, 'literal': 351}` | `5` | `0` | `0.000` |
| `60` | `[60, 65, 69]` | `392` | `388` | `{'copy': 2, 'literal': 386}` | `2` | `0` | `0.000` |

## Decision

- This maps the next blocker to copy-state/content control.
- It does not produce a decoder-visible source/length rule.
- Row0, plaintext, translation, and compression bound remain unchanged.
