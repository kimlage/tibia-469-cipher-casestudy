# 151. Row0 Artifact Provenance Audit

Classification: `AUDIT_ONLY`
Translation delta: `NONE`

The project reads/preserves row0-like tables and derived reports. No repository script is promoted as the origin generator for the pair labels.

## Selected provenance hits

- `analysis/audit_20260609/audit_final.out:1:=== probe_runs schema + row0 entries ===`
- `analysis/audit_20260609/audit_final.out:4:row0-matching rows: 0`
- `analysis/audit_20260609/audit_final2.out:1:=== tables like row0_code_symbol% ===`
- `analysis/audit_20260609/audit_final2.out:2:  row0_code_symbol_probe_runs: 1 rows`
- `analysis/audit_20260609/audit_final2.out:4:=== row0_code_symbol_probe_runs content (if exists) ===`
- `analysis/audit_20260609/audit_main.out:19:-- query returned 13 rows: SELECT name, type FROM pragma_table_info('row0_code_symbol_probe_books')`
- `analysis/audit_20260609/audit_main.out:33:-- query returned 70 rows: SELECT * FROM row0_code_symbol_probe_books`
- `analysis/audit_20260609/audit_main.out:133:--- row0_code_symbol_counts ---`
- `analysis/audit_20260609/audit_main.out:134:-- query returned 6 rows: SELECT name FROM pragma_table_info('row0_code_symbol_counts')`
- `analysis/audit_20260609/audit_main.out:141:-- query returned 99 rows: SELECT * FROM row0_code_symbol_counts LIMIT 100`
- `analysis/audit_20260609/audit_main.out:182:--- row0_symbol_code_counts ---`
- `analysis/audit_20260609/audit_main.out:183:-- query returned 6 rows: SELECT name FROM pragma_table_info('row0_symbol_code_counts')`
- `analysis/audit_20260609/audit_main.out:190:-- query returned 99 rows: SELECT * FROM row0_symbol_code_counts LIMIT 100`
- `analysis/audit_20260609/audit_main.py:66:for r in rows("SELECT name, type FROM pragma_table_info('row0_code_symbol_probe_books')"):`
- `analysis/audit_20260609/audit_main.py:68:pb = rows("SELECT * FROM row0_code_symbol_probe_books")`
- `analysis/audit_20260609/audit_main.py:194:for t in ("row0_code_symbol_counts", "row0_symbol_code_counts"):`
- `analysis/audit_20260609/audit_prov2.out:26:=== probe_runs entry for row0 code symbol probe ===`
- `analysis/audit_20260609/audit_recon.out:1:-- 99 rows: SELECT code, symbol, occurrence_count FROM row0_code_symbol_counts ORDER BY code`
- `analysis/audit_20260609/audit_recon.py:18:cmap_rows = rows("SELECT code, symbol, occurrence_count FROM row0_code_symbol_counts ORDER BY code")`
- `analysis/audit_20260609/audit_recon.py:38:for r in rows("SELECT bookid, digitslen, insertedzeros, omitted_positions_json, omitted_codes_json, reconstructed_code_stream, decodedbase, consumed_digits, valid FROM row0_code_symbol_probe_books"):`
- `analysis/audit_20260609/audit_recon2.py:11:cmap = {r["code"]: r["symbol"] for r in cur.execute("SELECT code, symbol FROM row0_code_symbol_counts")}`
- `analysis/audit_20260609/audit_recon2.py:17:    "SELECT bookid, omitted_positions_json, omitted_codes_json, reconstructed_code_stream, decodedbase FROM row0_code_symbol_probe_books")}`
- `analysis/audit_20260609/circ_check/check.py:11:cur.execute("SELECT bookid, omitted_positions_json FROM row0_code_symbol_probe_books WHERE run_id=1")`
- `analysis/audit_20260609/circ_check/check.py:16:cur.execute("SELECT bookid, omitidxs_1based, pathcount FROM row0_omission_probe_book_items WHERE run_id=1")`
- `analysis/audit_20260609/circ_check/check.py:22:cur.execute("SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1")`
- `analysis/audit_20260609/dedup_canonical/c1_dedup_disqualifiers.py:180:print(f"\n(e) REVERSAL INVARIANCE (map-level, unaffected by dedup; recheck from row0_code_symbol_counts)")`
- `analysis/audit_20260609/dedup_canonical/c1_dedup_disqualifiers.py:181:mrows = cur.execute("""SELECT code, symbol, occurrence_count FROM row0_code_symbol_counts`
- `analysis/audit_20260609/dedup_canonical/c1_out.txt:46:(e) REVERSAL INVARIANCE (map-level, unaffected by dedup; recheck from row0_code_symbol_counts)`
- `analysis/audit_20260609/dedup_canonical/c2_generative_mdl.py:43:prows = cur.execute("""SELECT bookid, reconstructed_code_stream FROM row0_code_symbol_probe_books`
- `analysis/audit_20260609/dedup_canonical/c2_generative_mdl.py:48:mrows = cur.execute("SELECT code, symbol, occurrence_count FROM row0_code_symbol_counts WHERE run_id=1").fetchall()`
