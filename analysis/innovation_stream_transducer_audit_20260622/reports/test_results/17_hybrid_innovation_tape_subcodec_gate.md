# Hybrid Innovation Tape Subcodec Gate

Classification: `hybrid_innovation_tape_subcodec_rejected`
Translation delta: `NONE`

## Purpose

Test whether the innovation tape can be reduced by a paid hybrid
subcodec that copies from seed-book text or from prior emitted tape,
instead of keeping all `266` digits as raw literal payload.

## Summary

- Literal tape digits: `266`.
- Seed text digits: `1696`.
- Raw tape bits: `883.633`.
- Best strategy/min_len: `max_cover` / `5`.
- Best total bits: `1075.983`.
- Best saving vs raw: `-192.350`.
- Best control saving p95: `-247.339`.
- Best copy/literal digits: `90` / `176`.
- Best copy items seed/prior: `14` / `3`.
- Best coverage strategy/min_len: `max_cover` / `2`.
- Best coverage digits/control p95: `266` / `266.000`.
- Promotes hybrid subcodec: `False`.
- Weak hybrid subcodec clue: `False`.

This gate tests a stronger paid subcodec for the innovation tape: copies may reference either seed-book text or prior emitted tape, with explicit mode, origin, source, length, and literal costs. It compares paid savings against raw tape and same-multiset shuffled controls.

## Rows

| Strategy | Min len | Total bits | Saving | Control p95 | Copy digits | Literal digits | Copy items | Seed/Prior items | Coverage p95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `max_cover` | `5` | `1075.983` | `-192.350` | `-247.339` | `90` | `176` | `17` | `14/3` | `25.000` |
| `max_cover` | `6` | `1098.528` | `-214.895` | `-254.973` | `38` | `228` | `6` | `5/1` | `6.000` |
| `local_saving` | `5` | `1112.452` | `-228.820` | `-253.129` | `27` | `239` | `5` | `2/3` | `10.000` |
| `local_saving` | `2` | `1114.473` | `-230.840` | `-251.836` | `26` | `240` | `5` | `1/4` | `11.000` |
| `local_saving` | `3` | `1114.473` | `-230.840` | `-250.685` | `26` | `240` | `5` | `1/4` | `10.050` |
| `local_saving` | `4` | `1114.473` | `-230.840` | `-251.405` | `26` | `240` | `5` | `1/4` | `11.000` |
| `local_saving` | `6` | `1114.835` | `-231.202` | `-256.170` | `20` | `246` | `3` | `2/1` | `6.000` |
| `max_cover` | `7` | `1131.692` | `-248.059` | `-266.000` | `8` | `258` | `1` | `1/0` | `0.000` |
| `max_cover` | `8` | `1131.692` | `-248.059` | `-266.000` | `8` | `258` | `1` | `1/0` | `0.000` |
| `local_saving` | `7` | `1131.692` | `-248.059` | `-266.000` | `8` | `258` | `1` | `1/0` | `0.000` |
| `local_saving` | `8` | `1131.692` | `-248.059` | `-266.000` | `8` | `258` | `1` | `1/0` | `0.000` |
| `max_cover` | `4` | `1137.561` | `-253.928` | `-261.022` | `159` | `107` | `36` | `30/6` | `80.050` |
| `max_cover` | `3` | `1337.407` | `-453.774` | `-508.754` | `237` | `29` | `65` | `51/14` | `201.000` |
| `max_cover` | `2` | `1520.279` | `-636.646` | `-912.030` | `266` | `0` | `84` | `53/31` | `266.000` |

## Decision

- The hybrid seed+prior-tape subcodec is promoted only if paid bits beat raw tape and shuffled controls.
- Coverage alone is not enough; source, origin, length, mode, and residual literal costs are charged.
- Under this gate the literal innovation tape remains an external payload dependency.
- Row0, plaintext, translation, and compression bound remain unchanged.
