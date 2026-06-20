# D&D Eye-Ray Order Model

Verdict: `blocked_waiting_for_fixed_external_order`. Translation delta: `NONE`.

This test is intentionally blocked unless a fixed external D&D ray order
is committed before fitting. Fitting an order from row0 would leak the
target and create a pareidolia route.

Required input: `analysis/inspiration_model_20260620/dnd_eye_ray_order_fixed.yaml`
