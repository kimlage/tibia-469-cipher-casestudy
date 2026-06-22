# Final Source Tape Removal Program Audit

Status: `analysis_only`
Classification: `source_tape_removal_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can the executable decoder remove the copy source/hint tape using only decoder-visible source policies plus paid exceptions?

## Evidence

- Best policy: `previous_source_end`.
- Default copy hits: `22/537`.
- Unrepaired exact books over repeated holdouts: `0`.
- Baseline copy-hint bits: `5062.568`.
- Policy+exception bits: `6672.081`.
- Saving vs copy-hint tape: `-1609.513`.
- Random visible-source p95 saving: `-8.288`.

## Decision

`source_tape_removal_not_promoted`. The copy source/hint tape remains external: simple decoder-visible source policies either emit wrong books or cost more after uniform source-address exceptions.

## Reproducible Artifacts

- [01_source_tape_removal_program_gate.py](../scripts/01_source_tape_removal_program_gate.py)
- [01_source_tape_removal_program_gate.json](test_results/01_source_tape_removal_program_gate.json)
- [01_source_tape_removal_program_gate.md](test_results/01_source_tape_removal_program_gate.md)
