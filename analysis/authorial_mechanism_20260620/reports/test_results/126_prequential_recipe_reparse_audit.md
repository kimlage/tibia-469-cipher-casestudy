# 126. Prequential Recipe Reparse Audit

Classification: `deterministic_recipe_reparse_predictive_improves_active_suffix`
Translation delta: `NONE`

## Purpose

Audit 125 showed that learned component streams retain holdout signal,
but it left the recipe itself fixed from the full corpus. This audit
tests that limitation directly: for each prefix cutoff, it learns only
component counts from the train prefix, then reparses the future suffix
with a deterministic LZ parser under the frozen active parameters.

## Result

| Cutoff | Test books | Raw digits | Active recipe frozen | Reparse frozen | Reparse gain vs raw | Reparse - active | Roundtrip |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `10` | `60` | `31780.886` | `5117.007` | `4928.668` | `26852.219` | `-188.339` | `60/60` |
| `20` | `50` | `26326.280` | `3622.075` | `3483.662` | `22842.618` | `-138.413` | `50/50` |
| `35` | `35` | `19383.450` | `2343.277` | `2219.894` | `17163.556` | `-123.382` | `35/35` |
| `50` | `20` | `11590.207` | `1239.982` | `1148.528` | `10441.679` | `-91.454` | `20/20` |
| `60` | `10` | `4846.693` | `401.448` | `379.438` | `4467.255` | `-22.010` | `10/10` |

## Interpretation

The deterministic parser can encode every future suffix, beats raw
uniform digit coding at every cutoff, and is cheaper than the active
full-corpus recipe under the same frozen train-prefix counts. This
is stronger than the audit-125 component-only result: a fixed
mechanical parser can rediscover useful suffix recipes without
retuning on the suffix.

This remains analysis-only because it is a split-specific predictive
test, not a new full-corpus charged formula. It does not lower
`compression_bound`, derive `row0`, translate the books, or promote
an authorial method.
