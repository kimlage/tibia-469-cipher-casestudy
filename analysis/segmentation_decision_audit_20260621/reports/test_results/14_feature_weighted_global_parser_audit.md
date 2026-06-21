# Feature Weighted Global Parser Audit

Classification: `feature_weighted_global_parser_rejected`
Translation delta: `NONE`

## Purpose

Gate 13 rejected crude global objectives. This gate tests a slightly
richer path-state family: book-local DP with feature-weighted costs for
literal mass, copy base cost, short-copy penalties, and book-start-copy
penalties.

## Scoreboard

- Profiles tested: `16`.
- Window5 baseline exact books: `48/60`.
- Best profile: `no_copy_reward`.
- Best exact books: `26/60`.
- Exact-book improvement vs window5: `-22`.

| Profile | Exact books | Ops | Literal gaps | Literal digits | Copies |
|---|---:|---:|---:|---:|---:|
| `copy_base_heavy` | `26/60` | `225` | `64` | `598` | `161` |
| `no_copy_reward` | `26/60` | `265` | `42` | `204` | `223` |
| `copy_moderate` | `25/60` | `276` | `47` | `175` | `229` |
| `literal_run_heavy` | `25/60` | `242` | `43` | `348` | `199` |
| `copy_light` | `23/60` | `283` | `36` | `142` | `247` |
| `shortcopy_guard` | `23/60` | `242` | `53` | `410` | `189` |
| `copy_conservative` | `5/60` | `294` | `95` | `368` | `199` |
| `copy_length_reward2` | `5/60` | `321` | `95` | `231` | `226` |
| `copy_very_conservative` | `5/60` | `282` | `106` | `510` | `176` |
| `literal_expensive_guarded` | `5/60` | `295` | `94` | `367` | `201` |
| `literal_tolerant` | `5/60` | `282` | `106` | `510` | `176` |
| `literal_expensive` | `4/60` | `326` | `95` | `216` | `231` |
| `stable_like_mid` | `4/60` | `287` | `98` | `449` | `189` |
| `bookstart_guard` | `3/60` | `326` | `97` | `225` | `229` |
| `copy_base_light_guarded` | `3/60` | `292` | `98` | `428` | `194` |
| `guarded_both` | `3/60` | `287` | `101` | `472` | `186` |

## Prequential Profile Selection

| Cutoff | Selected | Train hits | Test hits | Oracle | Oracle test hits |
|---:|---|---:|---:|---|---:|
| `20` | `no_copy_reward` | `3/10` | `23/50` | `no_copy_reward` | `23/50` |
| `30` | `no_copy_reward` | `7/20` | `19/40` | `no_copy_reward` | `19/40` |
| `40` | `copy_base_heavy` | `11/30` | `15/30` | `no_copy_reward` | `16/30` |
| `50` | `no_copy_reward` | `14/40` | `12/20` | `literal_run_heavy` | `13/20` |
| `60` | `copy_base_heavy` | `19/50` | `7/10` | `no_copy_reward` | `8/10` |

## Mismatch Sample

| Book | Predicted ops | Stable ops | First diff |
|---:|---:|---:|---|
| `10` | `2` | `2` | `{"index": 0, "predicted": {"length": 9, "source": 888, "target_start": 0, "type": "copy"}, "stable_projection": {"length": 5, "source": null, "target_start": 0, "type": "literal"}}` |
| `12` | `14` | `13` | `{"index": 5, "predicted": {"length": 4, "source": null, "target_start": 47, "type": "literal"}, "stable_projection": {"length": 9, "source": null, "target_start": 47, "type": "literal"}}` |
| `13` | `10` | `9` | `{"index": 4, "predicted": {"length": 7, "source": 4, "target_start": 48, "type": "copy"}, "stable_projection": {"length": 8, "source": 4, "target_start": 48, "type": "copy"}}` |
| `14` | `8` | `8` | `{"index": 2, "predicted": {"length": 5, "source": 510, "target_start": 45, "type": "copy"}, "stable_projection": {"length": 5, "source": null, "target_start": 45, "type": "literal"}}` |
| `15` | `11` | `11` | `{"index": 7, "predicted": {"length": 7, "source": 1392, "target_start": 95, "type": "copy"}, "stable_projection": {"length": 8, "source": 2550, "target_start": 95, "type": "copy"}}` |
| `16` | `11` | `12` | `{"index": 5, "predicted": {"length": 10, "source": 865, "target_start": 132, "type": "copy"}, "stable_projection": {"length": 12, "source": 865, "target_start": 132, "type": "copy"}}` |
| `17` | `14` | `14` | `{"index": 4, "predicted": {"length": 130, "source": 420, "target_start": 16, "type": "copy"}, "stable_projection": {"length": 133, "source": 420, "target_start": 16, "type": "copy"}}` |
| `20` | `7` | `7` | `{"index": 2, "predicted": {"length": 9, "source": 180, "target_start": 21, "type": "copy"}, "stable_projection": {"length": 10, "source": 180, "target_start": 21, "type": "copy"}}` |
| `21` | `3` | `3` | `{"index": 1, "predicted": {"length": 109, "source": 2116, "target_start": 9, "type": "copy"}, "stable_projection": {"length": 135, "source": 2116, "target_start": 9, "type": "copy"}}` |
| `23` | `12` | `12` | `{"index": 8, "predicted": {"length": 11, "source": 275, "target_start": 117, "type": "copy"}, "stable_projection": {"length": 12, "source": 275, "target_start": 117, "type": "copy"}}` |

## Decision

- Promotes feature-weighted parser: `False`.
- Feature-weighted DP tests whether a small structural cost over literal mass, copy base cost, short-copy penalties, and book-start copy penalties can replace the local peak parser.
- The result remains target-text-aware and analysis-only.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
