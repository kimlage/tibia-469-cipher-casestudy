# Prequential Generation Model Audit

Verdict: `prequential_generation_partial_not_final`. Translation delta: `NONE`.

This audit separates the current `compression_bound` from a stronger
`generation_explanation` claim. It freezes or pretrains the learned
adaptive components on prefix books and scores later books without
searching new parameters or changing the recipe.

## Current Boundary

- Compression bound: `8561.792` bits
- This is not promoted as the final authorial method.
- The row0 / 10x10 table origin remains open.

## Coverage

- Copy-length rows: `283`
- Literal-payload rows: `773`
- Item-type rows: `287`

## Aggregate Learned-Component Holdouts

| Train books | Holdout books | Posthoc bits | Prefix-online bits | Prefix-frozen bits | Uniform bits | Online vs uniform | Frozen vs uniform |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `10` | `60` | `2259.353` | `2205.607` | `2243.547` | `2359.989` | `-154.382` | `-116.442` |
| `20` | `50` | `1477.986` | `1467.620` | `1491.180` | `1553.677` | `-86.057` | `-62.497` |
| `35` | `35` | `967.611` | `968.175` | `980.298` | `1016.319` | `-48.145` | `-36.022` |
| `50` | `20` | `529.649` | `519.700` | `522.220` | `557.283` | `-37.583` | `-35.063` |
| `60` | `10` | `148.803` | `144.865` | `144.110` | `155.181` | `-10.316` | `-11.070` |

## Interpretation

The learned components are evaluated as predictive structure, not as
more post-hoc compression. Prefix-online scoring asks whether the same
adaptive rules continue to compress future books after seeing a prefix;
prefix-frozen scoring is stricter and asks whether prefix counts alone
are enough without further adaptation.

This audit therefore marks the current `8561.792` bit formula as the
active compression bound and moves mainline progress criteria toward
holdout behavior, structural mechanisms, simplification, or row0 origin
evidence.

## Boundary

This is a mechanical validation audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
