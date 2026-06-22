# Copy Hint Stream Lower Bound

Classification: `copy_hint_stream_lower_bound_open`
Translation delta: `NONE`

## Purpose

Measure the paid external copy hint still required after granting copy
start, copy type, copy length, and exact prior material. The hint chooses
the same-length chunk to copy; it does not generate op starts or lengths.

## Summary

- Copy ops: `208`.
- Copy digits: `9301`.
- Source-address bits: `2550.594`.
- Uniform same-length chunk hint bits: `2366.891`.
- Best rank-coded hint policy: `frequent_longest`.
- Best rank-coded hint bits: `1873.768`.
- Saving vs source address bits: `676.826`.
- Saving vs uniform chunk hint bits: `493.123`.
- Fraction of raw copied-digit literal bits: `0.060645`.
- Mean/median same-length chunks: `3253.663` / `2436`.
- Policy top-80 hits: `{'current_source_penalty': 12, 'earliest': 12, 'longest_recent': 17, 'frequent_longest': 20, 'rare_recent': 8}`.
- Promotes copy hint lower bound: `True`.

If copy length is granted, a target-free rank-coded chunk hint is substantially cheaper than raw source addressing and far cheaper than literalizing copied digits. This is a constructive lower bound for a paid copy-control stream, not a generator: op starts, copy type, and lengths are still granted.

## Policy Rank Bits

| Policy | Rank Bits | Top-80 Hits |
| --- | ---: | ---: |
| `current_source_penalty` | `1949.905` | `12` |
| `earliest` | `1949.905` | `12` |
| `longest_recent` | `1953.244` | `17` |
| `frequent_longest` | `1873.768` | `20` |
| `rare_recent` | `2150.832` | `8` |

## Prefix Cutoff Rows

| Cutoff | Copy Ops | Copy Digits | Best Policy | Best Bits | Source Bits | Saving vs Source |
| ---: | ---: | ---: | --- | ---: | ---: | ---: |
| `20` | `155` | `7799` | `frequent_longest` | `1434.174` | `1952.503` | `518.329` |
| `30` | `119` | `6530` | `frequent_longest` | `1114.375` | `1523.741` | `409.366` |
| `40` | `80` | `4977` | `frequent_longest` | `774.952` | `1041.564` | `266.612` |
| `50` | `49` | `3444` | `frequent_longest` | `491.769` | `645.868` | `154.099` |
| `60` | `18` | `1455` | `frequent_longest` | `183.590` | `239.750` | `56.161` |

## Decision

- This is a constructive lower bound for a paid copy-control stream.
- It does not solve op starts, type, length, or closed-loop generation.
- The next route is to test whether the copy hint stream has compressible structure or can be synchronized with the innovation/control tapes.
- Row0, plaintext, translation, and compression bound remain unchanged.
