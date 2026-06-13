#!/usr/bin/env python3
"""Step 1: verify reconstruction + straddle check for rare digit bigrams."""
import sqlite3, json, sys
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

# --- load books (dedupe by bookid) ---
cur.execute("""SELECT bookid, MIN(digits), MIN(decodedbase) FROM sheet__books
               GROUP BY bookid""")
books = cur.fetchall()
print(f"[rows] sheet__books deduped bookids: {len(books)}")
digits_by_book = {b: d for b, d, _ in books}
decoded_by_book = {b: dec for b, _, dec in books}

# --- load probe reconstructions ---
cur.execute("""SELECT bookid, reconstructed_code_stream, omitted_positions_json,
                      omitted_codes_json, valid, decodedbase
               FROM row0_code_symbol_probe_books WHERE run_id=1""")
probe = cur.fetchall()
print(f"[rows] probe_books run 1: {len(probe)}")

# --- code->symbol map ---
cur.execute("""SELECT code, symbol, occurrence_count, written_count
               FROM row0_code_symbol_counts WHERE run_id=1""")
csrows = cur.fetchall()
print(f"[rows] code_symbol_counts run 1: {len(csrows)}")
code2sym = {c: s for c, s, _, _ in csrows}
occ_table = {c: o for c, _, o, _ in csrows}
written_table = {c: w for c, _, _, w in csrows}

# --- verify reconstruction digit-exactness and decode-exactness ---
mismatch_digits = 0
mismatch_decode = 0
# per-book: list of (code, digit_start, digit_len) and boundary set
book_seg = {}
stream_counts = Counter()          # counts of codes as they appear in streams
written_stream_counts = Counter()  # only codes written with 2 digits
for bookid, stream, omit_pos_j, omit_codes_j, valid, dec in probe:
    codes = stream.split()
    omit_pos = set(p - 1 for p in json.loads(omit_pos_j))  # 1-based -> 0-based
    rebuilt = []
    segs = []
    p = 0
    for i, c in enumerate(codes):
        if i in omit_pos:
            w = c[1]  # leading zero omitted
        else:
            w = c
        segs.append((c, p, len(w)))
        rebuilt.append(w)
        p += len(w)
        stream_counts[c] += 1
        if len(w) == 2:
            written_stream_counts[c] += 1
    rebuilt = "".join(rebuilt)
    raw = digits_by_book[bookid]
    if rebuilt != raw:
        mismatch_digits += 1
        print(f"  DIGIT MISMATCH book {bookid}")
    dec_re = "".join(code2sym[c] for c in codes)
    if dec_re != decoded_by_book[bookid]:
        mismatch_decode += 1
        print(f"  DECODE MISMATCH book {bookid}: probe vs sheet")
    book_seg[bookid] = segs
print(f"[verify] digit-string mismatches: {mismatch_digits}/70")
print(f"[verify] decode mismatches vs sheet decodedbase: {mismatch_decode}/70")
print(f"[verify] total codes in streams: {sum(stream_counts.values())} (expect 5729)")
print(f"[verify] total raw digits: {sum(len(d) for d in digits_by_book.values())} (expect 11263)")

# --- compare stream counts to table counts ---
diff = {c: (stream_counts.get(c,0), occ_table.get(c,0)) for c in set(stream_counts)|set(occ_table)
        if stream_counts.get(c,0) != occ_table.get(c,0)}
print(f"[verify] stream-count vs table-count diffs: {len(diff)} -> {diff if diff else 'NONE'}")

# --- straddle check for target bigrams ---
targets = ["32", "33", "38", "39", "69", "66", "41", "07", "37", "02", "22"]
print("\n=== straddle check (raw digit bigrams at every alignment) ===")
for t in targets:
    on_boundary = 0
    straddle = 0
    locs_ob = []
    locs_str = []
    for bookid, segs in book_seg.items():
        raw = digits_by_book[bookid]
        starts = {p: (c, L) for (c, p, L) in segs}
        idx = raw.find(t)
        while idx != -1:
            if idx in starts and starts[idx][1] == 2 and starts[idx][0] == t:
                on_boundary += 1
                locs_ob.append((bookid, idx))
            else:
                straddle += 1
                locs_str.append((bookid, idx))
            idx = raw.find(t, idx + 1)
    print(f"bigram {t}: total_raw={on_boundary+straddle}  on_boundary={on_boundary}  straddle={straddle}")
    if on_boundary <= 6 and locs_ob:
        print(f"   on-boundary locs (book,digitpos): {locs_ob}")
    if straddle <= 8 and locs_str:
        print(f"   straddle locs: {locs_str}")

# --- context of the rare real codes: surrounding code window + symbol context ---
print("\n=== context windows for rare real codes ===")
for t in ["32", "33", "38", "69", "39"]:
    for bookid, segs in book_seg.items():
        codes = [c for c, _, _ in segs]
        for i, c in enumerate(codes):
            if c == t:
                lo, hi = max(0, i-5), min(len(codes), i+6)
                win = codes[lo:hi]
                sym = "".join(code2sym[x] for x in win)
                print(f"code {t} book {bookid} codeidx {i}: ...{' '.join(win)}...  syms={sym}")

# is the rare-code context inside a segment repeated in other books?
print("\n=== uniqueness of context (is the 11-code window found in any other book?) ===")
for t in ["32", "33", "38", "69"]:
    for bookid, segs in book_seg.items():
        codes = [c for c, _, _ in segs]
        for i, c in enumerate(codes):
            if c == t:
                lo, hi = max(0, i-3), min(len(codes), i+4)
                pat = " ".join(codes[lo:hi])
                hits = [b for b, s2 in book_seg.items()
                        if pat in " ".join(x for x, _, _ in s2)]
                print(f"code {t}: 7-code window appears in books: {hits}")
con.close()
