# Deep Statistical Exhaustion

Verdict: `source_family_closed_negative`. Translation delta: `NONE`.

This suite adds direct statistical probes beyond the earlier wrapper audits:
source-number exact hits, external-string coverage, seed-derived row0
feature models, book phase/motif tests, and identity-anchor co-occurrence.

## Source Number Exact Hits

| Seed | Hits | Tape hits | Random p>= | Multiset p>= | Class |
|---|---:|---:|---:|---:|---|
| `3478` | 24 | 4 | 0.0155 | 0.0385 | `rejected_control` |
| `486486` | 0 | 0 | 1.0000 | 1.0000 | `absent_or_blocked` |
| `486` | 0 | 0 | 1.0000 | 1.0000 | `absent_or_blocked` |
| `3478468486` | 0 | 0 | 1.0000 | 1.0000 | `absent_or_blocked` |
| `4864863478` | 0 | 0 | 1.0000 | 1.0000 | `absent_or_blocked` |
| `74032` | 0 | 0 | 1.0000 | 1.0000 | `absent_or_blocked` |
| `45331` | 0 | 0 | 1.0000 | 1.0000 | `absent_or_blocked` |
| `469` | 1 | 0 | 0.6402 | 0.6507 | `rejected_control` |
| `43153` | 0 | 0 | 1.0000 | 1.0000 | `absent_or_blocked` |
| `34784` | 0 | 0 | 1.0000 | 1.0000 | `absent_or_blocked` |
| `3700` | 0 | 0 | 1.0000 | 1.0000 | `absent_or_blocked` |
| `99` | 112 | 22 | 0.4778 | 1.0000 | `rejected_control` |
| `1` | 1869 | 349 | 0.1729 | 1.0000 | `rejected_control` |
| `0` | 855 | 157 | 0.9415 | 1.0000 | `rejected_control` |

## External Coverage

| Source | Covered | Random p>= | Multiset p>= | Class |
|---|---:|---:|---:|---|
| `chayenne` | 0.918 | 0.0005 | 0.0005 | `copy_holdout_like_secondary_validation` |
| `your_true_colour` | 0.000 | 1.0000 | 1.0000 | `external_anchor_not_supported` |
| `avar_tar` | 0.087 | 0.4738 | 0.1874 | `negative_control_leaky_short_substrings` |
| `secret_library_74032_45331` | 0.000 | 1.0000 | 1.0000 | `external_anchor_not_supported` |
| `honeminas_vectors` | 0.000 | 1.0000 | 1.0000 | `external_anchor_not_supported` |
| `knightmare_phrase` | 0.000 | 1.0000 | 1.0000 | `external_anchor_not_supported` |
| `elder_evil_eye` | 0.000 | 1.0000 | 1.0000 | `external_anchor_not_supported` |

## Seed-Derived Row0 Models

| Seed | Best family | Accuracy | Random p>= | Class |
|---|---|---:|---:|---|
| `3478` | `rank_sum_mod14` | 0.400 | 0.5792 | `rejected_control` |
| `486486` | `rank_sum_mod14` | 0.418 | 0.2924 | `rejected_control` |
| `486` | `rank_sum_mod14` | 0.418 | 0.3383 | `rejected_control` |
| `3478468486` | `rank_sum_mod14` | 0.382 | 0.8251 | `rejected_control` |
| `4864863478` | `rank_sum_mod14` | 0.436 | 0.1359 | `rejected_control` |
| `74032` | `rank_product_mod10` | 0.400 | 0.5782 | `rejected_control` |
| `45331` | `rank_sum_mod14` | 0.400 | 0.5657 | `rejected_control` |
| `469` | `rank_distance` | 0.382 | 0.8416 | `rejected_control` |
| `43153` | `rank_product_mod10` | 0.400 | 0.5712 | `rejected_control` |
| `34784` | `rank_sum_mod14` | 0.400 | 0.5502 | `rejected_control` |
| `3700` | `rank_sum_mod14` | 0.418 | 0.3283 | `rejected_control` |

## Book Phase / Quest Motif Tests

| Motif | Best metric | Observed | Random p>= | Class |
|---|---|---:|---:|---|
| `dreamer_duality_parity` | `module_digits` | 0.008 | 0.4508 | `rejected_control` |
| `yalahar_quarters_mod4` | `item_count` | 0.027 | 0.6167 | `rejected_control` |
| `poi_thrones_mod7` | `module_digits` | 0.158 | 0.0800 | `rejected_control` |
| `poi_14_symbols_mod14` | `tape_spans` | 0.276 | 0.1294 | `rejected_control` |
| `secret_library_table7_phase` | `tape_spans` | 0.167 | 0.2044 | `rejected_control` |

## Row0 Anomaly / E-Layer Statistics

| Feature | Cells | E rate | Random p>= | Class |
|---|---:|---:|---:|---|
| `tridiag_diagonal_e` | 10 | 0.500 | 0.0220 | `rejected_control` |
| `tridiag_33_66_anchor` | 2 | 1.000 | 0.0350 | `rejected_control` |
| `high_block_e_pressure` | 10 | 0.300 | 0.3233 | `rejected_control` |
| `donina_missing_39_or_93` | 1 | 0.000 | 1.0000 | `rejected_control` |
| `subjective_19_91_conflict` | 1 | 0.000 | 1.0000 | `rejected_control` |
| `zero_touch` | 10 | 0.000 | 1.0000 | `rejected_control` |
| `six_nine_orbit_touch` | 19 | 0.105 | 0.9505 | `rejected_control` |

## Identity Co-Occurrence

| Pair | Books with both | Multiset p>= | Class |
|---|---:|---:|---|
| `3478 / 486486` | 0 | 1.0000 | `rejected_control` |
| `3478 / 74032` | 0 | 1.0000 | `rejected_control` |
| `3478 / 45331` | 0 | 1.0000 | `rejected_control` |
| `3478 / 43153` | 0 | 1.0000 | `rejected_control` |
| `3478 / 34784` | 0 | 1.0000 | `rejected_control` |
| `3478 / 469` | 0 | 1.0000 | `rejected_control` |
| `486486 / 74032` | 0 | 1.0000 | `rejected_control` |
| `486486 / 45331` | 0 | 1.0000 | `rejected_control` |
| `486486 / 43153` | 0 | 1.0000 | `rejected_control` |
| `486486 / 34784` | 0 | 1.0000 | `rejected_control` |
| `486486 / 469` | 0 | 1.0000 | `rejected_control` |
| `74032 / 45331` | 0 | 1.0000 | `rejected_control` |
| `74032 / 43153` | 0 | 1.0000 | `rejected_control` |
| `74032 / 34784` | 0 | 1.0000 | `rejected_control` |
| `74032 / 469` | 0 | 1.0000 | `rejected_control` |
| `45331 / 43153` | 0 | 1.0000 | `rejected_control` |
| `45331 / 34784` | 0 | 1.0000 | `rejected_control` |
| `45331 / 469` | 0 | 1.0000 | `rejected_control` |
| `43153 / 34784` | 0 | 1.0000 | `rejected_control` |
| `43153 / 469` | 0 | 1.0000 | `rejected_control` |
| `34784 / 469` | 0 | 1.0000 | `rejected_control` |

## Conclusion

No test beats the current promoted mechanical baselines or supplies official
ground truth. Some short seeds such as `3478` are corpus-common, but the
controls classify them as structural overlap rather than a usable key.
Chayenne remains the only strong copy-holdout-like external string; Avar
Tar remains leaky at short substring lengths and is not validation. E-layer
features can be weak local clues, but they do not create a row0 formula.
