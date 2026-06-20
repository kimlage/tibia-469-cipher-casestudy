# Final Authorial Mechanism Report

Verdict: `controlled_mechanical_improvement_no_semantics`.
Translation delta: `NONE`.

The 2026-06-20 first-principles report was incorporated as a bounded
origin/mechanism front. It strengthens the working interpretation that 469's
book layer is a fabricated mechanical artifact rather than a recoverable
natural-language text.

## Added Value

- Converts the report's broad taxonomy into explicit H-AUTH/H-GEN hypotheses.
- Tests generation-method improvement routes against the current tape formula
  baseline.
- Keeps "Knightmare intent" as interpretation-only without source promotion.

## Current Test Outcome

Generated audits in this directory should be treated as the current state:

- `01_first_principles_hypothesis_audit`: `mechanism_prior_integrated`.
- `02_recipe_supermodule_search`: no exact higher-order recipe supermodules
  were promoted.
- `03_topology_module_signal_audit`: component-level topology signal is weak
  but real (`p=0.0030` adjacent, `p=0.0205` bookcase); module-identity signal
  itself does not promote.
- `04_literal_absorption_search`: remaining literals contain enough exact
  copies inside tape components to justify compilation.
- `05_literal_reference_formula_compile`: compiled
  `literal_reference_formula_469.json`, replacing 36 remaining literal items
  with tape references, referencing 579 literal digits, keeping 67 literal
  items / 1397 literal digits, saving roughly `1167.4` bits under the local
  address-cost screen, with 70/70 book roundtrip.
- `06_literal_reference_benchmark_controls`: promotes the literal-reference
  layer as a controlled mechanical improvement only. The rough cost ladder is
  `24350.7` bits for the base module formula, `17753.5` bits for the tape
  formula, and `16586.1` bits for the literal-reference formula. Component
  digit-shuffle and random length-matched literal controls both scored zero
  saved bits in 400 runs (`p=0.0025`). The same-book component exclusion still
  saves `646.3` bits, but shuffled book exclusions are not worse; therefore the
  result supports exact tape-substring reuse, not a local topology claim.
- `07_tape_inventory_self_reference_search`: finds a smaller generator for the
  16 tape component payloads. It saves roughly `2727.7` bits over literal tape
  storage, reconstructs 16/16 components, and beats component digit-shuffle and
  random same-length controls (`p=0.0033`). Component-order shuffles are not
  worse (`p=0.1561`), so the accepted claim is inventory reuse, not original
  tape order.
- `08_hierarchical_reference_formula_compile`: combines the inventory
  self-reference layer with the book-level literal-reference layer into
  `hierarchical_reference_formula_469.json`. The formula reconstructs 16/16
  components and 70/70 books. Its rough total is `13858.5` bits, a
  `10492.2` bit gain over the base module formula and `3895.1` bits over the
  tape formula.
- `09_hierarchical_provenance_pair_label_audit`: tests the remaining hard
  question, whether the new provenance features explain the unresolved 55-cell
  pair table. They do not: best stump is `diff <= 4.5`, only `16/55` hits,
  `-196.1` rough bits versus lookup, and hit control `p=0.4194`. The best
  inventory-preserving order fill reaches only `11/55` (`p=0.8816`).
- `10_sequential_lz_book_formula_compile`: materializes a direct book-level
  copy/reference generator. It reconstructs 70/70 books at `10190.0` bits,
  beating the hierarchical reference formula by `3668.5` bits. It emits only
  `812` literal digits and copies `10451` digits through `279` references.
  Digit-shuffle and random same-length controls are far worse (`p=0.0062`);
  book-order shuffles are also usually worse (`p=0.0311`), so numeric book
  order is weakly supported under this specific generator.
- `11_sequential_lz_order_search`: checks whether a non-numeric emission order
  improves the sequential LZ formula enough to justify itself. The best of 800
  sampled orders improves gross cost by `186.0` bits, but `log2(70!)` order
  cost is `332.5` bits, leaving `-146.5` net bits. Non-numeric order is not
  promoted without an external physical/source order supplied for free.
- `12_sequential_lz_literal_run_cost_compile`: re-costs the same sequential
  copy/reference generator by charging literal runs instead of a literal flag
  per digit. It reconstructs 70/70 books at `9944.0` bits, a `246.0` bit gain
  over sequential LZ v1, with `85` literal runs, `812` literal digits, `279`
  copy items, and `10451` copied digits. Digit-shuffle, random same-length,
  and book-order controls are all worse than the observed corpus
  (`p=0.0062` each).
- `13_sequential_lz_dp_parse_compile`: keeps the same run-literal
  copy/reference vocabulary, fixes the prior best `min_len=6`, and replaces the
  greedy parse with a dynamic-programming parse. It reconstructs 70/70 books at
  `9823.3` bits, a further `120.7` bit gain, with `84` literal runs, `795`
  literal digits, `281` copy items, and `10468` copied digits. Digit-shuffle
  and random same-length controls are much worse (`p=0.0099`); book-order
  shuffles are only moderately worse (`p=0.0396`), so the accepted claim is a
  tighter copy/reference bound, not original order.
- `14_copy_source_address_model_search`: tests whether copy sources become
  cheaper as back-distances, source deltas, or book-relative offsets. They do
  not. The current absolute `source_pos` ledger remains cheapest at `9823.3`
  total bits; the next-best tested address model costs `11507.9` bits.
- `15_copy_graph_provenance_audit`: materializes the DP LZ formula as copy
  edges and literal seed runs. It confirms `281` copy items over `10468` copied
  digits, only `5` same-book copies, `32` source books, `84` literal runs, and
  `52/84` literal runs reused later as source material. It also emits the copy
  graph and literal seed atlas for future formula work, with no formula or
  semantic promotion.
- `16_structured_physical_order_lz_test`: tests whether the partial public
  Hellgate overview/bookcase order is a cheaper zero-search-cost book order for
  the DP LZ generator. It is not: numeric order remains best at `9823.3` bits.
  The best public structured orders cost `9993.1` bits (`+169.8`), while
  candidate-resolved ambiguous orders cost still more. The manifest has 71
  rows, 64 resolved unique books, 6 ambiguous rows, and no fine tile/slot/order
  layer, so no physical or authorial order is promoted.

Any improvement must reduce cost or beat controls. No semantic route is opened.
