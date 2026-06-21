# Literal Copy Availability Gate

Classification: `literal_externality_reduced_local_repairs_rejected`
Translation delta: `NONE`

## Purpose

The active formula still contains literal payload text. This gate checks
how much of that literal payload is mechanically forced by absence of a
legal `min_len` copy, and whether the remaining optional literal starts
can be repaired by simple local copy substitutions.

## Summary

- Literal items: `87`.
- Literal digits: `857`.
- Forced literal items with no legal copy at start: `73` (`83.908%`).
- Forced literal digits with no legal copy: `760` (`88.681%`).
- Optional literal starts with copy candidates: `14`.
- Optional literal digits with copy candidates: `97`.
- In-literal repair candidates scored: `74`.
- Best in-literal repair delta: `1.180` bits.
- Cross-op repair candidates scored: `465`.
- Best cross-op repair delta: `0.027` bits.
- Near-tie source/length penalties: `11.237` / `1.639` bits.
- Near-tie literal-payload saving: `-7.431` bits.

## Interpretation

Literal payload is not treated as free authorial choice. Most literal
items and digits are forced by copy unavailability. The remaining optional
frontier is localized to `14` starts and `97` digits, and the two tested
repair families do not improve the active ledger: the best in-literal
repair is `+1.180` bits and the best cross-op repair is `+0.027` bits.
The near-tie saves literal and item bits, but pays `+11.237` source bits
and `+1.639` copy-length bits, so the current parser remains retained
unless a new source/length representation appears.

## Boundary

- Literal recipe externality is reduced but not removed.
- No compression bound is promoted.
- No plaintext, translation, semantic reading, row0 change, or case reopening is introduced.
