---
page_id: source-inspiration-model
page_type: finding
context: bonelord-469
visibility: public_candidate
status: frozen
updated_at: 2026-06-20
moc_parent: README.md
source_refs:
  - analysis/inspiration_model_20260620
  - docs/plans/2026-06-19_lore_evidence_mechanical_parallel_plan.md
---

# 15. Source-Inspiration Model

[<- Eye/Blink Arity Model](14-eye-blink-arity-model.md) . [Wiki home](README.md)

---

## Verdict

The lore/source-inspiration pass found no new official ground truth and no new
real formula-discovery direction. It closes source families and preserves
mechanism hypotheses as controlled comparanda, but it does not reopen semantic
decoding.

Translation delta: `NONE`.

Round result: `NEGATIVE / plateau confirmed`.

## Scope

The pass searched and consolidated:

- official/in-game/CipSoft-adjacent material;
- EN/global, PT-BR/BR, PL, ES/LATAM, DE, and other-language source lanes;
- Knightmare/profile/NPC and quest-mechanism comparanda;
- D&D/Beholder inspiration, Beholder -> Bonelord rename context, `3478`,
  `486486`, Bonelord Tome, Beware of the Bonelords, Secret Library
  `74032 45331`, Honeminas/Magic Web, and Excalibug;
- H19-H24 mechanism tests with controls or explicit blockers.
- deep statistical controls for lore seeds, external-string coverage, row0
  seed-derived models, book phase motifs, E/render anomalies, and identity
  co-occurrence.

The main artifact directory is
[`analysis/inspiration_model_20260620/`](../../analysis/inspiration_model_20260620/).

## Results

| Front | Result |
|---|---|
| Official ground truth | none found |
| Source registry | 18 evidence families, each with allowed and blocked uses |
| Language lanes | source hygiene and rejected-claim provenance; no semantic novelty |
| D&D/Beholder | weak clue only; cannot prove intent or semantics |
| Knightmare/quest mechanisms | useful ontology/source classifier only |
| Excalibug | blocked pending official Bonelord-language prompt/answer or gloss |
| Avar Tar | remains a negative control |
| Secret Library `74032 45331` | remains an unglossed external numeric anchor |
| Tridiag / Donina | local E/render clue only; no formula |
| Paradox / Spirit Grounds / Evil Mastermind | rejected controls / anti-overfit guardrails |
| Dreadeye / First Dragon | watchlist only |

## H19-H24 Classification

| ID | Hypothesis | Classification |
|---|---|---|
| H19 | D&D/Beholder eye rays as 10-channel digit system | `weak_clue` |
| H20 | central-eye / zero suppression | `weak_clue` |
| H21 | Knightmare quest mechanisms as comparanda | `accepted_mechanical` narrowly: ontology/source-class machinery only |
| H22 | Excalibug language-gated route | `blocked_waiting_for_official_source` |
| H23 | Dreamer/Bonelord duality as phrase/book split | `watchlist_only` |
| H24 | books as knowledge objects/entities | `weak_clue` |

## Reports

- [Final inspiration model report](../../analysis/inspiration_model_20260620/reports/final_inspiration_model_report.md)
- [Source corpus report](../../analysis/inspiration_model_20260620/reports/source_corpus_report.md)
- [Mechanism crosswalk report](../../analysis/inspiration_model_20260620/reports/mechanism_crosswalk_report.md)
- [Inspiration model leaderboard](../../analysis/inspiration_model_20260620/reports/inspiration_model_leaderboard.md)
- [Source registry](../../analysis/inspiration_model_20260620/source_registry.yaml)
- [Deep statistical exhaustion](../../analysis/inspiration_model_20260620/reports/test_results/14_deep_statistical_exhaustion.md)
- [Plan exhaustion audit](../../analysis/inspiration_model_20260620/reports/test_results/15_plan_exhaustion_audit.md)

## What Counts As Future Progress

Only a CipSoft/in-game number-to-text pair, book-to-text pair, symbol table, or
a lower-cost mechanical formula that beats the current controlled baselines can
move the verdict. More lore, fan vocabulary, or unglossed numbers do not.
