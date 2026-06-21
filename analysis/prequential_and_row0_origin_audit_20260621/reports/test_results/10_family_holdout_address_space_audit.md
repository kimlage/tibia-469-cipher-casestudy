# Family Holdout Address Space Audit

Classification: `family_copy_address_losses_are_holdout_coordinate_artifacts`
Translation delta: `NONE`

## Purpose

Audit 09 localized the five family holdout losses to copy-address bits.
This audit tests whether that is a real recipe loss or a coordinate
artifact: the active recipe was originally charged in global numeric
book order, while the family reparse emits held-out books after the
training complement.

## Summary

- Families checked: `5`.
- Active recipe roundtrips after holdout-coordinate rebase: `True`.
- Reparse roundtrips: `True`.
- Positive original-coordinate address losses: `4`.
- Nonpositive rebased-coordinate address losses: `5`.
- Mean original-coordinate address delta: `4.667` bits.
- Mean rebased-coordinate address delta: `0.000` bits.
- Total active rebase coordinate shift: `23.337` bits.

## Rows

| Family | Books | Original delta | Rebased delta | Coordinate shift | Explained share | Copy count |
|---|---|---:|---:|---:|---:|---:|
| `hellgate_public_bookcase_13` | `[40, 41, 42]` | `9.271` | `0.000` | `9.271` | `1.000` | `12` |
| `hellgate_public_bookcase_21` | `[62, 63, 64]` | `0.515` | `0.000` | `0.515` | `1.000` | `5` |
| `hellgate_public_bookcase_33` | `[18, 19]` | `8.986` | `0.000` | `8.986` | `1.000` | `5` |
| `hellgate_public_bookcase_7` | `[54, 55, 56]` | `4.565` | `0.000` | `4.564` | `1.000` | `14` |
| `hellgate_public_bookcase_8` | `[68, 69]` | `0.000` | `0.000` | `0.000` | `None` | `2` |

## Decision

- The copy-address losses from audit 09 do not survive a same-coordinate comparison.
- Rebased deltas are interpreted with epsilon `0.001` bits.
- The active recipe remains useful as a full-corpus compression reference, but original-coordinate active address bits are not a fair holdout comparator for families emitted after their training complement.
- This strengthens the family-holdout recipe validation without promoting a final authorial method.
- No plaintext, translation, row0-origin change, or case reopening is introduced.
