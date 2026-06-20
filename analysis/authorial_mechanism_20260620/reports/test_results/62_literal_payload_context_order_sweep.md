# Literal Payload Context Order Sweep

Verdict: `controlled_literal_payload_context_order_improvement`. Translation delta: `NONE`.

This audit keeps the full book recipe and every non-payload ledger fixed
after the promoted previous-emitted-digit literal payload model. It tests
whether longer deterministic contexts over the already emitted digit stream
reduce the final literal payload cost.

The active order-1 context is included as the baseline. Higher orders are
charged for alpha, the context family, and a declared context-order cost.

## Model Ranking

| Rank | Order | Alpha | Payload bits | Model bits | Total bits | Delta vs active | Contexts |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `1` | `2` | `1` | `2449.6` | `9` | `8805.7` | `-36.3` | `98` |
| `2` | `1` | `2` | `2488.9` | `6` | `8842.0` | `0.0` | `11` |
| `3` | `3` | `1` | `2517.3` | `9` | `8873.4` | `31.3` | `399` |
| `4` | `4` | `1` | `2569.2` | `11` | `8927.2` | `85.2` | `597` |
| `5` | `5` | `1` | `2578.0` | `11` | `8936.1` | `94.1` | `672` |

## Interpretation

The active contextual formula remains `8842.0` bits before
this sweep. A higher-order model is promoted only if it beats that
active order-1 context after all declaration bits are charged.

This is a mechanical payload-coding audit only. It does not change row0,
introduce plaintext, or claim authorial intent.

## Promoted Formula

- [`sequential_lz_digit_address_forced_length_literal_context_order_formula_469.json`](../../sequential_lz_digit_address_forced_length_literal_context_order_formula_469.json)
