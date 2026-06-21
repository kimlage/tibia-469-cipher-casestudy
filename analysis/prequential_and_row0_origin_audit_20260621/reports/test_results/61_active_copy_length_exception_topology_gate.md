# Active Copy Length Exception Topology Gate

Classification: `active_copy_length_exceptions_still_partial_next_op_intrusions`
Translation delta: `NONE`

## Purpose

Gate 51 mapped the 23 target-max exceptions on the source-substitution
fourth-pass formula. Gate 60 showed the active formula has four more
target-max hits. This gate maps the remaining active exceptions without
searching another resegmentation or compression improvement.

## Comparison

| Metric | Previous | Active | Delta |
|---|---:|---:|---:|
| Target-max matches | `238` | `242` | `+4` |
| Target-max exceptions | `23` | `19` | `-4` |
| Slack digits total | `128` | `115` | `-13` |
| Removed exception rows | `0` | `4` | `+4` |
| Added exception rows | `0` | `0` | `+0` |

## Active Topology

- Active exceptions: `19`.
- Active exceptions covering exactly one following op: `19`.
- Active exceptions with partial following-op cover: `19`.
- Active exceptions absorbing a full next op: `0`.
- Active exceptions reaching book end: `0`.
- Active covered following digits by type: `{'copy': 114, 'literal': 1}`.
- Active fully covered following ops by type: `{}`.

## Removed Exception Rows

| Book | Op | Pos | Source | Length | Target max | Slack | First next type |
|---:|---:|---:|---:|---:|---:|---:|---|
| `2` | `9` | `130` | `101` | `6` | `7` | `1` | `literal` |
| `9` | `0` | `0` | `695` | `267` | `271` | `4` | `copy` |
| `51` | `0` | `0` | `6977` | `127` | `134` | `7` | `copy` |
| `56` | `8` | `236` | `2157` | `8` | `9` | `1` | `copy` |

## Decision

- Active all-partial-single-next topology: `True`.
- Interpretation: The target-max resegmentation path eliminates four old length exceptions and reduces slack by 13 digits, but every remaining active exception still crosses into exactly one following op and stops inside it. The residual problem is still joint segmentation, not a scalar length-default choice.
- Current compression bound remains `8156.049986` bits.
- Copy length remains a declared dependency until a joint segmentation/source/length parser derives these boundaries.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- No new formula is emitted.
- No new resegmentation is searched.
