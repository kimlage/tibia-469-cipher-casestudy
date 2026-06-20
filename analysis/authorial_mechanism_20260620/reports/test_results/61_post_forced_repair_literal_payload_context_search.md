# Post-Forced-Repair Literal Payload Context Search

Verdict: `controlled_literal_payload_context_improvement`. Translation delta: `NONE`.

This audit incorporates the follow-up generation-formula report as a
frontier check rather than as a stale baseline. The report's major
recommendations were already tested in scripts `13` through `60`; this
script tests one remaining natural refinement: whether the final literal
payload is cheaper when coded by a decodable previous-digit context.

The recipe, copy addresses, item-type ledger, book-length ledger, forced
literal-length rule, and local repair are fixed. Only the literal payload
model is replaced. Candidate totals subtract the current payload plus its
declared model bits and add the contextual payload plus charged alpha and
context-family bits.

## Model Ranking

| Rank | Model | Alpha | Payload bits | Model bits | Total bits | Delta vs active | Contexts |
|---:|---|---:|---:|---:|---:|---:|---:|
| `1` | `adaptive_prev_emitted_digit` | `2` | `2488.9` | `6` | `8842.0` | `-80.8` | `11` |
| `2` | `adaptive_prev_literal_digit_run_reset` | `2` | `2500.5` | `6` | `8853.6` | `-69.2` | `11` |
| `3` | `adaptive_prev_literal_digit_book_reset` | `3` | `2507.5` | `8` | `8862.6` | `-60.2` | `11` |
| `4` | `adaptive_prev_literal_digit_global` | `3` | `2516.1` | `7` | `8870.2` | `-52.6` | `11` |
| `5` | `adaptive_dirichlet_zero_order_current` | `14` | `2568.7` | `7` | `8922.8` | `0.0` | `1` |

## Interpretation

The active formula remains `8922.8` bits. Its
literal payload costs `2568.7` bits plus
`7` declaration bits at `alpha=14`.
The best contextual candidate is `adaptive_prev_emitted_digit` at
`8842.0` bits.

A contextual model can only promote if it is decodable and beats the
current zero-order payload after declaration cost. This test does not
promote plaintext, row0 meaning, physical order, or authorial intent.

## Promoted Formula

The best contextual payload model is decodable from the already
generated stream, beats the active zero-order literal payload after
charged declaration bits, and therefore emits a new mechanical
formula artifact:

- [`sequential_lz_digit_address_forced_length_literal_context_formula_469.json`](../../sequential_lz_digit_address_forced_length_literal_context_formula_469.json)
