# Closed Loop Rescue Surface Audit

Classification: `closed_loop_rescue_surface_audit_only`
Translation delta: `NONE`

## Purpose

Classify where sampled closed-loop oracle rescues occur relative to the
canonical skeleton. This is a missing-state surface audit, not a
generator: the skeleton is used only after decoding to label events.

## Summary

- Sample book instances: `15`.
- Rescue events classified: `1732`.
- Surface counts: `{'book_end': 6, 'copy': 1721, 'literal': 5}`.
- Copy/literal surface fraction: `0.993649` / `0.002887`.
- Exact internal cutpoint events: `27` (`0.015589`).
- Near internal cutpoint events: `82` (`0.047344`).
- Operation-start events: `27` (`0.015589`).
- Early <=5% events: `86` (`0.049654`).
- Early <=20% events: `374` (`0.215935`).
- Mean rescue rank bits: `12.358`.
- Promotes rescue surface: `False`.

This audit classifies oracle rescue events from the sampled closed-loop rescue ledger against the canonical skeleton. It does not use the skeleton for generation; it asks whether the missing closed-loop state has an obvious surface such as operation boundaries or literal interiors.

## Cutoff Rows

| Cutoff | Books | Events | Surface Counts | Exact Cutpoint | Near Cutpoint | Op Start | Early <=20% | Mean Rank Bits |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `20` | `[20, 45, 69]` | `288` | `{'book_end': 1, 'copy': 287}` | `0.024` | `0.066` | `0.024` | `0.219` | `12.243` |
| `30` | `[30, 50, 69]` | `349` | `{'copy': 349}` | `0.014` | `0.043` | `0.014` | `0.229` | `12.396` |
| `40` | `[40, 55, 69]` | `347` | `{'book_end': 2, 'copy': 342, 'literal': 3}` | `0.017` | `0.049` | `0.017` | `0.190` | `12.287` |
| `50` | `[50, 60, 69]` | `356` | `{'book_end': 1, 'copy': 355}` | `0.011` | `0.037` | `0.011` | `0.225` | `12.367` |
| `60` | `[60, 65, 69]` | `392` | `{'book_end': 2, 'copy': 388, 'literal': 2}` | `0.013` | `0.046` | `0.013` | `0.217` | `12.463` |

## Decision

- Rescue events are diagnostic labels for the missing state, not generator outputs.
- A promotable next step would require a decoder-visible state that predicts these rescue surfaces without the canonical skeleton.
- Row0, plaintext, translation, and compression bound remain unchanged.
