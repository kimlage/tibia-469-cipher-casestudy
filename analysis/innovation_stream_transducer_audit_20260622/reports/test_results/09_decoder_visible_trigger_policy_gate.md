# Decoder Visible Trigger Policy Gate

Classification: `decoder_visible_trigger_policy_rejected`
Translation delta: `NONE`

## Purpose

Test whether the promoted literal-vs-copy trigger clue survives after
removing target-conditioned copy availability. Known operation starts,
true prior prefix, and true tape state are still granted.

## Summary

- Operation starts: `261`.
- Literal ops: `53`.
- Copy ops: `208`.
- Best overall feature: `global_majority`.
- Best overall cutoff: `20`.
- Best overall exact ops: `155/182`.
- Best overall saving vs literal-site lookup: `0.000` bits.
- Best global exact ops: `155/182`.
- Best global saving vs literal-site lookup: `0.000` bits.
- Best decoder-visible feature: `next_digit_seen`.
- Best decoder-visible cutoff: `20`.
- Best decoder-visible exact ops: `155/182`.
- Best decoder-visible literal hits: `0/27`.
- Best decoder-visible errors: `27`.
- Best decoder-visible saving vs lookup: `-4.807` bits.
- Best decoder-visible delta vs global: `-4.807` bits.
- Best decoder-visible exact delta vs global: `0`.
- Conditional trigger delta bits: `48.262`.
- Target-conditioning gap bits: `48.262`.
- Random delta bits p95: `-4.807`.
- Random delta exact p95: `0.000`.
- Random exact p95: `150.000`.
- Promotes decoder-visible trigger: `False`.
- Weak decoder-visible trigger: `False`.

This gate removes the target-conditioned copy-availability feature from the trigger policy while still granting known operation starts, true prior prefix, and true tape state. It tests whether the previous trigger clue survives with decoder-visible information.

## Best Rows

| Cutoff | Feature | Exact | Literals hit | Errors | Lookup bits | Total bits | Saving | Delta bits | Delta exact | Contexts |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `global_majority` | `155/182` | `0/27` | `27` | `106.645` | `106.645` | `0.000` | `0.000` | `0` | `0` |
| `30` | `global_majority` | `119/140` | `0/21` | `21` | `81.967` | `81.967` | `0.000` | `0.000` | `0` | `0` |
| `40` | `global_majority` | `80/95` | `0/15` | `15` | `56.615` | `56.615` | `0.000` | `0.000` | `0` | `0` |
| `50` | `global_majority` | `49/56` | `0/7` | `7` | `27.789` | `27.789` | `0.000` | `0.000` | `0` | `0` |
| `60` | `global_majority` | `18/20` | `0/2` | `2` | `7.570` | `7.570` | `0.000` | `0.000` | `0` | `0` |
| `20` | `next_digit_seen` | `155/182` | `0/27` | `27` | `106.645` | `111.453` | `-4.807` | `-4.807` | `0` | `1` |
| `20` | `next_digit_count_bucket` | `155/182` | `0/27` | `27` | `106.645` | `111.453` | `-4.807` | `-4.807` | `0` | `1` |
| `30` | `next_digit_seen` | `119/140` | `0/21` | `21` | `81.967` | `86.774` | `-4.807` | `-4.807` | `0` | `1` |
| `30` | `next_digit_count_bucket` | `119/140` | `0/21` | `21` | `81.967` | `86.774` | `-4.807` | `-4.807` | `0` | `1` |
| `60` | `next_digit_seen` | `18/20` | `0/2` | `2` | `7.570` | `12.377` | `-4.807` | `-4.807` | `0` | `1` |
| `60` | `next_digit_count_bucket` | `18/20` | `0/2` | `2` | `7.570` | `12.377` | `-4.807` | `-4.807` | `0` | `1` |
| `40` | `next_digit_seen` | `80/95` | `0/15` | `15` | `56.615` | `61.423` | `-4.807` | `-4.807` | `0` | `1` |

## Decision

- The decoder-visible trigger policy is not promoted unless a non-global feature beats the copy-majority baseline and shuffled-label controls after table/correction cost.
- Under current features, the promoted trigger clue from the conditional gate does not survive removal of target-conditioned copy availability.
- This preserves the prior conditional clue but classifies target-conditioned copy availability as an unresolved dependency.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
