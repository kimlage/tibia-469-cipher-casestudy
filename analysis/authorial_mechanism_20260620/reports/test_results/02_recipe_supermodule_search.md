# Recipe Supermodule Search

Verdict: `supermodule_not_promoted`. Translation delta: `NONE`.

This pass searches for higher-order repeated recipe patterns over the
current tape formula. Exact repeats can in principle reduce recipe cost;
component/length skeleton repeats are diagnostic only because they do not
roundtrip without extra payload.

## Baseline

- Formula: `analysis/generator_search_20260618/tape_based_formula_469.json`
- Books: `70`
- Recipe items: `215`
- Recipe length distribution: `{1: 13, 2: 23, 6: 5, 3: 12, 4: 7, 5: 6, 8: 2, 9: 1, 7: 1}`

## Exact Recipe Repeats

- Repeated exact sequences: `0`
- Rough-promotable exact sequences: `0`

## Skeleton Repeats

- Repeated skeleton sequences: `20`
- Rough-promotable skeleton sequences: `0`

Top skeleton rows are useful as style diagnostics, not as a generator
improvement unless a payload-free exact rule is found.

## Conclusion

No exact higher-order recipe grammar improves the current tape formula
under this rough item-cost screen.
