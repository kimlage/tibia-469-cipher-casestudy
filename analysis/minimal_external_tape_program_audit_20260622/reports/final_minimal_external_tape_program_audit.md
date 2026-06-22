# Final Minimal External Tape Program Audit

Status: `analysis_only`
Classification: `minimal_external_tape_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can the current 469 book-generation residual be represented as a small executable control program plus unified external tapes, and can a macro grammar over that IR reduce the external ledger after paying grammar and corrections?

This audit does not reopen row0, plaintext, translation, semantics, or fan glosses. `compression_bound` remains separate from `generation_explanation`.

## Executable Decoder Contract

- Roundtrip: `70/70` books.
- Derived operation count: `261`.
- Seed books paid externally: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`.
- Emitted digit stream: `11263` digits.
- Derived fields include target starts and emitted book text from literal/copy execution.
- Target-conditioned fields remain explicit: literal payload, copy hints, and composition index.

## Unified External Tape Ledger

- Derived books: `60`.
- Operations: `261` (`53` literal, `208` copy).
- Seed payload: `5633.990` bits.
- Uniform coarse control: `935.675` bits.
- Composition index: `665.782` bits.
- Literal payload: `883.633` bits.
- Copy-hint rank: `1873.768` bits.
- Total external tapes including seed: `9992.848` bits.

## Macro Program Gate

- Classification: `minimal_external_tape_program_not_promoted`.
- Program reduction vs separated coarse+composition ledger: `-4942.611` bits.
- Macro saving before composition carry-through: `-5727.844` bits.
- Template saving before composition carry-through: `-6065.757` bits.
- Coupling bucket-stream saving: `-186.594` bits.
- Exact books without sequence atlas/terminals: `35`.
- Nontrivial exact books without sequence atlas/terminals: `1`.
- Exact ops without sequence atlas/terminals: `36`.
- Same-multiset shuffled p95: `-164.908` bits.
- Permuted-order p95: `-57.359` bits.

## Decision

`minimal_external_tape_program_not_promoted`. The decoder contract is now executable and the external ledger is unified, but the tested macro/template grammar increases cost after grammar/correction charges. This organizes the blocker; it does not yet reduce the external tapes.

## Remaining External Fields

- seed books `0..9`
- coarse control stream when macro/template program misses
- book-level composition index
- literal innovation payload tape
- copy hint rank/source tape
- correction tape for macro/template misses
- `row0`

## Reproducible Artifacts

- [01_minimal_external_tape_program_gate.py](../scripts/01_minimal_external_tape_program_gate.py)
- [01_executable_decoder_contract.json](test_results/01_executable_decoder_contract.json)
- [01_executable_decoder_contract.md](test_results/01_executable_decoder_contract.md)
- [02_unified_external_tape_ledger.json](test_results/02_unified_external_tape_ledger.json)
- [02_unified_external_tape_ledger.md](test_results/02_unified_external_tape_ledger.md)
- [03_macro_program_gate.json](test_results/03_macro_program_gate.json)
- [03_macro_program_gate.md](test_results/03_macro_program_gate.md)
- [02_compile_final_minimal_external_tape_program_audit.py](../scripts/02_compile_final_minimal_external_tape_program_audit.py)
