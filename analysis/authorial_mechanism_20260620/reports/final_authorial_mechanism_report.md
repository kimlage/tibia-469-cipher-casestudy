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
- `32_literal_to_copy_pair_repair_search`: tests whether compatible pairs of
  literal-to-copy repairs become cheaper together under adaptive payload
  coding. They do not: `25` single candidates yield `293` compatible pairs,
  and the best pair costs `9538.2` bits, `+0.9` worse than the one-step
  repaired formula. No newer formula is promoted.
- `33_book_length_ledger_search`: keeps the repaired recipe fixed but replaces
  independent `gamma(length+1)` book lengths with a decodable signed-Rice
  residual ledger around declared `anchor=151`, `k=5`. Book-length cost drops
  from `1030.0` to `566.0` bits, improving the total formula from `9537.3` to
  `9073.3` bits with 70/70 roundtrip. This is a cost-ledger improvement, not a
  semantic or pair-table result.
- `34_book_length_multi_anchor_search`: tests whether a decodable multi-anchor
  signed-Rice length mixture beats the promoted single-anchor ledger. It does
  not: the best multi-anchor model uses `2` clusters at `k=4`, costs `581.0`
  book-length bits, and is `+15.0` bits worse than the active `anchor=151`,
  `k=5` ledger. No newer formula is promoted.
- `35_digit_only_copy_address_compile`: after book lengths make separators
  reconstructable, recompiles copy addresses over the digit-only emitted
  stream. This reduces copy-address cost from `3257.3` to `3254.9` bits and
  improves the total formula from `9073.3` to `9070.8` bits with 70/70
  roundtrip. The recipe and emitted books are unchanged.
- `36_digit_address_model_search`: retests alternate address ledgers in the
  digit-only coordinate system. Absolute `source_digit_pos` remains the best
  decodable ledger at `9070.8` bits. Literal-seed addressing reaches `9006.2`
  bits only as an undecodable no-mode lower bound; the best decodable sparse
  seed-run ledger costs `9081.5` bits, so no address model is promoted.
- `37_digit_address_literal_repair_search`: retests local literal-to-copy
  repairs under the digit-only address cost. One new repair replaces literal
  `57928` in book `13` with a prior copy from digit position `1976`, improving
  the total formula from `9070.8` to `9070.1` bits. A follow-up one-step search
  after applying it finds no second improvement.
- `38_post_digit_repair_payload_alpha_sweep`: retests adaptive literal-payload
  alpha after the digit-address repair changes the literal payload stream.
  `alpha=14` remains best at `2592.0` payload-plus-model bits; the nearest
  alternate is `alpha=13` at `2592.1` bits. No newer formula is promoted.
- `39_post_digit_repair_address_model_search`: retests alternate address
  ledgers after the digit-address literal-to-copy repair. Absolute
  `source_digit_pos` remains the best decodable ledger at `9070.1` bits.
  Literal-seed addressing reaches `9005.5` bits only as an undecodable no-mode
  lower bound; the best decodable sparse seed-run ledger costs `9080.8` bits.
- `40_item_type_ledger_compile`: replaces the one fixed literal/copy type bit
  charged per recipe item with a declared two-symbol adaptive item-type ledger.
  The same fixed recipe roundtrips 70/70 books and improves the current bound
  from `9070.1` to `8996.2` bits; `alpha=2` costs `291.2` item-type bits
  versus `365.0` fixed type bits.
- `41_markov_item_type_ledger_compile`: retells the same literal/copy type
  stream with a declared previous-type Markov ledger. The same fixed recipe
  roundtrips 70/70 books and improves the current bound from `8996.2` to
  `8977.6` bits; `alpha=1` costs `272.5` item-type bits.
- `42_book_start_item_type_ledger_compile`: uses already-declared book
  boundaries as `BOS` context in that item-type ledger. The same fixed recipe
  roundtrips 70/70 books and improves the current bound from `8977.6` to
  `8972.2` bits; `alpha=1` costs `267.2` item-type bits.
- `43_literal_forces_copy_type_ledger_compile`: charges an explicit one-bit
  deterministic rule that a literal item is followed by copy when the declared
  book length is not complete. The same fixed recipe roundtrips 70/70 books and
  improves the current bound from `8972.2` to `8966.7` bits; `alpha=2` costs
  `261.7` item-type bits.
- `44_remaining_short_forces_literal_type_ledger_compile`: adds a second
  charged deterministic rule: if fewer than `min_len=5` digits remain in the
  declared book, a copy item cannot fit and the type is forced to literal. The
  same fixed recipe roundtrips 70/70 books and improves the current bound from
  `8966.7` to `8953.9` bits; `alpha=2` costs `248.9` item-type bits.
- `45_remaining_short_literal_length_compile`: once those short suffixes are
  forced to literal, their literal length is forced to consume the remaining
  declared book suffix. After charging a one-bit length rule, the same fixed
  recipe roundtrips 70/70 books and improves the current bound from `8953.9` to
  `8922.9` bits by removing `32.0` redundant literal-length bits.
- `46_forced_length_literal_repair_search`: retests local literal-to-copy
  repairs under the current forced-length cost model. One additional repair
  replaces `65128` in book `12` with a prior copy from digit position `50`,
  lowering the bound from `8922.9` to `8922.8` bits. A follow-up one-step
  search after applying it is worse.
- `47_post_forced_repair_payload_alpha_sweep`: retests adaptive literal-payload
  alpha after the forced-length repair. `alpha=14` remains best; `alpha=13` is
  the nearest alternate at `+0.1` bit, so no newer formula is promoted.
- `48_post_forced_repair_address_model_search`: retests copy-source address
  ledgers after the forced-length repair. Literal-seed addressing reaches
  `8855.5` bits only as an undecodable no-mode lower bound; the best decodable
  sparse seed-run ledger costs `8933.5` bits, so absolute `source_digit_pos`
  remains the active address ledger.
- `49_post_forced_repair_pair_search`: tests whether two compatible
  literal-to-copy repairs become cheaper together after the forced-length local
  repair. They do not: `22` single candidates produce `227` compatible pairs,
  and the best pair is `+1.6` bits worse than the active formula.
- `50_post_forced_repair_triple_search`: tests whether three compatible
  literal-to-copy repairs become cheaper together. They do not: the same `22`
  single candidates produce `1462` compatible triples, and the best triple is
  `+2.7` bits worse than the active formula.
- `51_post_forced_repair_quad_search`: tests whether four compatible
  literal-to-copy repairs become cheaper together. They do not: the same `22`
  single candidates produce `6596` compatible quartets, and the best quartet is
  `+3.9` bits worse than the active formula.
- `52_post_forced_repair_quint_search`: tests whether five compatible
  literal-to-copy repairs become cheaper together. They do not: the same `22`
  single candidates produce `22168` compatible quintets, and the best quintet is
  `+5.5` bits worse than the active formula.
- `53_post_forced_repair_sext_search`: tests whether six compatible
  literal-to-copy repairs become cheaper together. They do not: the same `22`
  single candidates produce `57596` compatible sextets, and the best sextet is
  `+7.3` bits worse than the active formula.
- `54_post_forced_repair_sept_search`: tests whether seven compatible
  literal-to-copy repairs become cheaper together. They do not: the same `22`
  single candidates produce `118456` compatible septets, and the best septet is
  `+9.0` bits worse than the active formula.
- `55_post_forced_repair_oct_search`: tests whether eight compatible
  literal-to-copy repairs become cheaper together. They do not: the same `22`
  single candidates produce `195806` compatible octets, and the best octet is
  `+11.0` bits worse than the active formula.
- `56_post_forced_repair_nonet_search`: tests whether nine compatible
  literal-to-copy repairs become cheaper together. They do not: the same `22`
  single candidates produce `262548` compatible nonets, and the best nonet is
  `+12.9` bits worse than the active formula.
- `57_post_forced_repair_decet_search`: tests whether ten compatible
  literal-to-copy repairs become cheaper together. They do not: the same `22`
  single candidates produce `286858` compatible decets, and the best decet is
  `+15.1` bits worse than the active formula.
- `58_post_forced_repair_eleven_search`: tests whether eleven compatible
  literal-to-copy repairs become cheaper together. They do not: the same `22`
  single candidates produce `255476` compatible eleven-repair sets, and the
  best set is `+17.8` bits worse than the active formula.
- `59_post_forced_repair_twelve_search`: tests whether twelve compatible
  literal-to-copy repairs become cheaper together. They do not: the same `22`
  single candidates produce `184756` compatible twelve-repair sets, and the
  best set is `+20.6` bits worse than the active formula.
- `60_post_forced_repair_high_order_exhaustion`: closes the remaining
  high-order compatible local repair frontier. Exact rescoring of sizes
  `13..19` finds the best remaining set at size `13`, still `+23.7` bits worse
  than the active formula; sizes `20..22` have no compatible sets.
- `61_post_forced_repair_literal_payload_context_search`: retests the final
  literal payload with decodable previous-digit contexts. Conditioning on the
  previously emitted digit improves the active mechanical bound from `8922.8`
  to `8842.0` bits after charged declaration bits, with 70/70 roundtrip and
  `translation_delta: NONE`.
- `62_literal_payload_context_order_sweep`: sweeps deterministic
  previous-emitted-digit context orders on the same fixed recipe. A declared
  order-2 context with `alpha=1` improves the active mechanical bound from
  `8842.0` to `8805.7` bits after charged order bits, with 70/70 roundtrip and
  `translation_delta: NONE`.
- `63_item_type_context_order_sweep`: sweeps declared previous item-type
  context orders while retaining the deterministic item-type rules. Order `3`
  with `alpha=2` improves the active mechanical bound from `8805.7` to
  `8803.5` bits after charged order bits, with 70/70 roundtrip and
  `translation_delta: NONE`.
- `64_contextual_local_repair_search`: retests literal-to-copy repairs under
  the current contextual cost model. It tests `22` candidates; the best remains
  `+1.0` bit worse, so no literal-to-copy repair is promoted.
- `65_contextual_copy_to_literal_repair_search`: tests the reverse direction
  under the same contextual cost model. Replacing a short copy of `45765` in
  book `34` with a literal improves the active mechanical bound from `8803.5`
  to `8803.1` bits with 70/70 roundtrip and `translation_delta: NONE`.
- `66_post_copy_literal_local_frontier`: retests the immediate local frontier
  after that copy-to-literal repair. No further local edit promotes: the best
  literal-to-copy edit is `+0.4` bits worse, the best copy-to-literal edit is
  `+1.5` bits worse, and the best of `13530` copy-to-literal pairs is `+3.5`
  bits worse.
- `67_contextual_address_model_search`: retests copy-source address ledgers on
  the active contextual formula. Absolute `source_digit_pos` remains the best
  decodable ledger at `8803.1` bits; literal-seed addressing reaches `8739.3`
  bits only as an optimistic no-mode lower bound.
- `68_post_contextual_parameter_resweep`: retests the declared length,
  literal-payload context, and item-type context parameters after the
  contextual copy-to-literal repair. The current parameters remain best:
  copy Rice `k=4`, literal Rice `k=3`, payload order `2` / `alpha=1`, and
  item-type order `3` / `alpha=2`. No newer formula is promoted.
- `69_bounded_copy_length_code_compile`: replaces unbounded Rice `k=4` copy
  lengths with a decodable truncated-binary code over the legal length range
  known after decoding the copy source address. This reduces copy-length bits
  from `1860.0` to `1671.0` and improves the active 70/70 formula from
  `8803.1` to `8614.1` bits with `translation_delta: NONE`.
- `70_min_len_bounded_copy_address_compile`: tightens the absolute source
  address space by excluding the impossible last `min_len - 1` emitted digit
  positions. This reduces copy-address bits from `3264.817` to `3263.751` and
  improves the active 70/70 formula from `8614.133` to `8613.067` bits with
  `translation_delta: NONE`.
- `71_minaddr_local_frontier`: retests single literal-to-copy and
  copy-to-literal edits after bounded copy lengths and min_len-bounded copy
  addresses. One literal-to-copy edit promotes: `11216` in book `2` becomes a
  copy from source digit position `225`, improving the active 70/70 formula
  from `8613.067` to `8611.408` bits with `translation_delta: NONE`.
- `72_post_minaddr_repair_local_frontier`: retests that local frontier after
  the `11216` repair changes the recipe. A second literal-to-copy edit
  promotes: `45765` in book `34` becomes a copy from source digit position
  `183`, improving the active 70/70 formula from `8611.408` to `8609.773` bits
  with `translation_delta: NONE`.
- `73_post_minaddr_repair2_local_frontier`: retests the same frontier after
  the `45765` repair. No further one-step edit promotes: the best candidate is
  copy-to-literal `94343` in book `26`, but it is `+0.121` bits worse than the
  active `8609.773` bit formula.

Any improvement must reduce cost or beat controls. No semantic route is opened.
