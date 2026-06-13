#!/usr/bin/env python3
"""STEP 1: Extract per-occurrence homophone-choice streams + novelty (dedupe) mask.

Output: occ_streams.json in this dir with, per symbol (>=2 codes):
ordered occurrences (bookid, token_pos_0based, code, novel_flag), plus
class definitions and novelty stats.

Novelty: process books in sorted bookid order; a digit position is DUPLICATED
if it lies inside any window of length L=20 that already occurred earlier
(earlier book, or earlier in same book at distance >= L). A token is novel iff
its digit span contains at least one non-duplicated digit position.
"""
import json
import sqlite3
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
L = 20
OUT = "./tmp/audit_20260609/homophone_channel/occ_streams.json"

con = sqlite3.connect(DB, uri=True)
rows = con.execute(
    "SELECT bookid, reconstructed_code_stream, omitted_positions_json, decodedbase "
    "FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
print(f"probe rows: {len(rows)}"); assert len(rows) == 70
drows = con.execute("SELECT bookid, digits FROM sheet__books GROUP BY bookid").fetchall()
print(f"digit rows: {len(drows)}"); assert len(drows) == 70
digits = {b: d for b, d in drows}
con.close()

books = []
for bid, stream, opos, base in sorted(rows):
    codes = stream.split()
    omit = set(json.loads(opos))  # 1-based token indices
    assert len(codes) == len(base), bid
    # rendered digit length check
    rend = "".join(c[1] if (i + 1) in omit else c for i, c in enumerate(codes))
    assert rend == digits[bid], bid
    books.append((bid, codes, base, omit))
print("round-trip byte-exact: 70/70")

# ---- novelty mask at digit level
seen = set()
novel_digit = {}  # bid -> list[bool] per digit position
for bid, codes, base, omit in books:
    d = digits[bid]
    n = len(d)
    dup = [False] * n
    # mark duplicated windows (must already be in `seen` = earlier books or earlier same-book)
    local = set()
    for i in range(n - L + 1):
        w = d[i:i + L]
        if w in seen or w in local:
            for j in range(i, i + L):
                dup[j] = True
        local.add(w)
    seen |= local
    novel_digit[bid] = [not x for x in dup]

# ---- cross-book-unique mask (for honest LOBO eval): digit position NOT covered
# by any L-window that also appears in a DIFFERENT book.
win_books = defaultdict(set)  # window -> set of bookids
for bid, *_ in books:
    d = digits[bid]
    for i in range(len(d) - L + 1):
        win_books[d[i:i + L]].add(bid)
xuniq_digit = {}
for bid, *_ in books:
    d = digits[bid]
    n = len(d)
    shared = [False] * n
    for i in range(n - L + 1):
        w = d[i:i + L]
        if len(win_books[w]) > 1:
            for j in range(i, i + L):
                shared[j] = True
    xuniq_digit[bid] = [not x for x in shared]

# ---- map tokens to digit spans, build occurrence streams
sym_codes = defaultdict(set)
for bid, codes, base, omit in books:
    for c, s in zip(codes, base):
        sym_codes[s].add(c)
class_sizes = {s: sorted(v) for s, v in sym_codes.items()}
print("\nhomophone classes (symbol: codes):")
for s in sorted(class_sizes):
    print(f"  {s!r}: {class_sizes[s]} (size {len(class_sizes[s])})")

occ = defaultdict(list)  # symbol -> list of dicts
novel_tok_count = Counter()
xuniq_tok_count = Counter()
tot_tok_count = Counter()
for bid, codes, base, omit in books:
    nd = novel_digit[bid]
    xd = xuniq_digit[bid]
    dp = 0
    for i, (c, s) in enumerate(zip(codes, base)):
        w = 1 if (i + 1) in omit else len(c)
        novel = any(nd[j] for j in range(dp, dp + w))
        xuniq = any(xd[j] for j in range(dp, dp + w))
        dp += w
        tot_tok_count[s] += 1
        if novel:
            novel_tok_count[s] += 1
        if xuniq:
            xuniq_tok_count[s] += 1
        occ[s].append({"book": bid, "pos": i, "code": c, "novel": novel,
                       "xuniq": xuniq})
    assert dp == len(digits[bid])

total = sum(tot_tok_count.values())
novel_total = sum(novel_tok_count.values())
xuniq_total = sum(xuniq_tok_count.values())
print(f"\ntotal tokens: {total} (expect 5729); novel tokens: {novel_total} "
      f"({novel_total/total:.1%}); cross-book-unique tokens: {xuniq_total} "
      f"({xuniq_total/total:.1%})")

print("\nper-symbol stream lengths (occurrences), class size, novel, xuniq:")
for s in sorted(occ):
    print(f"  {s!r}: n={len(occ[s])} class={len(class_sizes[s])} "
          f"novel={novel_tok_count[s]} xuniq={xuniq_tok_count[s]}")

# books fully duplicated (no novel digit at all)
full_dup = [bid for bid, *_ in books if not any(novel_digit[bid])]
print(f"\nbooks with zero novel digits: {len(full_dup)}: {full_dup}")

multi = {s: class_sizes[s] for s in class_sizes if len(class_sizes[s]) >= 2}
json.dump({"class_sizes": class_sizes, "multi_symbols": sorted(multi),
           "occ": {s: occ[s] for s in occ},
           "full_dup_books": full_dup}, open(OUT, "w"))
print(f"\nwrote {OUT}")
