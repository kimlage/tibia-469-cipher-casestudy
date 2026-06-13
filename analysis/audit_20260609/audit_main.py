#!/usr/bin/env python3
"""Audit checks 1-4, 6 for Tibia 469 frozen verdict corpus."""
import sqlite3, json, sys
from collections import Counter, defaultdict

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()

def rows(q, *a):
    r = cur.execute(q, a).fetchall()
    print(f"-- query returned {len(r)} rows: {q[:90]}")
    return r

print("=== CHECK 1: dedupe ===")
all_rows = rows("SELECT __export_id, __row_index, bookid, clusterid, digitslen, digits, insertedzeros, baselen, decodedbase FROM sheet__books")
print("total rows:", len(all_rows))
by_book = defaultdict(list)
for r in all_rows:
    by_book[r["bookid"]].append(r)
print("distinct bookids:", len(by_book))
export_ids = Counter(r["__export_id"] for r in all_rows)
print("export_id distribution:", dict(export_ids))
conflicts = []
for bid, rs in by_book.items():
    keyset = set((r["digits"], r["insertedzeros"], r["baselen"], r["decodedbase"], r["digitslen"]) for r in rs)
    if len(rs) != 2:
        conflicts.append((bid, "rowcount", len(rs)))
    if len(keyset) != 1:
        conflicts.append((bid, "conflict", [dict(zip(("digits","iz","baselen","db","dl"), k)) for k in keyset]))
print("conflicting/odd bookids:", conflicts if conflicts else "NONE")

# dedupe to one row per book
books = {bid: rs[0] for bid, rs in by_book.items()}

print("\n=== CHECK 2: length identities ===")
ok_a = ok_b = 0
fails = []
total_digits = 0
total_symbols = 0
for bid, r in sorted(books.items(), key=lambda x: x[0]):
    digits = r["digits"]; iz = int(r["insertedzeros"]); bl = int(r["baselen"]); db = r["decodedbase"]
    dl_col = int(r["digitslen"])
    total_digits += len(digits)
    total_symbols += len(db)
    a = (len(digits) + iz == 2*bl)
    b = (len(db) == bl)
    c = (dl_col == len(digits))
    ok_a += a; ok_b += b
    if not (a and b and c):
        fails.append((bid, len(digits), dl_col, iz, bl, len(db), a, b, c))
print(f"identity len(digits)+insertedzeros==2*baselen: {ok_a}/70")
print(f"identity len(decodedbase)==baselen: {ok_b}/70")
print("digitslen col matches len(digits) failures:", [f for f in fails])
print("total digits:", total_digits, "(expect 11263)")
print("total symbols:", total_symbols, "(expect 5729)")
alpha = Counter()
for r in books.values():
    alpha.update(r["decodedbase"])
print("symbol alphabet:", "".join(sorted(alpha)))
print("symbol counts:", dict(sorted(alpha.items())))

print("\n=== CHECK 3: probe_books ===")
print("schema:")
for r in rows("SELECT name, type FROM pragma_table_info('row0_code_symbol_probe_books')"):
    print("  ", r["name"], r["type"])
pb = rows("SELECT * FROM row0_code_symbol_probe_books")
print("probe rows:", len(pb))
if pb:
    cols = pb[0].keys()
    print("columns:", list(cols))
    bad = []
    for r in pb:
        d = dict(r)
        valid = d.get("valid")
        cd = d.get("consumed_digits")
        dl = d.get("digitslen")
        if str(valid) != "1" or (cd is not None and dl is not None and int(cd) != int(dl)):
            bad.append(d)
    print("invalid or consumed!=digitslen:", len(bad))
    for b in bad[:10]:
        print("  BAD:", b)
    # cross-check digitslen vs sheet__books
    mism = []
    for r in pb:
        d = dict(r)
        bid = str(d.get("bookid"))
        if bid in books:
            if int(d.get("digitslen", -1)) != len(books[bid]["digits"]):
                mism.append(bid)
        else:
            mism.append(("missing-book", bid))
    print("probe vs sheet digitslen mismatches:", mism if mism else "NONE")
    sheet_ids = set(books.keys())
    probe_ids = set(str(dict(r).get("bookid")) for r in pb)
    print("books in sheet not in probe:", sorted(sheet_ids - probe_ids))
    print("books in probe not in sheet:", sorted(probe_ids - sheet_ids))

print("\n=== CHECK 4: duplicate / near-duplicate digit strings ===")
dig_map = defaultdict(list)
for bid, r in books.items():
    dig_map[r["digits"]].append(bid)
dups = {d: bs for d, bs in dig_map.items() if len(bs) > 1}
print("identical digit strings across different bookids:", dups if dups else "NONE")

# prefix relations on digits
bl_list = sorted(books.items(), key=lambda x: len(x[1]["digits"]))
prefix_hits = []
for i in range(len(bl_list)):
    for j in range(len(bl_list)):
        if i == j: continue
        a, ra = bl_list[i]; b, rb = bl_list[j]
        if len(ra["digits"]) < len(rb["digits"]) and rb["digits"].startswith(ra["digits"]):
            prefix_hits.append((a, b, len(ra["digits"]), len(rb["digits"])))
print("digit-prefix relations (A prefix of B):", prefix_hits if prefix_hits else "NONE")

# decodedbase duplicates and prefixes
db_map = defaultdict(list)
for bid, r in books.items():
    db_map[r["decodedbase"]].append(bid)
db_dups = {d[:60]: bs for d, bs in db_map.items() if len(bs) > 1}
print("identical decodedbase across different bookids:", db_dups if db_dups else "NONE")
db_prefix = []
items = sorted(books.items(), key=lambda x: len(x[1]["decodedbase"]))
for i in range(len(items)):
    for j in range(len(items)):
        if i == j: continue
        a, ra = items[i]; b, rb = items[j]
        if len(ra["decodedbase"]) < len(rb["decodedbase"]) and rb["decodedbase"].startswith(ra["decodedbase"]):
            db_prefix.append((a, b, len(ra["decodedbase"]), len(rb["decodedbase"])))
print("decodedbase prefix relations:", db_prefix if db_prefix else "NONE")

# near-duplicate: shared content via longest common substring approx using 20-gram overlap
def ngrams(s, n=20):
    return set(s[i:i+n] for i in range(len(s)-n+1)) if len(s) >= n else {s}
ng = {bid: ngrams(r["decodedbase"]) for bid, r in books.items()}
near = []
bids = sorted(books.keys(), key=lambda x: int(x) if x.isdigit() else 10**9)
for i in range(len(bids)):
    for j in range(i+1, len(bids)):
        a, b = bids[i], bids[j]
        ia, ib = ng[a], ng[b]
        inter = len(ia & ib)
        denom = min(len(ia), len(ib))
        if denom and inter/denom > 0.5:
            near.append((a, b, round(inter/denom, 3), len(books[a]["decodedbase"]), len(books[b]["decodedbase"])))
near.sort(key=lambda x: -x[2])
print("near-dup pairs (20-gram overlap >50% of smaller):", len(near))
for t in near[:40]:
    print("  ", t)

# also moderate overlap 20-50%
mid = []
for i in range(len(bids)):
    for j in range(i+1, len(bids)):
        a, b = bids[i], bids[j]
        ia, ib = ng[a], ng[b]
        inter = len(ia & ib)
        denom = min(len(ia), len(ib))
        frac = inter/denom if denom else 0
        if 0.2 < frac <= 0.5:
            mid.append((a, b, round(frac, 3)))
mid.sort(key=lambda x: -x[2])
print("moderate overlap pairs (20-50%):", len(mid))
for t in mid[:20]:
    print("  ", t)

print("\n=== CHECK 6: star mask ===")
mask_chars = {ch for ch in alpha if ch not in set("ABCEFILNORSTV")}
print("non-alphabet chars in decodedbase:", mask_chars, {c: alpha[c] for c in mask_chars})
star = "*" if "*" in alpha else (sorted(mask_chars)[0] if mask_chars else None)
print("mask char:", repr(star))
if star:
    per_book = []
    total_mask = 0
    for bid, r in books.items():
        c = r["decodedbase"].count(star)
        total_mask += c
        per_book.append((bid, c, len(r["decodedbase"]), round(c/len(r["decodedbase"]),4) if r["decodedbase"] else 0))
    per_book.sort(key=lambda x: -x[1])
    print(f"total mask symbols: {total_mask} / {total_symbols} = {total_mask/total_symbols:.4%}")
    books_with_mask = [p for p in per_book if p[1] > 0]
    print("books with >=1 mask:", len(books_with_mask))
    print("top books by mask count (bookid, maskcount, len, frac):")
    for p in per_book[:15]:
        print("  ", p)
    top5 = sum(p[1] for p in per_book[:5])
    print(f"top-5 books hold {top5}/{total_mask} = {top5/total_mask:.1%} of all masks" if total_mask else "no masks")

    # which 2-digit codes produce the mask: reconstruct per book using insertedzeros positions
    # need omitted-zero positions from probe table; first inspect probe table columns for zero positions
print("\n=== code->symbol map tables ===")
for t in ("row0_code_symbol_counts", "row0_symbol_code_counts"):
    print(f"--- {t} ---")
    for r in rows(f"SELECT name FROM pragma_table_info('{t}')"):
        print("  col:", r["name"])
    sample = rows(f"SELECT * FROM {t} LIMIT 100")
    for s in sample[:40]:
        print("  ", dict(s))

con.close()
