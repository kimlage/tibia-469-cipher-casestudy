# Closed Loop Rescue Ledger

Classification: `closed_loop_rescue_high_external_control`
Translation delta: `NONE`

## Purpose

Measure how much external steering the closed-loop latent transducer needs
after target teacher forcing is removed. When the true prefix falls
outside the beam, the best true-prefix state is injected back and charged
`log2(rank)` bits. This is a fixed first/middle/last suffix-book sample
per cutoff, not a full-corpus rescue total.

## Summary

- Prefix cutoffs tested: `5`.
- Beam width: `250`.
- Sample books per cutoff: `3`.
- Tested book instances: `15`.
- Forced exact books with rescue: `15`.
- Books needing no rescue: `0`.
- Total rescue events: `1732`.
- Mean rescue events per book: `115.467`.
- Total rescue bits: `21403.967`.
- Total raw digit bits: `6972.727`.
- Rescue bits / raw digit bits: `3.069669`.
- Max true-prefix rank: `22500`.
- Mean first rescue fraction: `0.015051`.
- Low external-control regime: `False`.

This sampled ledger turns closed-loop failure into a steering-cost measure. Whenever the true prefix falls outside the beam, an oracle rescue injects it back and charges log2(rank). A small rescue ledger would suggest a missing compact latent state; a large ledger means the closed-loop route still needs substantial external guidance.

## Cutoff Rows

| Cutoff | Sample Books | Forced Exact | No Rescue | Rescue Events | Rescue Bits | Rescue/Raw | Max Rank | Mean First Rescue |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `[20, 45, 69]` | `3` | `0` | `288` | `3525.946` | `3.015385` | `22498` | `0.019818` |
| `30` | `[30, 50, 69]` | `3` | `0` | `349` | `4326.224` | `3.021631` | `22498` | `0.013934` |
| `40` | `[40, 55, 69]` | `3` | `0` | `347` | `4263.696` | `3.027124` | `22500` | `0.014477` |
| `50` | `[50, 60, 69]` | `3` | `0` | `356` | `4402.553` | `3.067825` | `22499` | `0.013905` |
| `60` | `[60, 65, 69]` | `3` | `0` | `392` | `4885.547` | `3.197166` | `22499` | `0.013122` |

## Decision

- This is an oracle rescue ledger, not a generator.
- Promotion would require a low external-control regime and a concrete decoder-visible state that predicts the rescues.
- The current closed-loop transducer remains unpromoted.
- Row0, plaintext, translation, and compression bound remain unchanged.
