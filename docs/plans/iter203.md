# Iteration 203 - Macro Collapse Continues (Marker-Aware)

## Run Result (Iter 203)
- `mech_promoted=52`
- Evolution (Books, length-weighted):
  - EvAvg `2.335102 -> 2.337179` (d=`+0.002077`)
  - Weak `0.046081 -> 0.046081` (d=`+0.000000`)
  - Micro `0.028626 -> 0.028626` (d=`+0.000000`)
  - Single `0.051318 -> 0.035608` (d=`-0.015710`)
  - Tokens `1195 -> 1000` (d=`-195`)
- Backup:
  - `./tmp/spreadsheets/bonelord_469_iter129_backup_iter203.xlsx`

## Notes
- Promotions are heavily marker-aware macros like `TAE` (`to a <E>`), `EIV` (`<E> you've`), etc.
- This is mechanically safe because macros must match the existing lossless marker stream; it primarily reduces `SingleCharFrac` and token count.

## Validation
- `scripts/bonelord_validate_workbook.py` OK

