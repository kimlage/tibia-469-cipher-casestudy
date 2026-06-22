# Final Innovation Stream Transducer Audit

Status: `analysis_only`
Classification: `INNOVATION_STREAM_BOUNDARY_CANDIDATE_TRIGGER_CLUE_PROMOTED_GENERATOR_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Can the fixed operation skeleton be replaced by an online copy transducer
plus a small external innovation tape made from the literal payload?

## Result

- Literal tape digits: `266`.
- Literal tape chunks: `53`.
- Best threshold: `5`.
- Best exact books: `22/60`.
- Best exact nontrivial books: `12`.
- Best cutpoint hits: `40/201`.
- Best source+length hits: `47/208`.
- Best shuffled-tape exact-book p95: `23.0`.
- Best blind replay exact books: `0`.
- Best seed tape coverage: `266/266`.
- Best seed coverage control p95: `265.000`.
- Best prior-tape coverage: `205/266`.
- Best Markov tape bits: `879.609`.
- Promotes tape structure: `True`.
- Tape-synchronized exact books in beam: `0/60`.
- Tape-synchronized exact-in-beam shuffled p95: `0.0`.
- Tape-synchronized true-prefix survival: `19/60`.
- Tape-synchronized mean true-prefix max fraction: `0.002495`.
- Seed-subcodec best saving vs raw tape: `-180.128` bits.
- Seed-subcodec best control saving p95: `-249.663` bits.
- Seed-subcodec copy digits: `87/266`.
- Promotes seed subcodec: `False`.
- Weak seed subcodec clue: `True`.
- Seed-walk best total bits: `1106.842`.
- Seed-walk best saving vs absolute-source subcodec: `-43.081`.
- Seed-walk best saving vs raw tape: `-223.209`.
- Promotes seed-walk subcodec: `False`.
- Weak seed-walk clue: `False`.
- Tape schedule best feature: `global_majority`.
- Tape schedule exact books: `33/50`.
- Tape schedule saving vs count baseline: `221.844` bits.
- Tape schedule global-majority exact books: `33/50`.
- Tape schedule global-majority saving: `221.844` bits.
- Tape schedule best feature delta bits: `-5.585`.
- Tape schedule best feature delta exact: `0`.
- Tape schedule random exact p95: `31.000`.
- Promotes tape schedule: `False`.
- Trigger best feature: `copy_available`.
- Trigger best feature exact ops: `172/182`.
- Trigger best feature literal hits: `17/27`.
- Trigger best feature delta vs global: `48.262` bits.
- Trigger best feature exact delta vs global: `17`.
- Trigger forced literal ops with no copy available: `36/53`.
- Promotes conditional trigger clue: `True`.
- Decoder-visible trigger best feature: `next_digit_seen`.
- Decoder-visible trigger exact ops: `155/182`.
- Decoder-visible trigger literal hits: `0/27`.
- Decoder-visible trigger delta vs global: `-4.807` bits.
- Target-conditioning gap bits: `48.262`.
- Promotes decoder-visible trigger: `False`.
- Boundary-candidate trigger feature: `book_start_x_copy_available`.
- Boundary-candidate trigger exact candidates: `745/819`.
- Boundary-candidate trigger start hits: `46/120`.
- Boundary-candidate trigger literal/copy hits: `4/42`.
- Boundary-candidate trigger delta vs same-cutoff global: `169.492` bits.
- Promotes boundary-candidate trigger: `True`.

The first gate tests the right external-input hypothesis: a canonical
literal tape plus an online copy transducer. It separates a
target-conditioned upper bound from a blind replay control, so any
positive result is not overclaimed as a closed-loop generator. The
second gate asks whether the tape itself has seed-derived, recurrent,
or Markov structure beyond shuffled controls. The synchronization gate
then asks whether that structured tape is enough to drive a closed-loop
copy transducer when only the tape start, book length, and prior material
are granted. The seed-subcodec gate prices the seed-coverage clue as a
real dependency reduction for the tape itself. The seed-walk gate then
tests whether source addresses can be replaced by a cheaper source walk.
The schedule gate asks whether per-book tape consumption can be predicted
from online mechanical features beyond a global sparsity baseline. The
trigger gate then moves one level down, asking whether literal-vs-copy
can be predicted at known operation starts when true-prefix,
target-conditioned copy availability is granted. The decoder-visible
trigger gate removes that target-conditioned availability while still
granting known operation starts and true tape state. The boundary
candidate trigger gate then replaces exact operation starts with the
previously promoted `right_ge:4` boundary candidate set and asks for
three-way `nonstart/literal/copy` labels.

## Decision

- Innovation tape replay is not promoted as a generator.
- The literal payload can now be discussed as one tape-shaped dependency rather than only per-operation payload.
- Tape structure is promoted as a mechanical clue because it beats same-multiset shuffled controls.
- This does not yet derive when the transducer should consume the tape.
- Tape-synchronized closed-loop generation is not promoted unless exact books survive above shuffled controls.
- Tape synchronization is only a weak prefix-survival clue under the current beam.
- Seed-derived tape subcodec is not promoted because paid references are still worse than raw tape.
- Seed-derived tape subcodec remains a weak clue because paid coverage beats shuffled controls.
- Seed-walk source model is rejected because deltas are more expensive than absolute source positions.
- Tape schedule feature model is not promoted unless it improves over global-majority sparsity.
- Tape schedule sparsity is retained only as a weak clue.
- Conditional trigger policy is promoted as a dependency-reduction clue: copy availability explains many literal/copy decisions after paying table/correction cost.
- The trigger clue is not a closed-loop generator because it still grants operation starts and target-conditioned copy availability.
- Decoder-visible trigger policy is rejected: without target-conditioned copy availability, the trigger clue collapses to the copy-majority baseline.
- Boundary-candidate trigger policy is promoted as a composed dependency-reduction clue, but still leaves missed operation starts and target-conditioned copy availability unresolved.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Innovation tape replay gate](test_results/01_innovation_tape_replay_gate.md)
- [Innovation tape structure gate](test_results/03_innovation_tape_structure_gate.md)
- [Tape synchronized closed loop gate](test_results/04_tape_synchronized_closed_loop_gate.md)
- [Seed derived tape subcodec gate](test_results/05_seed_derived_tape_subcodec_gate.md)
- [Seed walk source model gate](test_results/06_seed_walk_source_model_gate.md)
- [Innovation tape schedule gate](test_results/07_innovation_tape_schedule_gate.md)
- [Tape trigger policy gate](test_results/08_tape_trigger_policy_gate.md)
- [Decoder visible trigger policy gate](test_results/09_decoder_visible_trigger_policy_gate.md)
- [Boundary candidate trigger gate](test_results/10_boundary_candidate_trigger_gate.md)
