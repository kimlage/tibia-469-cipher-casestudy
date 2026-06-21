# Stable Path Projection Boundary Audit

Classification: `stable_path_projection_boundary_only`
Translation delta: `NONE`

## Purpose

Gate 86 closes multi-cutoff exact path stability under global
item/literal-length controls. This audit asks whether that stable path
can be promoted as a generator, or whether it remains an encoder-side
projection that still needs target text and declared payload/source/length
material.

## Result

- Projection mode: `payload_uniform_no_item_or_literal_length`.
- Multi-cutoff stable books: `50/50`.
- Single-cutoff-only parsed books: `10`.
- Seed books still external: `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]`.
- Unstable projected books: `[]`.
- Coverage digits: `11263/11263`.
- Canonical parsed copy items: `208`.
- Canonical parsed literal runs/digits: `54` / `265`.
- Promotes generator: `False`.

## Dependency Boundary

- Materialized seed payload digits: `1696`.
- Materialized parsed literal payload digits: `265`.
- Materialized copy source fields: `208`.
- Materialized copy length fields: `208`.
- Operation dependency-field delta vs active formula: `-139`.
- Target text required for copy candidate search: `True`.
- Target text required for literal payload/endpoints: `True` / `True`.
- Decoder can choose projection without target text: `False`.

## Decision

- Gate 86 gives a stable encoder-side path projection under the no-item/no-literal-length control, but the projection is still chosen with the target book text available. It therefore bounds the path-stability problem without proving a decoder-side book generator.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
