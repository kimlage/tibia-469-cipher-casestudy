#!/usr/bin/env python3
"""Independent verification of the module-decomposition probe claims.
Independent implementations (no binary search; linear match extension; direct loops).
Read-only DB. Prints row counts after every query.
"""
import sqlite3, json, math
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
print("total digits:", sum(len(dig[b]) for b in ids), "(claim 11263)")
print("total symbols:", sum(len(dec[b]) for b in ids), "(claim 5729)")

# 1. containment (independent)
contained = set(); pairs = 0
for a in ids:
    for b in ids:
        if a != b and dig[a] in dig[b]:
            contained.add(a); pairs += 1
print("containment: distinct contained books =", len(contained), "(claim 20); pairs =", pairs, "(claim 31)")

# 2. independent LZ dedup, decoded level, min match 5, earlier-books-only corpus
def lz_novel_linear(strings, order, minM):
    corpus = ""
    masks = {}
    for b in order:
        s = strings[b]; mask = bytearray(len(s)); i = 0
        L = len(s)
        while i < L:
            if s[i:i+minM] in corpus:
                best = minM
                while i + best < L and s[i:i+best+1] in corpus:
                    best += 1
                i += best
            else:
                mask[i] = 1; i += 1
        masks[b] = mask
        corpus += "#" + s
    return masks

mdec = lz_novel_linear(dec, ids, 5)
nov = sum(sum(m) for m in mdec.values())
print("LZ novel decoded symbols:", nov, "(claim 995)")
mdig = lz_novel_linear(dig, ids, 10)
print("LZ novel digits:", sum(sum(m) for m in mdig.values()), "(claim 1305)")

# segments
segs = []
for b in ids:
    m = mdec[b]; i = 0
    while i < len(m):
        if m[i]:
            j = i
            while j < len(m) and m[j]: j += 1
            segs.append((b, i, dec[b][i:j])); i = j
        else: i += 1
print("segments:", len(segs), "(claim 162); longest:", max(len(t) for _,_,t in segs), "(claim 74)")

# 3. shared 10-gram coverage (independent implementation)
k = 10
gram_books = {}
for b in ids:
    s = dec[b]
    for i in range(len(s)-k+1):
        gram_books.setdefault(s[i:i+k], set()).add(b)
cov = 0
for b in ids:
    s = dec[b]; mask = bytearray(len(s))
    for i in range(len(s)-k+1):
        if len(gram_books[s[i:i+k]]) >= 2:
            for j in range(i, i+k): mask[j] = 1
    cov += sum(mask)
N = sum(len(dec[b]) for b in ids)
print(f"shared-10-gram coverage: {cov}/{N} = {100*cov/N:.1f}% (claim 4925/5729 = 86.0%)")

# 4. chi2 gate on residual, AND residual-vs-COMPLEMENT tests (part-vs-whole bias check)
ENGLISH = dict(A=8.167,B=1.492,C=2.782,D=4.253,E=12.702,F=2.228,G=2.015,H=6.094,
    I=6.966,J=0.153,K=0.772,L=4.025,M=2.406,N=6.749,O=7.507,P=1.929,Q=0.095,
    R=5.987,S=6.327,T=9.056,U=2.758,V=0.978,W=2.360,X=0.150,Y=1.974,Z=0.074)
SYMS13 = sorted(set("".join(dec.values())) - {"*"})
cnt_full = Counter("".join(dec.values()))
cnt_res = Counter()
for b in ids:
    for i, ch in enumerate(dec[b]):
        if mdec[b][i]: cnt_res[ch] += 1
cnt_comp = Counter({s: cnt_full[s]-cnt_res[s] for s in cnt_full})

def chisq(cnt, ref):
    obs = {s: cnt.get(s,0) for s in SYMS13}
    Nn = sum(obs.values()); tot = sum(ref[s] for s in SYMS13)
    return sum((obs[s]-Nn*ref[s]/tot)**2/(Nn*ref[s]/tot) for s in SYMS13)
uni = {s:1.0 for s in SYMS13}
print(f"residual gate N={sum(cnt_res.get(s,0) for s in SYMS13)}: UNIFORM {chisq(cnt_res,uni):.0f} (claim 639), English {chisq(cnt_res,ENGLISH):.0f} (claim 788)")
print(f"full gate: UNIFORM {chisq(cnt_full,uni):.0f} (claim 3691), English {chisq(cnt_full,ENGLISH):.0f} (claim 4296)")

# residual vs COMPLEMENT (independent samples, avoids part-vs-whole leakage)
chi = 0.0; df = 0
Nr = sum(cnt_res.values()); Nc = sum(cnt_comp.values())
for s in set(cnt_res) | set(cnt_comp):
    o_r, o_c = cnt_res.get(s,0), cnt_comp.get(s,0)
    tot = o_r + o_c
    e_r, e_c = tot*Nr/(Nr+Nc), tot*Nc/(Nr+Nc)
    if e_r >= 1 and e_c >= 1:
        chi += (o_r-e_r)**2/e_r + (o_c-e_c)**2/e_c; df += 1
print(f"SYMBOLS residual vs complement: chi2={chi:.1f} on {df-1} df (independent-samples version)")

# codes: residual vs complement
prows = con.execute("SELECT bookid, reconstructed_code_stream FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
print("rowcount probe_books:", len(prows))
codes = {r[0]: r[1].split() for r in prows}
cr, cc = Counter(), Counter()
for b in ids:
    cs = codes[b]
    if len(cs) != len(dec[b]): continue
    for i, c in enumerate(cs):
        (cr if mdec[b][i] else cc)[c] += 1
Nr, Nc = sum(cr.values()), sum(cc.values())
chi = 0.0; df = 0
for c in set(cr) | set(cc):
    o_r, o_c = cr.get(c,0), cc.get(c,0)
    tot = o_r + o_c
    e_r, e_c = tot*Nr/(Nr+Nc), tot*Nc/(Nr+Nc)
    if e_r >= 1 and e_c >= 1:
        chi += (o_r-e_r)**2/e_r + (o_c-e_c)**2/e_c; df += 1
print(f"CODES residual vs complement: chi2={chi:.1f} on {df-1} df (probe reported part-vs-whole 103.4 on ~91 df)")

# 5. max books per module at minL=20 (re-run probe's tiling algorithm to check 'max 3 books' claim
#    and count single-book (within-book-repeat-only) modules)
import sys
sys.setrecursionlimit(10000)
def tile(strings, minL):
    cov = {b: bytearray(len(strings[b])) for b in strings}
    modules = []
    cap = max(len(s) for s in strings.values())
    def segments():
        out = []
        for b in strings:
            s, c = strings[b], cov[b]
            i = 0
            while i < len(s):
                if not c[i]:
                    j = i
                    while j < len(s) and not c[j]: j += 1
                    out.append((b, i, s[i:j])); i = j
                else: i += 1
        return out
    while True:
        segs = segments()
        if not segs: break
        maxseg = max(len(t) for _,_,t in segs)
        hi = min(cap, maxseg); lo = minL
        if hi < lo: break
        def repeat_at(L):
            d = {}
            for b, off, t in segs:
                for i in range(len(t)-L+1):
                    d.setdefault(t[i:i+L], []).append((b, off+i))
            best = None
            for kk, occ in d.items():
                if len(occ) < 2: continue
                bb = set(o[0] for o in occ)
                if len(bb) >= 2 or (max(o[1] for o in occ) - min(o[1] for o in occ) >= L):
                    if best is None or len(occ) > len(d[best]): best = kk
            return best, d
        bestL = None
        a, z = lo, hi
        while a <= z:
            mid = (a+z)//2
            kk, _ = repeat_at(mid)
            if kk is not None: bestL, a = mid, mid+1
            else: z = mid-1
        if bestL is None: break
        key, d = repeat_at(bestL)
        occ = sorted(d[key])
        claimed = []; last = {}
        for b, p in occ:
            if b in last and p < last[b] + bestL: continue
            claimed.append((b,p)); last[b] = p
        if len(claimed) < 2:
            cap = bestL-1; continue
        modules.append((len(modules), key, claimed))
        for b,p in claimed:
            for i in range(p, p+bestL): cov[b][i] = 1
        cap = bestL
    return modules, cov

mods, cov = tile(dig, 20)
covd = sum(sum(c) for c in cov.values())
print(f"tiling minL=20 rerun: modules={len(mods)} covered={covd} (claim 62 / 9184)")
bpm = [len(set(o[0] for o in m[2])) for m in mods]
print("max books per module:", max(bpm), "(claim 3); modules in only 1 book (within-book repeat):",
      sum(1 for x in bpm if x == 1), "of", len(mods))
cross_cov = 0
for mid_, s, occ in mods:
    if len(set(o[0] for o in occ)) >= 2:
        cross_cov += len(s)*len(occ)
print(f"digits covered by CROSS-BOOK modules only: {cross_cov} ({100*cross_cov/11263:.1f}% of corpus)")
print("DONE")
