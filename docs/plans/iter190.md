# Iteration 190 - Fix Readability Regex + Apply Readable Output

## Goals
- Fix the readability rule matcher so enabled rules actually apply.
- Run iteration 190 and verify the readable columns update without affecting StrictPlus mechanics.

## Tasks (Status)
- [x] Fix regex boundary pattern in `apply_readability_rules` (`\\b` -> `\b`).
- [x] Print readability stats at end of runner (repl/books/master) so each iteration reports progress.
- [x] Run `scripts/bonelord_flow_next_iteration.py` on `bonelord_469_iter129.xlsx` (creates backup).
- [x] Verify `FlowRunLog` Step 75 reports non-zero replacements and `Books.Translation_Readable_Auto` changes where expected.

## Implementation Log
- Code:
  - `./scripts/bonelord_flow_next_iteration.py`
    - Fixed readability regex.
    - Added final stdout line: `Readability: repl=..., books_changed_rows=..., master_changed_rows=...`.

- Command:
  - `.venv/bin/python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx`

- Outputs:
  - Backup:
    - `./tmp/spreadsheets/bonelord_469_iter129_backup_iter190.xlsx`
  - Workbook updated:
    - `./bonelord_469_iter129.xlsx`

- Result (iter190):
  - Mechanical promotions accepted: 0
  - Mechanical metrics unchanged.
  - Readability:
    - `repl=2`, `books_changed_rows=2`, `master_changed_rows=0`
    - Books 15/16 readable now render `fiftin statue` as `fifteen statues` in `Translation_Readable_Auto`.

