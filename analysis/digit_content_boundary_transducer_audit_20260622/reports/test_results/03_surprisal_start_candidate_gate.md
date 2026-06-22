# Surprisal Start Candidate Gate

Classification: `SURPRISAL_START_CANDIDATE_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test whether the digit-boundary surprisal clue improves the internal-start candidate ledger. Decoder-visible scores are separated from target-conditioned right-surprisal diagnostics.

## Decoder-Visible Summary

- Candidate bits after policy: `1922.243`.
- Exact start composition baseline bits: `2063.661`.
- Delta vs baseline: `-141.417` bits.
- Cells beating random top-K p05: `0/5`.
- Candidate positions selected: `3904`.
- Start hits: `71/343`.
- Misses requiring correction: `272`.
- Recall: `0.207`.

## Diagnostic Target-Conditioned Summary

- Candidate bits after policy: `1665.114`.
- Exact start composition baseline bits: `2063.661`.
- Delta vs baseline: `-398.547` bits.
- Cells beating random top-K p05: `4/5`.
- Start hits: `171/343`.

## Decoder-Visible Prefix Holdouts

| Cutoff | Family | Rate | K | Hits | Misses | Candidate bits | Baseline bits | Delta | Random p05 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `20` | `left_peak2` | `0.160` | `1260` | `26` | `106` | `722.187` | `775.501` | `-53.313` | `False` |
| `30` | `left_ge4_then_suffix4` | `0.160` | `1054` | `18` | `82` | `559.285` | `598.810` | `-39.525` | `False` |
| `40` | `left_ge4_then_suffix4` | `0.160` | `804` | `14` | `51` | `366.390` | `395.378` | `-28.988` | `False` |
| `50` | `left_ge4_then_suffix4` | `0.160` | `554` | `9` | `27` | `212.940` | `229.691` | `-16.750` | `False` |
| `60` | `left_ge4_then_suffix4` | `0.160` | `232` | `4` | `6` | `56.533` | `64.281` | `-7.747` | `False` |

## Diagnostic Prefix Holdouts

| Cutoff | Family | Rate | K | Hits | Misses | Candidate bits | Baseline bits | Delta | Random p05 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `20` | `right_ge4_diagnostic` | `0.160` | `1260` | `71` | `61` | `626.053` | `775.501` | `-149.447` | `True` |
| `30` | `right_ge4_diagnostic` | `0.080` | `528` | `42` | `58` | `473.719` | `598.810` | `-125.091` | `True` |
| `40` | `right_ge4_diagnostic` | `0.160` | `804` | `34` | `31` | `321.168` | `395.378` | `-74.210` | `True` |
| `50` | `right_ge4_diagnostic` | `0.160` | `554` | `21` | `15` | `181.944` | `229.691` | `-47.747` | `True` |
| `60` | `right_ge4_diagnostic` | `0.160` | `232` | `3` | `7` | `57.908` | `64.281` | `-6.373` | `False` |

## Decision

Only decoder-visible scores can be promoted. Right-surprisal and sum2 diagnostics look at the next digit and therefore remain target-conditioned candidate diagnostics, not an executable start generator.
