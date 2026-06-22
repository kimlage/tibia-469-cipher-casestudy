# Final Latent Transducer Generation Audit

Status: `analysis_only`
Classification: `latent_transducer_copy_hint_stream_lower_bound_open`
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
- Rescue surface events classified: `1732`.
- Rescue surface counts: `{'book_end': 6, 'copy': 1721, 'literal': 5}`.
- Rescue surface copy/literal fraction: `0.993649` / `0.002887`.
- Rescue surface exact/near internal cutpoint fraction: `0.015589` / `0.047344`.
- Rescue surface operation-start fraction: `0.015589`.
- Rescue surface early <=20% fraction: `0.215935`.
- Copy-state diagnostic copy-surface last-kind counts: `{'copy': 16, 'literal': 1705}`.
- Copy-state diagnostic true-copy event fraction inside copy spans: `0.009297`.
- Copy-state diagnostic copy ops tested: `32`.
- Copy-state diagnostic source-match ops: `32/32`.
- Copy-state diagnostic inventory/pruned prefix digit fraction: `0.857258` / `0.000000`.
- Copy-state diagnostic ops with any pruned prefix: `0`.
- Ranking frontier best policy: `longest_recent`.
- Ranking frontier current/best prefix digits: `6` / `56`.
- Ranking frontier best prefix digit fraction: `0.045161`.
- Ranking frontier random digit p95 beaten: `True`.
- Ranking frontier promotes copy ranking rule: `False`.
- Copy hint lower-bound best policy: `frequent_longest`.
- Copy hint lower-bound rank bits: `1873.768`.
- Copy hint lower-bound source-address bits: `2550.594`.
- Copy hint lower-bound saving vs source address: `676.826`.
- Copy hint lower-bound fraction of raw copied-digit bits: `0.060645`.

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
artifact. A surface audit maps those rescues back onto the canonical
skeleton after decoding. The failures are not concentrated at visible
boundaries: only `27/1732` are exact internal cutpoints and `82/1732`
are within one digit of an internal cutpoint, while `1721/1732` fall
inside canonical copy spans. That leaves the blocker at decoder-visible
copy-state/content control, not a simple boundary trigger. A copy-state
diagnostic then asks whether those failures come from absent source
material or from candidate pruning/ranking. The answer is narrow but
useful: inside copy spans, only `16/1721` rescue events arrive via a
copy emission; `1705/1721` arrive by single literal steps. For the `32`
sampled canonical copy ops, the source payload matches in `32/32` and
some correct prefix exists in the raw inventory in `32/32`, covering
`1063/1240` copy digits, but the pruned candidate set contains a correct
prefix in `0/32`. The live blocker is therefore candidate pruning/ranking
or copy-continuation state, not missing prior material. A copy-candidate
ranking frontier then tests whether simple target-free rankings solve
that blocker at the same top-80 budget. They do not. The best unique-op
policy, `longest_recent`, improves over current source-penalty pruning
from `6` to `56` prefix digits and narrowly beats random top-80 digit p95
(`55`), but still covers only `56/1240` copy digits. Simple chunk ranking
is therefore a weak clue, not a promoted copy-control rule. A copy hint
stream lower-bound then asks the constructive version: if op start, copy
type, length, and prior material are granted, how much paid chunk choice
remains? The best known-length rank code is `frequent_longest` at
`1873.768` bits for all `208` copy ops and `9301` copied digits, saving
`676.826` bits versus raw source addressing and costing only `0.060645`
of literalizing the copied digits. That opens a real paid-control-stream
route, but it is not a generator because starts, types, and lengths are
still granted.

## Decision

- The route changes from local endpoint/source selectors to a joint latent-transducer audit.
- The first beam gate is a parser/generator prototype, not a promoted formula.
- Closed-loop digit survival is rejected under the current beam.
- The rescue ledger is high external-control, so oracle steering is not promoted as a compact latent state.
- Rescue surface labels are diagnostic only; they do not produce a decoder-visible state.
- Copy-state diagnostics identify a concrete next route: replace blind cheapest-chunk pruning with a decoder-visible copy-control state.
- Simple target-free chunk ranking is insufficient; a paid copy hint/control stream is now the cleaner constructive route.
- The copy hint lower bound reduces declared source addressing if length is granted, but it remains an external stream to explain.
- Promotion requires nontrivial exact holdout books and paid correction reduction.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Latent transducer beam gate](test_results/01_latent_transducer_beam_gate.md)
- [Closed loop digit survival gate](test_results/03_closed_loop_digit_survival_gate.md)
- [Closed loop rescue ledger](test_results/04_closed_loop_rescue_ledger.md)
- [Closed loop rescue surface audit](test_results/05_closed_loop_rescue_surface_audit.md)
- [Copy state rescue diagnostic](test_results/06_copy_state_rescue_diagnostic.md)
- [Copy candidate ranking frontier](test_results/07_copy_candidate_ranking_frontier.md)
- [Copy hint stream lower bound](test_results/08_copy_hint_stream_lower_bound.md)
