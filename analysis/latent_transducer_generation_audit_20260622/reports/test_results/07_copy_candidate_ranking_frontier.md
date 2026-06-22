# Copy Candidate Ranking Frontier

Classification: `simple_copy_candidate_ranking_not_promoted`
Translation delta: `NONE`

## Purpose

Test whether the copy-state blocker can be rescued by simple target-free
chunk ranking policies at the same top-k budget used by the closed-loop
candidate generator.

## Summary

- Unique sampled copy ops: `32`.
- Instance-weighted sampled copy ops: `42`.
- Raw inventory prefix digits: `1063/1240` (`0.857258`).
- Current source-penalty unique hits/digits: `1` / `6`.
- Best unique policy: `longest_recent`.
- Best unique hits/digits: `3` / `56`.
- Best unique prefix digit fraction: `0.045161`.
- Random top-k digit p95: `55`.
- Best beats random digit p95: `True`.
- Promotes copy ranking rule: `False`.

Target-free ranking policies can improve over the current source penalty pruning, with longest/recent and frequency-first variants providing weak signals, but the best policy still retains only a small fraction of canonical copy digits. This keeps copy candidate ranking open as a blocker, not as a solved generator component.

## Unique-Op Policy Frontier

| Policy | Hits | Full Hits | Prefix Digits | Prefix Digit Fraction |
| --- | ---: | ---: | ---: | ---: |
| `current_source_penalty` | `1` | `0` | `6` | `0.004839` |
| `earliest_longest` | `1` | `0` | `6` | `0.004839` |
| `recent_longest` | `2` | `0` | `48` | `0.038710` |
| `longest_recent` | `3` | `2` | `56` | `0.045161` |
| `frequent_longest` | `7` | `1` | `39` | `0.031452` |
| `rare_longest` | `0` | `0` | `0` | `0.000000` |

## Cutoff Rows

| Cutoff | Books | Copy Ops | Best Policy | Best Hits | Best Prefix Digits | Current Prefix Digits |
| ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `20` | `[20, 45, 69]` | `11` | `frequent_longest` | `3` | `18` | `6` |
| `30` | `[30, 50, 69]` | `8` | `frequent_longest` | `3` | `16` | `0` |
| `40` | `[40, 55, 69]` | `8` | `recent_longest` | `2` | `48` | `0` |
| `50` | `[50, 60, 69]` | `7` | `frequent_longest` | `2` | `10` | `0` |
| `60` | `[60, 65, 69]` | `8` | `frequent_longest` | `2` | `10` | `0` |

## Decision

- Simple target-free chunk ranking is not enough to rescue the closed-loop generator.
- Longest/recent and frequency-first rankings are weak clues because they improve over current pruning, but coverage is too small for promotion.
- The next constructive route must add a richer copy-control state or a paid copy hint stream.
- Row0, plaintext, translation, and compression bound remain unchanged.
