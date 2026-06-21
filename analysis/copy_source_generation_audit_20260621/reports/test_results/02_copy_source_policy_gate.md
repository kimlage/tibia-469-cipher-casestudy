# Copy Source Policy Gate

Classification: `copy_source_decoder_policy_rejected`
Translation delta: `NONE`

## Purpose

Grant the exact skeleton and literal payload, then test whether simple
decoder-visible source policies can replace the declared copy-source
fields. Target-aware matching policies are kept only as oracle controls.

## Summary

- Copy events: `208`.
- Decoder-visible policies: `7`.
- Target-aware controls: `3`.
- Best decoder-visible policy: `previous_end_else_earliest`.
- Best decoder-visible chunk hits: `8/208`.
- Best decoder-visible exact sources: `8/208`.
- Best decoder-visible sequential exact books: `1/60`.
- Best oracle control: `previous_end_matching_or_earliest_oracle`.
- Best oracle chunk hits: `208/208`.

## Policy Scoreboard

| Policy | Target-aware | Chunk hits | Source exact |
| --- | ---: | ---: | ---: |
| `previous_end_matching_or_earliest_oracle` | `True` | `208/208` | `200/208` |
| `earliest_matching_oracle` | `True` | `208/208` | `200/208` |
| `latest_matching_oracle` | `True` | `208/208` | `85/208` |
| `previous_end_else_earliest` | `False` | `8/208` | `8/208` |
| `latest_legal` | `False` | `4/208` | `4/208` |
| `previous_end_minus_length_else_earliest` | `False` | `2/208` | `1/208` |
| `same_op_index_else_earliest` | `False` | `1/208` | `1/208` |
| `previous_source_else_earliest` | `False` | `1/208` | `1/208` |
| `earliest_legal` | `False` | `1/208` | `1/208` |
| `same_target_start_else_latest` | `False` | `0/208` | `0/208` |

## Decision

- Promotes copy-source generator: `False`.
- Decoder-visible source policies do not remove the source field. Target-aware matching controls can copy correctly, but they use the target chunk and are therefore parser/oracle controls, not generation rules.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
