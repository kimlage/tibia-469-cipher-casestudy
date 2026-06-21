# 139. Literal Payload Structural Context Audit

Classification: `literal_payload_structural_context_not_promoted`
Translation delta: `NONE`

## Purpose

Audit 138 rejected modal default/exception literal payload models. This
audit tests a separate bounded family: whether structural context inside
literal runs improves the active previous-emitted-digit order-2 payload
model. Tested contexts include literal-run offset, run-length bucket, book
half/parity, and small combinations with the active `prev2` context.

## Result

- Active total bits: `8177.317`
- Active literal-payload bits: `2613.661`
- Literal digits: `857`
- Best candidate: `active_prev2`
- Best candidate bits: `2613.661`
- Delta vs active literal payload: `0.000` bits

| Rank | Candidate | Contexts | Stream bits | Decl bits | Total bits | Delta vs active |
|---:|---|---:|---:|---:|---:|---:|
| `1` | `active_prev2` | `98` | `2613.661` | `0.0` | `2613.661` | `0.000` |
| `2` | `prev2_plus_book_half` | `152` | `2628.820` | `4.0` | `2632.820` | `19.159` |
| `3` | `prev2_plus_offset_first_rest` | `148` | `2632.914` | `4.0` | `2636.914` | `23.253` |
| `4` | `prev2_plus_half_plus_offset_first_rest` | `201` | `2652.850` | `8.0` | `2660.850` | `47.189` |
| `5` | `prev2_plus_book_parity` | `184` | `2679.773` | `4.0` | `2683.773` | `70.112` |
| `6` | `prev2_plus_offset_4bucket` | `239` | `2685.429` | `6.0` | `2691.429` | `77.768` |
| `7` | `prev2_plus_run_length_bucket` | `240` | `2716.692` | `6.0` | `2722.692` | `109.031` |
| `8` | `prev1_plus_offset_first_rest` | `21` | `2725.173` | `4.0` | `2729.173` | `115.512` |
| `9` | `global_plus_offset_first_rest` | `2` | `2850.956` | `4.0` | `2854.956` | `241.295` |

## Decision

- No structural literal-payload context is promoted.
- Literal-run offset, run-length bucket, book half/parity, and their bounded combinations all over-split the literal stream.
- The active categorical previous-emitted-digit order-2 model remains the best tested literal-payload mechanism.
- `translation_delta`: `NONE`; row0/table origin is unchanged.
