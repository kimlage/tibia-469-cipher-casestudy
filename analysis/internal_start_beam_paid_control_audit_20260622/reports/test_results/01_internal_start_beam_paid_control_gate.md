# Internal Start Beam Paid Control Gate

Classification: `PROMOTED_X64_INTERNAL_START_PAID_CONTROLLED_CANDIDATE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Does the x64 internal-start beam reduce the paid coarse-control tape, not only the hit/start counts, compared with same-multiset shuffled payload controls?

## Summary

- Real sequence hits: `109`.
- Real generated internal starts: `98`.
- Real coarse paid bits: `1549.117`.
- Control coarse paid bits p05: `1900.549`.
- Real coarse saving: `818.269` bits.
- Control coarse saving p95: `466.838` bits.
- Beats paid same-multiset controls: `True`.

## Control Context

- Control sequence-hit p95: `62.050`.
- Control generated-start p95: `55.000`.
- Control coarse saving mean: `414.740` bits.
- Control rank bits mean: `173.134`.

## Cutoff Rows

| Cutoff | Real saving | Control p95 saving | Real paid bits | Real hits | Control p95 hits |
| ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `202.578` | `118.088` | `649.885` | `31` | `18.000` |
| `30` | `213.787` | `137.680` | `448.108` | `28` | `18.000` |
| `40` | `194.154` | `130.561` | `266.417` | `24` | `16.000` |
| `50` | `135.472` | `92.248` | `145.285` | `17` | `11.050` |
| `60` | `72.278` | `64.358` | `39.421` | `9` | `8.000` |

## Decision

The x64 route survives the paid control. It is now a controlled coarse-control tape reduction candidate: the beam plus rank/correction stream is cheaper for the real payload than for same-multiset shuffles.

Boundary: this still does not promote an executable generation formula. The fine residual composition index, missed sequences, literal payload, copy/source hints, seed payload, and `row0` remain external or paid.

`row0`, plaintext, translation, and `compression_bound` remain unchanged.
