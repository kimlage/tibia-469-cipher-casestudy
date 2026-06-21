---
title: "Research summary: generation formula next steps"
date: 2026-06-20
source_note: "/Users/sargam/Downloads/469_generation_formula_next_report.md"
status: incorporated_as_generation_tests
translation_delta: NONE
---

# Research Summary: Generation Formula Next Steps

The report reviewed an earlier public `main` state and proposed the next
mechanical improvements for the 70-book generator. Because the repository has
advanced beyond that snapshot, its numeric baseline is treated as historical;
the report is incorporated as a hypothesis queue and reconciliation checklist,
not as the current frontier. Its central recommendation was to replace the
greedy sequential LZ parser with a dynamic-programming parser under the final
run-literal cost.

That recommendation is now implemented by
[`13_sequential_lz_dp_parse_compile.py`](scripts/13_sequential_lz_dp_parse_compile.py):
the best generator moved from `9944.0` bits to `9823.3` bits while preserving
70/70 roundtrip and `translation_delta: NONE`.

Additional recommendations were converted into bounded tests:

- source-address alternatives are tested by
  [`14_copy_source_address_model_search.py`](scripts/14_copy_source_address_model_search.py);
  absolute `source_pos` remains cheapest, so no alternate address model is
  promoted.
- copy-graph provenance and the literal seed atlas are materialized by
  [`15_copy_graph_provenance_audit.py`](scripts/15_copy_graph_provenance_audit.py);
  this is diagnostic context for future formula work, not a new lower-cost
  generator.

Coverage of the remaining report recommendations and follow-on refinements:

- structured public/topology order tests under the DP parser are now covered by
  [`16_structured_physical_order_lz_test.py`](scripts/16_structured_physical_order_lz_test.py);
  the tested public/bookcase orders do not beat numeric order.
- literal-seed source addressing is now covered by
  [`17_literal_seed_address_model_search.py`](scripts/17_literal_seed_address_model_search.py);
  it improves only in an optimistic no-mode ledger and is rejected once
  source-mode bits are charged for decodability.
- grouped source-mode coding for literal-seed addresses is now covered by
  [`18_literal_seed_grouped_mode_search.py`](scripts/18_literal_seed_grouped_mode_search.py);
  the best seed-using decodable grouped ledger still costs `9830.0` bits,
  worse than the previous `9823.3` gamma-length absolute-address formula.
- source-book hub/default-source macro addressing is now covered by
  [`19_copy_hub_macro_model_search.py`](scripts/19_copy_hub_macro_model_search.py);
  even the optimistic target-default source lower bound costs `10326.9` bits.
- restricted hybrid vocabulary reparsing is now covered by
  [`20_restricted_hybrid_vocabulary_reparse.py`](scripts/20_restricted_hybrid_vocabulary_reparse.py);
  it roundtrips 70/70 but the best dictionary-using motif model still costs
  `9840.7` bits, worse than the previous `9823.3` gamma-length DP formula.
- DP `min_len` parameter sweep is now covered by
  [`21_dp_min_len_sweep_control.py`](scripts/21_dp_min_len_sweep_control.py);
  `min_len=6` remains best at `9823.3`, with `min_len=5` nearest at `9827.7`.
- copy-length code reparse is now covered by
  [`22_copy_length_code_reparse.py`](scripts/22_copy_length_code_reparse.py);
  Rice `k=4` with `min_len=5` improves the generator to `9596.5` bits with
  70/70 roundtrip and `translation_delta: NONE`.
- broader copy-length grid sweep is now covered by
  [`23_copy_length_grid_sweep.py`](scripts/23_copy_length_grid_sweep.py);
  it retains Rice `k=4`, `min_len=5`, with the nearest alternate at `9600.0`
  bits.
- Rice-parse copy address models are now covered by
  [`24_rice_copy_address_model_search.py`](scripts/24_rice_copy_address_model_search.py);
  absolute `source_pos` remains best decodable, while literal-seed addressing
  remains optimistic-only.
- literal-run length coding is now covered by
  [`25_literal_run_length_code_reparse.py`](scripts/25_literal_run_length_code_reparse.py);
  Rice `k=3` for literal lengths improves the current mechanical bound to
  `9545.5` bits with 70/70 roundtrip and `translation_delta: NONE`.
- joint copy/literal length-code interaction is now covered by
  [`26_joint_length_code_grid_sweep.py`](scripts/26_joint_length_code_grid_sweep.py);
  `605` DP reparses retain copy Rice `k=4`, literal Rice `k=3`, and
  `min_len=5` as the best tested parameter set.
- literal digit payload coding is now covered by
  [`27_literal_payload_model_search.py`](scripts/27_literal_payload_model_search.py);
  a decodable adaptive Dirichlet payload model improves the current bound to
  `9538.0` bits; the cheaper static histogram oracle is not promoted.
- current-formula copy-address ledgers are now covered by
  [`28_current_formula_address_model_search.py`](scripts/28_current_formula_address_model_search.py);
  absolute `source_pos` remains the best decodable ledger after the current
  parse and payload model are fixed.
- local literal-to-copy repair is now covered by
  [`29_literal_to_copy_repair_search.py`](scripts/29_literal_to_copy_repair_search.py);
  replacing one current literal substring with a valid prior copy improves the
  bound to `9537.3` bits and no second one-step repair improves it further.
- post-repair payload alpha is now covered by
  [`30_post_repair_payload_alpha_sweep.py`](scripts/30_post_repair_payload_alpha_sweep.py);
  `alpha=14` remains the best declared adaptive payload parameter after the
  local repair.
- post-repair copy-source address ledgers are now covered by
  [`31_post_repair_address_model_search.py`](scripts/31_post_repair_address_model_search.py);
  absolute `source_pos` remains the best decodable ledger, while the cheaper
  literal-seed lower bound is still undecodable.
- compatible two-repair literal-to-copy recipes are now covered by
  [`32_literal_to_copy_pair_repair_search.py`](scripts/32_literal_to_copy_pair_repair_search.py);
  no pair beats the current one-step repaired formula after exact rescoring.
- book-length ledger coding is now covered by
  [`33_book_length_ledger_search.py`](scripts/33_book_length_ledger_search.py);
  a declared signed-Rice residual ledger improves the current bound to
  `9073.3` bits while preserving 70/70 roundtrip.
- multi-anchor book-length ledgers are now covered by
  [`34_book_length_multi_anchor_search.py`](scripts/34_book_length_multi_anchor_search.py);
  the best multi-anchor mixture is worse once per-book mode bits and extra
  anchor declarations are charged.
- digit-only copy-source addressing is now covered by
  [`35_digit_only_copy_address_compile.py`](scripts/35_digit_only_copy_address_compile.py);
  after book lengths make separators reconstructable, excluding separators from
  the absolute address space improves the bound to `9070.8` bits.
- digit-only address alternatives are now covered by
  [`36_digit_address_model_search.py`](scripts/36_digit_address_model_search.py);
  absolute `source_digit_pos` remains the best decodable ledger in the
  digit-only coordinate system.
- digit-address literal-to-copy repair is now covered by
  [`37_digit_address_literal_repair_search.py`](scripts/37_digit_address_literal_repair_search.py);
  one local repair improves the current bound to `9070.1` bits, with no second
  one-step repair after applying it.
- post-digit-repair literal-payload alpha is now covered by
  [`38_post_digit_repair_payload_alpha_sweep.py`](scripts/38_post_digit_repair_payload_alpha_sweep.py);
  `alpha=14` remains the best declared adaptive payload parameter after the
  latest repair.
- post-digit-repair address alternatives are now covered by
  [`39_post_digit_repair_address_model_search.py`](scripts/39_post_digit_repair_address_model_search.py);
  absolute `source_digit_pos` remains the best decodable ledger after the
  latest repair.
- item-type ledger coding is now covered by
  [`40_item_type_ledger_compile.py`](scripts/40_item_type_ledger_compile.py);
  replacing fixed literal/copy item tags with a declared adaptive two-symbol
  ledger improves the current bound to `8996.2` bits while preserving 70/70
  roundtrip.
- Markov item-type ledger coding is now covered by
  [`41_markov_item_type_ledger_compile.py`](scripts/41_markov_item_type_ledger_compile.py);
  conditioning each item tag on the previous item tag improves the current
  bound to `8977.6` bits while preserving 70/70 roundtrip.
- book-start item-type ledger coding is now covered by
  [`42_book_start_item_type_ledger_compile.py`](scripts/42_book_start_item_type_ledger_compile.py);
  using declared book starts as an item-type context improves the current bound
  to `8972.2` bits while preserving 70/70 roundtrip.
- literal-forces-copy item-type coding is now covered by
  [`43_literal_forces_copy_type_ledger_compile.py`](scripts/43_literal_forces_copy_type_ledger_compile.py);
  after charging a deterministic rule bit, literal-to-copy forcing improves the
  current bound to `8966.7` bits while preserving 70/70 roundtrip.
- remaining-short-forces-literal item-type coding is now covered by
  [`44_remaining_short_forces_literal_type_ledger_compile.py`](scripts/44_remaining_short_forces_literal_type_ledger_compile.py);
  after charging a second deterministic rule bit, suffixes shorter than
  `min_len=5` force literal item type and improve the current bound to
  `8953.9` bits while preserving 70/70 roundtrip.
- remaining-short literal length coding is now covered by
  [`45_remaining_short_literal_length_compile.py`](scripts/45_remaining_short_literal_length_compile.py);
  once such suffixes are forced literal, their lengths are forced to consume
  the rest of the declared book, improving the current bound to `8922.9` bits
  while preserving 70/70 roundtrip.
- forced-length literal-to-copy repair is now covered by
  [`46_forced_length_literal_repair_search.py`](scripts/46_forced_length_literal_repair_search.py);
  one further local repair replaces `65128` in book `12` with a valid prior
  copy, improving the current bound to `8922.8` bits. A follow-up one-step
  search after applying it is worse.
- post-forced-repair payload alpha is now covered by
  [`47_post_forced_repair_payload_alpha_sweep.py`](scripts/47_post_forced_repair_payload_alpha_sweep.py);
  `alpha=14` remains the best declared adaptive payload parameter after the
  forced-length local repair, with `alpha=13` `+0.1` bit worse.
- post-forced-repair copy-source address ledgers are now covered by
  [`48_post_forced_repair_address_model_search.py`](scripts/48_post_forced_repair_address_model_search.py);
  absolute `source_digit_pos` remains the best decodable ledger. Literal-seed
  addressing reaches `8855.5` bits only as an optimistic no-mode lower bound;
  the best decodable sparse seed-run ledger costs `8933.5` bits.
- post-forced-repair pair search is now covered by
  [`49_post_forced_repair_pair_search.py`](scripts/49_post_forced_repair_pair_search.py);
  `22` single candidates yield `227` compatible pairs, and the best pair is
  still `+1.6` bits worse than the active formula.
- post-forced-repair triple search is now covered by
  [`50_post_forced_repair_triple_search.py`](scripts/50_post_forced_repair_triple_search.py);
  the same `22` single candidates yield `1462` compatible triples, and the best
  triple is `+2.7` bits worse than the active formula.
- post-forced-repair quad search is now covered by
  [`51_post_forced_repair_quad_search.py`](scripts/51_post_forced_repair_quad_search.py);
  the same `22` single candidates yield `6596` compatible quartets, and the
  best quartet is `+3.9` bits worse than the active formula.
- post-forced-repair quint search is now covered by
  [`52_post_forced_repair_quint_search.py`](scripts/52_post_forced_repair_quint_search.py);
  the same `22` single candidates yield `22168` compatible quintets, and the
  best quintet is `+5.5` bits worse than the active formula.
- post-forced-repair sext search is now covered by
  [`53_post_forced_repair_sext_search.py`](scripts/53_post_forced_repair_sext_search.py);
  the same `22` single candidates yield `57596` compatible sextets, and the
  best sextet is `+7.3` bits worse than the active formula.
- post-forced-repair sept search is now covered by
  [`54_post_forced_repair_sept_search.py`](scripts/54_post_forced_repair_sept_search.py);
  the same `22` single candidates yield `118456` compatible septets, and the
  best septet is `+9.0` bits worse than the active formula.
- post-forced-repair oct search is now covered by
  [`55_post_forced_repair_oct_search.py`](scripts/55_post_forced_repair_oct_search.py);
  the same `22` single candidates yield `195806` compatible octets, and the
  best octet is `+11.0` bits worse than the active formula.
- post-forced-repair nonet search is now covered by
  [`56_post_forced_repair_nonet_search.py`](scripts/56_post_forced_repair_nonet_search.py);
  the same `22` single candidates yield `262548` compatible nonets, and the
  best nonet is `+12.9` bits worse than the active formula.
- post-forced-repair decet search is now covered by
  [`57_post_forced_repair_decet_search.py`](scripts/57_post_forced_repair_decet_search.py);
  the same `22` single candidates yield `286858` compatible decets, and the
  best decet is `+15.1` bits worse than the active formula.
- post-forced-repair eleven-repair search is now covered by
  [`58_post_forced_repair_eleven_search.py`](scripts/58_post_forced_repair_eleven_search.py);
  the same `22` single candidates yield `255476` compatible eleven-repair
  sets, and the best set is `+17.8` bits worse than the active formula.
- post-forced-repair twelve-repair search is now covered by
  [`59_post_forced_repair_twelve_search.py`](scripts/59_post_forced_repair_twelve_search.py);
  the same `22` single candidates yield `184756` compatible twelve-repair
  sets, and the best set is `+20.6` bits worse than the active formula.
- post-forced-repair high-order exhaustion is now covered by
  [`60_post_forced_repair_high_order_exhaustion.py`](scripts/60_post_forced_repair_high_order_exhaustion.py);
  exact rescoring of compatible set sizes `13..19` and compatibility checks for
  `20..22` close the remaining local frontier. The best remaining high-order
  set is size `13` at `+23.7` bits worse than the active formula; sizes
  `20..22` have no compatible sets.
- post-forced-repair literal payload context coding is now covered by
  [`61_post_forced_repair_literal_payload_context_search.py`](scripts/61_post_forced_repair_literal_payload_context_search.py);
  conditioning each literal payload digit on the previously emitted digit in
  the already generated stream is decodable and improves the active formula
  from `8922.8` to `8842.0` bits after charged alpha and context-family bits.
- literal payload context-order sweep is now covered by
  [`62_literal_payload_context_order_sweep.py`](scripts/62_literal_payload_context_order_sweep.py);
  a declared previous-emitted-digit context of order `2` with `alpha=1`
  further improves the active formula from `8842.0` to `8805.7` bits after
  charged order bits.
- item-type context-order sweep is now covered by
  [`63_item_type_context_order_sweep.py`](scripts/63_item_type_context_order_sweep.py);
  a declared previous item-type context of order `3` with `alpha=2` further
  improves the active formula from `8805.7` to `8803.5` bits after charged
  order bits and retained forced-type rules.
- contextual literal-to-copy local repair is now covered by
  [`64_contextual_local_repair_search.py`](scripts/64_contextual_local_repair_search.py);
  after exact rescoring under contextual payload and item-type ledgers, `22`
  candidate literal-to-copy repairs are tested and the best remains `+1.0` bit
  worse than the active formula.
- contextual copy-to-literal local repair is now covered by
  [`65_contextual_copy_to_literal_repair_search.py`](scripts/65_contextual_copy_to_literal_repair_search.py);
  one short copy in book `34` becomes cheaper as an explicit literal, improving
  the active formula from `8803.5` to `8803.1` bits.
- post-copy-to-literal local frontier is now covered by
  [`66_post_copy_literal_local_frontier.py`](scripts/66_post_copy_literal_local_frontier.py);
  after applying that repair, the best literal-to-copy edit is `+0.4` bits
  worse, the best copy-to-literal edit is `+1.5` bits worse, and the best of
  `13530` copy-to-literal pairs is `+3.5` bits worse.
- contextual address-model retest is now covered by
  [`67_contextual_address_model_search.py`](scripts/67_contextual_address_model_search.py);
  absolute `source_digit_pos` remains the best decodable copy-source address
  ledger. Literal-seed addressing reaches `8739.3` bits only as an optimistic
  no-mode lower bound; the best decodable sparse seed-run ledger costs
  `8813.8` bits.
- post-contextual parameter resweep is now covered by
  [`68_post_contextual_parameter_resweep.py`](scripts/68_post_contextual_parameter_resweep.py);
  copy length Rice `k=4`, literal-run length Rice `k=3`, literal payload
  order `2` / `alpha=1`, and item-type order `3` / `alpha=2` all remain best
  after charged declarations. No newer formula is promoted.
- bounded copy-length coding is now covered by
  [`69_bounded_copy_length_code_compile.py`](scripts/69_bounded_copy_length_code_compile.py);
  after each source address is decoded, the legal copy length is bounded by
  declared remaining book digits and available emitted source digits. Replacing
  unbounded Rice `k=4` lengths with truncated binary over that range improves
  the active 70/70 formula from `8803.1` to `8614.1` bits.
- min_len-bounded copy addressing is now covered by
  [`70_min_len_bounded_copy_address_compile.py`](scripts/70_min_len_bounded_copy_address_compile.py);
  since every copy source must leave at least `min_len` emitted digits
  available, the last `min_len - 1` emitted positions are impossible source
  starts. Excluding them improves the active formula from `8614.133` to
  `8613.067` bits.
- minaddr local repair frontier is now covered by
  [`71_minaddr_local_frontier.py`](scripts/71_minaddr_local_frontier.py);
  after the address-bound cost change, a single literal-to-copy edit promotes:
  `11216` in book `2` becomes a valid prior copy from source digit position
  `225`, improving the active formula from `8613.067` to `8611.408` bits.
- post-minaddr-repair local frontier is now covered by
  [`72_post_minaddr_repair_local_frontier.py`](scripts/72_post_minaddr_repair_local_frontier.py);
  after the `11216` repair, a second literal-to-copy edit promotes: `45765` in
  book `34` becomes a valid prior copy from source digit position `183`,
  improving the active formula from `8611.408` to `8609.773` bits.
- post-minaddr-repair2 local frontier is now covered by
  [`73_post_minaddr_repair2_local_frontier.py`](scripts/73_post_minaddr_repair2_local_frontier.py);
  after those two repairs, the best one-step edit is copy-to-literal `94343`
  in book `26`, but it is `+0.121` bits worse, so the local one-step frontier
  is closed under the current cost model.
- post-repair2 parameter resweep is now covered by
  [`74_post_repair2_parameter_resweep.py`](scripts/74_post_repair2_parameter_resweep.py);
  literal Rice `k=3`, literal payload order `2` / `alpha=1`, and item-type
  order `3` / `alpha=2` all remain best after the two minaddr local repairs.
- post-repair2 pair frontier is now covered by
  [`75_post_repair2_pair_frontier.py`](scripts/75_post_repair2_pair_frontier.py);
  `17663` valid compatible pairs are fully rescored. The best pair is still
  `+0.692` bits worse, so compatible pairs do not improve the active formula.
- post-repair2 address models are now covered by
  [`76_post_repair2_address_model_search.py`](scripts/76_post_repair2_address_model_search.py);
  the active min_len-bounded absolute address ledger remains the best decodable
  row at `8609.8` bits. Literal-seed no-mode reaches `8540.4` bits, but it is
  non-decodable without source-mode bits and is not promoted.
- post-repair2 copy order is now covered by
  [`77_post_repair2_copy_order_search.py`](scripts/77_post_repair2_copy_order_search.py);
  pure length-first coding is `+18.295` bits worse, while best-order no-mode is
  `-3.539` bits optimistic only. Decodable order ledgers do not beat the active
  source-address-then-length order.
- post-repair2 adaptive copy length is now covered by
  [`78_post_repair2_adaptive_copy_length_compile.py`](scripts/78_post_repair2_adaptive_copy_length_compile.py);
  adaptive bounded copy-length index coding with `alpha=2` lowers the active
  bound from `8609.773` to `8575.986` bits after charged declaration bits, with
  no recipe or semantic change.
- post-adaptive-copy-length local frontier is now covered by
  [`79_post_adaptive_copy_length_local_frontier.py`](scripts/79_post_adaptive_copy_length_local_frontier.py);
  the best one-edit repair is copy-to-literal `45765` in book `34`, but it is
  `+1.084` bits worse, so the immediate local recipe frontier is closed under
  the active adaptive scorer.
- post-adaptive parameter resweep is now covered by
  [`80_post_adaptive_parameter_resweep.py`](scripts/80_post_adaptive_parameter_resweep.py);
  the active declared parameters remain best: copy-length `alpha=2`, literal
  Rice `k=3`, payload order `2` / `alpha=1`, and item-type order `3` /
  `alpha=2`.
- post-adaptive pair frontier is now covered by
  [`81_post_adaptive_pair_frontier.py`](scripts/81_post_adaptive_pair_frontier.py);
  `17663` valid compatible pairs are fully rescored. The best pair,
  copy-to-literal `71288` plus `45765`, is still `+2.516` bits worse.
- post-adaptive address models are now covered by
  [`82_post_adaptive_address_model_search.py`](scripts/82_post_adaptive_address_model_search.py);
  min_len-bounded absolute addresses remain the best decodable ledger at
  `8576.0` bits. Literal-seed no-mode reaches `8506.6` bits, but remains
  non-decodable without source-mode bits.
- post-adaptive copy order is now covered by
  [`83_post_adaptive_copy_order_search.py`](scripts/83_post_adaptive_copy_order_search.py);
  pure length-first adaptive coding is `+13.664` bits worse, while best-order
  no-mode remains `-3.539` bits optimistic only. Decodable order ledgers do not
  beat the active source-address-then-adaptive-length order.
- post-adaptive copy-length context is now covered by
  [`84_post_adaptive_copy_length_context_search.py`](scripts/84_post_adaptive_copy_length_context_search.py);
  a fixed book-midpoint context for the adaptive length-index prior lowers the
  bound from `8575.986` to `8574.407` bits after charged context declaration
  bits. Searched single splits show larger component savings but are not
  promoted once the split index is charged.
- post-midpoint local frontier is now covered by
  [`85_post_midpoint_local_frontier.py`](scripts/85_post_midpoint_local_frontier.py);
  after the midpoint context, the best one-edit local repair is still `+1.537`
  bits worse, so the immediate literal/copy recipe frontier remains closed.
- post-midpoint parameter resweep is now covered by
  [`86_post_midpoint_parameter_resweep.py`](scripts/86_post_midpoint_parameter_resweep.py);
  after the midpoint context, copy-length `alpha=1` improves the bound from
  `8574.407` to `8572.267` bits. Literal length, literal payload, and item-type
  parameters remain unchanged.
- post-midpoint alpha1 local frontier is now covered by
  [`87_post_midpoint_alpha1_local_frontier.py`](scripts/87_post_midpoint_alpha1_local_frontier.py);
  after the alpha change, the best one-edit local repair is still `+0.971`
  bits worse, so the immediate literal/copy recipe frontier remains closed.
- post-midpoint alpha1 pair frontier is now covered by
  [`88_post_midpoint_alpha1_pair_frontier.py`](scripts/88_post_midpoint_alpha1_pair_frontier.py);
  `17663` valid compatible pairs are fully rescored, and the best pair is
  still `+2.501` bits worse, so compatible pairs do not improve the active
  formula.
- the external next-formula report's address-ledger recommendation is now
  revalidated against the stronger midpoint alpha=1 formula by
  [`89_post_midpoint_alpha1_address_model_search.py`](scripts/89_post_midpoint_alpha1_address_model_search.py);
  literal-seed addressing reaches `8502.9` bits only as an undecodable no-mode
  lower bound, while the best decodable row remains the active min_len-bounded
  absolute ledger at `8572.267` bits.
- post-midpoint alpha1 copy-order alternatives are now covered by
  [`90_post_midpoint_alpha1_copy_order_search.py`](scripts/90_post_midpoint_alpha1_copy_order_search.py);
  pure length-first coding is `+12.194` bits worse, the best no-mode mixed
  order is `-3.539` bits optimistic-only, and the best sparse decodable mode
  ledger is still `+8.979` bits worse.
- post-midpoint alpha1 copy-length contexts are now reswept by
  [`91_post_midpoint_alpha1_copy_length_context_resweep.py`](scripts/91_post_midpoint_alpha1_copy_length_context_resweep.py);
  the active fixed midpoint context remains best at `8572.267` bits. Book
  quartiles are only `+1.941` bits worse after declaration, and the best
  searched split is still `+2.296` bits worse after charging the split index.
- midpoint context-specific smoothing is now covered by
  [`92_post_midpoint_alpha1_context_alpha_grid.py`](scripts/92_post_midpoint_alpha1_context_alpha_grid.py);
  the best per-context row, first-half `alpha=1` and second-half `alpha=2`,
  saves `1.611` component bits but is still `+1.389` bits worse after the
  extra alpha declarations.
- literal-payload contexts are now covered by
  [`93_post_midpoint_alpha1_literal_payload_context_search.py`](scripts/93_post_midpoint_alpha1_literal_payload_context_search.py);
  book-midpoint payload context saves `2.251` component bits but is still
  `+1.749` bits worse after declaration, so the global previous-emitted-digit
  payload model remains active.
- bounded triple probing is now covered by
  [`94_post_midpoint_alpha1_top60_triple_probe.py`](scripts/94_post_midpoint_alpha1_top60_triple_probe.py);
  among the top `60` local single-edit candidates, `33588` valid compatible
  triples are rescored and the best remains `+3.914` bits worse. This is
  negative evidence inside the bounded top60 scope, not an exhaustive triple
  frontier over all `189` candidates.
- item-type context search is now covered by
  [`95_post_midpoint_alpha1_item_type_context_search.py`](scripts/95_post_midpoint_alpha1_item_type_context_search.py);
  the non-decodable current-item-length context is recorded only as a lower
  bound, while a declared book split at `6` is decodable and lowers the active
  bound from `8572.267` to `8569.652` bits.
- post-itemctx parameter resweep is now covered by
  [`96_post_itemctx_parameter_resweep.py`](scripts/96_post_itemctx_parameter_resweep.py);
  after split book `6` is active, item-type extra-context order `1` with
  `alpha=2` lowers the active bound again from `8569.652` to `8561.792` bits.
  Literal-run length, literal payload, and midpoint copy-length parameters
  remain unchanged.
- post-itemctx_param local frontier is now covered by
  [`97_post_itemctx_param_local_frontier.py`](scripts/97_post_itemctx_param_local_frontier.py);
  the best one-step edit is literal-to-copy `60199` in book `3`, still
  `+0.957` bits worse than the active formula.
- post-itemctx_param pair frontier is now covered by
  [`98_post_itemctx_param_pair_frontier.py`](scripts/98_post_itemctx_param_pair_frontier.py);
  `17663` valid compatible pairs are rescored and the best pair remains
  `+1.809` bits worse.
- post-itemctx_param address models are now covered by
  [`99_post_itemctx_param_address_model_search.py`](scripts/99_post_itemctx_param_address_model_search.py);
  min_len-bounded absolute addresses remain the best decodable ledger at
  `8561.792` bits. Literal-seed no-mode reaches `8492.396` bits but is not
  decodable without source-mode bits, and the best sparse decodable seed-run
  ledger is `+9.060` bits worse.
- post-itemctx_param copy order is now covered by
  [`100_post_itemctx_param_copy_order_search.py`](scripts/100_post_itemctx_param_copy_order_search.py);
  source-first remains best decodable, pure length-first is `+12.194` bits
  worse, and the best no-mode mixed order is `-3.539` bits optimistic-only.
- post-itemctx_param copy-length context resweep is now covered by
  [`101_post_itemctx_param_copy_length_context_resweep.py`](scripts/101_post_itemctx_param_copy_length_context_resweep.py);
  the active fixed book-midpoint context remains best at `8561.792` bits.
  Book quartiles are `+1.941` bits worse and the best searched split is
  `+2.296` bits worse after declaration.
- post-itemctx_param context alpha grid is now covered by
  [`102_post_itemctx_param_context_alpha_grid.py`](scripts/102_post_itemctx_param_context_alpha_grid.py);
  first-half `alpha=1` plus second-half `alpha=2` saves `1.611` component
  bits but remains `+1.389` bits worse after per-context alpha declarations.
- post-itemctx_param literal-payload contexts are now covered by
  [`103_post_itemctx_param_literal_payload_context_search.py`](scripts/103_post_itemctx_param_literal_payload_context_search.py);
  book-midpoint payload context saves `2.251` component bits but remains
  `+1.749` bits worse after declaration, so the global previous-emitted-digit
  payload model remains active.
- post-itemctx_param item-type context family search is now covered by
  [`104_post_itemctx_param_item_type_context_family_search.py`](scripts/104_post_itemctx_param_item_type_context_family_search.py);
  `17024` family/order/alpha candidates are rescored. The active searched split
  at book `6`, order `1`, alpha `2` remains best at `8561.792` bits; the
  nearest alternate is split `9`, order `1`, alpha `2`, still `+1.335` bits
  worse.
- post-itemctx_param payload/item-type pair context search is now covered by
  [`105_post_itemctx_param_payload_item_type_pair_context_search.py`](scripts/105_post_itemctx_param_payload_item_type_pair_context_search.py);
  `77` payload contexts and `17024` item-type candidates form `1310848` pairs.
  The active global payload plus split `6`, order `1`, alpha `2` item-type model
  remains best; the best changed pair is `+0.415` bits worse and the best pair
  with both components changed is `+2.164` bits worse.
- post-itemctx_param copy-length/item-type pair context search is now covered by
  [`106_post_itemctx_param_copy_length_item_type_pair_context_search.py`](scripts/106_post_itemctx_param_copy_length_item_type_pair_context_search.py);
  `79` copy-length contexts and `17024` item-type candidates form `1344896`
  pairs. The active midpoint copy-length plus split `6`, order `1`, alpha `2`
  item-type model remains best; the best changed pair is `+0.415` bits worse
  and the best pair with both components changed is `+2.357` bits worse.
- post-itemctx_param payload/copy-length/item-type triple context search is now
  covered by
  [`107_post_itemctx_param_payload_copy_length_item_type_triple_context_search.py`](scripts/107_post_itemctx_param_payload_copy_length_item_type_triple_context_search.py);
  `77` payload contexts, `79` copy-length contexts, and `17024` item-type
  candidates imply `103556992` triples. Component minima keep the active triple
  best; the best changed triple is `+0.415` bits worse and the best triple with
  all three components changed is `+4.106` bits worse.
- post-itemctx_param copy-length alpha/item-type pair search is now covered by
  [`108_post_itemctx_param_copy_length_alpha_item_type_pair_search.py`](scripts/108_post_itemctx_param_copy_length_alpha_item_type_pair_search.py);
  `4097` copy-length alpha rows and `17024` item-type candidates imply
  `69747328` pairs. Component minima keep the active pair best; the best changed
  pair is `+0.415` bits worse and the best pair with both components changed is
  `+1.804` bits worse.
- post-itemctx_param copy-length alpha/payload pair search is now covered by
  [`109_post_itemctx_param_copy_length_alpha_payload_pair_search.py`](scripts/109_post_itemctx_param_copy_length_alpha_payload_pair_search.py);
  `4097` copy-length alpha rows and `77` literal-payload contexts imply
  `315469` pairs. Component minima keep the active pair best; the best changed
  pair is `+1.389` bits worse and the best pair with both components changed is
  `+3.138` bits worse.
- post-itemctx_param copy-alpha/payload/item-type triple search is now covered by
  [`110_post_itemctx_param_copy_alpha_payload_item_type_triple_search.py`](scripts/110_post_itemctx_param_copy_alpha_payload_item_type_triple_search.py);
  `4097` copy-length alpha rows, `77` literal-payload contexts, and `17024`
  item-type candidates imply `5370544256` triples. Component minima keep the
  active triple best; the best changed triple is `+0.415` bits worse and the
  best triple with all three components changed is `+3.553` bits worse.
- post-itemctx_param copy-length context/shared-alpha resweep is now covered by
  [`111_post_itemctx_param_copy_length_context_alpha_resweep.py`](scripts/111_post_itemctx_param_copy_length_context_alpha_resweep.py);
  `79` copy-length context candidates times `64` shared alpha values test
  `5056` context/alpha rows. The active fixed book-midpoint context with
  shared `alpha=1` remains best; the best context change is `+1.941` bits
  worse and the best alpha change on the active context is `+2.140` bits worse.
- post-itemctx_param literal-payload context/shared-alpha resweep is now covered
  by
  [`112_post_itemctx_param_literal_payload_context_alpha_resweep.py`](scripts/112_post_itemctx_param_literal_payload_context_alpha_resweep.py);
  `77` literal-payload context candidates times `64` shared alpha values test
  `4928` context/alpha rows. The active global previous-emitted-digit payload
  model with shared `alpha=1` remains best; the best context change is
  `+1.749` bits worse and the best alpha change on the active context is
  `+17.859` bits worse.
- post-itemctx_param copy/payload context-alpha pair search is now covered by
  [`113_post_itemctx_param_copy_payload_context_alpha_pair_search.py`](scripts/113_post_itemctx_param_copy_payload_context_alpha_pair_search.py);
  `5056` copy-length context/alpha rows and `4928` literal-payload
  context/alpha rows imply `24915968` pairs. Component minima keep the active
  pair best; the best changed pair is `+1.749` bits worse and the best pair
  with both components changed is `+3.690` bits worse.
- post-itemctx_param copy/payload/item context-alpha triple search is now
  covered by
  [`114_post_itemctx_param_copy_payload_item_context_alpha_triple_search.py`](scripts/114_post_itemctx_param_copy_payload_item_context_alpha_triple_search.py);
  `5056` copy-length context/alpha rows, `4928` literal-payload context/alpha
  rows, and `17024` item-type candidates imply `424169439232` triples.
  Component minima keep the active triple best; the best changed triple is
  `+0.415` bits worse and the best triple with all three components changed is
  `+4.106` bits worse.
- post-itemctx_param address/copy-order pair search is now covered by
  [`115_post_itemctx_param_address_copy_order_pair_search.py`](scripts/115_post_itemctx_param_address_copy_order_pair_search.py);
  `10` address rows and `5` copy-order rows form `50` pairs. The best overall
  pair is `-72.935` bits but is nondecodable because both sides require free
  mode bits; the active pair remains the best decodable row, and the best
  changed decodable pair is `+8.979` bits worse.
- post-itemctx_param address/item-type pair search is now covered by
  [`116_post_itemctx_param_address_item_type_pair_search.py`](scripts/116_post_itemctx_param_address_item_type_pair_search.py);
  `10` address rows and `17024` item-type rows form `170240` pairs. The best
  overall pair is a nondecodable lower bound from literal-seed no-mode
  addressing; the active pair remains the best decodable row, the best changed
  decodable pair is `+0.415` bits worse, and the best decodable pair with both
  components changed is `+9.476` bits worse.
- post-itemctx_param address/payload context-alpha pair search is now covered
  by
  [`117_post_itemctx_param_address_payload_context_alpha_pair_search.py`](scripts/117_post_itemctx_param_address_payload_context_alpha_pair_search.py);
  `10` address rows and `4928` literal-payload context/alpha rows form `49280`
  pairs. The best overall pair is a nondecodable lower bound from literal-seed
  no-mode addressing; the active pair remains the best decodable row, the best
  changed decodable pair is `+1.749` bits worse, and the best decodable pair
  with both components changed is `+10.809` bits worse.
- prequential generation validation is now covered by
  [`118_prequential_generation_model_audit.py`](scripts/118_prequential_generation_model_audit.py);
  the then-active `8561.792` bit formula was frozen as `compression_bound`, not as a
  final authorial method. Across train cutoffs `10/20/35/50/60`, prefix-online
  and prefix-frozen learned-component scoring both beat uniform on every
  holdout, but the result is classified
  `prequential_generation_partial_not_final` because row0/table origin remains
  open and no new structural mechanism is promoted.
- row0/table-origin consolidation is now covered by
  [`119_row0_origin_frontier_audit.py`](scripts/119_row0_origin_frontier_audit.py);
  the indexed matrix, pair-rule, orbit, tape-feature, low-rank, render,
  eye/blink, and provenance tests leave the frontier at
  `row0_origin_frontier_saturated_current_corpus`. This does not solve row0;
  it records that the current corpus has no charged, controlled, holdout-ready
  pair-label formula.
- prequential numeric-order control is now covered by
  [`120_prequential_order_control_audit.py`](scripts/120_prequential_order_control_audit.py);
  the prefix-trained components beat uniform, but random same-size train-book
  sets usually save more bits. The result is classified
  `prequential_predictive_not_numeric_order_specific`: useful learned-component
  evidence, not proof of numeric book-order generation.
- component-level prequential ablation is now covered by
  [`121_prequential_component_ablation_audit.py`](scripts/121_prequential_component_ablation_audit.py);
  copy-length midpoint survives, but literal payload generalizes better with
  previous-one-digit context and item type generalizes better with split-only
  context. The then-active `8561.792` bit code remained the compression bound at that stage, while
  the generation explanation is simplified.
- simplified generation-profile compilation is now covered by
  [`122_simplified_generation_profile_compile.py`](scripts/122_simplified_generation_profile_compile.py);
  the holdout-preferred profile roundtrips `70/70` but costs `8613.581` bits,
  `+51.789` versus the active bound. It is retained as
  `generation_explanation_profile`, not as a stronger compressor.
- split-only item-type formula compilation is now covered by
  [`123_item_type_split_only_formula_compile.py`](scripts/123_item_type_split_only_formula_compile.py);
  the same recipe and forced rules roundtrip `70/70` at `8558.667` bits,
  `3.125` bits below the prior `8561.792` bound. This is promoted as the new
  `compression_bound`, still with `translation_delta: NONE`.
- split-only item-type alpha validation is now covered by
  [`124_item_type_split_only_alpha_resweep.py`](scripts/124_item_type_split_only_alpha_resweep.py);
  `alpha=2` remains best at `8558.667` bits after alpha declaration deltas.
  The nearest alternate is `alpha=1`, `+0.309` bits worse.
- prequential and row0-origin audit is now covered by
  [`125_prequential_and_row0_origin_audit.py`](scripts/125_prequential_and_row0_origin_audit.py);
  the `8558.667` bit bound is frozen as `compression_bound`. Prefix
  future-suffix learned-component scoring beats uniform on all five cutoffs,
  but random same-size train-book controls are usually stronger, so numeric
  order is not promoted. Row0 origin remains exogenous: manual lookup,
  permutation/group, 10x10 grid, order/frequency, external-text, and
  workbook/script-artifact hypotheses yield no charged controlled origin
  formula.
- prequential recipe reparse is now covered by
  [`126_prequential_recipe_reparse_audit.py`](scripts/126_prequential_recipe_reparse_audit.py);
  under frozen train-prefix component counts, a deterministic LZ parser
  roundtrips every future suffix and is cheaper than the active full-corpus
  recipe on all five prefix cutoffs. This strengthens predictive validation of
  the mechanical copy/reference layer, but remains split-specific analysis and
  does not change `compression_bound`.
- prequential recipe reparse controls are now covered by
  [`127_prequential_recipe_reparse_controls.py`](scripts/127_prequential_recipe_reparse_controls.py);
  at cutoffs `20/35/50`, observed suffixes beat random same-length,
  per-book-shuffled, and suffix-pool-shuffled controls. Control gains are
  negative while observed gains remain large and positive, so the audit-126
  signal is not generic LZ behavior on arbitrary same-length decimal strings.
- prequential recipe train-set controls are now covered by
  [`128_prequential_recipe_reparse_trainset_controls.py`](scripts/128_prequential_recipe_reparse_trainset_controls.py);
  at focused cutoff `50`, the numeric prefix beats the random train-set mean
  but not all random inventories (`p(random >= observed)=0.1538`). The reparse
  signal remains predictive, but numeric order is not promoted as an authorial
  generation order.
- deterministic online reparse compilation is now covered by
  [`129_online_deterministic_reparse_compile.py`](scripts/129_online_deterministic_reparse_compile.py);
  the same parser becomes a full-corpus formula, roundtrips `70/70`, and lowers
  `compression_bound` from `8558.667` to `8343.062` bits (`-215.605`), with no
  row0 or semantic claim.
- online reparse order controls are now covered by
  [`130_online_reparse_order_control_audit.py`](scripts/130_online_reparse_order_control_audit.py);
  numeric order remains best among reverse, parity, length-derived, and 6
  seeded random controls. The best random raw order is still `+188.584` bits
  worse before the `log2(70!)` arbitrary-order charge.
- online formula recipe pruning is now covered by
  [`131_online_formula_recipe_prune_audit.py`](scripts/131_online_formula_recipe_prune_audit.py);
  book `length` and copy `target_start` are derivable representation fields.
  Removing them in-memory preserves `8343.062` bits and `70/70` roundtrip.
- canonical online recipe compilation is now covered by
  [`132_canonical_online_recipe_formula_compile.py`](scripts/132_canonical_online_recipe_formula_compile.py);
  it materializes the stripped formula as
  `sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_online_reparse_canonical_formula_469.json`
  with the same `8343.062` bits and no `target_start` or book `length` fields.
- literal-length-derived recipe compilation is now covered by
  [`133_literal_length_derived_recipe_compile.py`](scripts/133_literal_length_derived_recipe_compile.py);
  literal op `length` is derived from `len(text)`, removing 87 more redundant
  fields and preserving `8343.062` bits and `70/70`. Copy `length` remains a
  declared dependency.
- op-type-derived recipe compilation is now covered by
  [`134_op_type_derived_recipe_compile.py`](scripts/134_op_type_derived_recipe_compile.py);
  op `type` is derived from field shape, removing 348 more redundant fields and
  preserving `8343.062` bits and `70/70`. The remaining operation-level
  dependencies are literal text, copy source, and copy length.
- copy-source canonicality is now covered by
  [`135_copy_source_canonicality_audit.py`](scripts/135_copy_source_canonicality_audit.py);
  all 261 declared sources are the earliest legal occurrence of the copied
  chunk at the declared length. This supports a canonical encoder-side source
  rule, but source remains a decoding dependency.
- copy-length default decodability is now covered by
  [`136_copy_length_default_decodability_audit.py`](scripts/136_copy_length_default_decodability_audit.py);
  the tempting encoder-only max-extension rule matches `238/261` copies but is
  not decodable. A decodable `decoder_max_possible` default plus adaptive
  exception ledger lowers copy-length cost from `1485.689` to `1348.806` bits
  after an explicit `8` bit declaration delta, promoting the mechanical bound
  from `8343.062` to `8206.178` bits with `translation_delta: NONE`.
- copy-source default decodability is now covered by
  [`137_copy_source_default_decodability_audit.py`](scripts/137_copy_source_default_decodability_audit.py);
  a decodable previous-source-plus-length default matches only `5/261` sources,
  but combined with a global adaptive exception-source stream and a charged
  `12` bit declaration delta it lowers copy-address cost from `3031.700` to
  `3002.838` bits, promoting the mechanical bound to `8177.317` bits with
  `translation_delta: NONE`.
- literal-payload default decodability is now covered by
  [`138_literal_payload_default_decodability_audit.py`](scripts/138_literal_payload_default_decodability_audit.py);
  modal-default/exception literal digit models are decodable but worse than the
  active categorical previous-emitted-digit order-2 model. The best
  default/exception candidate is `+38.049` bits worse, so no literal-payload
  fallback is promoted.
- literal-payload structural context is now covered by
  [`139_literal_payload_structural_context_audit.py`](scripts/139_literal_payload_structural_context_audit.py);
  literal-run offset, run-length bucket, book half/parity, and bounded
  combinations with `prev2` all over-split the stream. The active categorical
  previous-emitted-digit order-2 model remains best.
- copy-source canonicality controls are now covered by
  [`140_online_copy_source_canonicality_audit.py`](scripts/140_online_copy_source_canonicality_audit.py);
  audit 135's earliest-occurrence rule remains `261/261`, while latest
  occurrence is only `123/261`, previous-source-plus-length is `5/261`, and
  uniform random candidate choice would expect `169.473` hits (`log2 P(all
  earliest)=-236.596`).
- default/exception prequential validation is now covered by
  [`141_default_exception_prequential_validation.py`](scripts/141_default_exception_prequential_validation.py);
  copy-length/source default-exception components have positive online gains
  on all prefix future-suffix splits (`min=43.582` bits), but frozen prefix-10
  scoring loses `-39.773` bits versus legal uniform because copy-source
  prediction is sparse. Family holdouts also include nonpositive failures, so
  this is not a frozen generation method.
- default/exception component profiling is now covered by
  [`142_default_exception_component_profile.py`](scripts/142_default_exception_component_profile.py);
  keep `8177.317` bits as `compression_bound`, but the frozen-prefix
  generation-explanation profile is `8206.178` bits because copy-source
  default/exception is retained only as compression-bound evidence.
- DP plus externally supplied fine physical order remains open only if a source
  gives a non-ambiguous tile/slot/orientation/read-order layer at zero search
  cost.

No semantic or authorial-intent claim is promoted.
