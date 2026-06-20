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
| `sequential_lz_dp_parse_formula_469` | `9823.3` | `120.7` |
| `sequential_lz_rice_length_formula_469` | `9596.5` | `226.8` |
| `sequential_lz_rice_literal_length_formula_469` | `9545.5` | `51.0` |
| `sequential_lz_literal_payload_formula_469` | `9538.0` | `7.5` |
| `sequential_lz_literal_copy_repair_formula_469` | `9537.3` | `0.7` |
| `sequential_lz_length_ledger_formula_469` | `9073.3` | `464.0` |
| `sequential_lz_digit_address_formula_469` | `9070.8` | `2.4` |
| `sequential_lz_digit_address_literal_repair_formula_469` | `9070.1` | `0.8` |
| `sequential_lz_digit_address_type_coded_formula_469` | `8996.2` | `73.8` |
| `sequential_lz_digit_address_markov_type_formula_469` | `8977.6` | `18.6` |
| `sequential_lz_digit_address_book_start_type_formula_469` | `8972.2` | `5.3` |
| `sequential_lz_digit_address_literal_force_type_formula_469` | `8966.7` | `5.5` |
| `sequential_lz_digit_address_remaining_force_type_formula_469` | `8953.9` | `12.8` |
| `sequential_lz_digit_address_forced_literal_length_formula_469` | `8922.9` | `31.0` |
| `sequential_lz_digit_address_forced_length_literal_repair_formula_469` | `8922.8` | `0.1` |

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

The dynamic-parse refinement keeps that same vocabulary and fixed `min_len=6`
but replaces the greedy parse with a dynamic-programming parse under the
run-literal cost. It roundtrips 70/70 books at `9823.3` bits, a further
`120.7` bit gain, with `84` literal runs, `795` literal digits, `281` copy
items, and `10468` copied digits. Digit-shuffle and random same-length controls
remain much worse (`p=0.0099`); book-order shuffles are only moderately worse
(`p=0.0396`), so this promotes a tighter copy/reference fabrication bound, not
an original-order claim.

The follow-up address search rejects a tempting refinement from the generation
formula report: back-distance, delta, and book-relative source addresses are
not cheaper under the fixed DP parse. Absolute `source_pos` remains the best
ledger at `9823.3` bits; the next-best tested address model costs `11507.9`
bits. The copy-graph audit is therefore diagnostic rather than compressive: it
materializes `281` copy edges, only `5` same-book copies, `32` source books,
and `52/84` literal runs reused later as source material. That atlas is useful
for future structured-order or seed-provenance tests, not a new formula.

The structured-order test closes the next public-topology variant for this
front. Numeric order remains best at `9823.3` bits. The partial public
Hellgate/bookcase orders cost at least `9993.1` bits (`+169.8`), and candidate
orders that fill ambiguous public rows cost still more. Because the manifest
has only `64` resolved unique books, `6` ambiguous rows, one duplicate resolved
row, and no fine tile/slot/orientation/read-order layer, no physical or
authorial order is promoted.

Literal-seed addressing is also only an optimistic clue. If copy sources are
allowed to address prior literal runs without paying a source-mode cost, the
ledger reaches `9752.8` bits. That ledger is not a decodable mixed address
model. Once mode bits are charged, the same refinement costs `10033.8` bits,
worse than the previous `9823.3` gamma-length absolute `source_pos` formula, so
H-GEN3L is not promoted.

The grouped-mode follow-up closes the obvious objection to that rejection. A
sparse seed-run list is the best seed-using decodable grouped ledger, but it
still costs `9830.0` bits (`+6.7`). A seed-required RLE mask costs `9843.0`
bits (`+19.7`). Source-mode grouping therefore reduces the penalty versus
per-copy mode bits, but does not rescue literal-seed addressing.

The copy-hub macro follow-up is also rejected. Declaring source-book hubs or
target-default source books makes the address ledger larger, not smaller. The
optimistic target-default source lower bound costs `10326.9` bits (`+503.6`),
and the best decodable default-source model costs `10430.2` bits (`+606.9`).
The current absolute `source_pos` ledger remains the compact baseline.

The restricted hybrid-vocabulary reparse closes the next obvious route:
declare a small repeated digit-motif dictionary, then parse with literal runs,
prior-copy LZ references, and motif references. It roundtrips 70/70, but still
does not beat the DP LZ baseline. The nearest dictionary-using model is an
optimistic non-decodable `K=4` filtered motif set at `9840.7` bits (`+17.4`);
the nearest decodable dictionary model costs `10123.2` bits (`+299.9`).

The DP `min_len` sweep keeps the same conclusion. Varying `min_len` from `3`
through `12` leaves `min_len=6` as the best setting at `9823.3` bits; the
nearest alternate is `min_len=5` at `9827.7` bits (`+4.4`). Order-shuffle gross
wins remain order-search diagnostics, not promoted formula changes, unless an
external zero-cost order appears.

The copy-length code reparse improves this front. Replacing gamma length
coding with Rice coding (`k=4`) and reparsing at `min_len=5` yields a new 70/70
roundtrip formula at `9596.5` bits, a `226.8` bit gain over the previous
`9823.3` DP baseline even after charging `5` bits for the Rice parameter. This
is a mechanical generation improvement only; it does not alter row0 or add
plaintext.

The broader length-code grid keeps that formula. Testing `min_len=3..12`,
gamma, delta, unary, and Rice `k=0..10` leaves `rice_k4` / `min_len=5` best at
`9596.5` bits. The nearest non-current model is `rice_k4` / `min_len=4` at
`9600.0` bits (`+3.5`).

Retesting copy-source address ledgers on the Rice-length parse keeps absolute
`source_pos` as the best decodable ledger at `9596.5` bits. Literal-seed
addressing reaches `9549.5` bits only as an undecodable optimistic no-mode
ledger; the best decodable sparse seed-run ledger costs `9607.1` bits, so it
remains an optimistic clue rather than a promoted formula change.

The literal-run length reparse improves the current mechanical frontier.
Keeping copy lengths at Rice `k=4`, source addresses absolute, and `min_len=5`,
but coding literal-run lengths with Rice `k=3`, yields a 70/70 roundtrip
formula at `9545.5` bits. This saves `51.0` bits after charging both Rice
parameters. Digit-shuffle controls remain far worse and sampled book-order
controls do not beat the observed formula.

The joint length-code grid keeps that frontier. Testing `605` combinations of
`min_len=3..7`, copy gamma/delta/Rice `k=0..8`, and literal gamma/delta/Rice
`k=0..8` leaves `rice_k4` copy lengths, `rice_k3` literal-run lengths, and
`min_len=5` best at `9545.5` bits. The nearest alternate is `rice_k4` copy /
`rice_k2` literal at `9552.2` bits (`+6.7`).

The literal-payload model search improves the formula again without changing
the recipe. Replacing uniform decimal payload cost for literal digits with a
decodable adaptive Dirichlet model (`alpha=14`, charged at `7` declaration
bits) yields `9538.0` bits, a `7.5` bit improvement. A static literal histogram
oracle reaches `9513.9` bits but is not promoted because it omits a decodable
table; the charged static table is worse.

Retesting copy-source address ledgers on that current formula keeps absolute
`source_pos` as the best decodable address ledger. Literal-seed addressing
reaches `9478.6` bits only as a no-mode lower bound; the best decodable sparse
seed-run ledger is `9548.7` bits (`+10.7`), so this remains an optimistic clue
rather than a formula promotion.

The literal-to-copy repair search then changes the recipe itself by one local
operation. A literal `972783` in book `8` can be replaced by a prior copy from
source position `370`, reducing the exact current formula from `9538.0` to
`9537.3` bits. A follow-up one-step repair search after applying it finds no
second local improvement.

The post-repair payload alpha sweep keeps the payload parameter unchanged.
After the repair, `alpha=14` remains the best adaptive literal-payload value at
`2608.9` payload-plus-model bits; the nearest alternate, `alpha=13`, costs
`2609.0` bits. No formula is promoted by this parameter sweep.

The post-repair address retest also keeps the formula unchanged. Absolute
`source_pos` remains the best decodable copy-address ledger at `9537.3` bits.
Literal-seed addressing reaches `9472.4` bits only as an undecodable no-mode
lower bound; the best decodable sparse seed-run ledger costs `9548.0` bits.
That preserves literal-seed provenance as an optimistic clue, not a formula.

The compatible pair-repair search closes the immediate combinatorial objection
to the one-step repair. There are `25` single literal-to-copy repair candidates
and `293` compatible pairs. The best pair costs `9538.2` bits, which is `+0.9`
bits worse than the one-step repaired formula, so no two-repair recipe is
promoted.

The book-length ledger search improves the cost accounting without changing the
recipe. Instead of charging each of the 70 book lengths independently with
`gamma(length+1)`, the promoted ledger stores signed Rice residuals from a
declared `anchor=151`, `k=5`. Book-length cost drops from `1030.0` to `566.0`
bits, and the total bound drops from `9537.3` to `9073.3` bits with 70/70
roundtrip. This is a ledger improvement, not a new semantic channel.

The multi-anchor length follow-up rejects the obvious mixture extension. The
best decodable multi-anchor ledger uses `2` clusters at `k=4`, but costs
`581.0` book-length bits after mode and anchor charges. That is `+15.0` bits
worse than the single-anchor `anchor=151`, `k=5` ledger, so no newer length
model is promoted.

The digit-only address compile then uses the new length ledger to remove book
separators from the absolute copy-address space. Copy operations now point into
the previously emitted digit stream rather than the digit-plus-separator stream,
reducing copy-address cost from `3257.3` to `3254.9` bits. The total bound
drops from `9073.3` to `9070.8` bits with 70/70 roundtrip.

The digit-only address-model follow-up keeps that result. Absolute
`source_digit_pos` remains the best decodable ledger at `9070.8` bits.
Literal-seed addressing reaches `9006.2` bits only as an undecodable lower
bound; the best decodable sparse seed-run ledger costs `9081.5` bits.

Retesting local repairs under the digit-only address cost yields one more small
recipe improvement. Literal `57928` in book `13` can be replaced by a prior copy
from digit position `1976`, lowering the bound from `9070.8` to `9070.1` bits.
A follow-up one-step search after applying it finds no second improvement.

The post-repair payload alpha sweep keeps the payload parameter unchanged.
After the digit-address repair, `alpha=14` remains best at `2592.0`
payload-plus-model bits; the nearest alternate, `alpha=13`, costs `2592.1`
bits. No formula is promoted by this parameter sweep.

The post-repair address-model follow-up also keeps the formula unchanged.
Absolute `source_digit_pos` remains the best decodable ledger at `9070.1` bits.
Literal-seed addressing reaches `9005.5` bits only as an undecodable lower
bound; the best decodable sparse seed-run ledger costs `9080.8` bits.

The item-type ledger compile improves the current mechanical bound without
changing the recipe. The previous formula charged one fixed bit for each
literal/copy item tag. Encoding the same `84` literal tags and `281` copy tags
with a declared two-symbol adaptive ledger (`alpha=2`) costs `291.2` bits
instead of `365.0`, lowering the 70/70 roundtrip bound from `9070.1` to
`8996.2` bits. This is a decodable ledger improvement, not a new text channel.

The Markov item-type ledger tightens that same tag stream again. Conditioning
the next item tag on the previous tag, with declared `alpha=1` and one bit for
the first item, costs `272.5` bits instead of the adaptive iid ledger's
`291.2` bits. The total 70/70 roundtrip bound drops from `8996.2` to `8977.6`
bits. The transition counts (`copy->copy=200`, `copy->literal=80`,
`literal->copy=81`, `literal->literal=3`) explain the gain as local item-type
persistence/alternation, not semantics.

The book-start item-type ledger uses the already-declared 70 book boundaries as
a `BOS` context in that same Markov ledger. Books start with copy items much
more often than literal items (`56` versus `14`), and inside-book transitions
remain copy-heavy. This lowers the item-type cost from `272.5` to `267.2` bits
and the total 70/70 bound from `8977.6` to `8972.2` bits without adding a new
order or text channel.

The literal-forces-copy item-type ledger then charges a one-bit deterministic
rule: after a literal item, if the declared book length is not complete, the
next item type is copy. The rule has `71` applications and `0` violations in
the fixed recipe. After charging the rule and `alpha=2`, item-type cost drops
from `267.2` to `261.7` bits, lowering the total bound from `8972.2` to
`8966.7` bits.

The remaining-short item-type ledger adds one more charged deterministic rule:
if fewer than `min_len=5` digits remain in the declared book, a copy item cannot
legally fit, so the type is forced to literal. This rule applies `8` times with
`0` violations. After charging both rules and `alpha=2`, item-type cost drops
from `261.7` to `248.9` bits, lowering the total bound from `8966.7` to
`8953.9` bits.

The remaining-short literal-length compile then removes redundant length bits
from those same `8` forced suffix literals. Because book lengths and `min_len`
are already declared, a forced short suffix literal must consume the remaining
book digits. After charging a one-bit length rule, literal length cost drops by
`31.0` net bits and the total 70/70 bound moves from `8953.9` to `8922.9` bits.

The forced-length literal repair search then retests local literal-to-copy
repairs under that updated cost model. One further repair replaces `65128` in
book `12` with a valid prior copy from digit position `50`, lowering the bound
from `8922.9` to `8922.8` bits. This is a marginal recipe improvement only; the
follow-up one-step repair search after applying it is worse.

The post-forced-repair payload alpha sweep then checks whether that final
payload-stream change requires retuning the adaptive Dirichlet parameter. It
does not: `alpha=14` remains best at `2575.7` payload-plus-model bits, with
`alpha=13` next at `+0.1` bit. No newer formula is promoted.

The post-forced-repair address-model search then retests copy source ledgers on
the active recipe. Literal-seed addressing reaches `8855.5` bits only as an
undecodable no-mode lower bound. The best decodable sparse seed-run ledger
costs `8933.5` bits (`+10.7`), so absolute digit-only `source_digit_pos`
remains the active address ledger.

The post-forced-repair pair search then checks whether two compatible
literal-to-copy repairs improve together even though no single follow-up repair
does. They do not: `22` single candidates yield `227` compatible pairs, and the
best pair remains `+1.6` bits worse than the active formula. The local
literal-to-copy frontier is therefore closed under compatible pairs for this
cost model.

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
| H-GEN3H | `controlled_sequential_lz_dp_parse_formula` |
| H-GEN3I | `copy_source_address_absolute_retained` |
| H-GEN3J | `copy_graph_literal_seed_atlas_compiled_no_formula_promotion` |
| H-GEN3K | `structured_physical_order_not_better_than_numeric` |
| H-GEN3L | `literal_seed_address_optimistic_only_not_promoted` |
| H-GEN3M | `literal_seed_grouped_mode_optimistic_only_not_promoted` |
| H-GEN3N | `copy_hub_macro_model_not_promoted` |
| H-GEN3O | `restricted_hybrid_vocabulary_not_promoted` |
| H-GEN3P | `dp_min_len_sweep_retains_min_len_6` |
| H-GEN3Q | `controlled_copy_length_code_improvement` |
| H-GEN3R | `copy_length_grid_retains_rice_k4_min_len_5` |
| H-GEN3S | `rice_copy_address_optimistic_only_not_promoted` |
| H-GEN3T | `controlled_literal_length_code_improvement` |
| H-GEN3U | `joint_length_grid_retains_rice_k4_literal_rice_k3_min_len_5` |
| H-GEN3V | `controlled_literal_payload_adaptive_improvement` |
| H-GEN3W | `current_formula_address_optimistic_only_not_promoted` |
| H-GEN3X | `controlled_literal_to_copy_single_repair_improvement` |
| H-GEN3Y | `post_repair_payload_alpha_retains_14` |
| H-GEN3Z | `post_repair_address_optimistic_only_not_promoted` |
| H-GEN3AA | `literal_to_copy_pair_repair_not_promoted` |
| H-GEN3AB | `controlled_book_length_ledger_improvement` |
| H-GEN3AC | `multi_anchor_book_length_ledger_not_promoted` |
| H-GEN3AD | `controlled_digit_only_copy_address_improvement` |
| H-GEN3AE | `digit_address_optimistic_only_not_promoted` |
| H-GEN3AF | `controlled_digit_address_literal_repair_improvement` |
| H-GEN3AG | `post_digit_repair_payload_alpha_retains_14` |
| H-GEN3AH | `post_digit_repair_address_optimistic_only_not_promoted` |
| H-GEN3AI | `controlled_item_type_ledger_improvement` |
| H-GEN3AJ | `controlled_markov_item_type_ledger_improvement` |
| H-GEN3AK | `controlled_book_start_item_type_ledger_improvement` |
| H-GEN3AL | `controlled_literal_forces_copy_type_ledger_improvement` |
| H-GEN3AM | `controlled_remaining_short_forces_literal_type_ledger_improvement` |
| H-GEN3AN | `controlled_remaining_short_literal_length_improvement` |
| H-GEN3AO | `controlled_forced_length_literal_repair_improvement` |
| H-GEN3AP | `post_forced_repair_payload_alpha_retains_14` |
| H-GEN3AQ | `post_forced_repair_address_optimistic_only_not_promoted` |
| H-GEN3AR | `post_forced_repair_pair_not_promoted` |
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
- [Sequential LZ dynamic-parse compile](../../analysis/authorial_mechanism_20260620/reports/test_results/13_sequential_lz_dp_parse_compile.md)
- [Copy source address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/14_copy_source_address_model_search.md)
- [Copy graph provenance audit](../../analysis/authorial_mechanism_20260620/reports/test_results/15_copy_graph_provenance_audit.md)
- [Structured physical order LZ test](../../analysis/authorial_mechanism_20260620/reports/test_results/16_structured_physical_order_lz_test.md)
- [Literal seed address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/17_literal_seed_address_model_search.md)
- [Literal seed grouped-mode search](../../analysis/authorial_mechanism_20260620/reports/test_results/18_literal_seed_grouped_mode_search.md)
- [Copy hub macro model search](../../analysis/authorial_mechanism_20260620/reports/test_results/19_copy_hub_macro_model_search.md)
- [Restricted hybrid vocabulary reparse](../../analysis/authorial_mechanism_20260620/reports/test_results/20_restricted_hybrid_vocabulary_reparse.md)
- [DP min-length sweep control](../../analysis/authorial_mechanism_20260620/reports/test_results/21_dp_min_len_sweep_control.md)
- [Copy length code reparse](../../analysis/authorial_mechanism_20260620/reports/test_results/22_copy_length_code_reparse.md)
- [Copy length grid sweep](../../analysis/authorial_mechanism_20260620/reports/test_results/23_copy_length_grid_sweep.md)
- [Rice copy address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/24_rice_copy_address_model_search.md)
- [Literal run length code reparse](../../analysis/authorial_mechanism_20260620/reports/test_results/25_literal_run_length_code_reparse.md)
- [Joint length code grid sweep](../../analysis/authorial_mechanism_20260620/reports/test_results/26_joint_length_code_grid_sweep.md)
- [Literal payload model search](../../analysis/authorial_mechanism_20260620/reports/test_results/27_literal_payload_model_search.md)
- [Current formula address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/28_current_formula_address_model_search.md)
- [Literal-to-copy repair search](../../analysis/authorial_mechanism_20260620/reports/test_results/29_literal_to_copy_repair_search.md)
- [Post-repair payload alpha sweep](../../analysis/authorial_mechanism_20260620/reports/test_results/30_post_repair_payload_alpha_sweep.md)
- [Post-repair address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/31_post_repair_address_model_search.md)
- [Literal-to-copy pair repair search](../../analysis/authorial_mechanism_20260620/reports/test_results/32_literal_to_copy_pair_repair_search.md)
- [Book length ledger search](../../analysis/authorial_mechanism_20260620/reports/test_results/33_book_length_ledger_search.md)
- [Book length multi-anchor search](../../analysis/authorial_mechanism_20260620/reports/test_results/34_book_length_multi_anchor_search.md)
- [Digit-only copy address compile](../../analysis/authorial_mechanism_20260620/reports/test_results/35_digit_only_copy_address_compile.md)
- [Digit address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/36_digit_address_model_search.md)
- [Digit-address literal repair search](../../analysis/authorial_mechanism_20260620/reports/test_results/37_digit_address_literal_repair_search.md)
- [Post-digit-repair payload alpha sweep](../../analysis/authorial_mechanism_20260620/reports/test_results/38_post_digit_repair_payload_alpha_sweep.md)
- [Post-digit-repair address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/39_post_digit_repair_address_model_search.md)
- [Item-type ledger compile](../../analysis/authorial_mechanism_20260620/reports/test_results/40_item_type_ledger_compile.md)
- [Markov item-type ledger compile](../../analysis/authorial_mechanism_20260620/reports/test_results/41_markov_item_type_ledger_compile.md)
- [Book-start item-type ledger compile](../../analysis/authorial_mechanism_20260620/reports/test_results/42_book_start_item_type_ledger_compile.md)
- [Literal-forces-copy item-type ledger compile](../../analysis/authorial_mechanism_20260620/reports/test_results/43_literal_forces_copy_type_ledger_compile.md)
- [Remaining-short-forces-literal item-type ledger compile](../../analysis/authorial_mechanism_20260620/reports/test_results/44_remaining_short_forces_literal_type_ledger_compile.md)
- [Remaining-short literal-length compile](../../analysis/authorial_mechanism_20260620/reports/test_results/45_remaining_short_literal_length_compile.md)
- [Forced-length literal repair search](../../analysis/authorial_mechanism_20260620/reports/test_results/46_forced_length_literal_repair_search.md)
- [Post-forced-repair payload alpha sweep](../../analysis/authorial_mechanism_20260620/reports/test_results/47_post_forced_repair_payload_alpha_sweep.md)
- [Post-forced-repair address model search](../../analysis/authorial_mechanism_20260620/reports/test_results/48_post_forced_repair_address_model_search.md)
- [Post-forced-repair pair search](../../analysis/authorial_mechanism_20260620/reports/test_results/49_post_forced_repair_pair_search.md)

## Boundary

This page changes the mechanical model, not the semantic verdict. Future work
should treat the Rice copy-length plus Rice literal-length sequential LZ formula
with adaptive literal-payload coding, the one-step literal-to-copy repair, the
signed-Rice book-length ledger, digit-only copy addresses, and the digit-address
literal repair, plus the adaptive/Markov/book-start/literal-force item-type
ledgers, remaining-short forced-literal rule, and forced short-suffix literal
lengths, and the final forced-length local repair with retained payload
`alpha=14` and retained absolute `source_digit_pos` addresses, as the current
strongest copy/reference fabrication bound. Follow-up single/pair local repairs
do not improve it; continue testing matrix origin, topology holdouts, and
official source watchlists under the same Outcome Ledger.
