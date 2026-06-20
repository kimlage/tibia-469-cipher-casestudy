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
| Literal-reference formula | 36 remaining literal items are replaced by references into existing tape components, saving roughly `1167.4` bits with 70/70 book roundtrip; component-shuffle and random-literal controls save `0.0` bits in 400 runs | controlled mechanical improvement |
| Hierarchical reference formula | 16 tape components are themselves reconstructed by literal runs plus self-references, then the improved book recipes reconstruct 70/70 books at roughly `13858.5` bits | strongest structured tape/module generator |
| Sequential LZ book formula | 70 books are emitted in numeric order as literal runs plus earlier/current-prefix digit references; `10190.0` rough bits, 70/70 roundtrip, digit-shuffle/random controls fail | strong copy/reference upper bound |
| Non-numeric LZ order search | best sampled order saves `186.0` gross bits but costs `332.5` bits to describe as a permutation | rejected unless externally supplied |
| Sequential LZ literal-run cost formula | the same sequential generator is charged by literal runs instead of per-digit literal flags; `9944.0` rough bits, 70/70 roundtrip, and digit-shuffle/random/book-order controls are worse (`p=0.0062`) | strong copy/reference upper bound |
| Sequential LZ dynamic-parse formula | the same run-literal vocabulary is parsed by dynamic programming at fixed `min_len=6`; `9823.3` rough bits, 70/70 roundtrip, digit-shuffle/random controls fail, and book-order support is only moderate (`p=0.0396`) | strongest copy/reference upper bound |
| Copy address model search | back-distance, source-delta, and book-relative source addresses all cost more than absolute `source_pos`; next-best tested address model is `11507.9` bits | rejected refinement |
| Copy graph / literal seed atlas | DP LZ edges and literal runs are materialized; `32` source books, `5` same-book copies, and `52/84` literal runs reused later | diagnostic provenance atlas |
| Tape MDL gain | Rough total gain `6597.1` bits over literal module table | accepted compression evidence |
| Residual exact repeats | MDL-pruned `exact_repeat` covers `1683/2083` residual digits; about `400` digits remain literal | accepted secondary mechanical layer |
| Chayenne holdout | minLen=8 coverage `45/49`; Avar Tar minLen=8 coverage `0/115` | secondary validation only |
| Zero omission | local previous/next context and geometry predict omission better than code-only | supporting render layer |

Primary sources:
[tape_based_formula_report.md](../../analysis/generator_search_20260618/tape_based_formula_report.md),
[literal_reference_benchmark_controls.md](../../analysis/authorial_mechanism_20260620/reports/test_results/06_literal_reference_benchmark_controls.md),
[tape_inventory_self_reference_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/07_tape_inventory_self_reference_search.md),
[hierarchical_reference_formula_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/08_hierarchical_reference_formula_compile.md),
[sequential_lz_book_formula_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/10_sequential_lz_book_formula_compile.md),
[sequential_lz_order_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/11_sequential_lz_order_search.md),
[sequential_lz_literal_run_cost_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/12_sequential_lz_literal_run_cost_compile.md),
[sequential_lz_dp_parse_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/13_sequential_lz_dp_parse_compile.md),
[copy_source_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/14_copy_source_address_model_search.md),
[copy_graph_provenance_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/15_copy_graph_provenance_audit.md),
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
| Hierarchical provenance | book/tape/inventory provenance improves generation, but does not predict pair labels (`16/55`, control `p=0.4194`) |

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
- Hierarchical provenance as row0 pair-label generator: the best feature stump
  costs more than lookup and is ordinary under inventory-preserving controls.

Primary sources:
[matrix_generator_exhaustive_report.md](../../analysis/generator_search_20260618/matrix_generator_exhaustive_report.md),
[generator_model_final_report.md](../../analysis/generator_search_20260618/generator_model_final_report.md),
[hierarchical_provenance_pair_label_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/09_hierarchical_provenance_pair_label_audit.md),
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
- Literal-reference follow-up:
  [literal_reference_formula_469.json](../../analysis/authorial_mechanism_20260620/literal_reference_formula_469.json)
- Hierarchical reference follow-up:
  [hierarchical_reference_formula_469.json](../../analysis/authorial_mechanism_20260620/hierarchical_reference_formula_469.json)
- Sequential LZ book formula:
  [sequential_lz_book_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_book_formula_469.json)
- Sequential LZ literal-run cost formula:
  [sequential_lz_run_literal_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_run_literal_formula_469.json)
- Sequential LZ dynamic-parse formula:
  [sequential_lz_dp_parse_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_dp_parse_formula_469.json)
- DP LZ copy graph:
  [dp_lz_copy_graph_edges.csv](../../analysis/authorial_mechanism_20260620/tables/dp_lz_copy_graph_edges.csv)
- DP LZ literal seed atlas:
  [dp_lz_literal_seed_atlas.md](../../analysis/authorial_mechanism_20260620/tables/dp_lz_literal_seed_atlas.md)

Translation delta: `NONE`.
