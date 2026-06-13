#!/usr/bin/env python3
"""Emit the canonical deduped residual corpus (novel decoded symbols, LZ min-match 5,
bookid order) as JSON for downstream attack items. Also basic segment stats."""
import sqlite3, json
from collections import Counter

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, MIN(decodedbase) FROM sheet__books GROUP BY bookid").fetchall()
print("ROWCOUNT:", len(rows)); assert len(rows) == 70
def keyf(b):
    try: return (0, int(b))
    except: return (1, b)
rows.sort(key=lambda r: keyf(r[0]))
dec = dict(rows)
ids = [r[0] for r in rows]

corpus = ""
segs = []
novel_tot = 0
for b in ids:
    s = dec[b]; mask = bytearray(len(s)); i = 0
    while i < len(s):
        lo, hi, best = 5, len(s) - i, 0
        while lo <= hi:
            mid = (lo + hi) // 2
            if s[i:i+mid] in corpus: best, lo = mid, mid + 1
            else: hi = mid - 1
        if best >= 5: i += best
        else: mask[i] = 1; i += 1
    corpus += "#" + s
    i = 0
    while i < len(s):
        if mask[i]:
            j = i
            while j < len(s) and mask[j]: j += 1
            segs.append({"book": b, "offset": i, "len": j - i, "text": s[i:j]})
            novel_tot += j - i
            i = j
        else: i += 1

lens = Counter(g["len"] for g in segs)
print(f"novel symbols={novel_tot}; segments={len(segs)}; len distribution: {sorted(lens.items())}")
print(f"segments >=10 symbols: {sum(1 for g in segs if g['len']>=10)} totaling {sum(g['len'] for g in segs if g['len']>=10)}")
print("longest 8 segments:")
for g in sorted(segs, key=lambda g: -g["len"])[:8]:
    print(f"  book {g['book']} off={g['offset']} len={g['len']}: {g['text']}")
out = "./tmp/audit_20260609/residual_corpus.json"
with open(out, "w") as f:
    json.dump({"method": "LZ dedup, min match 5 decoded symbols, bookid numeric order, earlier-text reference",
               "novel_symbols": novel_tot, "segments": segs}, f, indent=1)
print("wrote", out)
