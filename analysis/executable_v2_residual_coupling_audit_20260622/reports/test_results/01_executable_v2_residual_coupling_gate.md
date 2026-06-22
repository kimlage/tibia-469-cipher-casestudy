# Executable v2 Residual Coupling Gate

Classification: `PROMOTED_EXECUTABLE_V2_LEDGER_ONLY`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## A. Executable Ledger v2

Ledger v2 replaces the old uniform coarse-control tape with the promoted online x64 rank/correction tape. All other external tapes remain unchanged.

- Old external bits excluding seed: `4358.858`.
- v2 external bits excluding seed: `4299.595`.
- Reduction excluding seed: `59.263` bits.
- Old external bits including seed: `9992.848`.
- v2 external bits including seed: `9933.585`.

| Tape | Bits |
| --- | ---: |
| online x64 coarse-control rank/correction | `876.412` |
| composition index | `665.782` |
| literal payload | `883.633` |
| copy-hint rank | `1873.768` |
| seed payload | `5633.990` |

## B. Online-State Composition Index Coupling

- Best model: `op_count`.
- Best model bits: `1300.041`.
- Uniform composition bits: `1198.420`.
- Saving: `-101.620` bits.
- Shuffled-train p95 saving: `-9.046` bits.
- Classification: `ONLINE_STATE_COMPOSITION_INDEX_CODEC_NOT_PROMOTED`.

| Model | Bits | Uniform | Saving | Shuffled p95 |
| --- | ---: | ---: | ---: | ---: |
| `op_count` | `1300.041` | `1198.420` | `-101.620` | `-9.046` |
| `online_status_x_opcount` | `1309.107` | `1198.420` | `-110.686` | `-10.111` |
| `online_paid_x_opcount` | `1318.488` | `1198.420` | `-120.067` | `-10.215` |
| `online_status` | `1329.228` | `1198.420` | `-130.807` | `-9.673` |
| `online_rank` | `1331.540` | `1198.420` | `-133.120` | `-9.503` |
| `online_status_x_length` | `1336.461` | `1198.420` | `-138.041` | `-10.903` |
| `global` | `1340.811` | `1198.420` | `-142.391` | `-9.511` |
| `book_length` | `1350.100` | `1198.420` | `-151.680` | `-10.202` |

## Decision

Executable ledger v2 is promoted because it incorporates the online x64 coarse-control reduction. The online state does not promote a further composition-index codec; exact fine length composition remains external.

Remaining external fields: composition index, literal payload, copy-hint rank/source, seed payload, and `row0`.

`row0`, plaintext, translation, and `compression_bound` remain unchanged.
