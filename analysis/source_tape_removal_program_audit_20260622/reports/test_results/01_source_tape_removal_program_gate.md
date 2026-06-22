# Decoder-Visible Source Tape Removal Gate

Classification: `source_tape_removal_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Try to remove the copy source/hint tape from the executable decoder. The decoder receives seed books, coarse controls, exact lengths, and literal payloads. A decoder-visible policy chooses copy sources; misses are repaired by paid uniform source-address exceptions.

## Best Policy

- Best policy: `previous_source_end`.
- Best policy classification: `source_tape_removal_not_promoted`.
- Default copy hits: `22/537`.
- Unrepaired exact books over repeated holdouts: `0`.
- Baseline copy-hint bits: `5062.568`.
- Policy+exception bits: `6672.081`.
- Saving vs copy-hint tape: `-1609.513`.
- Random visible-source p95 saving: `-8.288`.

| Split | Test Books | Copy Ops | Default Hits | Exact Books Without Repairs | Saving |
| --- | ---: | ---: | ---: | ---: | ---: |
| `prefix_20` | `50` | `155` | `5` | `0` | `-486.732` |
| `prefix_30` | `40` | `119` | `5` | `0` | `-375.829` |
| `prefix_40` | `30` | `80` | `4` | `0` | `-238.998` |
| `prefix_50` | `20` | `49` | `1` | `0` | `-148.265` |
| `prefix_60` | `10` | `18` | `1` | `0` | `-48.560` |
| `family_hellgate_public_bookcase_1` | `2` | `14` | `0` | `0` | `-50.690` |
| `family_hellgate_public_bookcase_13` | `3` | `12` | `2` | `0` | `-34.916` |
| `family_hellgate_public_bookcase_2` | `2` | `16` | `0` | `0` | `-49.593` |
| `family_hellgate_public_bookcase_20` | `2` | `4` | `0` | `0` | `-4.372` |
| `family_hellgate_public_bookcase_21` | `3` | `5` | `1` | `0` | `-9.215` |
| `family_hellgate_public_bookcase_23` | `2` | `9` | `0` | `0` | `-24.519` |
| `family_hellgate_public_bookcase_27` | `2` | `4` | `1` | `0` | `-7.454` |
| `family_hellgate_public_bookcase_3` | `2` | `10` | `0` | `0` | `-29.555` |
| `family_hellgate_public_bookcase_30` | `2` | `3` | `0` | `0` | `-7.723` |
| `family_hellgate_public_bookcase_33` | `2` | `5` | `1` | `0` | `-8.355` |
| `family_hellgate_public_bookcase_4` | `3` | `7` | `0` | `0` | `-16.005` |
| `family_hellgate_public_bookcase_40` | `4` | `5` | `0` | `0` | `-12.326` |
| `family_hellgate_public_bookcase_6` | `2` | `5` | `1` | `0` | `-1.999` |
| `family_hellgate_public_bookcase_7` | `3` | `15` | `0` | `0` | `-48.013` |
| `family_hellgate_public_bookcase_8` | `2` | `2` | `0` | `0` | `-6.394` |

## Decision

`source_tape_removal_not_promoted`: decoder-visible policies do not beat the existing copy-hint/source tape after exception costs. The source tape remains external in the minimal program.

## Remaining External Fields

- copy source/hint tape
- coarse control stream when macro/template program misses
- book-level composition index
- literal innovation payload tape
- seed books `0..9`
- `row0`
