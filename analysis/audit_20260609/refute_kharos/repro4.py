#!/usr/bin/env python3
"""Part 4: resolve chunk@109 ambiguity; inspect projections; final constrained decode."""
import sqlite3, json, math
from collections import Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True); cur = con.cursor()
q = lambda s, *a: cur.execute(s, a).fetchall()
books = {bid: dict(digits=d, decodedbase=db_) for bid, d, db_ in
         q("SELECT bookid, MIN(digits), MIN(decodedbase) FROM sheet__books GROUP BY bookid")}
K = q("SELECT sequence_digits FROM s2ward_corpus_audit_items WHERE source_set='sorted_unique_with_kharos' AND source_index=22")[0][0]
occ = Counter(); om = Counter(); wr = Counter(); c2s = {}
for c, s, o, omc, wrc in q("SELECT code, symbol, occurrence_count, omitted_count, written_count FROM row0_code_symbol_counts WHERE run_id=1"):
    occ[c]+=o; om[c]+=omc; wr[c]+=wrc; c2s[c]=s
tokmaps = {}
for bid, rcs, opj in q("SELECT bookid, reconstructed_code_stream, omitted_positions_json FROM row0_code_symbol_probe_books WHERE run_id=1"):
    cs = rcs.split(); omitted = set(x-1 for x in json.loads(opj))
    toks = []; pos = 0
    for ti, c in enumerate(cs):
        n = 1 if ti in omitted else 2
        toks.append((pos, n, c, ti in omitted)); pos += n
    tokmaps[bid] = toks

chunks = [(0,16,'13',120),(16,24,'13',95),(40,12,'2',108),(52,18,'2',43),(70,15,'2',84),(90,14,'2',65),(109,14,'2',161)]
# show the two distinct projections for chunk@109 and the conflict position
kpos, L = 109, 14
sub = K[kpos:kpos+L]
seen = {}
for bid, b in books.items():
    d = b['digits']; st = 0
    while True:
        j = d.find(sub, st)
        if j < 0: break
        st = j+1
        inside = [t for t in tokmaps[bid] if t[0] >= j and t[0]+t[1] <= j+L]
        key = tuple((t[0]-j, t[1], t[2], t[3]) for t in inside)
        seen.setdefault(key, []).append((bid, j))
print("chunk@109 distinct projections:")
for key, srcs in seen.items():
    print("  srcs:", srcs)
    print("   toks:", key, "->", "".join(c2s[c] for _,_,c,_ in key))

# build forced tokens using SOURCE occurrence only (greedy source book/pos)
forced = {}
for (kpos, L, bid, j) in chunks:
    inside = [t for t in tokmaps[bid] if t[0] >= j and t[0]+t[1] <= j+L]
    for (p, n, c, omf) in inside:
        forced[p - j + kpos] = (c, n, omf)
dec_pos = set()
for s0, (c, n, omf) in forced.items(): dec_pos.update(range(s0, s0+n))
print("decoded positions (source-occurrence projection):", len(dec_pos))

N = sum(occ.values())
def lpw(c):
    return (math.log(occ[c]/N) + math.log((wr[c]+0.5)/(occ[c]+1.0))) if c in c2s else None
def lpo(c):
    return (math.log(occ[c]/N) + math.log((om[c]+0.5)/(occ[c]+1.0))) if c in c2s else None
n = len(K); NEG = float('-inf')
dp = [NEG]*(n+1); bk = [None]*(n+1); dp[0] = 0.0
for i in range(n):
    if dp[i] == NEG: continue
    if i in forced:
        c, nd, omf = forced[i]
        lp = lpo(c) if omf else lpw(c)
        if lp is not None and dp[i]+lp > dp[i+nd]:
            dp[i+nd] = dp[i]+lp; bk[i+nd] = (i, c, omf)
        continue
    c = '0'+K[i]; lp = lpo(c)
    if lp is not None and dp[i]+lp > dp[i+1]:
        dp[i+1] = dp[i]+lp; bk[i+1] = (i, c, True)
    if i+2 <= n and (i+1) not in forced:
        c = K[i:i+2]; lp = lpw(c)
        if lp is not None and dp[i]+lp > dp[i+2]:
            dp[i+2] = dp[i]+lp; bk[i+2] = (i, c, False)
toks = []; i = n
while i > 0:
    pi, c, omf = bk[i]; toks.append((c, omf)); i = pi
toks.reverse()
dec = "".join(c2s[c] for c,_ in toks)
CLAIM = "TEINTAAETTEIVIFASTFNEVVTISETAFSETBASIESTIENFITFAIFVI*NIFATAEFTNESFEVIII"
nom = sum(1 for _, o in toks if o)
print(f"constrained decode: {len(toks)} symbols, {nom} omitted, identity {137+nom==2*len(toks)}")
print("mine :", dec)
print("claim:", CLAIM)
print("match:", dec == CLAIM)
if dec != CLAIM:
    if len(dec)==len(CLAIM):
        diffs=[i for i in range(len(dec)) if dec[i]!=CLAIM[i]]
        print("diffs:", diffs, [(dec[i],CLAIM[i]) for i in diffs])
# tail parse of novel digits 27215196805970 (kharos 123-136)
print("tail tokens (kharos digit pos>=109):")
pos = 0
for c, omf in toks:
    nd = 1 if omf else 2
    if pos >= 100:
        print(f"  pos{pos} code={c} om={omf} sym={c2s[c]}")
    pos += nd
con.close()
