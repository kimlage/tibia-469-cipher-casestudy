# Shared Literal-Length Innovation Tape Gate

Classification: `shared_literal_length_tape_weak_clue`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether the already-paid literal innovation tape can also drive the within-bucket length residual tape. Each operation reads one literal-tape digit at a prefix-selected offset and applies a small arithmetic policy; mismatches are paid as correction sites plus residual payload.

## Summary

- Literal tape digits: `266`.
- Length residual events: `261`.
- Policies tested: `264`.
- Observed uniform residual bits: `1945.074`.
- Observed correction bits after tape prediction: `1981.829`.
- Observed saving vs uniform residual: `-36.755`.
- Shuffled literal-tape p95 saving: `-56.770`.
- Hits: `53/493` (`0.107505`).
- Selected policies: `{"{'name': 'digit_mod', 'offset': 5, 'a': 1, 'b': 0}": 4, "{'name': 'digit_scaled_round', 'offset': 5, 'a': 1, 'b': 0}": 1}`.

## Prefix-Holdout Rows

| Cutoff | Policy | Train Ops | Test Ops | Test Hits | Test Correction Bits | Test Saving |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `20` | `digit_scaled_round:off5:a1:b0` | `79` | `182` | `27` | `707.812` | `-9.487` |
| `30` | `digit_mod:off5:a1:b0` | `121` | `140` | `15` | `567.284` | `-14.076` |
| `40` | `digit_mod:off5:a1:b0` | `166` | `95` | `9` | `388.890` | `-10.604` |
| `50` | `digit_mod:off5:a1:b0` | `205` | `56` | `2` | `233.946` | `-2.589` |
| `60` | `digit_mod:off5:a1:b0` | `241` | `20` | `0` | `83.898` | `0.000` |

## Decision

The literal tape beats shuffled controls but does not save enough bits to replace the residual tape. It remains a weak clue only.

`row0`, translation, plaintext, and the compression bound remain unchanged.

## Remaining External Fields

- `type:length_bucket` control stream
- within-bucket length residual innovation tape
- literal innovation tape payload and schedule
- copy-hint rank stream
- seed books `0..9`
- `row0`
