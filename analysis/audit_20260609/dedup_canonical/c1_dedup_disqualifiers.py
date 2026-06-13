#!/usr/bin/env python3
"""CANONICAL deduped disqualifiers for the 469 book layer.

Dedup object: LZ first-occurrence residual at the decoded-symbol level
(min match 5 symbols, numeric bookid order, matches allowed against all
previously emitted text including the current book's own prefix).
Everything in Task 1 is computed on that residual and compared to the
full 70-book corpus (5729 symbols).
Read-only DB. Prints exact numbers.
"""
import sqlite3, math, random
from collections import Counter

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
cur = con.cursor()

rows = cur.execute("""SELECT bookid, MIN(digits), MIN(decodedbase), COUNT(*)
                      FROM sheet__books GROUP BY bookid""").fetchall()
print("ROWCOUNT sheet__books grouped:", len(rows))
assert len(rows) == 70, "expected 70 books"
def keyf(b):
    try: return (0, int(b))
    except: return (1, b)
ids = sorted([r[0] for r in rows], key=keyf)
dec = {r[0]: r[2] for r in rows}
dig = {r[0]: r[1] for r in rows}
tot_syms = sum(len(dec[b]) for b in ids)
tot_digits = sum(len(dig[b]) for b in ids)
print(f"books=70 total_digits={tot_digits} total_symbols={tot_syms}")

# ---------------- dedup object (LZ first occurrence) ----------------
def lz_novel(strings, order, minM):
    corpus = ""
    novel_mask = {}
    for b in order:
        s = strings[b]; mask = bytearray(len(s)); i = 0
        while i < len(s):
            lo, hi, best = minM, len(s) - i, 0
            while lo <= hi:
                mid = (lo + hi) // 2
                if s[i:i+mid] in corpus: best, lo = mid, mid + 1
                else: hi = mid - 1
            if best >= minM:
                i += best
            else:
                mask[i] = 1; i += 1
        novel_mask[b] = mask
        corpus += "#" + s
    return novel_mask

novel = lz_novel(dec, ids, 5)
nov_syms = sum(sum(m) for m in novel.values())
# maximal novel runs = segments
segments = []
for b in ids:
    m = novel[b]; s = dec[b]; i = 0
    while i < len(m):
        if m[i]:
            j = i
            while j < len(m) and m[j]: j += 1
            segments.append((b, i, s[i:j])); i = j
        else: i += 1
print(f"\nDEDUP OBJECT: LZ first-occurrence residual, symbol level, min match 5, bookid order")
print(f"  novel symbols = {nov_syms} / {tot_syms} ({100*nov_syms/tot_syms:.1f}%)")
print(f"  novel segments = {len(segments)}  (lengths min={min(len(t) for _,_,t in segments)} "
      f"median={sorted(len(t) for _,_,t in segments)[len(segments)//2]} max={max(len(t) for _,_,t in segments)})")
print(f"  books contributing novel material = {sum(1 for b in ids if sum(novel[b]))}/70")

cnt_full = Counter("".join(dec.values()))
cnt_ded = Counter()
for b in ids:
    for i, ch in enumerate(dec[b]):
        if novel[b][i]: cnt_ded[ch] += 1

SYMS13 = sorted(set("".join(dec.values())) - {"*"})
print("  alphabet:", "".join(SYMS13), "+ '*'")

# ---------------- (a) frequency profile ----------------
nf = sum(v for k, v in cnt_full.items() if k != "*")
nd = sum(v for k, v in cnt_ded.items() if k != "*")
print(f"\n(a) SYMBOL FREQUENCY PROFILE (pct of non-star; star shown separately)")
print(f"    {'sym':>3} {'full%':>7} {'dedup%':>7}")
for s in sorted(SYMS13, key=lambda x: -cnt_ded[x]):
    print(f"    {s:>3} {100*cnt_full[s]/nf:7.2f} {100*cnt_ded[s]/nd:7.2f}")
print(f"    '*' count: full {cnt_full.get('*',0)} ({100*cnt_full.get('*',0)/tot_syms:.2f}% of all) "
      f"dedup {cnt_ded.get('*',0)} ({100*cnt_ded.get('*',0)/nov_syms:.2f}% of all)")
# Gini coefficient of the 13-symbol distribution (peakedness, disqualifier 3 adjunct)
def gini(ps):
    ps = sorted(ps); n = len(ps); cum = 0.0
    for i, p in enumerate(ps, 1): cum += i * p
    return (2*cum)/(n*sum(ps)) - (n+1)/n
gf = gini([cnt_full[s]/nf for s in SYMS13])
gd = gini([cnt_ded[s]/nd for s in SYMS13])
print(f"    Gini(13-sym dist): full {gf:.3f}  dedup {gd:.3f}")

# ---------------- (b) chi-square gate ----------------
ENGLISH = dict(A=8.167,B=1.492,C=2.782,D=4.253,E=12.702,F=2.228,G=2.015,H=6.094,
    I=6.966,J=0.153,K=0.772,L=4.025,M=2.406,N=6.749,O=7.507,P=1.929,Q=0.095,
    R=5.987,S=6.327,T=9.056,U=2.758,V=0.978,W=2.360,X=0.150,Y=1.974,Z=0.074)
GERMAN = dict(A=6.516,B=1.886,C=2.732,D=5.076,E=16.396,F=1.656,G=3.009,H=4.577,
    I=6.550,J=0.268,K=1.417,L=3.437,M=2.534,N=9.776,O=2.594,P=0.670,Q=0.018,
    R=7.003,S=7.270,T=6.154,U=4.166,V=0.846,W=1.921,X=0.034,Y=0.039,Z=1.134)
SPANISH = dict(A=11.525,B=2.215,C=4.019,D=5.010,E=12.181,F=0.692,G=1.768,H=0.703,
    I=6.247,J=0.493,K=0.011,L=4.967,M=3.157,N=6.712,O=8.683,P=2.510,Q=0.877,
    R=6.871,S=7.977,T=4.632,U=2.927,V=1.138,W=0.017,X=0.215,Y=1.008,Z=0.467)

def chigate(cnt, label):
    obs = {s: cnt.get(s, 0) for s in SYMS13}
    N = sum(obs.values())
    def chisq(ref):
        tot = sum(ref[s] for s in SYMS13)
        return sum((obs[s]-N*ref[s]/tot)**2/(N*ref[s]/tot) for s in SYMS13)
    res = {"UNIFORM": chisq({s:1.0 for s in SYMS13}), "English": chisq(ENGLISH),
           "German": chisq(GERMAN), "Spanish": chisq(SPANISH)}
    order = sorted(res.items(), key=lambda kv: kv[1])
    print(f"    [{label}] N={N}: " + " < ".join(f"{k} {v:.0f}" for k, v in order))
    return res, N

print(f"\n(b) CHI-SQUARE vs renormalized 13-symbol references (12 df)")
rf, Nf_ = chigate(cnt_full, "FULL corpus")
rd, Nd_ = chigate(cnt_ded, "DEDUP residual")
print(f"    per-N normalization (chi2/N, scale-free): full " +
      " ".join(f"{k}={v/Nf_:.3f}" for k,v in sorted(rf.items(), key=lambda kv: kv[1])))
print(f"                                              dedup " +
      " ".join(f"{k}={v/Nd_:.3f}" for k,v in sorted(rd.items(), key=lambda kv: kv[1])))

# ---------------- (c) per-symbol anomalies ----------------
print(f"\n(c) PER-SYMBOL ANOMALIES (dedup residual, pct of non-star)")
en13 = {s: 100*ENGLISH[s]/sum(ENGLISH[t] for t in SYMS13) for s in SYMS13}
de13 = {s: 100*GERMAN[s]/sum(GERMAN[t] for t in SYMS13) for s in SYMS13}
for s in ["F","V","I","R","O"]:
    d = 100*cnt_ded[s]/nd; f = 100*cnt_full[s]/nf
    print(f"    {s}: dedup {d:5.2f}% (full {f:5.2f}%)  vs renorm-English {en13[s]:5.2f}% renorm-German {de13[s]:5.2f}%")

# ---------------- (d) vowel fraction + dictionary coverage ----------------
print(f"\n(d) VOWEL FRACTION + DICTIONARY COVERAGE")
vow = set("AEIO")
vf_full = sum(cnt_full[s] for s in vow)/nf
vf_ded = sum(cnt_ded[s] for s in vow)/nd
en_vf = sum(ENGLISH[s] for s in "AEIOU")/sum(ENGLISH.values())
print(f"    vowel fraction (A,E,I,O over non-star): full {100*vf_full:.1f}%  dedup {100*vf_ded:.1f}%  "
      f"(English AEIOU = {100*en_vf:.1f}%)")
# dictionary coverage: fraction of residual symbols covered by >=3-letter dict words
allowed = set(SYMS13)
words = set()
try:
    for w in open("/usr/share/dict/words"):
        w = w.strip().upper()
        if len(w) >= 3 and set(w) <= allowed: words.add(w)
except FileNotFoundError:
    pass
print(f"    dictionary: {len(words)} words of len>=3 writable in 13-letter alphabet")
maxw = max((len(w) for w in words), default=0)
def cov_frac(seglist):
    covd = tot = 0
    for t in seglist:
        t = t.replace("*","#")
        n = len(t); mark = bytearray(n)
        for i in range(n):
            for L in range(3, min(maxw, n-i)+1):
                if t[i:i+L] in words:
                    for k in range(i, i+L): mark[k] = 1
        covd += sum(mark); tot += n
    return covd/tot if tot else 0.0
segs_txt = [t for _,_,t in segments]
real_cov = cov_frac(segs_txt)
# control: random strings, same lengths, drawn from dedup unigram dist
rng = random.Random(469)
pool = list(cnt_ded.elements())
ctrl = []
for _ in range(20):
    ctrl.append(cov_frac(["".join(rng.choice(pool) for _ in t) for t in segs_txt]))
mu = sum(ctrl)/len(ctrl); sd = (sum((x-mu)**2 for x in ctrl)/len(ctrl))**0.5
z = (real_cov-mu)/sd if sd>0 else float("nan")
print(f"    dict coverage of dedup residual: {100*real_cov:.1f}%  "
      f"unigram-control mean {100*mu:.1f}% sd {100*sd:.1f}% -> z={z:+.2f}")

# ---------------- (e) reversal invariance (map-level; recheck) ----------------
print(f"\n(e) REVERSAL INVARIANCE (map-level, unaffected by dedup; recheck from row0_code_symbol_counts)")
mrows = cur.execute("""SELECT code, symbol, occurrence_count FROM row0_code_symbol_counts
                       WHERE run_id=1""").fetchall()
print(f"    ROWCOUNT map rows: {len(mrows)}")
best = {}
for c, s, n in mrows:
    if c not in best or n > best[c][1]: best[c] = (s, n)
code2sym = {c: s for c, (s, n) in best.items()}
nonpal = [c for c in code2sym if len(c)==2 and c[0]!=c[1] and c[::-1] in code2sym]
same = sum(1 for c in nonpal if code2sym[c]==code2sym[c[::-1]])
pairs = {}
for c in code2sym:
    if len(c)==2: pairs.setdefault(frozenset(c) if c[0]!=c[1] else (c[0],), set()).add(code2sym[c])
pure = sum(1 for v in pairs.values() if len(v)==1)
print(f"    non-palindrome codes whose reverse is also in map: {len(nonpal)}; map to SAME symbol: {same} "
      f"({same}/{len(nonpal)})")
print(f"    unordered digit-pair classes: {len(pairs)}; pure (single symbol): {pure}")
print(f"    -> property of the lookup TABLE, not of any particular text; dedup cannot affect it. HELD by construction.")

# ---------------- (f) effective sample size ----------------
print(f"\n(f) EFFECTIVE SAMPLE SIZE")
print(f"    full corpus: 5729 symbols across 70 books; LZ dedup shows only {nov_syms} ({100*nov_syms/tot_syms:.1f}%) are first-occurrence material")
print(f"    -> the published full-corpus tests were computed on ~{tot_syms/nov_syms:.1f}x pseudo-replicated data")
print(f"    chi2 statistics scale ~N, so dedup values are ~{tot_syms/nov_syms:.1f}x smaller in magnitude;")
print(f"    the DISQUALIFIER is the ordering + per-symbol profile, both of which must be re-checked above.")
print("\nDONE c1")
