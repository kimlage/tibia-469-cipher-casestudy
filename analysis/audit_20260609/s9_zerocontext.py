#!/usr/bin/env python3
"""0X bigram landscape in raw digits + omission context from probe table."""
import sqlite3, collections

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, digits FROM sheet__books GROUP BY bookid").fetchall()
print("ROWCOUNT", len(rows)); assert len(rows)==70
dig={r[0]:r[1] for r in rows}

big=collections.Counter()
for d in dig.values():
    for i in range(len(d)-1): big[d[i:i+2]]+=1
print("0X bigram counts:", {f"0{x}": big.get(f"0{x}",0) for x in "0123456789"})
print("X0 bigram counts:", {f"{x}0": big.get(f"{x}0",0) for x in "0123456789"})

# probe table: omitted-zero positions
cols=[c[1] for c in con.execute("PRAGMA table_info(row0_code_symbol_probe_books)").fetchall()]
print("\nprobe cols:", cols)
r=con.execute("SELECT * FROM row0_code_symbol_probe_books LIMIT 3").fetchall()
for x in r: print(x)
n=con.execute("SELECT COUNT(*) FROM row0_code_symbol_probe_books").fetchone()[0]
print("probe rows:", n)
con.close()
