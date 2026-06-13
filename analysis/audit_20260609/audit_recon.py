#!/usr/bin/env python3
"""Check 7: end-to-end reconstruction of book 0 and book with most insertedzeros.
Also: which codes produce '*', and code-map consistency check across whole corpus."""
import sqlite3, json
from collections import defaultdict

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()

def rows(q, *a):
    r = cur.execute(q, a).fetchall()
    print(f"-- {len(r)} rows: {q[:80]}")
    return r

# full code->symbol map
cmap_rows = rows("SELECT code, symbol, occurrence_count FROM row0_code_symbol_counts ORDER BY code")
cmap = {}
for r in cmap_rows:
    if r["code"] in cmap and cmap[r["code"]] != r["symbol"]:
        print("CODE MAP CONFLICT:", r["code"], cmap[r["code"]], r["symbol"])
    cmap[r["code"]] = r["symbol"]
print("distinct codes:", len(cmap))
star_codes = {c: s for c, s in cmap.items() if s == "*"}
print("codes producing '*':", star_codes)
sym_codes = defaultdict(list)
for c, s in cmap.items():
    sym_codes[s].append(c)
print("codes per symbol:", {s: sorted(v) for s, v in sorted(sym_codes.items())})

books = {}
for r in rows("SELECT bookid, digits, insertedzeros, baselen, decodedbase FROM sheet__books GROUP BY bookid"):
    books[r["bookid"]] = dict(r)
print("books loaded:", len(books))

probe = {}
for r in rows("SELECT bookid, digitslen, insertedzeros, omitted_positions_json, omitted_codes_json, reconstructed_code_stream, decodedbase, consumed_digits, valid FROM row0_code_symbol_probe_books"):
    probe[r["bookid"]] = dict(r)
print("probe rows loaded:", len(probe))

# probe decodedbase vs sheet decodedbase consistency, all 70
mism = [b for b in books if probe[b]["decodedbase"] != books[b]["decodedbase"]]
print("probe.decodedbase != sheet.decodedbase:", mism if mism else "NONE (70/70 match)")

def reconstruct(bid, verbose=False):
    b = books[bid]; p = probe[bid]
    digits = b["digits"]
    omit_pos = json.loads(p["omitted_positions_json"])
    # interpret omitted positions: indices in code stream where leading zero omitted? inspect
    if verbose:
        print(f"book {bid}: digitslen={len(digits)} insertedzeros={b['insertedzeros']} baselen={b['baselen']}")
        print("  omitted_positions_json:", p["omitted_positions_json"])
        print("  omitted_codes_json:", p["omitted_codes_json"])
        print("  digits:", digits)
    # Try interpretation: omitted positions are code indices (0-based) where the code was
    # written with a single digit (leading zero omitted). Reconstruct stream:
    omit = set(omit_pos)
    codes = []
    i = 0
    ci = 0
    while i < len(digits):
        if ci in omit:
            codes.append("0" + digits[i]); i += 1
        else:
            codes.append(digits[i:i+2]); i += 2
        ci += 1
    consumed = i
    decoded = "".join(cmap.get(c, "?") for c in codes)
    stream = "".join(codes)
    ok_decoded = decoded == b["decodedbase"]
    ok_stream = stream == p["reconstructed_code_stream"]
    ok_count = len(codes) == int(b["baselen"])
    ok_zeros = sum(1 for c in codes if c.startswith("0") and codes.index) and True
    nz = len(omit & set(range(len(codes))))
    print(f"book {bid}: codes={len(codes)} consumed={consumed}/{len(digits)} "
          f"decoded==sheet.decodedbase: {ok_decoded}  stream==probe.stream: {ok_stream}  "
          f"ncodes==baselen: {ok_count}  omitted_used={len(omit)} (insertedzeros={b['insertedzeros']})")
    if verbose:
        print("  codes:", " ".join(codes))
        print("  decoded:", decoded)
        print("  sheet  :", b["decodedbase"])
    return ok_decoded and ok_stream and ok_count and consumed == len(digits)

print("\n=== hand reconstruction: book 0 ===")
reconstruct("0", verbose=True)

# second book: pick the one with the most insertedzeros
most_iz = max(books, key=lambda b: int(books[b]["insertedzeros"]))
print(f"\n=== hand reconstruction: book {most_iz} (most insertedzeros={books[most_iz]['insertedzeros']}) ===")
reconstruct(most_iz, verbose=True)

print("\n=== reconstruction across all 70 books ===")
allok = 0
fails = []
for bid in sorted(books, key=lambda x: int(x)):
    b = books[bid]; p = probe[bid]
    digits = b["digits"]
    omit = set(json.loads(p["omitted_positions_json"]))
    codes = []
    i = 0; ci = 0
    while i < len(digits):
        if ci in omit:
            codes.append("0" + digits[i]); i += 1
        else:
            codes.append(digits[i:i+2]); i += 2
        ci += 1
    decoded = "".join(cmap.get(c, "?") for c in codes)
    ok = decoded == b["decodedbase"] and "".join(codes) == p["reconstructed_code_stream"] and i == len(digits) and len(codes) == int(b["baselen"]) and len(omit) == int(b["insertedzeros"])
    if ok: allok += 1
    else: fails.append(bid)
print(f"full reconstruction OK: {allok}/70; fails: {fails if fails else 'NONE'}")

# star mask distribution by code per book and whether masked codes are uniform
print("\n=== star context ===")
star_total = 0
for bid in sorted(books, key=lambda x: int(x)):
    b = books[bid]; p = probe[bid]
    stream = p["reconstructed_code_stream"]
    codes = [stream[i:i+2] for i in range(0, len(stream), 2)]
    stars = [c for c in codes if cmap.get(c) == "*"]
    star_total += len(stars)
    uniq = set(stars)
    if stars and uniq != {"00"}:
        print(f"book {bid}: star codes other than 00: {uniq}")
print("total star occurrences from streams:", star_total)
con.close()
