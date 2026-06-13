#!/usr/bin/env python3
"""Independent reproduction of the Kharos holdout-decode claim. Read-only."""
import sqlite3, json, math, random, sys
from collections import Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

def q(sql, *a):
    return cur.execute(sql, a).fetchall()

# ---------- 1. Books ----------
rows = q("""SELECT bookid, MIN(digits), MIN(insertedzeros), MIN(baselen), MIN(decodedbase),
                   COUNT(*), COUNT(DISTINCT digits)
            FROM sheet__books GROUP BY bookid""")
print("BOOKS: deduped rows =", len(rows))
books = {}
ident_ok = 0
tot_digits = 0; tot_sym = 0
for bid, digits, iz, bl, db_, n, nd in rows:
    assert nd == 1, f"book {bid} divergent dup digits"
    iz, bl = int(iz), int(bl)
    books[bid] = dict(digits=digits, iz=iz, baselen=bl, decodedbase=db_)
    tot_digits += len(digits); tot_sym += bl
    if len(digits) + iz == 2*bl: ident_ok += 1
print(f"total digits={tot_digits} (claim 11263), total symbols={tot_sym} (claim 5729), identity {ident_ok}/{len(rows)}")

# ---------- 2. Kharos ----------
r = q("""SELECT sequence_digits, sequence_len, candidate_status
         FROM s2ward_corpus_audit_items
         WHERE source_set='sorted_unique_with_kharos' AND source_index=22""")
print("kharos rows:", len(r))
K = r[0][0]
print(f"KHAROS len={len(K)} (claim 137), status={r[0][2]}")
print("kharos digits:", K)
for bid, b in books.items():
    if K in b['digits']: print("!! kharos substring of book", bid)

# ---------- 3. row0 inventory run_id=1 ----------
inv = q("""SELECT code, symbol, occurrence_count, omitted_count, written_count
           FROM row0_code_symbol_counts WHERE run_id=1""")
print("inventory rows:", len(inv))
codes = sorted(set(c for c,_,_,_,_ in inv))
print("distinct codes:", len(codes), "(claim 99)")
missing = [f"{i:02d}" for i in range(100) if f"{i:02d}" not in codes]
print("missing codes:", missing, "(claim only '39')")
occ = Counter(); om = Counter(); wr = Counter()
code2sym = {}
for c,s,o,omc,wrc in inv:
    occ[c]+=o; om[c]+=omc; wr[c]+=wrc
    code2sym.setdefault(c, []).append((s,o))
multi = {c:v for c,v in code2sym.items() if len(v)>1}
print("codes mapping to >1 symbol:", len(multi))
omitted_codes = sorted(c for c in codes if om[c]>0)
print("codes ever omitted:", omitted_codes, "(claim subset of 00-09)")
print("07: occ=%d om=%d wr=%d (claim always omitted)" % (occ['07'], om['07'], wr['07']))
print("02: occ=%d om=%d wr=%d (claim never omitted)" % (occ['02'], om['02'], wr['02']))
print("0d stats (occ,om,wr):", {f"0{d}": (occ[f"0{d}"], om[f"0{d}"], wr[f"0{d}"]) for d in range(10)})

# ---------- 4. probe_books token maps, verify byte-exact ----------
pb = q("""SELECT bookid, reconstructed_code_stream, omitted_positions_json, valid
          FROM row0_code_symbol_probe_books WHERE run_id=1""")
print("probe_books rows:", len(pb), "valid:", sum(x[3] for x in pb))
tokmaps = {}
ok_tokidx = 0
for bid, rcs, opj, valid in pb:
    cs = [rcs[i:i+2] for i in range(0, len(rcs), 2)]
    omitted = set(json.loads(opj))
    raw_parts = []; toks = []; pos = 0
    for ti, c in enumerate(cs):
        emit = c[1] if ti in omitted else c
        toks.append((pos, len(emit), c, ti in omitted))
        raw_parts.append(emit); pos += len(emit)
    raw = "".join(raw_parts)
    if bid in books and raw == books[bid]['digits']:
        ok_tokidx += 1; tokmaps[bid] = toks
print(f"byte-exact (omitted=token-index): {ok_tokidx}/{len(pb)}")
if ok_tokidx < len(pb):
    tokmaps = {}; ok2 = 0
    for bid, rcs, opj, valid in pb:
        cs = [rcs[i:i+2] for i in range(0, len(rcs), 2)]
        omitset = set(json.loads(opj))
        full = "".join(cs)
        raw = "".join(ch for i, ch in enumerate(full) if i not in omitset)
        if bid in books and raw == books[bid]['digits']:
            ok2 += 1
            toks = []; pos = 0
            for ti, c in enumerate(cs):
                a, b = 2*ti, 2*ti+1
                n = (a not in omitset) + (b not in omitset)
                toks.append((pos, n, c, a in omitset))
                pos += n
            tokmaps[bid] = toks
    print(f"byte-exact (omitted=full-stream digit pos): {ok2}/{len(pb)}")
print("books with token maps:", len(tokmaps))

# code -> top symbol map (for decode)
best_sym = {c: max(v, key=lambda x: x[1])[0] for c, v in code2sym.items()}

# ---------- 5. template coverage ----------
allcat = list((bid, b['digits']) for bid, b in books.items())

grams = [K[i:i+10] for i in range(len(K)-9)]
hitpos = set(); hits = 0
for i, g in enumerate(grams):
    if any(g in d for _, d in allcat):
        hits += 1; hitpos.update(range(i, i+10))
print(f"10-gram cov: grams {hits}/{len(grams)}={hits/len(grams):.4f} (claim .414), positions {len(hitpos)}/{len(K)}={len(hitpos)/len(K):.4f} (claim .825)")

def longest_at(s, i, minlen=1):
    best = 0; src = None
    for Ltry in range(len(s)-i, minlen-1, -1):
        sub = s[i:i+Ltry]
        for bid, d in allcat:
            j = d.find(sub)
            if j >= 0:
                return Ltry, (bid, j)
    return 0, None

# LSS
bestL = 0; bestinfo = None
for i in range(len(K)):
    L, src = longest_at(K, i)
    if L > bestL: bestL = L; bestinfo = (i, src)
print(f"LSS={bestL} at kharos[{bestinfo[0]}] from book {bestinfo[1][0]} @ {bestinfo[1][1]} (claim 24)")

# greedy leftmost-longest chunks >=8
chunks = []; i = 0
while i < len(K):
    L, src = longest_at(K, i, minlen=8)
    if L >= 8:
        chunks.append((i, L, src[0], src[1])); i += L
    else:
        i += 1
cov = sum(c[1] for c in chunks)
print(f"GREEDY CHUNKS>=8: n={len(chunks)} cover={cov}/{len(K)}={cov/len(K):.4f} (claim 7, 113/137)")
for c in chunks:
    print(f"  kharos@{c[0]} len={c[1]} <- book {c[2]} @ {c[3]} : {K[c[0]:c[0]+c[1]]}")
covered = set()
for c in chunks: covered.update(range(c[0], c[0]+c[1]))
gaps = []; i = 0
while i < len(K):
    if i not in covered:
        j = i
        while j < len(K) and j not in covered: j += 1
        gaps.append((i, K[i:j])); i = j
    else: i += 1
print("GAPS:", gaps)
print("(claim gaps: 76145@85, 65128@104, 27215196805970@123)")
con.close()
print("PART1 DONE")
