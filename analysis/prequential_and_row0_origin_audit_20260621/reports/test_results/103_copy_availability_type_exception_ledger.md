# Copy Availability Type Exception Ledger

Classification: `copy_availability_type_exception_audit_only`
Translation delta: `NONE`

## Purpose

Gate 100 showed that simple source-free rules do not generate the
operation skeleton. This ledger tests the stronger target-dependent
copy-availability clue: predict `copy` whenever a min-length copy is
available at the target position, otherwise predict `literal`.

## Result

- Operations: `261`.
- Copies/literals: `208` / `53`.
- Copy-available rows: `225`.
- Unavailable copy exceptions: `0`.
- Forced literal rows with no copy available: `36`.
- Optional literal exceptions while copy is available: `17`.
- Availability-rule hits/errors: `244` / `17`.
- Availability-rule coverage: `0.934866`.
- Error delta vs always-copy baseline: `-36`.
- Type fields if target availability is allowed: `17`.
- Type-field delta vs explicit op types: `-244`.
- Availability-conditioned skeleton records: `278`.
- Record delta vs exact skeleton atlas: `17`.
- Record delta vs gate-99 total materialized records: `17`.

## Controls

- Corpus availability shuffle errors min/median/mean/max: `57` / `75.0` / `74.333` / `89`.
- Corpus shuffle empirical p(errors <= observed): `0.000000`.
- Book availability shuffle errors min/median/mean/max: `45` / `65.0` / `65.838` / `87`.
- Book shuffle empirical p(errors <= observed): `0.000000`.
- Hypergeometric p(all copies inside available set): `1.514065e-31`.

## Decision

- Promotes generator: `False`.
- Target-dependent copy availability contains every copy event and forces 36 literal rows; only 17 available-copy literal exceptions remain. This is a strong mechanical clue about op type, but it depends on target text/copy availability and, after length/source/payload records are paid, it does not replace the exact skeleton atlas with a smaller generator.
- Taxonomy: `AUDIT_ONLY`.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
