# Sequential LZ Book Order Search

Verdict: `order_search_not_promoted_after_permutation_cost`. Translation delta: `NONE`.

This audit checks whether changing the emission order of the 70 books
improves the sequential LZ book formula enough to justify storing or
explaining a non-numeric order. The sampled order is charged by a rough
`log2(70!)` permutation cost before any promotion.

| Metric | Value |
|---|---:|
| Numeric-order bits | `10190.0` |
| Best sampled-order bits | `10004.0` |
| Gross gain | `186.0` |
| Permutation cost `log2(70!)` | `332.5` |
| Net gain after order cost | `-146.5` |
| Random sampled orders | `800` |
| p(sampled <= numeric) | `0.0412` |

## Boundary

Some arbitrary orders compress slightly better than numeric order, but the
sampled gain does not pay for the order description. Numeric book order
therefore remains the preferred mechanical default for the sequential LZ
formula unless a source-backed physical/order manifest supplies the order
for free.
