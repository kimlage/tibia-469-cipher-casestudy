#!/usr/bin/env python3
"""Independent reproduction (clean-room where feasible) of the module-decomposition
claim's deterministic numbers. Read-only DB access."""
import sqlite3, math
from collections import Counter

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)

rows = con.execute("SELECT bookid, MIN(digits), MIN(decodedbase) FROM sheet__books GROUP BY bookid").fetchall()
print("rowcount sheet__books grouped:", len(rows))
assert len(rows) == 70
def keyf(b):
    try: return (0, int(b))
    except Exception: return (1, b)
rows.sort(key=lambda r: keyf(r[0]))
ids = [r[0] for r in rows]
dig = {r[0]: r[1] for r in rows}
dec = {r[0]: r[2] for r in rows}
TD = sum(len(dig[b]) for b in ids); TS = sum(len(dec[b]) for b in ids)
print(f"total digits={TD} (claim 11263) total symbols={TS} (claim 5729)")

# cross-check decodedbase vs probe table
p = con.execute("SELECT bookid, decodedbase, reconstructed_code_stream FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
print("rowcount probe run_id=1:", len(p))
mism = [r[0] for r in p if dec.get(r[0]) != r[1]]
print("decodedbase mismatches vs probe table:", mism, "(claim: none)")
codes = {r[0]: r[2].split() for r in p}
badlen = [b for b in ids if len(codes[b]) != len(dec[b])]
print("books where code-stream len != decoded len:", badlen)

# exact duplicate books?
dup_digits = TD and len(set(dig.values()))
print(f"distinct digit strings among 70 books: {len(set(dig.values()))}; distinct decoded: {len(set(dec.values()))}")

# (1) containment census
contained = set(); pairs = 0
for a in ids:
    for b in ids:
        if a != b and dig[a] in dig[b]:
            contained.add(a); pairs += 1
print(f"\nCONTAINMENT: distinct contained books={len(contained)} (claim 20); ordered pairs={pairs} (claim 31)")

# (2) LZ dedup, clean-room implementation (greedy longest match vs all earlier text,
# earlier text = previously processed books joined with separator + current book's prefix? )
# NOTE: m1/m3 matched only against PREVIOUS books' corpus (corpus updated after each book),
# i.e. within-book repeats are NOT deduped. Reproduce that exact spec, my own loop:
def lz_dedup(strs, order, minM):
    earlier = ""
    masks = {}
    for b in order:
        s = strs[b]; n = len(s); mask = [0]*n; i = 0
        while i < n:
            # longest L >= minM with s[i:i+L] in earlier (linear scan up, not binary search)
            # guard: a candidate match must have full length >= minM (no truncated tails)
            L = 0
            top = n - i
            if top >= minM and s[i:i+minM] in earlier:
                L = minM
                while L < top and s[i:i+L+1] in earlier:
                    L += 1
            if L >= minM:
                i += L
            else:
                mask[i] = 1; i += 1
        masks[b] = mask
        earlier += "#" + s
    return masks

mdec = lz_dedup(dec, ids, 5)
novel_syms = sum(sum(m) for m in mdec.values())
mdig = lz_dedup(dig, ids, 10)
novel_digs = sum(sum(m) for m in mdig.values())
print(f"LZ dedup decoded min5: novel={novel_syms} (claim 995)  digits min10: novel={novel_digs} (claim 1305)")
# segments
segs = []
for b in ids:
    m = mdec[b]; i = 0
    while i < len(m):
        if m[i]:
            j = i
            while j < len(m) and m[j]: j += 1
            segs.append((b, i, j - i)); i = j
        else: i += 1
print(f"segments={len(segs)} (claim 162); >=10: {sum(1 for s in segs if s[2]>=10)} (claim 20) totaling {sum(s[2] for s in segs if s[2]>=10)} (claim 495); longest={max(s[2] for s in segs)} (claim 74)")

# (3) chi-square gate, my own code (13 symbols, renormalized refs)
EN = dict(A=8.167,B=1.492,C=2.782,D=4.253,E=12.702,F=2.228,G=2.015,H=6.094,I=6.966,J=0.153,K=0.772,L=4.025,M=2.406,N=6.749,O=7.507,P=1.929,Q=0.095,R=5.987,S=6.327,T=9.056,U=2.758,V=0.978,W=2.360,X=0.150,Y=1.974,Z=0.074)
DE = dict(A=6.516,B=1.886,C=2.732,D=5.076,E=16.396,F=1.656,G=3.009,H=4.577,I=6.550,J=0.268,K=1.417,L=3.437,M=2.534,N=9.776,O=2.594,P=0.670,Q=0.018,R=7.003,S=7.270,T=6.154,U=4.166,V=0.846,W=1.921,X=0.034,Y=0.039,Z=1.134)
ES = dict(A=11.525,B=2.215,C=4.019,D=5.010,E=12.181,F=0.692,G=1.768,H=0.703,I=6.247,J=0.493,K=0.011,L=4.967,M=3.157,N=6.712,O=8.683,P=2.510,Q=0.877,R=6.871,S=7.977,T=4.632,U=2.927,V=1.138,W=0.017,X=0.215,Y=1.008,Z=0.467)
S13 = sorted(set("".join(dec.values())) - {"*"})
print("\nsymbols:", "".join(S13))
def gate(cnt, label):
    N = sum(cnt[s] for s in S13)
    out = {}
    for name, ref in (("UNIFORM", {s:1.0 for s in S13}), ("English", EN), ("German", DE), ("Spanish", ES)):
        t = sum(ref[s] for s in S13)
        out[name] = sum((cnt[s] - N*ref[s]/t)**2/(N*ref[s]/t) for s in S13)
    print(f"chi2 [{label}] N={N}: " + " < ".join(f"{k} {v:.0f}" for k, v in sorted(out.items(), key=lambda kv: kv[1])))
cf = Counter("".join(dec.values()))
cr = Counter()
for b in ids:
    for i, ch in enumerate(dec[b]):
        if mdec[b][i]: cr[ch] += 1
gate(cf, "FULL (claim UNIFORM 3691 < EN 4296 < DE 4850 < ES 9408)")
gate(cr, "RESIDUAL (claim UNIFORM 639 < EN 788 < DE 887 < ES 1737)")
print("star: full", cf.get("*",0), "(claim 120) residual", cr.get("*",0), "(claim 18)")
print("I pct full %.1f (claim 20.6) residual %.1f (claim 18.8); E full %.1f (17.7) residual %.1f (18.8)" % (
    100*cf["I"]/sum(cf[s] for s in S13), 100*cr["I"]/sum(cr[s] for s in S13),
    100*cf["E"]/sum(cf[s] for s in S13), 100*cr["E"]/sum(cr[s] for s in S13)))

# code distribution residual vs full, independent
ccf, ccr = Counter(), Counter()
for b in ids:
    cs = codes[b]
    ccf.update(cs)
    for i, c in enumerate(cs):
        if mdec[b][i]: ccr[c] += 1
Nf, Nd = sum(ccf.values()), sum(ccr.values())
chi = 0.0; cells = 0
for c, v in ccf.items():
    e = Nd*v/Nf
    if e >= 1:
        chi += (ccr.get(c,0)-e)**2/e; cells += 1
print(f"code chi2 residual-vs-full = {chi:.1f} on ~{cells-1} df (claim 103.4 on ~91)")
try:
    from math import lgamma, exp
    # chi2 survival via regularized gamma Q(k/2, x/2) using continued fraction
    def gammq(a, x):
        if x < a+1:
            # series for P, return 1-P
            ap = a; s = 1.0/a; d = s
            for _ in range(500):
                ap += 1; d *= x/ap; s += d
                if abs(d) < abs(s)*1e-12: break
            return 1.0 - s*exp(-x + a*math.log(x) - lgamma(a))
        b0 = x+1-a; c0 = 1e300; d0 = 1/b0; h = d0
        for i in range(1, 500):
            an = -i*(i-a); b0 += 2
            d0 = an*d0 + b0; d0 = 1e-300 if abs(d0) < 1e-300 else d0
            c0 = b0 + an/c0; c0 = 1e-300 if abs(c0) < 1e-300 else c0
            d0 = 1/d0; de = d0*c0; h *= de
            if abs(de-1) < 1e-12: break
        return exp(-x + a*math.log(x) - lgamma(a)) * h
    print(f"p-value(chi2={chi:.1f}, df={cells-1}) = {gammq((cells-1)/2, chi/2):.3f} (claim ~0.18)")
except Exception as e:
    print("pval calc failed:", e)

# (4) shared 10-gram coverage, my own code
K = 10
where = {}
for bi, b in enumerate(ids):
    s = dec[b]
    for i in range(len(s)-K+1):
        where.setdefault(s[i:i+K], set()).add(bi)
cov = 0
for bi, b in enumerate(ids):
    s = dec[b]; m = [0]*len(s)
    for i in range(len(s)-K+1):
        if len(where[s[i:i+K]]) >= 2:
            for j in range(i, i+K): m[j] = 1
    cov += sum(m)
print(f"\nshared 10-gram coverage: {cov}/{TS} = {100*cov/TS:.1f}% (claim 4925/5729 = 86.0%)")

# baseline MDL
print(f"baseline MDL = {TS*math.log2(14):.0f} bits (claim 21812); alphabet size = {len(set(''.join(dec.values())))}")

# (5) max books per module at minL=20 -- reuse claim's tiling algorithm verbatim is in m1;
# here only verify the *interpretive* numbers from m1's saved module data via a re-tile
import importlib.util, io, contextlib, sys
sys.argv = ["x"]
spec = importlib.util.spec_from_file_location("m1", "./tmp/audit_20260609/m1_modules.py")
# don't import (it executes everything); instead re-implement greedy tiling check quickly is skipped here.
print("\nDONE indep")
