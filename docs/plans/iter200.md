# Iteration 200 - Plateau (No New Safe Promotions)

## Run Result
- `mech_promoted=0`
- Evolution (Books, length-weighted): no change
  - EvAvg `2.332082 -> 2.332082` (d=`+0.000000`)
  - Weak `0.081166 -> 0.081166` (d=`+0.000000`)
  - Micro `0.035608 -> 0.035608` (d=`+0.000000`)
  - Single `0.076628 -> 0.076628` (d=`+0.000000`)
  - Tokens `1458 -> 1458` (d=`+0`)
- Structural: `superanchors=2` (unchanged)
- Backup:
  - `./tmp/spreadsheets/bonelord_469_iter129_backup_iter200.xlsx`

## Diagnostics
- CandidatePromotions: `60` scanned, all skipped.
  - `51` skipped as `No effect in DP metrics (not used)`
  - `6` skipped as `No improvement ...`
  - Others blocked by `SingleCharFrac increase` or `GT live check mismatch`

## Validation
- `scripts/bonelord_validate_workbook.py` OK

