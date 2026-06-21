# Active Source-Length Joint Refresh Gate

Classification: `active_source_length_joint_refresh_encoder_gain_decoder_boundary_unchanged`
Translation delta: `NONE`

## Purpose

Gate 49 tested joint source/length derivability on the source-substitution
fourth-pass formula. This refresh repeats the same structural checks on
the active post-target-max formula. It does not search new sources,
lengths, plaintext, or another compression bound.

## Formula Comparison

| Metric | Previous | Active | Delta |
|---|---:|---:|---:|
| Copy events | `261` | `261` | `+0` |
| Copied digits | `10406` | `10407` | `+1` |
| Earliest source at declared length | `251` | `247` | `-4` |
| Encoder target-max length | `238` | `242` | `+4` |
| Joint earliest+target-max | `230` | `230` | `+0` |
| Declared-source+decoder-max | `60` | `60` | `+0` |
| Unique-source+decoder-max | `28` | `28` | `+0` |
| Previous-end+decoder-max | `1` | `1` | `+0` |

## Controls

- Active target-max permutation p-value: `0.0000`.
- Active decoder-max permutation p-value: `0.0000`.
- Changed ops between formulas: `12`.

## Result

- Active target-max hit delta: `+4`.
- Active earliest-source hit delta: `-4`.
- Active joint earliest+target-max delta: `+0`.
- Declared-source+decoder-max delta: `+0`.
- Unique-source+decoder-max delta: `+0`.
- Previous-end+decoder-max delta: `+0`.
- Decoder-valid joint rule improved: `False`.
- Interpretation: The active formula converts four additional copy lengths into target-max hits, but this is encoder-side evidence only. The decoder-valid joint checks do not improve: declared-source plus decoder-max stays at 60/261, unique-source plus decoder-max stays at 28/261, and previous-end plus decoder-max stays at 1/261.

## Decision

- The active formula improves encoder-side target-max regularity but not a decoder-valid source/length derivation.
- Source and copy length remain declared dependencies.
- Current compression bound remains `8156.049986` bits.

## Boundary

- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0 origin remains unchanged and exogenous.
- No new formula is emitted.
