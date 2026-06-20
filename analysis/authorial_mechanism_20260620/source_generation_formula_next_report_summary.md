---
title: "Research summary: generation formula next steps"
date: 2026-06-20
source_note: "/Users/sargam/Downloads/469_generation_formula_next_report.md"
status: incorporated_as_generation_tests
translation_delta: NONE
---

# Research Summary: Generation Formula Next Steps

The report reviewed the current public `main` state and proposed the next
mechanical improvements for the 70-book generator. Its central recommendation
was to replace the greedy sequential LZ parser with a dynamic-programming
parser under the final run-literal cost.

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

Still open from the report:

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
- DP plus externally supplied fine physical order remains open only if a source
  gives a non-ambiguous tile/slot/orientation/read-order layer at zero search
  cost.

No semantic or authorial-intent claim is promoted.
