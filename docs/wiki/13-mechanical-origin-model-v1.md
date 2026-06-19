---
page_id: mechanical-origin-model-v1
page_type: finding
context: bonelord-469
visibility: public_candidate
status: frozen
updated_at: 2026-06-19
moc_parent: README.md
source_refs:
  - analysis/mechanism_model_20260618
  - analysis/generator_search_20260618
  - analysis/ml_formula_probe_20260618
---

# 13. Mechanical Origin Model v1

[<- Generator-Origin Search](12-generator-origin-search.md) . [Wiki home](README.md)

---

## Verdict

The strongest current result is a partial mechanical fabrication model for the
70-book layer. It improves the explanation of how the numeric material was
assembled, but it does not find a translation, a new glossary, a plaintext
channel, or the original compact formula for the 10x10 pair matrix.

This page freezes that state as `mechanical_origin_model_v1`.

## Model Stack

`mechanical_origin_model_v1` is:

```text
row0 code table
+ unordered pair / mirror geometry
+ directed render exceptions ({19,91}, missing 39)
+ homophone classes
+ 16 numeric tape components
+ 62 module slices
+ merged same-component spans
+ exact residual repeats
+ remaining literals
+ zero-rendering support layer
```

The model is mechanical only. It is not a semantic decoder.

## Accepted Mechanical Layers

| Layer | Current evidence | Status |
|---|---|---|
| `row0` code table | 99-entry code->symbol substrate; byte-exact 70/70 reconstruction | accepted mechanical substrate |
| Pair/mirror geometry | 54/55 unordered pairs pure; one conflict `{19,91}`; ordered surface has only missing `39` | accepted render/geometry layer |
| Tape formula | 16 tape components, 62 module slices, 12 tape spans, 70/70 book roundtrip | accepted mechanical formula |
| Tape MDL gain | Rough total gain `6597.1` bits over literal module table | accepted compression evidence |
| Residual exact repeats | MDL-pruned `exact_repeat` covers `1683/2083` residual digits; about `400` digits remain literal | accepted secondary mechanical layer |
| Chayenne holdout | minLen=8 coverage `45/49`; Avar Tar minLen=8 coverage `0/115` | secondary validation only |
| Zero omission | local previous/next context and geometry predict omission better than code-only | supporting render layer |

Primary sources:
[tape_based_formula_report.md](../../analysis/generator_search_20260618/tape_based_formula_report.md),
[residual_coverage_mdl_report.md](../../analysis/mechanism_model_20260618/residual_coverage_mdl_report.md),
[external_holdout_chayenne_ytc_report.md](../../analysis/generator_search_20260618/external_holdout_chayenne_ytc_report.md),
[zero_compact_rule_report.md](../../analysis/generator_search_20260618/zero_compact_rule_report.md).

## Weak Clues

These are real or suggestive mechanical signals, but they are not promoted as
the origin formula.

| Clue | Why it remains weak |
|---|---|
| `6<->9` orbit | compresses/structures a small part of the pair table, but mixed-orbit overhead and controls prevent promotion |
| E layer | diagonal/high-block E pressure is real locally, but blockers, residuals, and render-origin probes fail controls |
| Orientation/render | ordered `ab` vs `ba` has strong context signal, but does not generalize as a grid formula |
| Chayenne | compatible with 469 module/copy layer, but not an attested plaintext or training source |
| ML zero signal | confirms local render predictability; does not discover a matrix formula |
| Eye/blink arity | `5 eyes -> C(5,2)=10 -> 55 cells` matches the row0 scale, but K5/5x2 tests reject it as the pair-cell formula |

## Rejected As Origin Formula

The following remain documented but not promoted:

- 10x10 matrix formula searches, including the no-hard-gate ledger of
  `294528` candidates. Best coverage is only `21/55`, classified
  `lookup_disguise`.
- PRNG/seeds, Magic Web/Honeminas numbers, `1 = Tibia`, and lore-number masks.
- Short repeats and permissive residual operators that also cover controls.
- Avar Tar as 469: it is a negative control, not validation.
- ML pair-cell formula: it does not beat the simple/mechanical baselines.
- High-block blocker drawing/stroke and render-origin E-priority probes:
  both explain local patterns descriptively but fail controls.
- Eye/blink K5 and `5x2` arity models as row0 label generators: both are
  useful lore bridges but cost more than lookup and are ordinary under
  controls.

Primary sources:
[matrix_generator_exhaustive_report.md](../../analysis/generator_search_20260618/matrix_generator_exhaustive_report.md),
[generator_model_final_report.md](../../analysis/generator_search_20260618/generator_model_final_report.md),
[accepted_rejected_hypotheses.json](../../analysis/generator_search_20260618/accepted_rejected_hypotheses.json),
[k5_eye_pair_model_report.md](../../analysis/eye_model_20260619/k5_eye_pair_model_report.md),
[eye_state_5x2_model_report.md](../../analysis/eye_model_20260619/eye_state_5x2_model_report.md).

## What Counts As Future Progress

Further work should not count progress by the number of new fronts or scripts.
It should count only if it improves one of these axes:

1. Matrix origin: a compact rule that predicts pair-cell labels under MDL and
   controls.
2. Assembly origin: a smaller or better-validated tape/module/literal formula.
3. External truth: CipSoft-attested number->plaintext, book->plaintext, or a
   symbol table.

Without external truth, new semantic translations, glossaries, or plaintext
claims remain inadmissible.

## Reproduction Pointers

- Main consolidated leaderboard:
  [generator_mdl_leaderboard.md](../../analysis/generator_search_20260618/generator_mdl_leaderboard.md)
- Final generator verdict:
  [generator_model_final_report.md](../../analysis/generator_search_20260618/generator_model_final_report.md)
- Self-contained tape formula:
  [tape_based_formula_469.json](../../analysis/generator_search_20260618/tape_based_formula_469.json)
- Base mechanism formula:
  [mechanical_formula_469.json](../../analysis/mechanism_model_20260618/mechanical_formula_469.json)

Translation delta: `NONE`.
