# Post-Midpoint Alpha1 Top60 Triple Probe

Verdict: `bounded_post_midpoint_alpha1_top60_triple_probe_not_promoted`. Translation delta: `NONE`.

This bounded probe tests compatible triples among the top local single
edits after the midpoint alpha=1 pair frontier closed. It is deliberately
not an exhaustive triple frontier over all local candidates.

## Scope

- Current formula bits: `8572.267`
- Valid single candidates: `189`
- Top-N candidates used: `60`
- Total triples considered: `34220`
- Compatible triples: `33990`
- Valid triples: `33588`
- Invalid triples: `402`

## Best Single

- Delta: `0.971` bits
- Book/op/text: `17` / `1` / `477090`

## Best Bounded Triple

- Delta: `3.914` bits
- Total bits: `8576.181`
- Repair 1: `literal_to_copy` book `17`, op `1`, text `477090`, length `6`
- Repair 2: `literal_to_copy` book `3`, op `4`, text `60199`, length `5`
- Repair 3: `literal_to_copy` book `2`, op `11`, text `14519`, length `5`

## Interpretation

This probe can find a candidate improvement inside its bounded top-N
scope. A negative result here is evidence against the most plausible
triple combinations, but it is not an exhaustive closure of every
possible triple of the 189 local candidates.

## Boundary

This is a mechanical recipe-cost audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
