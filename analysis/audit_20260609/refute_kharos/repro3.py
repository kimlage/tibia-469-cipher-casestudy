#!/usr/bin/env python3
"""Part 3: projection with tokens-fully-inside interpretation + constrained decode."""
import sqlite3, json, math
from collections import Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
q = lambda s, *a: cur.execute(s, a).fetchall()

books = {}
for bid, digits, iz, bl, db_ in q("SELECT bookid, MIN(digits), MIN(insertedzeros), MIN(baselen), MIN(decodedbase) FROM sheet__books GROUP BY bookid"):
    books[bid] = dict(digits=digits, baselen=int(bl), decodedbase=db_)
K = q("SELECT sequence_digits FROM s2ward_corpus_audit_items WHERE source_set='sorted_unique_with_kharos' AND source_index=22")[0][0]
inv = q("SELECT code, symbol, occurrence_count, omitted_count, written_count FROM row0_code_symbol_counts WHERE run_id=1")
occ = Counter(); om = Counter(); wr = Counter(); c2s = {}
for c, s, o, omc, wrc in inv:
    occ[c]+=o; om[c]+=omc; wr[c]+=wrc; c2s[c]=s

pb = q("SELECT bookid, reconstructed_code_stream, omitted_positions_json FROM row0_code_symbol_probe_books WHERE run_id=1")
tokmaps = {}
for bid, rcs, opj in pb:
    cs = rcs.split()
    omitted = set(x-1 for x in json.loads(opj))
    toks = []; pos = 0
    for ti, c in enumerate(cs):
        n = 1 if ti in omitted else 2
        toks.append((pos, n, c, ti in omitted)); pos += n
    tokmaps[bid] = toks

allcat = [(bid, b['digits']) for bid, b in books.items()]
def longest_at(s, i, minlen=8):
    for L in range(len(s)-i, minlen-1, -1):
        sub = s[i:i+L]
        for bid, d in allcat:
            j = d.find(sub)
            if j >= 0: return L, bid, j
    return 0, None, None
chunks = []; i = 0
while i < len(K):
    L, bid, j = longest_at(K, i)
    if L >= 8: chunks.append((i, L, bid, j)); i += L
    else: i += 1

# projection: tokens fully inside window
proj = {}        # kharos pos -> (code, role) role: 0=first digit of written,1=second,(-1)=omitted single
conflicts = 0
unique_cnt = 0
decoded_positions = set()
forced_tokens = {}   # start kharos pos -> (code, ndigits, omitted)
print("PROJECTION (tokens fully inside window):")
for (kpos, L, bid0, j0) in chunks:
    sub = K[kpos:kpos+L]
    projs = []
    for bid, d in allcat:
        st = 0
        while True:
            j = d.find(sub, st)
            if j < 0: break
            st = j + 1
            toks = tokmaps[bid]
            inside = [t for t in toks if t[0] >= j and t[0]+t[1] <= j+L]
            if inside:
                projs.append((bid, j, inside))
    seqs = set(tuple((t[0]-j, t[1], t[2], t[3]) for t in inside) for (bid, j, inside) in projs)
    print(f"  chunk@{kpos} len={L}: occurrences-with-tokens={len(projs)}, distinct projections={len(seqs)}")
    if len(seqs) == 1: unique_cnt += 1
    # merge all projections; flag conflicts
    local = {}
    for bid, j, inside in projs:
        off = kpos - j
        for (p, n, c, omf) in inside:
            key = (p+off, n, c, omf)
            s0 = p + off
            if s0 in local and local[s0] != (n, c, omf):
                conflicts += 1
            local[s0] = (n, c, omf)
    for s0, (n, c, omf) in local.items():
        forced_tokens[s0] = (c, n, omf)
        for dp_ in range(s0, s0+n): decoded_positions.add(dp_)
print(f"unique projections: {unique_cnt}/7 (claim 6/7)")
print(f"decoded positions: {len(decoded_positions)}/137 (claim 109 = 79.6%)")
print(f"conflicts: {conflicts} (claim 0)")

# ---------- constrained Viterbi: forced tokens at projected starts ----------
N = sum(occ.values())
def lpw(c):
    if c not in c2s or wr[c]+0.5 <= 0: return None
    return math.log(occ[c]/N) + math.log((wr[c]+0.5)/(occ[c]+1.0))
def lpo(c):
    if c not in c2s: return None
    return math.log(occ[c]/N) + math.log((om[c]+0.5)/(occ[c]+1.0))

n = len(K); NEG = float('-inf')
dp = [NEG]*(n+1); bk = [None]*(n+1); dp[0] = 0.0
for i in range(n):
    if dp[i] == NEG: continue
    if i in forced_tokens:
        c, nd, omf = forced_tokens[i]
        lp = lpo(c) if omf else lpw(c)
        if lp is not None and dp[i]+lp > dp[i+nd]:
            dp[i+nd] = dp[i]+lp; bk[i+nd] = (i, c, omf)
        continue
    # also must not start a token that would straddle into a forced-token start mid-token
    c = '0'+K[i]; lp = lpo(c)
    if lp is not None and dp[i]+lp > dp[i+1]:
        dp[i+1] = dp[i]+lp; bk[i+1] = (i, c, True)
    if i+2 <= n and (i+1) not in forced_tokens:
        c = K[i:i+2]; lp = lpw(c)
        if lp is not None and dp[i]+lp > dp[i+2]:
            dp[i+2] = dp[i]+lp; bk[i+2] = (i, c, False)
toks = []
i = n
while i > 0:
    pi, c, omf = bk[i]
    toks.append((c, omf)); i = pi
toks.reverse()
dec = "".join(c2s[c] for c, _ in toks)
CLAIM = "TEINTAAETTEIVIFASTFNEVVTISETAFSETBASIESTIENFITFAIFVI*NIFATAEFTNESFEVIII"
nom = sum(1 for _, o in toks if o)
print(f"\nconstrained decode: {len(toks)} symbols, {nom} omitted, identity {137+nom}=={2*len(toks)}: {137+nom==2*len(toks)}")
print("mine :", dec)
print("claim:", CLAIM)
print("match:", dec == CLAIM)
if dec != CLAIM and len(dec) == len(CLAIM):
    diffs = [i for i in range(len(dec)) if dec[i] != CLAIM[i]]
    print("diffs:", diffs, [(dec[i], CLAIM[i]) for i in diffs])
omitted_used = sorted(c for c, o in toks if o)
print("omitted codes used:", omitted_used)
viol = (any(c=='39' for c,_ in toks), any(c=='07' and not o for c,o in toks), any(o and om[c]==0 for c,o in toks))
print("violations (39, written07, omit-never):", viol)
con.close()
print("PART3 DONE")
