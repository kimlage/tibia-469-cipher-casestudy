import sqlite3, json
con = sqlite3.connect("file:./data/bonelord_operational.sqlite?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()
def show(t, lim=2):
    try: rows = cur.execute(f"SELECT * FROM {t} ORDER BY 1 DESC LIMIT {lim}").fetchall()
    except Exception as e: print(f"## {t}: ERR {e}"); return
    print(f"## {t} rows={len(rows)}")
    for r in rows:
        d = {k: (str(v)[:200]) for k, v in dict(r).items()}
        print("  ", json.dumps(d)[:900])
for t in ["literal_homophonic_books_v1_runs","s2ward_corpus_audit_runs","row0_path_reconstruction_probe_runs",
          "narcissist_homophonic_external_control_runs","external_corpus_sources","row0_omission_probe_book_items"]:
    show(t)
