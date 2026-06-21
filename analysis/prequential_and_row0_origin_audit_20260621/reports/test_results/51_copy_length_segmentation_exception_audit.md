# Copy Length Segmentation Exception Audit

Classification: `copy_length_target_max_exceptions_are_partial_next_op_intrusions`
Translation delta: `NONE`

## Purpose

The target-max copy-length rule matches most copy events, but it is
encoder-only and has `23` exceptions. This audit maps those exceptions
as segmentation boundaries: if the copy were extended to target-max,
which following operations would be crossed or absorbed?

## Summary

- Copy events: `261`.
- Target-max matches/exceptions: `238` / `23`.
- Exception fraction: `0.088123`.
- Total target-max slack digits in exceptions: `128`.
- Slack min/mean/max: `1` / `5.565` / `72`.
- Exceptions reaching book end: `0`.
- Exceptions covering exactly one following op: `23`.
- Exceptions absorbing the full next op: `0`.
- Exceptions where slack equals first following op length: `0`.
- Exceptions with partial following-op cover: `23`.
- Covered following digits by type: `{'copy': 126, 'literal': 2}`.
- Fully covered following ops by type: `{}`.

## Exception Rows

| Book | Op | Pos | Source | Length | Target max | Slack | First next type | Covered ops | Full ops | Book end |
|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| `2` | `9` | `130` | `101` | `6` | `7` | `1` | `literal` | `1` | `0` | `False` |
| `9` | `0` | `0` | `695` | `267` | `271` | `4` | `copy` | `1` | `0` | `False` |
| `10` | `0` | `0` | `888` | `6` | `78` | `72` | `copy` | `1` | `0` | `False` |
| `13` | `4` | `48` | `4` | `7` | `8` | `1` | `copy` | `1` | `0` | `False` |
| `13` | `8` | `82` | `90` | `6` | `7` | `1` | `copy` | `1` | `0` | `False` |
| `14` | `3` | `115` | `889` | `6` | `7` | `1` | `copy` | `1` | `0` | `False` |
| `17` | `7` | `213` | `2514` | `9` | `10` | `1` | `literal` | `1` | `0` | `False` |
| `20` | `2` | `21` | `180` | `9` | `10` | `1` | `copy` | `1` | `0` | `False` |
| `20` | `5` | `45` | `459` | `9` | `10` | `1` | `copy` | `1` | `0` | `False` |
| `21` | `1` | `9` | `2116` | `133` | `135` | `2` | `copy` | `1` | `0` | `False` |
| `23` | `8` | `117` | `275` | `11` | `12` | `1` | `copy` | `1` | `0` | `False` |
| `24` | `0` | `0` | `3413` | `36` | `37` | `1` | `copy` | `1` | `0` | `False` |
| `28` | `1` | `89` | `2778` | `6` | `7` | `1` | `copy` | `1` | `0` | `False` |
| `28` | `2` | `95` | `2160` | `11` | `12` | `1` | `copy` | `1` | `0` | `False` |
| `30` | `3` | `60` | `2232` | `19` | `20` | `1` | `copy` | `1` | `0` | `False` |
| `34` | `4` | `69` | `129` | `22` | `23` | `1` | `copy` | `1` | `0` | `False` |
| `46` | `1` | `124` | `2320` | `17` | `20` | `3` | `copy` | `1` | `0` | `False` |
| `51` | `0` | `0` | `6977` | `127` | `134` | `7` | `copy` | `1` | `0` | `False` |
| `54` | `0` | `0` | `3350` | `49` | `51` | `2` | `copy` | `1` | `0` | `False` |
| `56` | `5` | `141` | `2260` | `12` | `13` | `1` | `copy` | `1` | `0` | `False` |
| `56` | `8` | `236` | `2157` | `8` | `9` | `1` | `copy` | `1` | `0` | `False` |
| `61` | `0` | `0` | `4514` | `112` | `122` | `10` | `copy` | `1` | `0` | `False` |
| `65` | `0` | `0` | `4511` | `112` | `125` | `13` | `copy` | `1` | `0` | `False` |

## Interpretation

The non-target-max copy lengths are not random length noise. In every
case, extending the copy to target-max would enter exactly one following
operation and stop inside it; it never cleanly absorbs a whole next op.
This explains why a length-only target-max rule cannot be promoted: the
missing mechanism is a joint segmentation/source/length parser, not
another scalar copy-length default.

## Boundary

- No new formula is emitted.
- Compression bound is unchanged.
- Copy length remains declared in the current formula.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
