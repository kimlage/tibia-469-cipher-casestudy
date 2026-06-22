# Causal Event Graph Program Gate

Classification: `causal_event_graph_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Graph Ledger

- Event rows: `261`.
- Node counts: `{'seed_span': 10, 'operation': 261, 'operation_span': 261, 'literal_innovation_span': 53, 'copy_source_span': 208, 'endpoint_memory_mark': 336}`.
- Edge counts: `{'emits': 261, 'consumes_literal': 53, 'creates_boundary': 522, 'copies_from': 208, 'derives_source': 208, 'creates_endpoint_mark': 416}`.

## Current Executable Baseline

- `external_bits_excluding_seed`: `4065.013`.
- `external_bits_including_seed`: `9699.003`.
- `copy_bits`: `1863.425`.
- `copy_fallback_hint_bits_remaining`: `779.571`.
- `literal_payload_bits`: `883.633`.
- `online_x64_coarse_bits`: `876.412`.
- `residual_composition_bits`: `439.959`.
- `seed_payload_bits`: `5633.990`.

## Macro Program

- Rows tested: `72`.
- Positive macro rows: `0`.
- Rows beating shuffled p05: `2`.
- Best delta vs direct event labels: `88.238` bits.
- Whole sequences without raw corrections: `1`.

| Symbol stream | Rows | Positive | Beat control p05 | Mean delta |
| --- | ---: | ---: | ---: | ---: |
| `coarse_symbol` | `24` | `0` | `1` | `1062.367` |
| `lineage_symbol` | `24` | `0` | `1` | `1009.857` |
| `event_symbol` | `24` | `0` | `0` | `216.562` |

## Required Controls

- Same-multiset shuffled graph controls: `2`/`72` rows beat p05.
- Permuted book order best/positive: `169.585` / `0`.
- Randomized source spans best/positive: `166.353` / `0`.
- Macro labels shuffled best/positive: `159.902` / `0`.
- Shuffled literal tape exact chunks: `0`/`53`.

## Decision

`causal_event_graph_program_not_promoted`: macros organize graph recurrence but do not replace the executable residual tapes after paid corrections.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
