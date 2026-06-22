# Final Sequence Mutation Program Audit

Status: `analysis_only`
Classification: `SEQUENCE_MUTATION_PROGRAM_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can a held-out book's joint operation-token sequence be generated as a small edit/mutation from a previous book sequence, instead of declaring bag and order independently?

## Result

The selected mutation policies cost `4742.368` optimistic edit bits versus `3525.674` sequence-unigram bits (`1216.694` bits worse). They beat shuffled-train p95 in `0/5` cells and random-source p95 in `2/5`. The oracle lower bound with paid source index is `832.040` bits worse than unigram.

## Decision

This is a lower-bound edit test, not a full executable codec. Row0, plaintext, translation, and compression_bound remain unchanged.

## Reproducible Artifacts

- [01_sequence_mutation_program_gate.py](../scripts/01_sequence_mutation_program_gate.py)
- [01_sequence_mutation_program_gate.json](test_results/01_sequence_mutation_program_gate.json)
- [01_sequence_mutation_program_gate.md](test_results/01_sequence_mutation_program_gate.md)
