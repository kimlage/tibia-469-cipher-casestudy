# Final Digit Content Boundary Transducer Audit

Status: `analysis_only`
Classification: `LAGGED_SURPRISAL_BOUNDARY_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can the strong right-surprisal boundary signal be made less oracle-like by treating it as a one-digit-lag boundary annotation program?

## Result

The one-digit-lag contract costs `2153.437` bits versus `2063.661` exact start-composition bits (`89.777`). The lag tax alone is `488.323` bits for `147` recovered copy starts. It still beats random top-K p05 in `0/5` cells.

## Decision

This preserves a weak boundary-annotation clue, but it does not produce an executable copy/literal decoder. The next blocker remains deriving starts and copy/literal mode before target-conditioned source availability or paying the remaining correction tape explicitly. Row0, plaintext, translation, and compression_bound remain unchanged.

## Reproducible Artifacts

- [01_all_position_boundary_transducer_gate.py](../scripts/01_all_position_boundary_transducer_gate.py)
- [02_start_candidate_ranking_gate.py](../scripts/02_start_candidate_ranking_gate.py)
- [03_surprisal_start_candidate_gate.py](../scripts/03_surprisal_start_candidate_gate.py)
- [04_lagged_surprisal_boundary_contract_gate.py](../scripts/04_lagged_surprisal_boundary_contract_gate.py)
- [01_all_position_boundary_transducer_gate.json](test_results/01_all_position_boundary_transducer_gate.json)
- [02_start_candidate_ranking_gate.json](test_results/02_start_candidate_ranking_gate.json)
- [03_surprisal_start_candidate_gate.json](test_results/03_surprisal_start_candidate_gate.json)
- [04_lagged_surprisal_boundary_contract_gate.json](test_results/04_lagged_surprisal_boundary_contract_gate.json)
- [04_lagged_surprisal_boundary_contract_gate.md](test_results/04_lagged_surprisal_boundary_contract_gate.md)
