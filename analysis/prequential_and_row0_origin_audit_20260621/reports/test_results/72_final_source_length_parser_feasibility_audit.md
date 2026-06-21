# Final Source/Length Parser Feasibility Audit

Classification: `final_source_length_parser_feasible_by_proxy_not_tractable_full_suffix`
Translation delta: `NONE`

## Purpose

Gate 71 showed that the final formula still needs a source/length parser.
This audit recomputes candidate-state and transition proxies on the
current `8154.676268`-bit formula to decide how to attack that parser
without running an unbounded suffix DP.

## Summary

- Total old frozen-count DP states: `85350`.
- Total previous-end state proxy: `26758611`.
- Total copy-transition proxy: `1966897365`.
- End-state proxy multiplier over old DP: `313.5x`.
- Transition proxy multiplier over old DP: `23045.1x`.
- All books below `1,000,000` end-state proxy: `True`.
- Cutoff 60 max book end-state proxy: `258264`.
- Cutoff 60 max book transition proxy: `26096904`.
- Cutoff 60 books below `250,000` end-state proxy: `9/10`.

## Prefix Frontier

| Cutoff | Books | Old states | End proxy | Transition proxy | End/old | Transition/old | <=250k | <=1m | Max transition |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `10` | `60` | `28881` | `8286852` | `577278498` | `286.9` | `19988.2` | `51` | `60` | `78675822` |
| `20` | `50` | `23925` | `7288953` | `520639734` | `304.7` | `21761.3` | `42` | `50` | `78675822` |
| `35` | `35` | `17610` | `6068094` | `471714906` | `344.6` | `26786.8` | `27` | `35` | `78675822` |
| `50` | `20` | `10527` | `4035321` | `329219349` | `383.3` | `31273.8` | `14` | `20` | `78675822` |
| `60` | `10` | `4407` | `1079391` | `68044878` | `244.9` | `15440.2` | `9` | `10` | `26096904` |

## Hardest Books By Transition Proxy

| Cutoff | Book | Digits | End proxy | Transition proxy | Copy edges | Distinct end states |
|---:|---:|---:|---:|---:|---:|---:|
| `10` | `53` | `271` | `598128` | `78675822` | `35778` | `733` |
| `20` | `53` | `271` | `598128` | `78675822` | `35778` | `733` |
| `35` | `53` | `271` | `598128` | `78675822` | `35778` | `733` |
| `50` | `53` | `271` | `598128` | `78675822` | `35778` | `733` |
| `10` | `51` | `268` | `585075` | `73167000` | `33640` | `725` |
| `20` | `51` | `268` | `585075` | `73167000` | `33640` | `725` |
| `35` | `51` | `268` | `585075` | `73167000` | `33640` | `725` |
| `50` | `51` | `268` | `585075` | `73167000` | `33640` | `725` |
| `10` | `35` | `286` | `525210` | `71395620` | `39014` | `610` |
| `20` | `35` | `286` | `525210` | `71395620` | `39014` | `610` |
| `35` | `35` | `286` | `525210` | `71395620` | `39014` | `610` |
| `10` | `58` | `272` | `614250` | `66206250` | `29425` | `750` |

## Decision

- Compression to previous_copy_end keeps all per-book end-state proxies below one million, but the transition proxy is still hundreds to thousands of times the old frozen-count DP. A full suffix parser should be built with per-book pruning/caching or decomposed by hard books, not run as one naive cutoff-60 DP.
- No compression-bound change is introduced.
- No parser or recipe-discovery promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
