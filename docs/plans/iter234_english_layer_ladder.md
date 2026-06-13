# iter234: English Layer Ladder (Auto-Relax on Plateau)

## Summary
After iter231 introduced `Translation_English_Auto`, the loop became stale again because the default
English mapping thresholds were conservative (`min_total=20`, `min_share=0.95`) and produced only 3 mappings.

This adds an **auto-relax ladder** tied to the existing plateau ladder so that when mechanical progress
stalls, the runner automatically expands the English layer mapping set (still display-only).

## Tasks (Status)
- [x] Add English ladder logic (reuse `PlateauLadder_Rung`) to relax:
  - rung0: `EnglishLayer_MinTotalCount=20`, `EnglishLayer_MinTopShare=0.95`
  - rung1: `10`, `0.93`
  - rung2: `5`, `0.90`
- [x] Ensure changes are logged in FlowSettings notes and reflected in Step 98 output.
- [x] Run iterations until stale and record evolution stats.

## Safety
- English ladder remains **display-only** (Books/MasterText columns only).
- No DP/tokenization/Glossary edits.

## Implementation Log
- Code:
  - Updated runner: `./scripts/bonelord_flow_next_iteration.py`
    - Added an English-layer ladder inside the existing plateau auto-relax block.
    - On plateau, relaxes `EnglishLayer_MinTotalCount` and `EnglishLayer_MinTopShare` based on `PlateauLadder_Rung`.

- Runs:
  - Iter234:
    - English thresholds relaxed by ladder (rung=2): `min_total=5`, `min_share=0.90`.
    - Step 98: `EnglishLayer: map_rows=6, repl=103, books_changed_rows=11, master_changed_rows=1`.
  - Iter235-236: stale (no new mechanical/semantic/english changes).

- Validation:
  - `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx` => OK (iteration=236, status=RESOLVED).
