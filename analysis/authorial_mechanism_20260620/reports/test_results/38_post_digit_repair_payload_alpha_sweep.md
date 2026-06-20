# Post-Digit-Repair Payload Alpha Sweep

Verdict: `post_digit_repair_payload_alpha_retains_14`. Translation delta: `NONE`.

This audit retests the adaptive literal-payload `alpha` parameter after
the digit-address literal-to-copy repair changed the literal payload
stream. The recipe, copy model, literal-run length model, book-length
ledger, and digit-only address model are fixed; only the declared
integer alpha is swept.

## Best Alpha Values

| Rank | Alpha | Payload bits | Model bits | Payload+model bits | Delta vs current alpha |
|---:|---:|---:|---:|---:|---:|
| `1` | `14` | `2585.0` | `7` | `2592.0` | `0.0` |
| `2` | `13` | `2585.1` | `7` | `2592.1` | `0.1` |
| `3` | `12` | `2585.2` | `7` | `2592.2` | `0.2` |
| `4` | `6` | `2587.2` | `5` | `2592.2` | `0.2` |
| `5` | `11` | `2585.4` | `7` | `2592.4` | `0.4` |
| `6` | `10` | `2585.6` | `7` | `2592.6` | `0.6` |
| `7` | `9` | `2585.8` | `7` | `2592.8` | `0.9` |
| `8` | `5` | `2588.0` | `5` | `2593.0` | `1.0` |
| `9` | `8` | `2586.2` | `7` | `2593.2` | `1.2` |
| `10` | `7` | `2586.6` | `7` | `2593.6` | `1.7` |
| `11` | `19` | `2584.8` | `9` | `2593.8` | `1.8` |
| `12` | `18` | `2584.8` | `9` | `2593.8` | `1.8` |
| `13` | `20` | `2584.8` | `9` | `2593.8` | `1.8` |
| `14` | `17` | `2584.8` | `9` | `2593.8` | `1.9` |
| `15` | `21` | `2584.8` | `9` | `2593.8` | `1.9` |
| `16` | `16` | `2584.9` | `9` | `2593.9` | `1.9` |

## Interpretation

The current formula uses `alpha=14`. The best swept value
is `alpha=14` with payload-plus-model cost
`2592.0` bits. No formula is
promoted if the current alpha remains best.

## Boundary

This is a mechanical parameter audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
