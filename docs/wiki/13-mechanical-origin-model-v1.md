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
| Sequential LZ dynamic-parse formula | the same run-literal vocabulary is parsed by dynamic programming at fixed `min_len=6`; `9823.3` rough bits, 70/70 roundtrip, digit-shuffle/random controls fail, and book-order support is only moderate (`p=0.0396`) | previous strongest copy/reference upper bound |
| Copy address model search | back-distance, source-delta, and book-relative source addresses all cost more than absolute `source_pos`; next-best tested address model is `11507.9` bits | rejected refinement |
| Copy graph / literal seed atlas | DP LZ edges and literal runs are materialized; `32` source books, `5` same-book copies, and `52/84` literal runs reused later | diagnostic provenance atlas |
| Structured public physical order | partial Hellgate/bookcase orders under DP LZ cost at least `9993.1` bits, worse than numeric `9823.3`; manifest ambiguity blocks authorial-order promotion | rejected refinement |
| Literal seed address model | prior literal-run addressing can reach `9752.8` only without mode bits; decodable mixed ledger costs `10033.8`, worse than numeric `9823.3` | rejected refinement / optimistic clue |
| Literal seed grouped-mode model | grouped mode coding reduces the seed-address penalty, but the best decodable seed-using sparse-run ledger is still `9830.0` bits versus the previous `9823.3` gamma-length DP formula | rejected refinement |
| Copy hub macro model | source-book hubs and target-default source macros cost at least `10326.9` bits even in the optimistic lower bound, worse than the previous `9823.3` gamma-length DP formula | rejected refinement |
| Restricted hybrid vocabulary reparse | declared repeated digit motifs plus LZ references roundtrip 70/70, but the best dictionary-using model is `9840.7` bits, worse than the previous `9823.3` gamma-length DP formula | rejected refinement |
| DP min_len sweep | `min_len=6` remains best in the modern DP sequential LZ sweep; `min_len=5` is nearest at `9827.7` bits, `+4.4` worse | retained parameter |
| Sequential LZ Rice-length formula | copy lengths are encoded with Rice `k=4` after reparsing at `min_len=5`; `9596.5` rough bits, 70/70 roundtrip, `226.8` bits better than gamma-length DP | strongest copy/reference upper bound |
| Copy length grid sweep | broader `min_len=3..12` and Rice `k=0..10` grid retains Rice `k=4`, `min_len=5`; nearest alternate is `9600.0` bits | retained parameter |
| Rice parse copy address models | absolute `source_pos` remains best decodable at `9596.5`; literal-seed no-mode reaches `9549.5` but sparse decodable seed-run costs `9607.1` | rejected refinement / optimistic clue |
| Sequential LZ Rice literal-length formula | literal-run lengths are encoded with Rice `k=3` while copy lengths remain Rice `k=4`; `9545.5` rough bits, 70/70 roundtrip, `51.0` bits better than the prior Rice-length formula | strongest copy/reference upper bound |
| Joint length code grid | `605` joint DP reparses keep copy Rice `k=4`, literal Rice `k=3`, `min_len=5`; nearest alternate is `9552.2` bits | retained parameter set |
| Sequential LZ literal-payload formula | literal digits use an adaptive Dirichlet payload model with `alpha=14`; `9538.0` rough bits, `7.5` bits better than uniform decimal payload cost | strongest copy/reference upper bound |
| Current formula copy address models | absolute `source_pos` remains best decodable at `9538.0`; literal-seed no-mode reaches `9478.6` but sparse decodable seed-run costs `9548.7` | rejected refinement / optimistic clue |
| Sequential LZ literal-to-copy repair formula | one local replacement turns literal `972783` in book `8` into a valid prior copy; `9537.3` rough bits, `0.7` bits better than the literal-payload formula | strongest copy/reference upper bound |
| Post-repair payload alpha sweep | adaptive literal-payload `alpha=14` remains best after the local repair; nearest alternate `alpha=13` is slightly worse | retained parameter |
| Post-repair copy address models | absolute `source_pos` remains best decodable at `9537.3`; literal-seed no-mode reaches `9472.4` but the best sparse decodable seed-run costs `9548.0` | rejected refinement / optimistic clue |
| Literal-to-copy pair repair search | `293` compatible two-repair recipes are tested; the best costs `9538.2`, worse than the one-step repaired formula | rejected refinement |
| Sequential LZ book-length ledger formula | independent gamma-coded book lengths are replaced by signed Rice residuals from declared `anchor=151`, `k=5`; total bound drops to `9073.3` bits with 70/70 roundtrip | strongest copy/reference upper bound |
| Multi-anchor book-length ledger search | best decodable multi-anchor length mixture costs `581.0` length bits, `+15.0` worse than the single-anchor ledger | rejected refinement |
| Sequential LZ digit-address formula | book separators are removed from the absolute copy-address space after lengths make them reconstructable; total bound drops to `9070.8` bits | strongest copy/reference upper bound |
| Digit-only copy address models | absolute `source_digit_pos` remains best decodable at `9070.8`; literal-seed no-mode reaches `9006.2` but sparse decodable seed-run costs `9081.5` | rejected refinement / optimistic clue |
| Sequential LZ digit-address literal-repair formula | one local replacement turns literal `57928` in book `13` into a valid prior copy; total bound drops to `9070.1` bits and follow-up one-step repair is worse | strongest copy/reference upper bound |
| Post digit-address repair payload alpha sweep | adaptive literal-payload `alpha=14` remains best after the latest repair; nearest alternate `alpha=13` is slightly worse | retained parameter |
| Post digit-address repair address models | absolute `source_digit_pos` remains best decodable at `9070.1`; literal-seed no-mode reaches `9005.5` but sparse decodable seed-run costs `9080.8` | rejected refinement / optimistic clue |
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
[structured_physical_order_lz_test.md](../../analysis/authorial_mechanism_20260620/reports/test_results/16_structured_physical_order_lz_test.md),
[literal_seed_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/17_literal_seed_address_model_search.md),
[literal_seed_grouped_mode_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/18_literal_seed_grouped_mode_search.md),
[copy_hub_macro_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/19_copy_hub_macro_model_search.md),
[restricted_hybrid_vocabulary_reparse.md](../../analysis/authorial_mechanism_20260620/reports/test_results/20_restricted_hybrid_vocabulary_reparse.md),
[dp_min_len_sweep_control.md](../../analysis/authorial_mechanism_20260620/reports/test_results/21_dp_min_len_sweep_control.md),
[copy_length_code_reparse.md](../../analysis/authorial_mechanism_20260620/reports/test_results/22_copy_length_code_reparse.md),
[copy_length_grid_sweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/23_copy_length_grid_sweep.md),
[rice_copy_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/24_rice_copy_address_model_search.md),
[literal_run_length_code_reparse.md](../../analysis/authorial_mechanism_20260620/reports/test_results/25_literal_run_length_code_reparse.md),
[joint_length_code_grid_sweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/26_joint_length_code_grid_sweep.md),
[literal_payload_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/27_literal_payload_model_search.md),
[current_formula_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/28_current_formula_address_model_search.md),
[literal_to_copy_repair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/29_literal_to_copy_repair_search.md),
[post_repair_payload_alpha_sweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/30_post_repair_payload_alpha_sweep.md),
[post_repair_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/31_post_repair_address_model_search.md),
[literal_to_copy_pair_repair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/32_literal_to_copy_pair_repair_search.md),
[book_length_ledger_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/33_book_length_ledger_search.md),
[book_length_multi_anchor_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/34_book_length_multi_anchor_search.md),
[digit_only_copy_address_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/35_digit_only_copy_address_compile.md),
[digit_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/36_digit_address_model_search.md),
[digit_address_literal_repair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/37_digit_address_literal_repair_search.md),
[post_digit_repair_payload_alpha_sweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/38_post_digit_repair_payload_alpha_sweep.md),
[post_digit_repair_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/39_post_digit_repair_address_model_search.md),
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
- Sequential LZ Rice-length formula:
  [sequential_lz_rice_length_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_rice_length_formula_469.json)
- Sequential LZ Rice literal-length formula:
  [sequential_lz_rice_literal_length_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_rice_literal_length_formula_469.json)
- Sequential LZ literal-payload formula:
  [sequential_lz_literal_payload_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_literal_payload_formula_469.json)
- Sequential LZ literal-to-copy repair formula:
  [sequential_lz_literal_copy_repair_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_literal_copy_repair_formula_469.json)
- Sequential LZ book-length ledger formula:
  [sequential_lz_length_ledger_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_length_ledger_formula_469.json)
- Sequential LZ digit-address formula:
  [sequential_lz_digit_address_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_digit_address_formula_469.json)
- Sequential LZ digit-address literal-repair formula:
  [sequential_lz_digit_address_literal_repair_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_digit_address_literal_repair_formula_469.json)
- DP LZ copy graph:
  [dp_lz_copy_graph_edges.csv](../../analysis/authorial_mechanism_20260620/tables/dp_lz_copy_graph_edges.csv)
- DP LZ literal seed atlas:
  [dp_lz_literal_seed_atlas.md](../../analysis/authorial_mechanism_20260620/tables/dp_lz_literal_seed_atlas.md)

Translation delta: `NONE`.
