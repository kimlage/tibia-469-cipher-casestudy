# Online x64 Coarse-Control Program Gate

Classification: `PROMOTED_ONLINE_X64_MINIMAL_LEDGER_REDUCTION`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can the x64 book-level controller run as a one-pass executable coarse-control program for books `10..69`, training only on previous decoded/corrected books?

## Summary

- Sequence hits without correction: `37/60`.
- Exact ops without coarse correction: `78/261`.
- Internal starts generated before correction: `41/201`.
- Online paid coarse bits: `876.412`.
- Explicit op_count+coarse bits: `1175.675`.
- Saving vs explicit op_count+coarse: `299.263` bits.
- Control p95 saving vs explicit: `188.216` bits.
- Current minimal coarse bits: `935.675`.
- Saving vs current minimal coarse ledger: `59.263` bits.
- Control p95 saving vs minimal coarse: `-51.784` bits.
- Coarse+composition after online program: `1542.194`.
- Current minimal coarse+composition ledger: `1601.457`.

## Interpretation

The online x64 controller reduces the current minimal executable coarse ledger after same-multiset controls. This is a real executable-program dependency reduction, while the fine composition index and other tapes remain external.

## Book Rows

| Book | Ops | Rank | Paid Coarse | Explicit Coarse | Minimal Coarse |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `10` | `2` | `MISS` | `11.170` | `11.170` | `7.170` |
| `11` | `6` | `MISS` | `25.510` | `25.510` | `21.510` |
| `12` | `14` | `MISS` | `54.189` | `54.189` | `50.189` |
| `13` | `9` | `MISS` | `36.265` | `36.265` | `32.265` |
| `14` | `8` | `MISS` | `32.680` | `32.680` | `28.680` |
| `15` | `11` | `MISS` | `43.435` | `43.435` | `39.435` |
| `16` | `12` | `MISS` | `47.020` | `47.020` | `43.020` |
| `17` | `12` | `MISS` | `47.020` | `47.020` | `43.020` |
| `18` | `2` | `15` | `3.907` | `11.170` | `7.170` |
| `19` | `3` | `2` | `1.000` | `14.755` | `10.755` |
| `20` | `7` | `MISS` | `29.095` | `29.095` | `25.095` |
| `21` | `3` | `261` | `8.028` | `14.755` | `10.755` |
| `22` | `1` | `8` | `3.000` | `7.585` | `3.585` |
| `23` | `12` | `MISS` | `47.020` | `47.020` | `43.020` |
| `24` | `3` | `102` | `6.672` | `14.755` | `10.755` |
| `25` | `2` | `11` | `3.459` | `11.170` | `7.170` |
| `26` | `4` | `MISS` | `18.340` | `18.340` | `14.340` |
| `27` | `1` | `3` | `1.585` | `7.585` | `3.585` |
| `28` | `5` | `MISS` | `21.925` | `21.925` | `17.925` |
| `29` | `4` | `523` | `9.031` | `18.340` | `14.340` |
| `30` | `6` | `MISS` | `25.510` | `25.510` | `21.510` |
| `31` | `8` | `MISS` | `32.680` | `32.680` | `28.680` |
| `32` | `3` | `82` | `6.358` | `14.755` | `10.755` |
| `33` | `1` | `1` | `0.000` | `7.585` | `3.585` |
| `34` | `9` | `MISS` | `36.265` | `36.265` | `32.265` |
| `35` | `2` | `12` | `3.585` | `11.170` | `7.170` |
| `36` | `6` | `MISS` | `25.510` | `25.510` | `21.510` |
| `37` | `2` | `10` | `3.322` | `11.170` | `7.170` |
| `38` | `5` | `MISS` | `21.925` | `21.925` | `17.925` |
| `39` | `3` | `258` | `8.011` | `14.755` | `10.755` |
| `40` | `4` | `MISS` | `18.340` | `18.340` | `14.340` |
| `41` | `4` | `275` | `8.103` | `18.340` | `14.340` |
| `42` | `7` | `MISS` | `29.095` | `29.095` | `25.095` |
| `43` | `1` | `1` | `0.000` | `7.585` | `3.585` |
| `44` | `2` | `7` | `2.807` | `11.170` | `7.170` |
| `45` | `3` | `71` | `6.150` | `14.755` | `10.755` |
| `46` | `3` | `58` | `5.858` | `14.755` | `10.755` |
| `47` | `1` | `1` | `0.000` | `7.585` | `3.585` |
| `48` | `2` | `4` | `2.000` | `11.170` | `7.170` |
| `49` | `12` | `MISS` | `47.020` | `47.020` | `43.020` |
| `50` | `1` | `1` | `0.000` | `7.585` | `3.585` |
| `51` | `2` | `13` | `3.700` | `11.170` | `7.170` |
| `52` | `2` | `15` | `3.907` | `11.170` | `7.170` |
| `53` | `1` | `1` | `0.000` | `7.585` | `3.585` |
| `54` | `2` | `8` | `3.000` | `11.170` | `7.170` |
| `55` | `4` | `517` | `9.014` | `18.340` | `14.340` |
| `56` | `10` | `MISS` | `39.850` | `39.850` | `35.850` |
| `57` | `8` | `MISS` | `32.680` | `32.680` | `28.680` |
| `58` | `3` | `121` | `6.919` | `14.755` | `10.755` |
| `59` | `3` | `27` | `4.755` | `14.755` | `10.755` |
| `60` | `6` | `MISS` | `25.510` | `25.510` | `21.510` |
| `61` | `2` | `13` | `3.700` | `11.170` | `7.170` |
| `62` | `1` | `1` | `0.000` | `7.585` | `3.585` |
| `63` | `2` | `4` | `2.000` | `11.170` | `7.170` |
| `64` | `2` | `4` | `2.000` | `11.170` | `7.170` |
| `65` | `3` | `90` | `6.492` | `14.755` | `10.755` |
| `66` | `1` | `1` | `0.000` | `7.585` | `3.585` |
| `67` | `1` | `1` | `0.000` | `7.585` | `3.585` |
| `68` | `1` | `1` | `0.000` | `7.585` | `3.585` |
| `69` | `1` | `1` | `0.000` | `7.585` | `3.585` |

## Boundary

`row0`, plaintext, translation, and `compression_bound` remain unchanged. The fine residual composition index, literal payload, copy/source hints, and seed payload remain external or paid.
