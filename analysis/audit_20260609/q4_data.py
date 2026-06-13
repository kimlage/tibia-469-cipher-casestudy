import sqlite3, json, collections
con = sqlite3.connect("file:./data/bonelord_operational.sqlite?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()

# sheet__books columns
cols = [r[1] for r in cur.execute("PRAGMA table_info(sheet__books)")]
print("sheet__books cols:", cols)

rows = cur.execute("SELECT bookid, MAX(digits) d, MAX(insertedzeros) iz, MAX(baselen) bl, MAX(decodedbase) db FROM sheet__books WHERE bookid IS NOT NULL GROUP BY bookid").fetchall()
print("books:", len(rows))
lens = [len(r["d"]) for r in rows]
print("digit len: min", min(lens), "max", max(lens), "total", sum(lens))
iz = [r["iz"] for r in rows]
print("insertedzeros sample:", iz[:10])

# cluster tables?
names = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%cluster%' OR name LIKE '%order%' OR name LIKE '%location%' OR name LIKE '%length%')").fetchall()]
print("cluster/order/location tables:", names)

# omitted zero positions
cols2 = [r[1] for r in cur.execute("PRAGMA table_info(row0_code_symbol_probe_books)")]
print("row0_code_symbol_probe_books cols:", cols2)
r = cur.execute("SELECT * FROM row0_code_symbol_probe_books LIMIT 2").fetchall()
for row in r:
    print({k: (str(row[k])[:80]) for k in row.keys()})
