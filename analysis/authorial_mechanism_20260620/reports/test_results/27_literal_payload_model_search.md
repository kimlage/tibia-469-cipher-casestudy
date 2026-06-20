# Literal Payload Model Search

Verdict: `controlled_literal_payload_adaptive_improvement`. Translation delta: `NONE`.

This audit keeps the current sequential LZ recipe fixed and tests the
payload cost of literal digits. Length coding, source addresses, book
order, and copy operations are unchanged; only the code for literal
payload digits is varied.

## Payload Models

| Model | Payload bits | Model bits | Total bits | Delta vs current | Decodable |
|---|---:|---:|---:|---:|---:|
| `static_literal_histogram_oracle_no_table` | `2606.0` | `0` | `9513.9` | `-31.7` | `False` |
| `adaptive_dirichlet_alpha_14` | `2623.1` | `7` | `9538.0` | `-7.5` | `True` |
| `uniform_decimal_payload` | `2637.6` | `0` | `9545.5` | `0.0` | `True` |
| `static_literal_histogram_with_counts` | `2606.0` | `145` | `9658.9` | `113.3` | `True` |

## Controls

| Control | Runs | Min delta | Mean delta | Count <= observed |
|---|---:|---:|---:|---:|
| `random_uniform_literal_payloads` | `200` | `5.4` | `12.6` | `0` |

## Interpretation

The best decodable payload model is adaptive Dirichlet with
`alpha=14`. After charging
`7` bits to declare alpha,
it improves the current formula by
`7.5` bits.
The static histogram oracle is cheaper but not promoted because it
omits a decodable table; the charged static table is worse.

## Boundary

This is a mechanical literal-payload coding audit only. It does not
alter row0, introduce plaintext, or make an authorial-intent claim.
