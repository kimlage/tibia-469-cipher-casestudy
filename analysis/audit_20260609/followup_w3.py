#!/usr/bin/env python3
"""Follow-up: is columnar_w3's 0 invalid ('39') pairs an anomaly?
Count '3...9' at lag k (k=1..40) within each book's digit string; compare
observed vs shuffle expectation; and count invalid pairs per transform family.
"""
import sqlite3
from collections import Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
rows = con.execute("SELECT bookid, digits FROM sheet__books GROUP BY bookid").fetchall()
print(f"books: {len(rows)}")
books = {b: d for b, d in rows}

# digit frequencies
dc = Counter()
for d in books.values():
    dc += Counter(d)
tot = sum(dc.values())
print("digit counts:", dict(sorted(dc.items())), "total", tot)
p3 = dc['3']/tot; p9 = dc['9']/tot
print(f"p3={p3:.4f} p9={p9:.4f} p3*p9={p3*p9:.5f}")

# lag-k '3 then 9' counts (within book)
print(f"\n{'lag':>4}{'obs_39':>8}{'exp':>8}{'npos':>8}")
for k in range(1, 41):
    obs = 0; npos = 0
    for d in books.values():
        for i in range(len(d)-k):
            npos += 1
            if d[i] == '3' and d[i+k] == '9':
                obs += 1
    exp = npos * p3 * p9
    flag = " <-- " if k == 3 else ""
    print(f"{k:>4}{obs:>8}{exp:>8.1f}{npos:>8}{flag}")

# how many of the lag-3 39s would actually land on a PAIR boundary in columnar_w3?
# In columnar_w3 read of book digits, count invalid pairs explicitly:
def reorder_columnar(s, w):
    return "".join(s[c::w] for c in range(w))
inv = 0; pairs = 0
for d in books.values():
    r = reorder_columnar(d, 3)
    for i in range(len(r)//2):
        pairs += 1
        if r[2*i:2*i+2] == '39':
            inv += 1
print(f"\ncolumnar_w3: pairs={pairs} invalid={inv}")
# canonical raw pairing invalid count
inv_c = 0; pairs_c = 0
inv_books = []
for b, d in books.items():
    for i in range(len(d)//2):
        pairs_c += 1
        if d[2*i:2*i+2] == '39':
            inv_c += 1
            inv_books.append(b)
print(f"canonical_raw: pairs={pairs_c} invalid={inv_c} in books {inv_books}")
