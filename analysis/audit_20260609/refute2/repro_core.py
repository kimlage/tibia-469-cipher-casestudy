#!/usr/bin/env python3
"""Independent reproduction of the Kharos holdout-decode claim.
Written from the claim text (not copied from the probe scripts), different RNG seed.
"""
import sqlite3, math, random, json
from collections import Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
random.seed(20260609)  # different seed from probe (469)

con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

# ---- 1. books ----
rows = cur.execute("SELECT bookid, MIN(digits), MIN(insertedzeros), MIN(baselen), MIN(decodedbase), MIN(digitslen) FROM sheet__books GROUP BY bookid").fetchall()
print(f"BOOKS deduped={len(rows)}")
books = []
for bid, d, iz, bl, base, dl in rows:
    books.append(dict(bid=bid, d=d.strip(), iz=int(iz), bl=int(bl), base=base.strip(), dl=int(dl)))
print(f"TOTAL digits={sum(len(b['d']) for b in books)} baselen={sum(b['bl'] for b in books)}")
viol = [b['bid'] for b in books if len(b['d']) != b['dl'] or b['dl'] + b['iz'] != 2*b['bl'] or len(b['base']) != b['bl']]
print(f"IDENTITY violations: {len(viol)} {viol}")

# ---- 2. inventory ----
crow = cur.execute("SELECT code, symbol, occurrence_count, omitted_count, written_count FROM row0_code_symbol_counts WHERE run_id=1").fetchall()
print(f"INVENTORY codes={len(crow)}")
code_sym = {c: s for c, s, *_ in crow}
occ = {c: o for c, s, o, om, w in crow}
omc = {c: om for c, s, o, om, w in crow}
wrc = {c: w for c, s, o, om, w in crow}
inv = set(code_sym)
missing = sorted(set(f"{i:02d}" for i in range(100)) - inv)
print(f"MISSING codes: {missing}")
omit_codes = sorted(c for c in inv if omc[c] > 0)
print(f"CODES with omitted_count>0: {omit_codes}")
print(f"NON-0x codes with omissions: {[c for c in omit_codes if not c.startswith('0')]}")
print(f"code 07: occ={occ.get('07')} omitted={omc.get('07')} written={wrc.get('07')}")
print(f"code 02: occ={occ.get('02')} omitted={omc.get('02')} written={wrc.get('02')}")
zero_codes = sorted(c for c in inv if c.startswith('0'))
print("0x codes detail:", {c: (occ[c], omc[c], wrc[c]) for c in zero_codes})

TOT = sum(occ.values()); AL = 0.5
def lp_w(c): return math.log((occ.get(c,0)+AL)/(TOT+100*AL)) + math.log((wrc.get(c,0)+AL)/(occ.get(c,0)+2*AL))
def lp_o(c): return math.log((occ.get(c,0)+AL)/(TOT+100*AL)) + math.log((omc.get(c,0)+AL)/(occ.get(c,0)+2*AL))

# ---- 3. Kharos ----
KH = cur.execute("SELECT sequence_digits FROM s2ward_corpus_audit_items WHERE source_set='sorted_unique_with_kharos' AND source_index=22").fetchone()[0].strip()
L = len(KH)
print(f"KHAROS len={L} digits={KH}")

def count_paths(s):
    n = len(s); dp = [0]*(n+1); dp[n] = 1
    for i in range(n-1, -1, -1):
        v = dp[i+1]  # 1-digit token: code '0'+s[i]; all 00..09 in inventory
        assert ('0'+s[i]) in inv
        if i+1 < n and s[i:i+2] in inv:
            v += dp[i+2]
        dp[i] = v
    return dp[0]

def viterbi(s):
    n = len(s); best = [None]*(n+1); best[n] = (0.0, None, None)
    for i in range(n-1, -1, -1):
        cand = []
        if best[i+1] is not None:
            cand.append((best[i+1][0]+lp_o('0'+s[i]), ('0'+s[i], True), i+1))
        if i+1 < n and s[i:i+2] in inv and best[i+2] is not None:
            cand.append((best[i+2][0]+lp_w(s[i:i+2]), (s[i:i+2], False), i+2))
        best[i] = max(cand) if cand else None
    toks = []; i = 0
    while i < n:
        _, t, nx = best[i]; toks.append(t); i = nx
    return best[0][0], toks

paths = count_paths(KH)
print(f"DP path count log10={math.log10(paths):.4f}")
lpv, toks = viterbi(KH)
nom = sum(1 for _, o in toks if o)
flags = Counter()
for c, o in toks:
    if c not in inv: flags['invalid'] += 1
    if o and omc.get(c, 0) == 0: flags['omit_never_omitted'] += 1
    if (not o) and wrc.get(c, 0) == 0: flags['write_always_omitted'] += 1
print(f"ML tokens={len(toks)} omitted={nom} lp={lpv:.4f} lp/token={lpv/len(toks):.4f} identity {L}+{nom}==2*{len(toks)}: {L+nom==2*len(toks)}")
print(f"FLAGS: {dict(flags)}")
print(f"ML omitted-token codes: {Counter(c for c,o in toks if o)}")
print(f"ML written 0x codes: {Counter(c for c,o in toks if (not o) and c.startswith('0'))}")
print(f"uses code 39: {sum(1 for c,o in toks if c=='39')}")

# ---- 4. coverage ----
NG = 10
grams = set()
for b in books:
    d = b['d']
    for i in range(len(d)-NG+1): grams.add(d[i:i+NG])
hits = 0; covered = [False]*L
for i in range(L-NG+1):
    if KH[i:i+NG] in grams:
        hits += 1
        for j in range(i, i+NG): covered[j] = True
print(f"digit10 gramcov={hits}/{L-NG+1}={hits/(L-NG+1):.4f} poscov={sum(covered)}/{L}={sum(covered)/L:.4f}")

def lss(s, corpus):
    joined = "\x01".join(corpus)
    lo, hi = 0, len(s)
    while lo < hi:
        mid = (lo+hi+1)//2
        if any(s[i:i+mid] in joined for i in range(len(s)-mid+1)): lo = mid
        else: hi = mid-1
    return lo
print(f"LSS digits vs books: {lss(KH, [b['d'] for b in books])}")

# ---- 5. greedy chunk cover ----
def longest_at(s, i, corpus):
    lo, hi = 0, len(s)-i; best = []
    while lo < hi:
        mid = (lo+hi+1)//2; sub = s[i:i+mid]; h = []
        for b in corpus:
            st = b['d'].find(sub)
            while st != -1:
                h.append((b['bid'], st)); st = b['d'].find(sub, st+1)
        if h: lo = mid; best = h
        else: hi = mid-1
    return lo, best

def greedy(s, corpus, minlen=8):
    segs = []; i = 0
    while i < len(s):
        n, h = longest_at(s, i, corpus)
        if n >= minlen:
            segs.append(('M', i, n, h)); i += n
        else:
            if segs and segs[-1][0] == 'G':
                segs[-1] = ('G', segs[-1][1], segs[-1][2]+1, None)
            else:
                segs.append(('G', i, 1, None))
            i += 1
    return segs

segs = greedy(KH, books)
mt = sum(ln for t, st, ln, h in segs if t == 'M')
nm = sum(1 for t, *_ in segs if t == 'M')
print(f"GREEDY cover: {nm} chunks, {mt}/{L} = {mt/L:.4f}")
for t, st, ln, h in segs:
    if t == 'M':
        print(f"  MATCH @{st} len{ln} sub={KH[st:st+ln]} hits={h}")
    else:
        print(f"  GAP   @{st} len{ln} sub={KH[st:st+ln]}")

con.close()
print("CORE DONE")
