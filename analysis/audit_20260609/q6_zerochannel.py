import sqlite3, json
con = sqlite3.connect("file:./data/bonelord_operational.sqlite?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()
rows = cur.execute("SELECT bookid, reconstructed_code_stream, omitted_positions_json FROM row0_code_symbol_probe_books WHERE valid=1").fetchall()
print("books:", len(rows))
tot0X = 0; tot_omit = 0; books_mixed = 0; det_violations = 0
percode = {}
for r in rows:
    codes = r["reconstructed_code_stream"].split()
    omit = set(json.loads(r["omitted_positions_json"]))  # 1-based positions
    zx = [(i+1, c) for i, c in enumerate(codes) if c.startswith("0")]
    omitted = [p for p, c in zx if p in omit]
    retained = [p for p, c in zx if p not in omit]
    tot0X += len(zx); tot_omit += len(omitted)
    if omitted and retained: books_mixed += 1
    for p, c in zx:
        key = c
        percode.setdefault(key, [0,0])
        percode[key][0 if p in omit else 1] += 1
print("total 0X code occurrences:", tot0X, "| omitted:", tot_omit, "| retained:", tot0X - tot_omit)
print("books with BOTH omitted and retained 0X codes:", books_mixed)
print("per-code omitted/retained:", {k: v for k, v in sorted(percode.items())})

# clusterid
rows2 = cur.execute("SELECT clusterid, COUNT(DISTINCT bookid) FROM sheet__books GROUP BY clusterid").fetchall()
print("clusterid distribution:", [(r[0], r[1]) for r in rows2])
