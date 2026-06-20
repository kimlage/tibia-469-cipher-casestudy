# Topology Module Signal Audit

Verdict: `weak_topology_module_signal`. Translation delta: `NONE`.

This pass tests whether public Hellgate order/bookcase grouping predicts
shared tape modules or tape components. It uses the partial public
topology manifest and deterministic shuffles.

| Metric | Observed | Control mean | p(control >= observed) |
|---|---:|---:|---:|
| `module_adjacent` | `0.035156` | `0.031077` | `0.3845` |
| `module_bookcase_group` | `0.055556` | `0.030150` | `0.2345` |
| `component_adjacent` | `0.380208` | `0.280720` | `0.0030` |
| `component_bookcase_group` | `0.430556` | `0.289933` | `0.0205` |

## Conclusion

The current partial topology does not predict module/component sharing
strongly enough to improve the generation model.
