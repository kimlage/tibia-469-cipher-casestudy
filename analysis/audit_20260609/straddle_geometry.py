#!/usr/bin/env python3
import sqlite3, json, itertools, math
from collections import Counter, defaultdict

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
cur = con.cursor()

# ---------- load code->symbol table ----------
cur.execute("""SELECT code,symbol,occurrence_count,omitted_count,written_count
               FROM row0_code_symbol_counts WHERE run_id=1""")
rows = cur.fetchall()
print("code_symbol_counts rows:", len(rows))
code_info = {}
for code, sym, occ, om, wr in rows:
    code_info[code] = dict(symbol=sym, occ=occ, om=om, wr=wr)

# all 100 cells
all_cells = [f"{i:02d}" for i in range(100)]
present = set(code_info.keys())
absent = [c for c in all_cells if c not in present]
print("present codes:", len(present), "absent codes:", absent)

# ---------- load reconstructed code streams ----------
cur.execute("""SELECT bookid, reconstructed_code_stream, valid
               FROM row0_code_symbol_probe_books WHERE run_id=1""")
streams = {}
for bookid, rcs, valid in cur.fetchall():
    streams[bookid] = (rcs.split(), valid)
print("probe books:", len(streams), "all valid:", all(v for _, v in streams.values()))

# set of real codes that actually appear as a TOKEN in any reconstructed stream
codes_in_streams = Counter()
for bookid, (toks, valid) in streams.items():
    for t in toks:
        codes_in_streams[t] += 1
print("distinct codes appearing as real tokens:", len(codes_in_streams))

# ---------- load raw digits ----------
cur.execute("""SELECT bookid, digits, insertedzeros FROM sheet__books
               WHERE bookid IS NOT NULL GROUP BY bookid""")
raw = {}
for bookid, digits, iz in cur.fetchall():
    raw[bookid] = digits.strip()
print("raw books:", len(raw))

# ============================================================
# STEP 1: straddle check for target bigrams 32, 33, 38, and also 07,69,66,41,79 etc.
# A raw occurrence of bigram XY at position i is a "real code" iff the reconstruction
# places a token boundary exactly at i (token starting at i equals XY and aligned).
# Because zeros are inserted, raw string != concatenation of code tokens directly.
# Strategy: for each book reconstruct the alignment between raw digits and the
# reconstructed code stream by replaying the omitted-zero insertion.
# Simpler robust approach: the reconstructed_code_stream tokens, when concatenated,
# should equal a string we can align to raw by accounting for inserted zeros.
# We instead directly tabulate, for every code TOKEN in every stream, its (d1,d2).
# That gives the *real* occupancy. Then we separately scan RAW bigrams at all offsets
# to see how often 32/33/38 appear as substrings vs. as actual aligned tokens.
# ============================================================

# Build the digit-stream-with-inserted-zeros for each book by concatenating tokens
def concat(toks):
    return "".join(toks)

# real token occupancy from streams
token_occ = Counter()
for bookid, (toks, valid) in streams.items():
    for t in toks:
        token_occ[t] += 1
print("\n--- real token occupancy (from reconstructed streams) ---")
for c in ["32","33","38","07","69","66","41","79","22","37","23","02","13","62","26","10"]:
    print(f"  {c}: stream_tokens={token_occ.get(c,0)}  table_occ={code_info.get(c,{}).get('occ','-')}  sym={code_info.get(c,{}).get('symbol','-')}")

# RAW substring scan: count bigram XY at EVERY offset (overlapping) and at EVEN offsets
def raw_bigram_counts(strings):
    any_off = Counter()
    for s in strings:
        for i in range(len(s)-1):
            any_off[s[i:i+2]] += 1
    return any_off

raw_strings = list(raw.values())
raw_any = raw_bigram_counts(raw_strings)
print("\n--- RAW substring occurrences (overlapping, any offset) ---")
for c in ["32","33","38","07","69","66","41","79","19","51","11","45"]:
    print(f"  {c}: raw_substr={raw_any.get(c,0)}  table_occ={code_info.get(c,{}).get('occ','-')}")

# For 32, 33, 38: locate each raw substring occurrence and test if it aligns to a token boundary.
# We need per-book alignment. Reconstruct alignment: the reconstructed stream consumed
# `consumed_digits` from raw with insertedzeros zeros omitted at omitted_positions.
# Pull full probe rows for alignment.
cur.execute("""SELECT bookid, reconstructed_code_stream, omitted_positions_json, omitted_codes_json, consumed_digits
               FROM row0_code_symbol_probe_books WHERE run_id=1""")
align = {}
for bookid, rcs, opj, ocj, cd in cur.fetchall():
    align[bookid] = (rcs.split(), json.loads(opj), json.loads(ocj), cd)

# The reconstructed code stream IS the canonical 2-digit framing (with inserted zeros baked in).
# Concatenating tokens gives the "filled" digit string. The raw string is the filled string
# with the inserted zeros REMOVED at omitted_positions. So to map raw bigram positions to
# token boundaries we work in the FILLED coordinate system.
def token_boundaries(toks):
    # returns set of start indices (even) and a map index->token for boundaries
    starts = {}
    pos = 0
    for t in toks:
        starts[pos] = t
        pos += len(t)
    return starts, pos

straddle_report = {}
for target in ["32","33","38"]:
    occs = []  # (bookid, filled_index, is_boundary, token_if_boundary, neighbors)
    for bookid, (toks, ops, ocs, cd) in align.items():
        filled = concat(toks)
        starts, total = token_boundaries(toks)
        # scan filled string for target
        idx = filled.find(target)
        while idx != -1:
            is_boundary = idx in starts and starts[idx] == target
            occs.append((bookid, idx, is_boundary,
                         starts.get(idx, None)))
            idx = filled.find(target, idx+1)
    straddle_report[target] = occs

print("\n--- STRADDLE CHECK (filled coordinate system) ---")
for target, occs in straddle_report.items():
    boundary = [o for o in occs if o[2]]
    straddle = [o for o in occs if not o[2]]
    print(f"  bigram {target}: total_substr_in_filled={len(occs)}  as_real_token(boundary)={len(boundary)}  straddle={len(straddle)}")
    # show a few straddle examples
    for o in straddle[:4]:
        print(f"      straddle book={o[0]} filled_idx={o[1]} token_at_idx={o[3]}")
    for o in boundary[:4]:
        print(f"      BOUNDARY book={o[0]} filled_idx={o[1]} token={o[3]}")

# Confirm against table occ: 32,33,38 each have occ=1 in table. Does the boundary count match?
print("\n--- consistency: table occ vs boundary token count ---")
for target in ["32","33","38"]:
    boundary = [o for o in straddle_report[target] if o[2]]
    print(f"  {target}: table_occ={code_info[target]['occ']} boundary_count={len(boundary)} stream_token={token_occ.get(target,0)}")

con.close()
