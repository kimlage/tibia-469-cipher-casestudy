# Iteration 347 - Add Project Gutenberg "Through the Looking-Glass" (12) to PD Corpus (Safe)

## Goal
Increase context/corpus coverage using **public-domain** text only, to try to break the plateau without touching StrictPlus DP:
- Add Project Gutenberg ebook `12` (Through the Looking-Glass) as an extra PD source.
- Force a derived refresh of `LoreBigrams_Auto` so ContextEnglish and downstream matching can benefit.

Guardrails unchanged:
- `Coverage_StrictPlus_v108 == 1` for all books.
- `groundtruth_live_check()` must pass.
- No mechanical promotions unless the usual no-regression checks pass.

## Changes
File: `./scripts/bonelord_flow_next_iteration.py`
- Added constant:
  - `DEFAULT_PD_LOOKING_GLASS_URL = "https://www.gutenberg.org/files/12/12-0.txt"`
- Added PD source into the default PD list:
  - `("GUTENBERG_LOOKING_GLASS_12", DEFAULT_PD_LOOKING_GLASS_URL)`

## Execution Log
- 2026-02-08
  - Ran next iteration:
    - `python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx`
      - Produced iter `347`
      - `LoreBigrams_Auto` rebuilt/refreshed (derived-only) with the new PD source:
        - Rows `127986 -> 128903` (refreshed)
      - ContextEnglish changed slightly (display-only):
        - `avg_score 5.988454 -> 5.981666`
        - `oov 0.125819 -> 0.129800`
        - `books_changed_rows=1`
      - Core metrics unchanged:
        - `EvAvg=2.326444`, `Weak=0.039798`, `Micro=0.030023`, `Single=0.019899`, `Tokens=893`
      - No new SequenceMatches / ReversePhrase hits.
  - Auto-chain until stale:
    - `python scripts/bonelord_run_until_stale.py bonelord_469_iter129.xlsx --max-iters 20 --stale-consecutive 2`
      - Produced iters `348` and `349` (no additional changes)
  - Validation:
    - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`
      - OK

## Outcome
- PD corpus coverage expanded safely (public-domain only).
- `LoreBigrams_Auto` refreshed successfully and ContextEnglish reacted (small shift), but the plateau persists:
  - no new matches, no hits, no retext, no promotions.
