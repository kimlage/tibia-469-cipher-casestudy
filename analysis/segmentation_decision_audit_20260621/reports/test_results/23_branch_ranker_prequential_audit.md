# Branch Ranker Prequential Audit

Classification: `branch_ranker_prequential_rejected`
Translation delta: `NONE`

## Purpose

Gate 23 asks whether the branch choices rejected by gate 22 can be
learned as a small prefix-trained ranker. The ranker sees only
observable branch and continuation features; stable projection is
used as the training/evaluation label, not as a feature.

## Scoreboard

- Decisions: `234`.
- Residual decisions: `10`.
- Clean controls: `224`.
- Features: `17`.
- Training modes: `['uniform', 'residual_weight5', 'residual_weight20', 'residual_only']`.

| Model | Total hits | Residual hits | Clean false changes |
|---|---:|---:|---:|
| Active-branch baseline | `224/234` | `0/10` | `0` |
| Full-fit pairwise ranker `residual_weight20` | `223/234` | `0/10` | `1` |

## Full-Fit Modes

| Mode | Total hits | Residual hits | Clean false changes |
|---|---:|---:|---:|
| `residual_weight20` | `223/234` | `0/10` | `1` |
| `uniform` | `222/234` | `0/10` | `2` |
| `residual_weight5` | `221/234` | `0/10` | `3` |
| `residual_only` | `10/234` | `7/10` | `221` |

## Prefix/Holdout

| Cutoff | Mode | Train hits | Test hits | Test residual hits | Test clean false changes |
|---:|---|---:|---:|---:|---:|
| `20` | `uniform` | `69/71` | `155/163` | `0/8` | `0` |
| `30` | `uniform` | `99/104` | `122/130` | `1/5` | `4` |
| `40` | `uniform` | `140/146` | `81/88` | `0/3` | `4` |
| `50` | `residual_weight5` | `172/184` | `45/50` | `0/2` | `3` |
| `60` | `residual_weight20` | `204/214` | `19/20` | `0/0` | `1` |

## Permutation Control

- Controls: `100`.
- Total-hit range under random branch labels: `0..207`.
- Median total hits under random branch labels: `2`.
- Max residual hits under random branch labels: `6`.
- Minimum clean false changes under random branch labels: `22`.
- `p(total_hits >= real_full_fit)`: `0.010`.

## Decision

- Promotes branch ranker: `False`.
- Prequential zero-clean-false-change cells: `1/5`.
- Prequential cover-all-test-residual cells: `1/5`.
- Gate 23 trains a small pairwise branch ranker on prefix stable-projection labels and evaluates it on future books. Features are observable branch and continuation metrics; stable prefix match is not used as a feature.
- The learned ranker does not become a generative parser under prefix/holdout.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
