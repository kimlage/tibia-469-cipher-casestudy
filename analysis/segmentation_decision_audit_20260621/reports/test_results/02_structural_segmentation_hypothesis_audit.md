# Structural Segmentation Hypothesis Audit

Classification: `target_text_longest_earliest_parser_clue_not_source_free_generator`
Translation delta: `NONE`

## Purpose

This gate tests structural segmentation hypotheses against the
decision trace. It is not a bit sweep and it does not search
plaintext.

## Hypothesis Scoreboard

| Hypothesis | Hits | Coverage | Boundary | Source-free promoted |
|---|---:|---:|---|---|
| `declared_source_target_match_max_length` | `207/208` | `0.995` | `declared_source_and_target_text_dependent` | `False` |
| `global_longest_target_match_pair` | `207/208` | `0.995` | `target_text_dependent_pair_oracle` | `False` |
| `earliest_global_max_source` | `207/208` | `0.995` | `target_text_dependent_source_tie_policy` | `False` |
| `latest_global_max_source` | `78/208` | `0.375` | `target_text_dependent_source_tie_policy` | `False` |
| `copy_preserves_recurrent_next_boundary` | `123/208` | `0.591` | `target_text_dependent_boundary_clue` | `False` |
| `stop_before_max_protects_literal_payload` | `0/208` | `0.000` | `rejected_control` | `False` |
| `declared_boundary_has_more_future_copy_options_than_max_boundary` | `1/208` | `0.005` | `target_text_dependent_boundary_clue` | `False` |

## Source Tie Boundary

- Unique global-max source rows: `78/208`.
- Best source tie policy: `earliest_global_max_source` = `207/208`.
- Random global-max source expected hits: `119.739/208`.
- Prequential tie-policy cells matching suffix oracle: `5/5`.

## Exception Rows

| Book | Op | Projection copy | Declared length | Max length | Candidate pairs | Declared boundary pairs | Max boundary pairs |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `55` | `2` | `2` | `44` | `45` | `95` | `7` | `0` |

## Decision

- Promotes target-text parser clue: `True`.
- Promotes source-free segmentation rule: `False`.
- The strongest structural finding is that target-text-aware longest-copy segmentation with earliest-source tie recovers nearly every copy pair in the stable projection. This is a real parser clue for segmentation, but not a source-free generator: it requires the target suffix being parsed and still has one exception. Literal-protection and recurrent-boundary shortcuts do not explain the decision trace.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
