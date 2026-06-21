# Final Literal Payload Generation Audit

Status: `analysis_only`
Classification: `LITERAL_PAYLOAD_GENERATOR_REJECTED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

After granting the exact source-free skeleton, can the remaining
`53` literal chunks / `266` literal digits be generated from
source-free contexts rather than declared as payload?

## Payload Ledger

- Literal chunks/digits: `53` / `266`.
- Unique payload chunks: `49`.
- Repeated literal payload rows/digits: `8` / `10`.
- Whole chunks already seen in emitted text: `38` / `103` digits.
- Previous-literal repeats: `4` / `5` digits.
- Raw uniform literal payload bits: `883.633`.
- Empirical digit-histogram savings only: `7.037` bits.

Whole-chunk prior occurrence is a diagnostic clue only here: selecting
which prior chunk or which new digits to emit is still the payload
generation problem.

## Context Gate

| Diagnostic | Value |
|---|---:|
| Context families | `11` |
| Payload labels | `49` |
| Best context | `op_index_x_length` |
| Best exact chunks | `39/53` |
| Best exact digits | `222/266` |
| Best model payload digits carried in table | `222` |
| Best net vs raw uniform literal bits | `44.588` bits |
| Prefix/holdout any-exact-chunk cells | `0/5` |
| Prefix/holdout cover-all cells | `0/5` |

The full-fit context hits are lookup-like: the model carries `222`
payload digits in its table and still costs `+44.588` bits versus
raw uniform payload after corrections. Prefix/holdout is stronger:
the selected contexts get `0/5` cells with any exact literal chunk.

## Decision

- No literal payload generator is promoted.
- The `266` literal digits remain external after the exact skeleton.
- Source-free context tables are rejected as a generator under paid payload costs and prefix/holdout.
- This does not change the compression bound.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Literal payload ledger](test_results/01_literal_payload_ledger.md)
- [Literal payload context gate](test_results/02_literal_payload_context_gate.md)
