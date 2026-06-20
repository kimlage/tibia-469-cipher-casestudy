# Literal Run Length Code Reparse

Verdict: `controlled_literal_length_code_improvement`. Translation delta: `NONE`.

This audit reparses the promoted Rice-length sequential LZ formula while
keeping copy-source addressing and copy-length coding fixed. It varies
only the code used for literal-run lengths, including gamma, delta,
unary, and Rice `k=0..10` with explicit parameter cost.

## Literal-Length Sweep

| Rank | min_len | Copy length | Literal length | Model bits | Total bits | Delta vs current | Copy items | Literal runs | Literal digits | Literal length bits | Roundtrip |
|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `1` | `5` | `rice_k4` | `rice_k3` | `10` | `9545.5` | `-51.0` | `279` | `83` | `794` | `396` | `70/70` |
| `2` | `5` | `rice_k4` | `rice_k2` | `8` | `9552.2` | `-44.3` | `286` | `90` | `756` | `418` | `70/70` |
| `3` | `4` | `rice_k4` | `rice_k3` | `10` | `9554.6` | `-41.9` | `284` | `78` | `775` | `376` | `70/70` |
| `4` | `6` | `rice_k4` | `rice_k3` | `10` | `9558.5` | `-38.0` | `268` | `85` | `849` | `413` | `70/70` |
| `5` | `4` | `rice_k4` | `rice_k2` | `8` | `9562.2` | `-34.3` | `290` | `86` | `740` | `402` | `70/70` |
| `6` | `3` | `rice_k4` | `rice_k3` | `10` | `9563.6` | `-32.9` | `284` | `78` | `775` | `376` | `70/70` |
| `7` | `6` | `rice_k4` | `rice_k2` | `8` | `9570.4` | `-26.1` | `272` | `89` | `825` | `435` | `70/70` |
| `8` | `3` | `rice_k4` | `rice_k2` | `8` | `9571.2` | `-25.3` | `290` | `86` | `740` | `402` | `70/70` |
| `9` | `5` | `rice_k4` | `rice_k4` | `10` | `9582.2` | `-14.4` | `275` | `76` | `822` | `406` | `70/70` |
| `10` | `4` | `rice_k4` | `rice_k4` | `10` | `9585.6` | `-10.9` | `281` | `70` | `798` | `376` | `70/70` |
| `11` | `3` | `rice_k4` | `rice_k4` | `10` | `9593.4` | `-3.2` | `283` | `68` | `792` | `366` | `70/70` |
| `12` | `6` | `rice_k4` | `rice_k4` | `10` | `9594.8` | `-1.7` | `262` | `80` | `885` | `431` | `70/70` |
| `13` | `5` | `rice_k4` | `gamma` | `5` | `9596.5` | `0.0` | `278` | `77` | `808` | `417` | `70/70` |
| `14` | `4` | `rice_k4` | `gamma` | `5` | `9600.0` | `3.5` | `284` | `71` | `784` | `387` | `70/70` |
| `15` | `3` | `rice_k4` | `gamma` | `5` | `9607.7` | `11.2` | `286` | `69` | `778` | `377` | `70/70` |
| `16` | `7` | `rice_k4` | `rice_k3` | `10` | `9609.8` | `13.3` | `251` | `83` | `948` | `417` | `70/70` |

## Focused Controls

| Control | Runs | Min bits | Mean bits | Count <= observed |
|---|---:|---:|---:|---:|
| `digit_shuffle_preserve_book_lengths` | `20` | `40169.1` | `40182.5` | `0` |
| `book_order_shuffle` | `20` | `9574.6` | `9777.7` | `0` |

## Interpretation

The best tested literal-length model is `rice_k3`
with `min_len=5`, reaching `9545.5`
bits. The previous Rice-length formula costs `9596.5`
bits, so the controlled delta is `-51.0`
bits with 70/70 roundtrip.

## Boundary

This is a mechanical literal-length coding audit only. It does not
alter row0, introduce plaintext, or make an authorial-intent claim.
