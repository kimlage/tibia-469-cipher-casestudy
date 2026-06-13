# Iter 379+: Permutation ReversePhrase + Parallel Agent Workflow

## Goal
Break the current plateau safely (no StrictPlus regressions, GT checks intact) by:
- Adding a permutation-aware ReversePhrase scan (analysis-first) to catch word-order shuffles.
- Expanding corpus/signature index coverage without importing full copyrighted text (derived counts only).
- Formalizing a “parallel agents” workflow: multiple safe experiments on workbook copies, then merge only vetted knobs/insights into the canonical XLSX.

## Constraints / Guardrails
- Canonical workbook: `bonelord_469_iter129.xlsx` (increment in place).
- Never increase `WEAK`, `MICRO`, `SingleCharFrac`; keep `Coverage_StrictPlus_v108==1`.
- GroundTruth Live Check remains a hard guardrail.
- Corpus: do not persist full copyrighted text in XLSX; allow only derived counts/hashes + short excerpts + URL.
- ReversePhrase permutation step is analysis-only by default (no auto-emission into Glossary unless explicitly enabled).

## Tasks (Status)
- [x] Run `next iteration` once to capture baseline at iter378 and verify invariants.
- [ ] Add Step 29: permutation-aware ReversePhrase scan (bag-of-words over spans, order-free assignment).
- [ ] Add new sheets for permutation hits/candidates (`ReversePhrasePermuteHits_Auto`, `ReversePhrasePermuteCands_Auto`).
- [ ] Add FlowSettings toggles/limits for permutation scan (runtime caps, max words, enable flag).
- [ ] Update `FlowSteps` (workbook) to include the new step.
- [ ] Update validation script to assert new sheet schemas exist and remain analysis-only.
- [ ] Run iter379 and report evolution stats (EvAvg/Weak/Micro/Single/Tokens + reverse-permute hits/candidates).
- [ ] Parallel agent workflow:
  - Run safe experiments on copies under `tmp/spreadsheets/lab/` (different knobs) and compare metrics/hits.
  - Merge only chosen knobs into canonical FlowSettings, never bulk-merge sheets.

## Implementation Log
- 2026-02-09: iter378 executed on `bonelord_469_iter129.xlsx` (no mech/GT changes; metrics stable; invariants OK).
- 2026-02-09: Implemented Step 29 (permutation-aware ReversePhrase) + new sheets `ReversePhrasePermuteHits_Auto`/`ReversePhrasePermuteCands_Auto`; validated iter379 (no hits yet; invariants OK).
- 2026-02-09: Improved `SestinaScan` scoring robustness (token-signature keys + envoi scoring/ranking columns). Ran iter380; `SestinaScan fp_changed=1` (candidate set updated), invariants OK.
- 2026-02-09: Added local dictionary-derived sig-index (`LoreSigIndex_Dict_Auto`) + Step 112; merged into `LoreAlignment_Auto`. Ran iter381: display layers improved materially (semantic/english/context/codeaware changed; ContextEnglish avg_score increased to 6.377957; CodeAware overrides 56). Ran iter382: stabilized (no further changes). Invariants OK.
