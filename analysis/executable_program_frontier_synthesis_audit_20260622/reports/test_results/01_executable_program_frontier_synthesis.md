# Executable Program Frontier Synthesis

Classification: `executable_program_frontier_requires_representation_change`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Consolidate the executable decoder contract and recent integration/removal gates. This is a frontier decision: whether the current external tapes have a promoted reduction path, or whether the representation itself needs to change.

## Summary

- Executable contract roundtrip: `True`.
- External bits excluding seed: `4358.858`.
- External bits including seed: `9992.848`.
- Promoted executable tape reductions: `0`.
- Rejected executable program routes: `3`.

| External Tape / Route | Baseline Bits | Best Attempt | Delta Bits | Classification |
| --- | ---: | --- | ---: | --- |
| `seed_books_0_9` | `5633.990` | `seed_primacy_audit_prior` |  | `EXTERNAL_RETAINED` |
| `coarse_control_plus_composition_index` | `1601.457` | `book_level_controller_program_integration` | `-244.881` | `EXECUTABLE_REDUCTION_REJECTED` |
| `copy_source_hint` | `1873.768` | `decoder_visible_source_tape_removal` | `-1609.513` | `EXECUTABLE_REDUCTION_REJECTED` |
| `literal_payload` | `883.633` | `innovation_stream_transducer_prior` |  | `WEAK_CLUE_NOT_EXECUTABLE_REDUCTION` |
| `macro_template_program` | `1601.457` | `minimal_external_tape_macro_program` | `-4942.611` | `EXECUTABLE_MACRO_PROGRAM_REJECTED` |
| `composition_index_rank_structure` | `665.782` | `composition_index_structure_audit` | `-13.327` | `FIELD_STRUCTURE_REJECTED` |
| `shared_literal_length_tape` |  | `shared_innovation_tape_audit` |  | `WEAK_CLUE_NOT_EXECUTABLE_REDUCTION` |

## Decision

No current tape reducer has promoted inside the executable decoder. The current program is a valid roundtrip contract, but not a generative formula: source, coarse/length, literal, composition, and seed payloads remain external. The next aligned route is not another local tape codec; it must change representation, most likely toward a joint chunk-origin program that explains operation chunks, source choice, and innovation together.
