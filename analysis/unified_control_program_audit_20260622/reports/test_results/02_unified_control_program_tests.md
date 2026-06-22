# Unified Control Program Tests

Classification: `unified_control_program_partial_coupling`
Translation delta: `NONE`

## Residual Cost Ledger

- Source-address bits: `2550.594`.
- Copy-hint rank bits: `1873.768`.
- Literal innovation tape bits: `883.633`.
- Type:length stream bits: `775.003`.
- Separated source model: `5289.866`.
- Separated copy-hint model: `4613.040`.
- Innovation tape + copy hint + type:length stream: `3532.404`.
- Copy-hint saving vs source address: `676.826`.
- Best unified saving vs separated source: `1757.462`.
- External streams remaining: `['op_type_control', 'length_control', 'literal_innovation_tape', 'copy_hint_rank_stream']`.

## Control-Tape Coupling Gate

- Promoted relations: `['previous_op_to_next_control_symbol']`.
- Promotes control coupling: `True`.

| Relation | Rows | Observed Saving | Random p95 | Promoted | Status |
| --- | ---: | ---: | ---: | --- | --- |
| `length_bucket_to_hint_rank_bucket` | `208` | `2.997` | `-54.234` | `False` | `WEAK_COUPLING_BELOW_EFFECT_GATE` |
| `op_type_position_to_literal_consumption` | `261` | `187.716` | `-69.498` | `False` | `AUDIT_ONLY_LEAKY_FEATURE` |
| `book_phase_to_control_symbol` | `261` | `1.406` | `-0.898` | `False` | `WEAK_COUPLING_BELOW_EFFECT_GATE` |
| `previous_op_to_next_control_symbol` | `261` | `47.178` | `-61.852` | `True` | `PROMOTED_COUPLING_CLUE` |
| `joint_type_length_to_hint_or_literal_behavior` | `261` | `215.066` | `-101.399` | `False` | `AUDIT_ONLY_LEAKY_FEATURE` |

## Unified Program Holdout

- Total independent source bits: `10178.609`.
- Total best unified bits: `6757.999`.
- Total reduction vs independent source: `3420.610`.
- Exact books without atlas: `0`.
- Exact ops without atlas: `0`.
- Fields still external: `['type_length_control_stream', 'literal_innovation_tape', 'copy_hint_rank_stream', 'seed_books_0_9', 'row0']`.

| Cutoff | Test Ops | Independent Source | Best Unified | Reduction | Exact Books |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `182` | `3681.154` | `2444.422` | `1236.731` | `0` |
| `30` | `140` | `2867.023` | `1880.973` | `986.050` | `0` |
| `40` | `95` | `2008.905` | `1350.468` | `658.437` | `0` |
| `50` | `56` | `1217.649` | `821.851` | `395.799` | `0` |
| `60` | `20` | `403.878` | `260.284` | `143.594` | `0` |

## Decision

- This organizes the residual program into explicit streams; it does not generate books without those streams.
- A promoted coupling relation would be evidence for synchronization; otherwise the result is residual organization, not a generator.
- Row0, plaintext, translation, and compression bound remain unchanged.
