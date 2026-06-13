# Iter239: AutoPhraseCribs (Targeted Reverse Phrase Mining)

## Goal
Break the reverse-phrase plateau (Step 28 hits=0) by generating a *targeted* phrase set derived from a public Tibia corpus, using signature-feasibility against the current decode token stream.

Constraints:
- Safe: never touch DP core invariants; keep `Coverage_StrictPlus_v108==1`.
- Guardrail: GroundTruth live check must pass before expanding any search.
- Do not persist full external corpora in the workbook; only store a small, capped phrase crib set + URLs.

## Tasks
- [x] Add Step `27` to the auto-chain: **AutoPhraseCribs**.
- [x] Add new sheet `PhraseCribs_Auto` (runner-managed; analysis-only).
- [x] Fetch public Tibia corpus (NPC transcripts + books) with on-disk cache under `tmp/`.
- [x] Build a global span-signature feasibility set from the current Books token stream (max span = `ReversePhrase_MaxSpanTokens`).
- [x] Select a capped set of phrases whose *all word signatures* are feasible (share=1.0) and that maximize distinctiveness (rarity-weighted).
- [x] Wire Step 28 to include `PhraseCribs_Auto` when `ReversePhrase_IncludePhraseCribsAuto=TRUE`.
- [x] Update `FlowSteps` entries, `FlowRunLog`, and `FlowState.LastChangeSummary` to include Step 27 stats.
- [x] Update `scripts/bonelord_run_until_stale.py` to treat Step 27 changes as “progress” (not stale).
- [x] Update `scripts/bonelord_validate_workbook.py` expected steps to include `27`, `98` (and keep guardrails).

## Acceptance Criteria
- Running `python scripts/bonelord_flow_next_iteration.py bonelord_469_iter129.xlsx`:
  - Produces a `FlowRunLog` entry for Step 27 (NO_CHANGE/CHANGED).
  - Creates/updates `PhraseCribs_Auto` deterministically and idempotently.
  - Step 28 consumes `PhraseCribs_Auto` (visible by `reverse_phrase_scanned` increasing from it).
  - All invariants still pass via `python scripts/bonelord_validate_workbook.py bonelord_469_iter129.xlsx`.

## Implementation Log
- 2026-02-07: Implemented Step 27 + PhraseCribs_Auto + caching and wired Step 28 inclusion.
- 2026-02-07: Iter239 wrote `PhraseCribs_Auto` with 27 feasible Tibia phrases (scanned=50k, eligible=27) but Step 28 still had hits=0.
- 2026-02-07: Added plateau ladder bump for `ReversePhrase_MaxSpanTokens` (6 -> 10); Iter240 still hits=0.
- 2026-02-07: Added Step 99 (EnglishMap -> Glossary retext) to actually advance readability; Iter241 applied 9 GT-safe retexts, changing StrictPlus output for 19/70 books.
- 2026-02-07: Iter242–243 reached staleness again (no further safe promotions/retexts; metrics unchanged).
