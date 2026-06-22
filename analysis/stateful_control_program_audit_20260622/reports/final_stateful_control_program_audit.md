# Final Stateful Control Program Audit

Status: `analysis_only`
Classification: `stateful_control_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

This audit tests the next constructive route after the unified residual ledger: can a target-free stateful control program generate or economically encode the exact `type:length` stream, using only prefix training, book id, book length, remaining length, and previous emitted control state?

It does not test translation, plaintext, fan glosses, semantics, or row0 origin. Row0 remains exogenous and the compression bound is unchanged.

## Result

- Best model: `remaining_prev_bucket` with features `remaining_bucket+prev_bucket`.
- Best model bits over prefix/suffix cutoffs: `4600.432`.
- Saving vs independent exact type+length declaration: `-1001.211` bits.
- Shuffled-control p95 saving: `-850.701` bits.
- Fallback rows: `463`.
- Promoted models: `[]`.
- Generator-promoted models: `[]`.

All tested state models are rejected. The best model, `remaining_prev_bucket`, is still `1001.211` bits worse than declaring exact op type and length independently, and it is worse than shuffled-control p95. This means the observed `previous_op` coupling from the unified ledger is not sufficient to become an exact control program.

## Generation Check

| Cutoff | Test Books | Greedy Exact | Beam20 Exact | Beam20 Nontrivial | Greedy Prefix Ops |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `50` | `0` | `0` | `0` | `0` |
| `30` | `40` | `0` | `0` | `0` | `0` |
| `40` | `30` | `0` | `0` | `0` | `0` |
| `50` | `20` | `0` | `2` | `0` | `0` |
| `60` | `10` | `0` | `1` | `0` | `0` |

The few Beam20 exact hits occur only in trivial one-operation books and only under a codec that already fails the cost/control gate. They are therefore not generation evidence.

## Decision

- `stateful_control_program_not_promoted`.
- Exact `type:length` remains an external control stream.
- The route did not move the generator closer except by closing this direct stateful-program shortcut.
- The current model remains a strong mechanical parser/compressor with explicit residual streams, not a complete authorial generator.

## Remaining External Fields

- exact `type:length` control sequence
- literal innovation tape payload and schedule
- copy-hint rank stream
- seed books `0..9`
- `row0`

## Next Blocker

The next route should not be another exact-action Markov/context model. The control stream likely needs either a different representation of length innovation, a joint latent state that also explains literal/copy hint choices, or an external source for the control tape. The direct observable state program over previous control and remaining length is closed under this evidence.

## Reproducible Artifacts

- [01_stateful_control_program_gate.py](../scripts/01_stateful_control_program_gate.py)
- [01_stateful_control_program_gate.json](test_results/01_stateful_control_program_gate.json)
- [01_stateful_control_program_gate.md](test_results/01_stateful_control_program_gate.md)
- [02_compile_final_stateful_control_program_audit.py](../scripts/02_compile_final_stateful_control_program_audit.py)
