# Final Physical Topology Control Signal Audit

Status: `analysis_only`
Classification: `PARTIAL_TOPOLOGY_CONTROL_SIGNAL_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can partial public Hellgate bookcase/order metadata predict residual generation-control streams in the executable decoder ledger?

## Result

Promoted targets: `[]`. Weak positive targets: `[]`.

| Target | Saving | Permutation p95 | Beats p95 |
| --- | ---: | ---: | --- |
| `coarse_control` | `-107.149` | `-49.292` | `False` |
| `copy_hint_rank_bucket` | `-102.873` | `-27.864` | `False` |
| `op_type` | `-46.439` | `-41.988` | `False` |

## Decision

Partial public topology does not become a generator unless it predicts residual streams above permutation controls. Row0, plaintext, translation, and compression_bound remain unchanged.

## Reproducible Artifacts

- [01_physical_topology_control_signal_gate.py](../scripts/01_physical_topology_control_signal_gate.py)
- [01_physical_topology_control_signal_gate.json](test_results/01_physical_topology_control_signal_gate.json)
- [01_physical_topology_control_signal_gate.md](test_results/01_physical_topology_control_signal_gate.md)
