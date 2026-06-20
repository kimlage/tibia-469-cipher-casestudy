# Post-Repair Payload Alpha Sweep

Verdict: `post_repair_payload_alpha_retains_14`. Translation delta: `NONE`.

This audit retests the adaptive literal-payload `alpha` parameter after
the one-step literal-to-copy repair changed the literal payload stream.
The recipe, copy model, literal-run length model, and address model are
fixed; only the declared integer alpha is swept.

## Best Alpha Values

| Rank | Alpha | Payload bits | Model bits | Payload+model bits | Delta vs current alpha |
|---:|---:|---:|---:|---:|---:|
| `1` | `14` | `2601.9` | `7` | `2608.9` | `0.0` |
| `2` | `13` | `2602.0` | `7` | `2609.0` | `0.1` |
| `3` | `12` | `2602.1` | `7` | `2609.1` | `0.2` |
| `4` | `6` | `2604.2` | `5` | `2609.2` | `0.3` |
| `5` | `11` | `2602.3` | `7` | `2609.3` | `0.4` |
| `6` | `10` | `2602.5` | `7` | `2609.5` | `0.6` |
| `7` | `9` | `2602.8` | `7` | `2609.8` | `0.9` |
| `8` | `5` | `2605.0` | `5` | `2610.0` | `1.0` |
| `9` | `8` | `2603.2` | `7` | `2610.2` | `1.3` |
| `10` | `7` | `2603.6` | `7` | `2610.6` | `1.7` |
| `11` | `19` | `2601.7` | `9` | `2610.7` | `1.8` |
| `12` | `18` | `2601.7` | `9` | `2610.7` | `1.8` |
| `13` | `20` | `2601.7` | `9` | `2610.7` | `1.8` |
| `14` | `17` | `2601.7` | `9` | `2610.7` | `1.8` |
| `15` | `21` | `2601.7` | `9` | `2610.7` | `1.8` |
| `16` | `22` | `2601.8` | `9` | `2610.8` | `1.9` |

## Interpretation

The current formula uses `alpha=14`. The best swept value
is `alpha=14` with payload-plus-model cost
`2608.9` bits. No formula is
promoted if the current alpha remains best.

## Boundary

This is a mechanical parameter audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
