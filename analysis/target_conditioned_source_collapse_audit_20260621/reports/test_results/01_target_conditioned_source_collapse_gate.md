# Target-Conditioned Source Collapse Gate

Classification: `target_conditioned_source_collapse_clue_not_generator`
Translation delta: `NONE`

## Purpose

Test whether copy-source choice remains a primary blocker once the
copied target chunk is granted by a hypothetical target-stream mechanism.

## Summary

- Copy events: `208`.
- Earliest matching source: `200/208` (`0.962`).
- Non-earliest exceptions: `8`.
- Legal source bits without target stream: `2550.594`.
- Oracle rank bits among matching sources: `232.902`.
- Earliest+exception total bits: `58.085`.
- Earliest+exception delta vs oracle rank: `-174.817` bits.
- Earliest+exception delta vs legal source: `-2492.509` bits.

## Random Rank Controls

- Trials: `10000`.
- Earliest-hit mean/p95/max: `120.011` / `129.000` / `139`.
- P(random earliest hits >= observed): `0.0000`.
- Random exception cost mean/p05/p95: `323.457` / `308.651` / `336.490`.

## Non-Earliest Exceptions

| Book | Op | Target | Length | Canonical rank | Matching sources |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `12` | `4` | `37` | `10` | `4` | `5` |
| `12` | `6` | `51` | `7` | `7` | `8` |
| `17` | `0` | `0` | `7` | `1` | `4` |
| `23` | `1` | `4` | `14` | `3` | `4` |
| `49` | `6` | `61` | `8` | `8` | `9` |
| `55` | `2` | `67` | `44` | `1` | `2` |
| `57` | `4` | `141` | `33` | `1` | `2` |
| `59` | `0` | `0` | `141` | `2` | `3` |

## Decision

- Target-conditioned source-collapse clue: `True`.
- Promotes source generator: `False`.
- This is not a decoder-side generator because it grants the future copied chunk.
- The result shifts the blocker toward a target-stream mechanism: if copied chunks are generated first, source choice becomes mostly canonical.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
