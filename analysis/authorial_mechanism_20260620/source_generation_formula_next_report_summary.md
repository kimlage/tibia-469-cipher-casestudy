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
- DP plus externally supplied fine physical order remains open only if a source
  gives a non-ambiguous tile/slot/orientation/read-order layer at zero search
  cost.

No semantic or authorial-intent claim is promoted.
