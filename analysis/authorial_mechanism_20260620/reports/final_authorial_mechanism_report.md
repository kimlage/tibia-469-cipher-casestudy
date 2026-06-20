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
  not. Within that fixed gamma-length DP parse, the absolute `source_pos` ledger
  remains cheapest at `9823.3` total bits; the next-best tested address model
  costs `11507.9` bits.
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
- `17_literal_seed_address_model_search`: tests whether copy sources can be
  addressed through earlier literal seed runs instead of absolute `source_pos`.
  An optimistic no-mode ledger reaches `9752.8` bits (`-70.5`), but it does not
  pay to distinguish seed addresses from absolute stream addresses. Once a
  source-mode bit is charged for a decodable mixed ledger, the total becomes
  `10033.8` bits (`+210.5`). The model is therefore a useful provenance clue,
  not a promoted formula.
- `18_literal_seed_grouped_mode_search`: tests whether that mode cost can be
  paid by grouped ledgers instead of once per copy. The best seed-using
  decodable ledger is a sparse seed-run list at `9830.0` bits (`+6.7`), while
  the RLE seed-required mask costs `9843.0` bits (`+19.7`). Grouping narrows the
  penalty but still does not beat the previous `9823.3` gamma-length
  absolute-address formula.
- `19_copy_hub_macro_model_search`: tests whether copy sources can be declared
  as global or target-local source-book hubs, or as a target-default source with
  exceptions. This is not cheaper: the optimistic default-source lower bound is
  `10326.9` bits (`+503.6`), and the best decodable default-source ledger is
  `10430.2` bits (`+606.9`). The source-hub macro path is therefore not
  promoted.
- `20_restricted_hybrid_vocabulary_reparse`: reparses all 70 books with a
  declared dictionary of repeated digit motifs plus the existing literal-run and
  prior-copy vocabulary. It roundtrips 70/70, but no dictionary model beats the
  DP LZ baseline. The closest dictionary-using model is an optimistic non-
  decodable `K=4` redundancy-filtered motif set at `9840.7` bits (`+17.4`); the
  closest decodable dictionary model costs `10123.2` bits (`+299.9`).
- `21_dp_min_len_sweep_control`: sweeps the modern DP sequential LZ `min_len`
  parameter from `3` through `12`. The current `min_len=6` remains best at
  `9823.3` bits; the nearest alternate is `min_len=5` at `9827.7` bits
  (`+4.4`). Focused digit-shuffle controls are far worse; book-order shuffle
  wins remain diagnostic only because they do not supply a zero-cost external
  order or pay permutation cost.
- `22_copy_length_code_reparse`: reparses the same sequential LZ family with
  alternate copy-length codes. Rice coding with `k=4` and `min_len=5` is a
  controlled mechanical improvement: it roundtrips 70/70 at `9596.5` bits,
  improving the previous gamma-length DP baseline by `226.8` bits after
  charging `5` parameter bits. Digit-shuffle and book-order-shuffle controls do
  not beat the observed formula.
- `23_copy_length_grid_sweep`: broadens that search to `min_len=3..12`, gamma,
  delta, unary, and Rice `k=0..10`. It retains the promoted `rice_k4` /
  `min_len=5` model at `9596.5` bits. The nearest non-current model is
  `rice_k4` / `min_len=4` at `9600.0` bits (`+3.5`), so no newer formula is
  promoted.
- `24_rice_copy_address_model_search`: retests copy-source address ledgers on
  the Rice-length parse. Absolute `source_pos` remains the best decodable
  ledger at `9596.5` bits. A literal-seed optimistic no-mode ledger reaches
  `9549.5` bits, but it is not decodable; the best decodable sparse seed-run
  ledger is `9607.1` bits and per-copy mode is `9827.5` bits, so no address
  model is promoted.
- `25_literal_run_length_code_reparse`: reparses the promoted Rice-length
  formula while varying only literal-run length coding. Rice `k=3` for literal
  lengths, with copy lengths still Rice `k=4` and `min_len=5`, roundtrips 70/70
  at `9545.5` bits. This is a `51.0` bit improvement over the prior `9596.5`
  bit formula after charging both Rice parameters. Digit-shuffle and book-order
  controls do not beat the observed formula.
- `26_joint_length_code_grid_sweep`: tests the interaction between copy-length
  and literal-run length codes over `605` joint DP reparses. The current
  `rice_k4` copy / `rice_k3` literal / `min_len=5` formula remains best at
  `9545.5` bits. The nearest alternate is `rice_k4` copy / `rice_k2` literal /
  `min_len=5` at `9552.2` bits (`+6.7`), so no newer formula is promoted.
- `27_literal_payload_model_search`: keeps the current recipe fixed and tests
  literal digit payload coding. A decodable adaptive Dirichlet payload model
  with integer `alpha=14` improves the formula from `9545.5` to `9538.0` bits
  after charging `7` bits to declare alpha. Random uniform literal-payload
  controls do not beat the observed distribution. A cheaper static histogram
  oracle is recorded as non-decodable and not promoted.
- `28_current_formula_address_model_search`: retests copy-source address
  ledgers on the current `9538.0` bit formula. Absolute `source_pos` remains
  the best decodable ledger. Literal-seed addressing reaches `9478.6` bits only
  as an undecodable no-mode lower bound; the best decodable sparse seed-run
  ledger is `9548.7` bits (`+10.7`), so no address model is promoted.
- `29_literal_to_copy_repair_search`: tests whether adaptive literal-payload
  coding left the recipe locally stale. One valid repair replaces literal
  `972783` in book `8` with a prior copy from source position `370`, improving
  the formula from `9538.0` to `9537.3` bits. A follow-up one-step repair search
  after applying it finds no second improvement.
- `30_post_repair_payload_alpha_sweep`: retests the adaptive literal-payload
  alpha after the literal-to-copy repair changes the literal payload stream.
  `alpha=14` remains best at `2608.9` payload-plus-model bits; the nearest
  alternate is `alpha=13` at `2609.0` bits. No newer formula is promoted.
- `31_post_repair_address_model_search`: retests copy-source address ledgers
  after the literal-to-copy repair. Absolute `source_pos` remains the best
  decodable ledger at `9537.3` bits. Literal-seed addressing reaches `9472.4`
  bits only as an undecodable no-mode lower bound; the best decodable sparse
  seed-run ledger costs `9548.0` bits, so no address model is promoted.

Any improvement must reduce cost or beat controls. No semantic route is opened.
