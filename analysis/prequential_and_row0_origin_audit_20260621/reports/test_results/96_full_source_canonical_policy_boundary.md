# Full Source Canonical Policy Boundary

Classification: `no_static_canonical_source_policy_cost_safe`
Translation delta: `NONE`

## Purpose

Gate 95 showed that operation shape is policy-invariant but exact
source-bearing signatures are not. This audit checks whether any
static source tie policy can be frozen as canonical without paying
parser-cost penalty.

## Result

- Cases compared: `175`.
- Primary canonical policy tested: `earliest_source`.
- Primary canonical policy cost-safe: `False`.
- Primary canonical min-cost cases: `170/175`.
- Primary canonical extra bits vs per-case min: `39.331294937145`.
- Static cost-safe policies: `[]`.
- Policy min-counts: `{'earliest_source': 170, 'latest_source': 170, 'prefer_previous_end_then_earliest': 170}`.
- Policy extra bits vs per-case min: `{'earliest_source': 39.33129493714541, 'latest_source': 39.41967584396795, 'prefer_previous_end_then_earliest': 39.33129493714541}`.
- Signature-variant cases inherited from gate 95: `127/175`.
- Latest-source worse than canonical cases: `5/175`.
- Latest-source better than canonical cases: `5/175`.
- Latest-source positive extra bits vs canonical: `39.419675843968`.
- Latest-source positive savings vs canonical: `39.331294937145`.
- Previous-end-preferred differs from canonical cases: `0/175`.
- Max latest-source penalty: `8.214528` at cutoff `50`, book `64`.
- Max latest-source savings: `-8.196852` at cutoff `50`, book `63`.

## Decision

- Source fields removed: `False`.
- No single static source tie policy is cost-safe across the gate95 cases. Earliest-source and previous-end-preferred tie on most cases, but latest-source is cheaper on five book-63 cases. Source tie policy therefore cannot be globally frozen without either paying bits or adding a selector.
- No static canonical tie policy is promoted.
- It does not promote a decoder-side source rule.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
