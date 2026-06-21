# Literal Gap Boundary Audit

Classification: `literal_gap_local_window_clue_source_free_window_not_promoted`
Translation delta: `NONE`

## Purpose

The copy parser rule reduces `(source,length)` once copy starts are
known. This gate tests whether literal gaps and copy starts are also
derivable by simple lookahead objectives.

## Scoreboard

| Hypothesis | Hits | Boundary |
|---|---:|---|
| Stop at first available match | `23/54` | rejected |
| Stop at local-window best copy length | `54/54` | declared-window clue |
| Stop at local-window best literal+copy advance | `54/54` | declared-window clue |
| Stop at full-suffix best literal+copy advance | `11/49` | source-free rule rejected |

## Diagnostics

- Literal gaps: `54`.
- Literal gaps followed by copy: `49`.
- Copy available at literal start: `17`.
- Future stable copy improves immediate copy in `48` followed-by-copy gaps.
- Promotes local-window boundary clue: `True`.
- Promotes source-free literal-window rule: `False`.

## Decision

- Inside each declared literal window, the stable boundary is the point that maximizes literal offset plus next-copy length. This explains why first-match greedy parsing fails, but it does not derive the literal window itself: over the full remaining suffix, the same objective selects the stable boundary in only a minority of followed-by-copy literal gaps.
- The operation-start/literal-window atlas remains retained.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
