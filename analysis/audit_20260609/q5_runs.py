import sqlite3, json
con = sqlite3.connect("file:./data/bonelord_operational.sqlite?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()

def show(table, cols="*", limit=3):
    try:
        rows = cur.execute(f"SELECT {cols} FROM {table} ORDER BY 1 DESC LIMIT {limit}").fetchall()
    except Exception as e:
        print(f"## {table}: ERROR {e}"); return
    print(f"## {table}: rows_shown={len(rows)}")
    for r in rows:
        d = dict(r)
        for k,v in list(d.items()):
            if isinstance(v,str) and len(v)>220: d[k]=v[:220]+"..."
        print("  ", json.dumps(d, default=str)[:1000])

for t in ["row0_omission_probe_runs","zero_pair_alignment_probe_runs","zero_boundary_segment_cluster_v2_runs",
          "template_slot_grammar_probe_v1_runs","template_slot_probe_runs","display_template_concordance_gate_v1_runs",
          "charset_base_sweep_runs","charset_base_sweep_audit_runs","cp1252_authentic_base_sweep_runs",
          "tibia710_visual_font_alphabet_sweep_runs","tibia760_visual_slot_base_sweep_runs",
          "old_client_asset_context_probe_runs","import_s2ward_corpus_audit_runs",
          "mathemagic_order_permutation_gate_v1_runs","human_q6_external_corpus_order_residual_probe_v1_runs",
          "internal_bpe_mdl_runs","hard_residual_segmentation_probe_runs","phase_segmentation_probe_runs"]:
    show(t)
