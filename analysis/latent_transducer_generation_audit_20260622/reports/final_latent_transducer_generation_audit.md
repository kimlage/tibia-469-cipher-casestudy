# Final Latent Transducer Generation Audit

Status: `analysis_only`
Classification: `latent_transducer_first_gate_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Can a prefix-trained joint transducer choose literal spans, copy spans,
boundaries, and copy sources together, instead of relying on the fixed
261-operation skeleton atlas?

## Result

- Beam width: `80`.
- Aggregate exact books: `34`.
- Aggregate nontrivial exact books: `0`.
- Aggregate cutpoint hits: `224/343`.
- Cells beating random cutpoint p95: `5/5`.
- Aggregate source+length hits: `131/421`.
- Aggregate cutpoint atlas bits: `2063.661`.
- Aggregate cutpoint correction bits: `1387.992`.
- Aggregate cutpoint saving vs atlas: `675.669`.
- Predicted literal digits: `202`.
- Canonical literal digits: `354`.

The new route tests the right object: a single parser where literal, copy,
length, source, and boundary decisions compete in one beam. But this first
gate is still teacher-forced by the target digit stream and does not
promote a closed-loop generator unless it produces nontrivial exact books
under holdout.

## Decision

- The route changes from local endpoint/source selectors to a joint latent-transducer audit.
- The first beam gate is a parser/generator prototype, not a promoted formula.
- Promotion requires nontrivial exact holdout books and paid correction reduction.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Latent transducer beam gate](test_results/01_latent_transducer_beam_gate.md)
