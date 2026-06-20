---
page_id: authorial-mechanism-model
page_type: finding
context: bonelord-469
visibility: public_candidate
status: frozen
updated_at: 2026-06-20
moc_parent: README.md
source_refs:
  - analysis/authorial_mechanism_20260620
---

# 18. Authorial Mechanism Model

[<- Physical Library Topology](17-physical-library-topology.md) . [Wiki home](README.md)

---

## Verdict

The first-principles/Knightmare report is incorporated as a mechanism-search
prior, not as proof of private authorial intent. Its useful conclusion is that
the best working model remains:

```text
limited phrase-code layer
+ mechanically fabricated book layer
+ lore/math atmosphere
```

Translation delta: `NONE`.

Round result: `MECHANICAL IMPROVEMENT / semantic plateau unchanged`.

## What Changed Mechanically

The new search found a small but real improvement to the current tape formula.
Remaining literal strings in the tape recipe were checked against existing tape
components. When a literal could be replaced by a cheaper
`component_id/start/length` reference, the compiler emitted a new recipe item.

Result:

| Metric | Value |
|---|---:|
| New book-recipe formula | `literal_reference_formula_469.json` |
| New hierarchical formula | `hierarchical_reference_formula_469.json` |
| Reference items | `36` |
| Referenced literal digits | `579` |
| Kept literal items | `67` |
| Kept literal digits | `1397` |
| Rough saved bits | `1167.4` |
| Book roundtrip | `70/70` |
| Controlled benchmark verdict | `controlled_mechanical_improvement_no_semantics` |

This improves the mechanical generation method. It does not explain the
10x10 pair-table origin and does not translate the books.

The follow-up benchmark compares the cost ladder directly:

| Model | Rough total bits | Gain vs previous |
|---|---:|---:|
| `mechanical_formula_469` | `24350.7` | `0.0` |
| `tape_based_formula_469` | `17753.5` | `6597.1` |
| `literal_reference_formula_469` | `16586.1` | `1167.4` |
| `hierarchical_reference_formula_469` | `13858.5` | `2727.7` |
| `sequential_lz_book_formula_469` | `10190.0` | `3668.5` |
| `sequential_lz_run_literal_formula_469` | `9944.0` | `246.0` |

Negative controls separate this from random substring opportunity: component
digit shuffles and random length-matched literals both saved `0.0` bits in 400
runs (`p=0.0025`). A stricter same-book component exclusion still saved `646.3`
bits, but shuffled book exclusions were not worse, so the controlled claim is
exact tape-substring reuse, not physical topology.

The later tape-inventory self-reference search compresses the 16 tape component
payloads themselves. It reconstructs 16/16 components, saves roughly `2727.7`
bits over literal tape storage, and beats component digit-shuffle/random
same-length controls (`p=0.0033`). Component-order shuffles are not worse
(`p=0.1561`), so the result promotes inventory reuse, not original tape order.
Combined with the literal-reference book recipes, the hierarchical formula
roundtrips 70/70 books at roughly `13858.5` bits.

The strongest book-generator upper bound in this front is now the sequential
LZ formula. It emits the 70 raw digit books in numeric order as literal runs
plus references to already emitted prior-book/current-prefix digits. It
roundtrips 70/70 books at roughly `10190.0` bits, with `812` literal digits,
`279` copy items, and `10451` copied digits. Controls are much worse for
within-book digit shuffles and random same-length books (`p=0.0062` each);
book-order shuffles are also usually worse (`p=0.0311`). This is a stronger
copy/reference fabrication upper bound, not a row0 origin.

The order-search follow-up does not promote an arbitrary non-numeric order.
The best of 800 sampled orders reaches `10004.0` bits, a gross `186.0` bit
gain over numeric order, but storing an arbitrary 70-book permutation costs
about `332.5` bits (`log2(70!)`). Net gain is therefore `-146.5` bits. Numeric
order remains the default unless a physical/source order supplies the order
without charging it as a searched permutation.

The cost-model refinement keeps the same sequential copy/reference generator
but charges literal runs as runs rather than as one flag per literal digit. It
roundtrips 70/70 books at `9944.0` bits, a further `246.0` bit gain over
sequential LZ v1, with `85` literal runs, `812` literal digits, `279` copy
items, and `10451` copied digits. Within-book digit shuffles, random
same-length books, and book-order shuffles remain worse than the observed
corpus (`p=0.0062` each). This tightens the fabrication-cost upper bound; it
does not explain row0 or add plaintext.

The same provenance does not solve the unresolved pair table. The
hierarchical-provenance audit derived 31 features per unordered pair from
book operations, tape component references, inventory self-references,
omitted-zero rendering, and canonical token positions. The best stump was
`diff <= 4.5`, with only `16/55` hits, `-196.1` rough bits versus lookup, and
inventory-preserving hit control `p=0.4194`. The best order-fill diagnostic
reached `11/55` (`p=0.8816`). Therefore the hierarchical formula improves
book generation, not row0 pair-cell placement.

## H-AUTH / H-GEN Status

| ID | Status |
|---|---|
| H-AUTH1 | `best_design_model_no_intent_claim` |
| H-AUTH2 | `plausible_mechanism_frame` |
| H-AUTH3 | `plausible_design_interpretation` |
| H-GEN1 | `supermodule_not_promoted` |
| H-GEN2 | `weak_topology_module_signal` |
| H-GEN3 | `candidate_compiled_in_this_front` |
| H-GEN3B | `controlled_mechanical_improvement_no_semantics` |
| H-GEN3C | `controlled_inventory_reuse_order_not_promoted` |
| H-GEN3D | `hierarchical_reference_formula_roundtrips_no_semantics` |
| H-GEN3E | `controlled_sequential_lz_book_formula` |
| H-GEN3F | `order_search_not_promoted_after_permutation_cost` |
| H-GEN3G | `controlled_sequential_lz_run_literal_formula` |
| H-GEN4 | `open_low_expectation` |
| H-GEN4A | `hierarchical_provenance_not_pair_table_formula` |
| H-GEN5 | `watchlist_only` |

## Reports

- [Authorial mechanism synthesis report](../../analysis/authorial_mechanism_20260620/reports/authorial_mechanism_synthesis_report.md)
- [Final authorial mechanism report](../../analysis/authorial_mechanism_20260620/reports/final_authorial_mechanism_report.md)
- [First-principles hypothesis audit](../../analysis/authorial_mechanism_20260620/reports/test_results/01_first_principles_hypothesis_audit.md)
- [Recipe supermodule search](../../analysis/authorial_mechanism_20260620/reports/test_results/02_recipe_supermodule_search.md)
- [Topology module signal audit](../../analysis/authorial_mechanism_20260620/reports/test_results/03_topology_module_signal_audit.md)
- [Literal absorption search](../../analysis/authorial_mechanism_20260620/reports/test_results/04_literal_absorption_search.md)
- [Literal reference formula compile](../../analysis/authorial_mechanism_20260620/reports/test_results/05_literal_reference_formula_compile.md)
- [Literal reference benchmark and controls](../../analysis/authorial_mechanism_20260620/reports/test_results/06_literal_reference_benchmark_controls.md)
- [Tape inventory self-reference search](../../analysis/authorial_mechanism_20260620/reports/test_results/07_tape_inventory_self_reference_search.md)
- [Hierarchical reference formula compile](../../analysis/authorial_mechanism_20260620/reports/test_results/08_hierarchical_reference_formula_compile.md)
- [Hierarchical provenance pair-label audit](../../analysis/authorial_mechanism_20260620/reports/test_results/09_hierarchical_provenance_pair_label_audit.md)
- [Sequential LZ book formula compile](../../analysis/authorial_mechanism_20260620/reports/test_results/10_sequential_lz_book_formula_compile.md)
- [Sequential LZ book order search](../../analysis/authorial_mechanism_20260620/reports/test_results/11_sequential_lz_order_search.md)
- [Sequential LZ literal-run cost compile](../../analysis/authorial_mechanism_20260620/reports/test_results/12_sequential_lz_literal_run_cost_compile.md)

## Boundary

This page changes the mechanical model, not the semantic verdict. Future work
should treat the run-literal sequential LZ formula as the current strongest
copy/reference fabrication bound and continue testing matrix origin, topology
holdouts, and official source watchlists under the same Outcome Ledger.
