import sqlite3, json
con = sqlite3.connect("file:./data/bonelord_operational.sqlite?mode=ro", uri=True)
cur = con.cursor()

def q(sql, params=()):
    rows = cur.execute(sql, params).fetchall()
    print(f"-- {sql[:90]} | rows={len(rows)}")
    return rows

# schema of probe_runs and cipher_mode_hypotheses
for t in ("probe_runs","cipher_mode_hypotheses"):
    r = q("SELECT sql FROM sqlite_master WHERE name=?", (t,))
    for row in r: print(row[0])

rows = q("SELECT COUNT(*) FROM probe_runs")
print("probe_runs count:", rows)
rows = q("SELECT * FROM probe_runs LIMIT 5")
for r in rows: print(r)
