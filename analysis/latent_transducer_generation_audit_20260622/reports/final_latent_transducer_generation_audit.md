# Final Latent Transducer Generation Audit

Status: `analysis_only`
Classification: `latent_transducer_closed_loop_high_external_control`
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
- Closed-loop top-1 exact books: `0/150`.
- Closed-loop exact books surviving finished beam: `0/150`.
- Closed-loop true-prefix survival books: `0/150`.
- Closed-loop mean true-prefix max fraction: `0.007754`.
- Rescue ledger sampled book instances: `15`.
- Rescue ledger forced exact books: `15`.
- Rescue ledger books needing no rescue: `0`.
- Rescue ledger total rescue events: `1732`.
- Rescue ledger total rescue bits: `21403.967`.
- Rescue ledger rescue/raw ratio: `3.069669`.
- Rescue ledger max true-prefix rank: `22500`.
- Rescue ledger low external-control regime: `False`.

The new route tests the right object: a single parser where literal, copy,
length, source, and boundary decisions compete in one beam. But this first
gate is still teacher-forced by the target digit stream and does not
promote a closed-loop generator unless it produces nontrivial exact books
under holdout. A second survival gate removes within-book target teacher
forcing while still granting book length and true prior material; the
true stream does not survive as a closed-loop generator. A sampled rescue
ledger then measures how much oracle steering would be needed to keep the
true prefix alive. The answer is not small: on first/middle/last suffix
books per cutoff, every instance needs rescues and the rescue ledger costs
more than raw digit emission. The closed-loop blocker is therefore a
substantial missing state/control problem, not a near-miss beam-width
artifact.

## Decision

- The route changes from local endpoint/source selectors to a joint latent-transducer audit.
- The first beam gate is a parser/generator prototype, not a promoted formula.
- Closed-loop digit survival is rejected under the current beam.
- The rescue ledger is high external-control, so oracle steering is not promoted as a compact latent state.
- Promotion requires nontrivial exact holdout books and paid correction reduction.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Latent transducer beam gate](test_results/01_latent_transducer_beam_gate.md)
- [Closed loop digit survival gate](test_results/03_closed_loop_digit_survival_gate.md)
- [Closed loop rescue ledger](test_results/04_closed_loop_rescue_ledger.md)
