# Post-Itemctx Param Address/Copy-Order Pair Search

Verdict: `post_itemctx_param_address_copy_order_pair_optimistic_only_not_promoted`. Translation delta: `NONE`.

This audit combines the post-itemctx_param address-model frontier with
the copy-order frontier. A pair can promote only if both sides are
decodable. Rows that rely on literal-seed source-mode bits or per-copy
copy-order mode bits being free remain optimistic lower bounds.

## Coverage

- Address candidates: `10`
- Copy-order candidates: `5`
- Pair candidates proven by component minima: `50`

## Top Pairs

| Rank | Address model | Order model | Decodable | Total bits | Delta |
|---:|---|---|---:|---:|---:|
| `1` | `literal_seed_address_optimistic_no_mode` | `best_midpoint_alpha1_copy_order_optimistic_no_mode` | `False` | `8488.857` | `-72.935` |
| `2` | `literal_seed_address_optimistic_no_mode` | `source_first_then_midpoint_alpha1_length_active` | `False` | `8492.396` | `-69.396` |
| `3` | `literal_seed_address_optimistic_no_mode` | `midpoint_alpha1_copy_order_sparse_run_list_length_first_required` | `False` | `8501.375` | `-60.417` |
| `4` | `literal_seed_address_optimistic_no_mode` | `midpoint_alpha1_length_first_then_source` | `False` | `8504.590` | `-57.202` |
| `5` | `absolute_digit_source_pos_min_len_bounded` | `best_midpoint_alpha1_copy_order_optimistic_no_mode` | `False` | `8558.253` | `-3.539` |
| `6` | `absolute_digit_source_pos_min_len_bounded` | `source_first_then_midpoint_alpha1_length_active` | `True` | `8561.792` | `-0.000` |
| `7` | `literal_seed_sparse_run_list_seed_required` | `best_midpoint_alpha1_copy_order_optimistic_no_mode` | `False` | `8567.313` | `5.521` |
| `8` | `absolute_digit_source_pos_min_len_bounded` | `midpoint_alpha1_copy_order_sparse_run_list_length_first_required` | `True` | `8570.771` | `8.979` |
| `9` | `literal_seed_sparse_run_list_seed_required` | `source_first_then_midpoint_alpha1_length_active` | `True` | `8570.852` | `9.060` |
| `10` | `absolute_digit_source_pos_min_len_bounded` | `midpoint_alpha1_length_first_then_source` | `True` | `8573.986` | `12.194` |
| `11` | `literal_seed_sparse_run_list_seed_required` | `midpoint_alpha1_copy_order_sparse_run_list_length_first_required` | `True` | `8579.831` | `18.039` |
| `12` | `literal_seed_sparse_run_list_seed_required` | `midpoint_alpha1_length_first_then_source` | `True` | `8583.046` | `21.255` |
| `13` | `literal_seed_address_conservative_mode_per_copy` | `best_midpoint_alpha1_copy_order_optimistic_no_mode` | `False` | `8771.857` | `210.065` |
| `14` | `literal_seed_address_optimistic_no_mode` | `midpoint_alpha1_copy_order_mode_per_copy` | `False` | `8771.857` | `210.065` |
| `15` | `literal_seed_address_conservative_mode_per_copy` | `source_first_then_midpoint_alpha1_length_active` | `True` | `8775.396` | `213.604` |
| `16` | `literal_seed_address_conservative_mode_per_copy` | `midpoint_alpha1_copy_order_sparse_run_list_length_first_required` | `True` | `8784.375` | `222.583` |
| `17` | `literal_seed_address_conservative_mode_per_copy` | `midpoint_alpha1_length_first_then_source` | `True` | `8787.590` | `225.798` |
| `18` | `absolute_digit_source_pos_min_len_bounded` | `midpoint_alpha1_copy_order_mode_per_copy` | `True` | `8841.253` | `279.461` |
| `19` | `literal_seed_sparse_run_list_seed_required` | `midpoint_alpha1_copy_order_mode_per_copy` | `True` | `8850.313` | `288.521` |
| `20` | `literal_seed_address_conservative_mode_per_copy` | `midpoint_alpha1_copy_order_mode_per_copy` | `True` | `9054.857` | `493.065` |

## Best Decodable Pair

- Delta vs current: `-0.000` bits
- Address: `absolute_digit_source_pos_min_len_bounded`
- Copy order: `source_first_then_midpoint_alpha1_length_active`

## Best Changed Decodable Pair

- Delta vs current: `8.979` bits
- Address: `absolute_digit_source_pos_min_len_bounded`
- Copy order: `midpoint_alpha1_copy_order_sparse_run_list_length_first_required`

## Best Decodable Pair With Both Components Changed

- Delta vs current: `18.039` bits
- Address: `literal_seed_sparse_run_list_seed_required`
- Copy order: `midpoint_alpha1_copy_order_sparse_run_list_length_first_required`

## Interpretation

The best overall pair is an optimistic lower bound because it combines
no-mode address and no-mode copy-order rows. The best decodable pair is
the active ledger, and every changed decodable pair is worse after mode
and declaration costs.

## Boundary

This is a mechanical copy-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
