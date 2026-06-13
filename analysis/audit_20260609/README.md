# Audit artifacts — 2026-06-09/10 final adversarial audit

Committed mirror of the scratch directory `tmp/audit_20260609/` (text artifacts only; binary `.npz` model caches and files >2 MB excluded — all are regenerable by re-running the `.py` scripts against the read-only operational DB).

These are the scripts and raw outputs behind every number in [`docs/469_final_report.md`](../../docs/469_final_report.md). Layout:

- root `*.py` / `*_out.txt` / `*.out` — claim re-derivations (`main_audit.py`, `claim7_*`), fresh-eyes battery (`s1`–`s11`), module/grammar proof (`m1_modules.py`, `m2_grammar.py`), the ten executed attacks (Kharos pipeline, `markov_generator_constraint.py`, `homophone_rotation_test.py`, MDL contest, …)
- `refute/`, `circ_check/` — independent re-implementations by the adversarial refuters
- `homophone_channel/` — final channel closure (§6.1): `step1_extract.py` … `step6_attribution.py`
- `lang_residual/` — pre-registered split-half language test (§6.2)
- `ytc_2012/` — the 2012 "Your True Colour" string sourcing + test (§6.3)
- `dedup_canonical/` — deduped disqualifiers + generative MDL proof (§6.4)

DB required to re-run: `data/bonelord_operational.sqlite` (not committed; regenerable from the `.xlsx` workbooks via `scripts/export_workbook_to_sqlite.py`). Always open read-only (`file:...?mode=ro`).
