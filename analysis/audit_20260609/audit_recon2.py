#!/usr/bin/env python3
"""Figure out omitted-zero convention by diffing reconstructed_code_stream vs digits,
then redo independent end-to-end reconstruction for all 70 books."""
import sqlite3, json

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()

cmap = {r["code"]: r["symbol"] for r in cur.execute("SELECT code, symbol FROM row0_code_symbol_counts")}
print("codes in map:", len(cmap))

books = {r["bookid"]: dict(r) for r in cur.execute(
    "SELECT bookid, digits, insertedzeros, baselen, decodedbase FROM sheet__books GROUP BY bookid")}
probe = {r["bookid"]: dict(r) for r in cur.execute(
    "SELECT bookid, omitted_positions_json, omitted_codes_json, reconstructed_code_stream, decodedbase FROM row0_code_symbol_probe_books")}
print("books:", len(books), "probe:", len(probe))

# Book 0: find insertion points of '0' that turn digits into stream
b = books["0"]; p = probe["0"]
digits = b["digits"]; stream = p["reconstructed_code_stream"]
print("len digits", len(digits), "len stream", len(stream))
ins = []
i = j = 0
while j < len(stream):
    if i < len(digits) and digits[i] == stream[j]:
        i += 1; j += 1
    else:
        assert stream[j] == "0", (i, j, stream[j])
        ins.append(j); j += 1
print("book 0 greedy '0'-insertion positions in stream (digit-index):", ins)
print("book 0 omitted_positions_json:", p["omitted_positions_json"])
print("book 0 omitted codes at those stream positions:",
      [stream[(pos//2)*2:(pos//2)*2+2] for pos in ins])
print("book 0 omitted_codes_json:", p["omitted_codes_json"])
# code indices
print("book 0 code indices of insertions:", [pos//2 for pos in ins])

# Hypothesis: omitted_positions_json are DIGIT-STREAM positions (index in full stream) where '0' inserted.
def reconstruct(bid):
    b = books[bid]; p = probe[bid]
    digits = b["digits"]
    omit = json.loads(p["omitted_positions_json"])
    s = list(digits)
    for pos in sorted(omit):
        s.insert(pos, "0")
    stream = "".join(s)
    codes = [stream[k:k+2] for k in range(0, len(stream), 2)]
    decoded = "".join(cmap.get(c, "?") for c in codes)
    okS = stream == p["reconstructed_code_stream"]
    okD = decoded == b["decodedbase"]
    okP = p["decodedbase"] == b["decodedbase"]
    okL = len(codes) == int(b["baselen"]) and len(omit) == int(b["insertedzeros"])
    okC = json.loads(p["omitted_codes_json"]) == [stream[(pos//2)*2:(pos//2)*2+2] for pos in sorted(omit)]
    return okS, okD, okP, okL, okC, stream, decoded

print("\n=== BOOK 0 full hand check ===")
okS, okD, okP, okL, okC, stream, decoded = reconstruct("0")
print("stream matches probe:", okS, "| decoded matches sheet decodedbase:", okD,
      "| probe decodedbase matches sheet:", okP, "| lengths ok:", okL, "| omitted codes match:", okC)
print("digits :", books["0"]["digits"])
print("stream :", stream)
print("codes  :", " ".join(stream[k:k+2] for k in range(0, len(stream), 2)))
print("decoded:", decoded)
print("sheet  :", books["0"]["decodedbase"])

print("\n=== BOOK 10 full hand check (7 inserted zeros) ===")
okS, okD, okP, okL, okC, stream, decoded = reconstruct("10")
print("stream matches probe:", okS, "| decoded matches sheet decodedbase:", okD,
      "| probe decodedbase matches sheet:", okP, "| lengths ok:", okL, "| omitted codes match:", okC)
print("decoded:", decoded)
print("sheet  :", books["10"]["decodedbase"])

print("\n=== ALL 70 BOOKS ===")
allok = []
fails = []
star_by_code = {}
for bid in sorted(books, key=int):
    okS, okD, okP, okL, okC, stream, decoded = reconstruct(bid)
    if okS and okD and okP and okL and okC:
        allok.append(bid)
    else:
        fails.append((bid, okS, okD, okP, okL, okC))
print(f"PASS {len(allok)}/70")
print("FAILS:", fails if fails else "NONE")

# star codes across all reconstructed streams
from collections import Counter
star_codes = Counter()
total_codes = 0
for bid in books:
    _,_,_,_,_, stream, decoded = reconstruct(bid)
    codes = [stream[k:k+2] for k in range(0, len(stream), 2)]
    total_codes += len(codes)
    for c in codes:
        if cmap.get(c) == "*":
            star_codes[c] += 1
print("total codes (symbols):", total_codes)
print("star-producing code occurrences:", dict(star_codes))
con.close()
