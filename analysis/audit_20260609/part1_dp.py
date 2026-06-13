#!/usr/bin/env python3
"""Part 1: Independent DP over zero-omission placements.

DP-A (decodedbase-constrained): count all ways to insert `insertedzeros` zeros
into the written digit stream s.t. the resulting 2-digit code stream is in the
99-code inventory AND decodes (code->symbol) to the known decodedbase.
Verify stored pathcount + omitidxs.

DP-B (inventory-only): count all ways consistent ONLY with the 99-code
inventory (each inserted zero forms a 0X code). Compute per-position symbol
marginals across all parses -> expected fraction of symbol positions that
differ from decodedbase (parse-underdetermination measure).
"""
import sqlite3, json, sys
from functools import lru_cache

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

# code -> symbol map
cur.execute("SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1")
rows = cur.fetchall()
print(f"code_symbol rows: {len(rows)}", flush=True)
assert len(rows) == 99
SYM = {c: s for c, s in rows}
INV = set(SYM)  # valid codes

cur.execute("""SELECT bookid, digits, CAST(insertedzeros AS INT), CAST(baselen AS INT), decodedbase
               FROM sheet__books GROUP BY bookid""")
books = cur.fetchall()
print(f"books: {len(books)}", flush=True)
assert len(books) == 70

cur.execute("""SELECT bookid, pathcount, omitidxs_1based, altomitpatterns_1based
               FROM row0_omission_probe_book_items WHERE run_id=1""")
stored = {b: (pc, oi, alt) for b, pc, oi, alt in cur.fetchall()}
print(f"stored probe items: {len(stored)}", flush=True)

cur.execute("""SELECT bookid, omitted_positions_json, reconstructed_code_stream, decodedbase
               FROM row0_code_symbol_probe_books WHERE run_id=1""")
probe = {r[0]: r[1:] for r in cur.fetchall()}
print(f"probe books: {len(probe)}", flush=True)

def dp_paths(digits, base, constrain_symbols):
    """Returns (#paths, list of omission patterns (1-based code idx) if small, code streams)."""
    n, m = len(digits), len(base)
    sys.setrecursionlimit(100000)

    @lru_cache(maxsize=None)
    def count(i, t):
        if t == m:
            return 1 if i == n else 0
        total = 0
        # take two written digits
        if i + 2 <= n:
            c = digits[i:i+2]
            if c in INV and (not constrain_symbols or SYM[c] == base[t]):
                total += count(i+2, t+1)
        # insert a zero (code 0X, leading zero omitted in writing)
        if i + 1 <= n:
            c = '0' + digits[i]
            if c in INV and (not constrain_symbols or SYM[c] == base[t]):
                # ensure we don't exceed allowed insertions
                ins = 2*(t+1) - (i+1)
                if ins <= 2*m - n:
                    total += count(i+1, t+1)
        return total

    total = count(0, 0)
    pats = []
    if constrain_symbols and total <= 64:
        # enumerate patterns
        stack = [(0, 0, ())]
        while stack:
            i, t, pat = stack.pop()
            if t == m:
                if i == n:
                    pats.append(pat)
                continue
            if i + 2 <= n:
                c = digits[i:i+2]
                if c in INV and SYM[c] == base[t]:
                    stack.append((i+2, t+1, pat))
            if i + 1 <= n:
                c = '0' + digits[i]
                if c in INV and SYM[c] == base[t]:
                    stack.append((i+1, t+1, pat + (t+1,)))
        assert len(pats) == total, (len(pats), total)
    return total, pats

def dp_marginals(digits, base):
    """Inventory-only DP: forward/backward counts, per-position symbol marginals."""
    n, m = len(digits), len(base)
    maxins = 2*m - n
    # forward[t][i] = #ways to reach (i digits consumed, t codes emitted)
    F = [dict() for _ in range(m+1)]
    F[0][0] = 1
    for t in range(m):
        for i, v in F[t].items():
            if i+2 <= n and digits[i:i+2] in INV:
                F[t+1][i+2] = F[t+1].get(i+2, 0) + v
            if i+1 <= n and ('0'+digits[i]) in INV and 2*(t+1)-(i+1) <= maxins:
                F[t+1][i+1] = F[t+1].get(i+1, 0) + v
    B = [dict() for _ in range(m+1)]
    B[m][n] = 1
    for t in range(m-1, -1, -1):
        for i in list(F[t].keys()):
            tot = 0
            if i+2 <= n and digits[i:i+2] in INV:
                tot += B[t+1].get(i+2, 0)
            if i+1 <= n and ('0'+digits[i]) in INV and 2*(t+1)-(i+1) <= maxins:
                tot += B[t+1].get(i+1, 0)
            if tot:
                B[t][i] = tot
    total = F[m].get(n, 0)
    if total == 0:
        return 0, None
    # expected number of positions where symbol != decodedbase[t]
    exp_diff = 0.0
    for t in range(m):
        wrong = 0
        for i, v in F[t].items():
            bi = B[t]
            if i+2 <= n:
                c = digits[i:i+2]
                if c in INV:
                    w = v * B[t+1].get(i+2, 0)
                    if w and SYM[c] != base[t]:
                        wrong += w
            if i+1 <= n:
                c = '0'+digits[i]
                if c in INV and 2*(t+1)-(i+1) <= maxins:
                    w = v * B[t+1].get(i+1, 0)
                    if w and SYM[c] != base[t]:
                        wrong += w
        exp_diff += wrong / total
    return total, exp_diff / m

results = []
mismatch_pc = 0
mismatch_pat = 0
multi = []
invonly_counts = []
for bookid, digits, iz, baselen, base in books:
    assert len(digits) + iz == 2*baselen, bookid
    pc, pats = dp_paths(digits, base, True)
    spc = stored[bookid][0]
    if pc != spc:
        mismatch_pc += 1
        print(f"PATHCOUNT MISMATCH book {bookid}: mine={pc} stored={spc}")
    # check stored omit pattern is among enumerated
    s_omit = stored[bookid][1]
    if s_omit:
        s_pat = tuple(int(x) for x in s_omit.split(','))
    else:
        s_pat = ()
    if pats and s_pat not in pats:
        mismatch_pat += 1
        print(f"PATTERN MISMATCH book {bookid}: stored {s_pat} not in mine {pats}")
    # also check probe table omitted positions
    p_omit = tuple(json.loads(probe[bookid][0]))
    if pats and p_omit not in pats:
        print(f"PROBE PATTERN MISMATCH book {bookid}")
    tot_b, fdiff = dp_marginals(digits, base)
    invonly_counts.append((bookid, pc, tot_b, fdiff))
    if pc > 1:
        multi.append((bookid, pc, pats))
    results.append((bookid, iz, pc, tot_b, fdiff))

print(f"\npathcount mismatches vs stored: {mismatch_pc}/70")
print(f"pattern mismatches vs stored: {mismatch_pat}/70")
pcs = [r[2] for r in results]
print(f"pathcount=1 books: {sum(1 for p in pcs if p==1)}; multipath: {sum(1 for p in pcs if p>1)}")
print(f"pathcount distribution: {sorted(set(pcs))} counts: {[(v, pcs.count(v)) for v in sorted(set(pcs))]}")
import statistics
print(f"median pathcount (decodedbase-constrained): {statistics.median(pcs)}")

# multipath: decodedbase divergence across alternative parses = 0 by construction
# (all constrained parses reproduce decodedbase exactly). Quantify CODE-stream divergence:
print("\n-- multipath books (decodedbase-constrained): code-stream divergence --")
for bookid, pc, pats in multi:
    # positions where omission patterns differ
    allpos = set()
    for p in pats:
        allpos |= set(p)
    common = set(pats[0])
    for p in pats[1:]:
        common &= set(p)
    print(f"book {bookid}: paths={pc} ambiguous omit slots={sorted(allpos - common)}")

print("\n-- inventory-only DP (no decodedbase constraint) --")
totals = [r[3] for r in results]
fdiffs = [r[4] for r in results]
import math
logs = [math.log10(t) for t in totals]
print(f"min paths {min(totals):.3g}, median log10(paths) {statistics.median(logs):.2f}, max log10 {max(logs):.2f}")
print(f"expected fraction of symbol positions differing from decodedbase across inventory-only parses:")
print(f"  min {min(fdiffs):.4f} median {statistics.median(fdiffs):.4f} max {max(fdiffs):.4f}")

with open('./tmp/audit_20260609/part1_results.json','w') as f:
    json.dump({'results':[(b,iz,pc,str(t),fd) for b,iz,pc,t,fd in results]}, f)
print("done")
