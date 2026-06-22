# Boundary Hazard State Gate

Classification: `boundary_hazard_state_dependency_reduced_not_generator`
Translation delta: `NONE`

## Purpose

Test whether a sequential parser state can reduce boundary dependency:
the state is available during generation and includes age since the last
emitted boundary, remaining length, progress, and emitted-boundary count.

## Summary

- Features tested: `10`.
- Prefix cutoffs tested: `5`.
- Best feature: `age_bucket`.
- Aggregate gain before feature charge: `173.497` bits.
- Aggregate gain after feature charge: `170.175` bits.
- Positive cells: `5/5`.
- Random same-count p95 before feature charge: `167.705` bits.
- Beats random p95: `True`.
- Promotes hazard state: `True`.
- Promotes exact parser: `False`.

A sequential boundary hazard state based on age since the last emitted boundary reduces boundary-flag coding under prefix holdout and beats same-count random boundary controls. It is a real parser-state clue, but it still emits probabilities rather than exact endpoints.

## Feature Scoreboard

| Feature | Gain after charge | Gain before charge | Positive cells |
| --- | ---: | ---: | ---: |
| `age_bucket` | `170.175` | `173.497` | `5/5` |
| `count_bucket` | `140.291` | `143.613` | `5/5` |
| `age_x_count` | `128.065` | `131.387` | `5/5` |
| `age_exact_cap20` | `97.731` | `101.053` | `5/5` |
| `age_x_progress` | `66.114` | `69.436` | `4/5` |
| `age_x_remaining` | `33.849` | `37.170` | `4/5` |
| `remaining_bucket` | `-30.845` | `-27.523` | `0/5` |
| `progress_quint` | `-33.293` | `-29.971` | `2/5` |
| `count_mod3` | `-83.983` | `-80.661` | `2/5` |
| `age_exact_cap50` | `-89.379` | `-86.057` | `0/5` |

## Decision

- Sequential hazard state is promoted as a boundary dependency reducer.
- Exact parser/generator is not promoted.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
