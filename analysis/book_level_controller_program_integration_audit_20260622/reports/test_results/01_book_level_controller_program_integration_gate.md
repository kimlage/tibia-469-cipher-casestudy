# Book-Level Controller Program Integration Gate

Classification: `book_level_controller_program_integration_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Integrate the previously promoted book-level coarse length controller into the executable minimal external tape program. The comparison target is the program ledger's uniform `coarse type:length_bucket` stream plus book-level composition index.

## Summary

- Frozen controller pair: `book_length__op_count`.
- Baseline coarse+composition bits over splits: `3824.176`.
- Controller+correction bits over splits: `4069.056`.
- Saving: `-244.881` bits.
- True sequence in beam: `66/186`.
- Nontrivial true sequence in beam: `16`.
- Top-1 exact books: `38`.
- Top-1 nontrivial exact books: `0`.
- Top-1 exact ops: `38`.
- Model/grammar descriptor cost charged here: `0.000` bits (generous lower bound).
- Same-multiset shuffled p95: `7.170` bits.
- Random trainset p95: `-13.320` bits.

| Split | Test Books | Baseline | Controller | Saving | Sequence In Beam | Top1 Exact |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `prefix_20` | `50` | `1102.893` | `1207.255` | `-104.362` | `15` | `0` |
| `prefix_30` | `40` | `852.056` | `910.633` | `-58.577` | `13` | `10` |
| `prefix_40` | `30` | `567.575` | `593.292` | `-25.717` | `12` | `9` |
| `prefix_50` | `20` | `333.510` | `341.982` | `-8.472` | `9` | `7` |
| `prefix_60` | `10` | `109.773` | `93.416` | `16.358` | `7` | `5` |
| `family_hellgate_public_bookcase_1` | `2` | `141.300` | `149.300` | `-8.000` | `0` | `0` |
| `family_hellgate_public_bookcase_13` | `3` | `90.742` | `102.742` | `-12.000` | `0` | `0` |
| `family_hellgate_public_bookcase_2` | `2` | `145.074` | `153.074` | `-8.000` | `0` | `0` |
| `family_hellgate_public_bookcase_20` | `2` | `28.925` | `28.562` | `0.363` | `1` | `0` |
| `family_hellgate_public_bookcase_21` | `3` | `27.242` | `13.224` | `14.018` | `3` | `1` |
| `family_hellgate_public_bookcase_23` | `2` | `56.246` | `64.246` | `-8.000` | `0` | `0` |
| `family_hellgate_public_bookcase_27` | `2` | `23.173` | `23.588` | `-0.415` | `1` | `1` |
| `family_hellgate_public_bookcase_3` | `2` | `59.876` | `67.876` | `-8.000` | `0` | `0` |
| `family_hellgate_public_bookcase_30` | `2` | `20.340` | `20.755` | `-0.415` | `1` | `1` |
| `family_hellgate_public_bookcase_33` | `2` | `31.686` | `39.686` | `-8.000` | `0` | `0` |
| `family_hellgate_public_bookcase_4` | `3` | `50.098` | `62.098` | `-12.000` | `0` | `0` |
| `family_hellgate_public_bookcase_40` | `4` | `27.969` | `28.799` | `-0.830` | `2` | `2` |
| `family_hellgate_public_bookcase_6` | `2` | `46.680` | `54.680` | `-8.000` | `0` | `0` |
| `family_hellgate_public_bookcase_7` | `3` | `101.849` | `113.849` | `-12.000` | `0` | `0` |
| `family_hellgate_public_bookcase_8` | `2` | `7.170` | `0.000` | `7.170` | `2` | `2` |

## Decision

`book_level_controller_program_integration_not_promoted`: the controller does not reduce the executable coarse+composition tape after corrections and controls.
