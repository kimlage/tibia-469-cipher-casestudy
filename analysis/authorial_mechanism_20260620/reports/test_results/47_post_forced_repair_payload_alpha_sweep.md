# Post-Forced-Repair Payload Alpha Sweep

Verdict: `post_forced_repair_payload_alpha_retains_14`. Translation delta: `NONE`.

This audit retests the adaptive literal-payload `alpha` parameter after
the forced-length literal-to-copy repair changed the literal payload
stream. The recipe, copy model, item-type ledger, forced literal-length
rule, literal-run length model, book-length ledger, and digit-only
address model are fixed; only the declared integer alpha is swept.

## Best Alpha Values

| Rank | Alpha | Payload bits | Model bits | Payload+model bits | Delta vs current alpha |
|---:|---:|---:|---:|---:|---:|
| `1` | `14` | `2568.7` | `7` | `2575.7` | `0.0` |
| `2` | `13` | `2568.8` | `7` | `2575.8` | `0.1` |
| `3` | `12` | `2569.0` | `7` | `2576.0` | `0.2` |
| `4` | `6` | `2571.0` | `5` | `2576.0` | `0.3` |
| `5` | `11` | `2569.1` | `7` | `2576.1` | `0.4` |
| `6` | `10` | `2569.3` | `7` | `2576.3` | `0.6` |
| `7` | `9` | `2569.6` | `7` | `2576.6` | `0.9` |
| `8` | `5` | `2571.7` | `5` | `2576.7` | `1.0` |
| `9` | `8` | `2570.0` | `7` | `2577.0` | `1.2` |
| `10` | `7` | `2570.4` | `7` | `2577.4` | `1.7` |
| `11` | `19` | `2568.6` | `9` | `2577.6` | `1.8` |
| `12` | `18` | `2568.6` | `9` | `2577.6` | `1.8` |
| `13` | `20` | `2568.6` | `9` | `2577.6` | `1.8` |
| `14` | `17` | `2568.6` | `9` | `2577.6` | `1.8` |
| `15` | `21` | `2568.6` | `9` | `2577.6` | `1.9` |
| `16` | `16` | `2568.6` | `9` | `2577.6` | `1.9` |

## Interpretation

The current formula uses `alpha=14`. The best swept value
is `alpha=14` with payload-plus-model cost
`2575.7` bits. No formula is
promoted if the current alpha remains best.

## Boundary

This is a mechanical parameter audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
