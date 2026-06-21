# Online Order Frontier Controls

Classification: `online_frontier_predictive_but_not_numeric_order_unique`
Translation delta: `NONE`

## Purpose

Audit 17 showed that previous-books-only online reparsing beats raw digit
coding for `69/69` books after the numeric-order bootstrap book. Audit 130
tested full-formula order controls only as aggregate bit counts. This
audit combines those questions: it reruns the book-bounded online frontier
under the same named and random order controls and measures the
after-bootstrap per-book raw-win frontier.

## Summary

- Orders tested: `11`.
- Numeric after-bootstrap raw wins: `69/69`.
- Numeric failure books: `[0]`.
- Numeric after-bootstrap failures: `[]`.
- Orders with perfect after-bootstrap raw wins: `10/11`.
- Random orders with perfect after-bootstrap raw wins: `6/6`.
- Best after-bootstrap mean-gain order: `random_04` (`+0.549` bits vs numeric mean).
- Best total-gain order: `random_04` (`+61.452` bits vs numeric total).

## Order Table

| Order | Family | Raw wins | After bootstrap | Failures | Mean after gain | Total gain | Delta total vs numeric |
|---|---|---:|---:|---|---:|---:|---:|
| `numeric` | `canonical` | `69/70` | `69/69` | `[0]` | `425.997` | `29383.262` | `+0.000` |
| `reverse_numeric` | `simple_control` | `69/70` | `69/69` | `[69]` | `418.567` | `28876.194` | `-507.068` |
| `evens_then_odds` | `simple_control` | `69/70` | `69/69` | `[0]` | `424.656` | `29290.744` | `-92.518` |
| `odds_then_evens` | `simple_control` | `69/70` | `69/69` | `[1]` | `425.434` | `29353.372` | `-29.890` |
| `length_ascending` | `content_derived_control` | `68/70` | `67/69` | `[54, 7]` | `419.171` | `28937.953` | `-445.308` |
| `random_00` | `random_permutation_control` | `69/70` | `69/69` | `[58]` | `423.316` | `29197.409` | `-185.853` |
| `random_01` | `random_permutation_control` | `70/70` | `69/69` | `[]` | `423.063` | `29191.973` | `-191.288` |
| `random_02` | `random_permutation_control` | `70/70` | `69/69` | `[]` | `423.019` | `29228.474` | `-154.788` |
| `random_03` | `random_permutation_control` | `69/70` | `69/69` | `[23]` | `423.733` | `29214.952` | `-168.310` |
| `random_04` | `random_permutation_control` | `70/70` | `69/69` | `[]` | `426.545` | `29444.713` | `+61.452` |
| `random_05` | `random_permutation_control` | `69/70` | `69/69` | `[6]` | `423.982` | `29230.514` | `-152.747` |

## Highest Mean After-Bootstrap Gains

| Rank | Order | Family | Mean after gain | After failures |
|---:|---|---|---:|---|
| 1 | `random_04` | `random_permutation_control` | `426.545` | `[]` |
| 2 | `numeric` | `canonical` | `425.997` | `[]` |
| 3 | `odds_then_evens` | `simple_control` | `425.434` | `[]` |
| 4 | `evens_then_odds` | `simple_control` | `424.656` | `[]` |
| 5 | `random_05` | `random_permutation_control` | `423.982` | `[]` |
| 6 | `random_03` | `random_permutation_control` | `423.733` | `[]` |
| 7 | `random_00` | `random_permutation_control` | `423.316` | `[]` |
| 8 | `random_01` | `random_permutation_control` | `423.063` | `[]` |

## Highest Total Gains

| Rank | Order | Family | Total gain | Delta vs numeric | Break-even position |
|---:|---|---|---:|---:|---:|
| 1 | `random_04` | `random_permutation_control` | `29444.713` | `+61.452` | `0` |
| 2 | `numeric` | `canonical` | `29383.262` | `+0.000` | `2` |
| 3 | `odds_then_evens` | `simple_control` | `29353.372` | `-29.890` | `1` |
| 4 | `evens_then_odds` | `simple_control` | `29290.744` | `-92.518` | `1` |
| 5 | `random_05` | `random_permutation_control` | `29230.514` | `-152.747` | `2` |
| 6 | `random_02` | `random_permutation_control` | `29228.474` | `-154.788` | `0` |
| 7 | `random_03` | `random_permutation_control` | `29214.952` | `-168.310` | `1` |
| 8 | `random_00` | `random_permutation_control` | `29197.409` | `-185.853` | `1` |

## Interpretation

The numeric previous-book frontier remains predictive after the
bootstrap position, but the criterion is not unique: at least one
control order also reaches a perfect after-bootstrap raw-win
frontier. The result therefore strengthens the predictive-parser
signal while rejecting the stronger claim that numeric order is
proved by the per-book frontier alone.

## Boundary

- No compression bound is promoted by this audit.
- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0/table origin remains exogenous.
- After-bootstrap means position `1..69` of each tested order, not book IDs `1..69`.
