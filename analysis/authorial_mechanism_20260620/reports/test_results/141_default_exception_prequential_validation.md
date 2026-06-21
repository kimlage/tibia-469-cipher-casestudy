# 141. Default/Exception Prequential Validation

Classification: `default_exception_components_partial_under_family_holdout`
Translation delta: `NONE`

## Purpose

Audits 136 and 137 promoted copy-length and copy-source
default/exception ledgers. This audit asks whether those components
predict held-out books with frozen train counts, or whether the gains
are only full-corpus compression. It does not search new parameters.
Frozen mode uses counts learned on train books and scores test books
without updating those counts.

## Prefix Future-Suffix Splits

| Split | Train books | Test books | Online gain | Frozen gain | Copy-length online | Copy-source online |
|---|---:|---:|---:|---:|---:|---:|
| `prefix_10_future_suffix` | `10` | `60` | `233.881` | `199.839` | `190.230` | `43.651` |
| `prefix_20_future_suffix` | `20` | `50` | `191.097` | `167.550` | `153.083` | `38.014` |
| `prefix_35_future_suffix` | `35` | `35` | `137.077` | `121.530` | `101.760` | `35.318` |
| `prefix_50_future_suffix` | `50` | `20` | `75.207` | `74.726` | `65.095` | `10.113` |
| `prefix_60_future_suffix` | `60` | `10` | `51.534` | `50.303` | `40.392` | `11.142` |

## Summary

- Prefix online gain summary: `{'n': 5, 'min': 51.53433983036683, 'median': 137.07744945441254, 'mean': 137.75938634918037, 'max': 233.88111965474718}`
- Prefix frozen gain summary: `{'n': 5, 'min': 50.302730582122905, 'median': 121.5303299043137, 'mean': 122.78966005404541, 'max': 199.83900181130048}`
- Block online gain summary: `{'n': 7, 'min': 24.959167664009897, 'median': 42.9048309898256, 'mean': 41.20574002264957, 'max': 51.53433983036683}`
- Family online gain summary: `{'n': 19, 'min': -5.351156193906689, 'median': 10.934414114000738, 'mean': 10.120841240998361, 'max': 22.619155162922247}`
- Family nonpositive failures: `[{'label': 'hellgate_public_bookcase_36', 'online_gain_vs_uniform_bits': -5.351156193906689, 'frozen_gain_vs_uniform_bits': -5.227183905684541, 'component_gain_vs_uniform_bits': {'copy_length_online': -5.880750869392543, 'copy_length_frozen': -5.777389537607576, 'copy_source_online': 0.5295946754858534, 'copy_source_frozen': 0.5502056319230348}}, {'label': 'hellgate_public_bookcase_7', 'online_gain_vs_uniform_bits': -1.0591732952756274, 'frozen_gain_vs_uniform_bits': -0.7945983095106612, 'component_gain_vs_uniform_bits': {'copy_length_online': -0.021790231005255123, 'copy_length_frozen': 0.24113412697239767, 'copy_source_online': -1.0373830642703865, 'copy_source_frozen': -1.0357324364831015}}]`

## Decision

The default/exception components retain prefix predictive value but have family-holdout failures, so they remain partial generation evidence rather than a final authorial method.

## Boundary

- No compression-bound change is introduced here.
- No plaintext or translation is introduced.
- Row0/table origin is unchanged.
