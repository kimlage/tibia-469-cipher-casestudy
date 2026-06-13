#!/usr/bin/env python3
"""Module decomposition attack, part 1:
(a) digit-level greedy longest-repeated-substring module extraction (minL 10 and 20)
(c) recompute headline stats (symbol freqs, chi-square gate, code freqs) on deduped residual
(d) module-order syntax tests with permutation controls
Read-only DB access. Prints exact numbers.
"""
import sqlite3, json, random, math, sys
from collections import Counter, defaultdict

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
cur = con.cursor()

rows = cur.execute("""SELECT bookid, MIN(digits), MIN(decodedbase), COUNT(*)
                      FROM sheet__books GROUP BY bookid""").fetchall()
print("ROWCOUNT sheet__books grouped:", len(rows))
assert len(rows) == 70, "expected 70 books"
# numeric sort of bookids for deterministic order
def keyf(b):
    try: return (0, int(b))
    except: return (1, b)
ids = sorted([r[0] for r in rows], key=keyf)
dig = {r[0]: r[1] for r in rows}
dec = {r[0]: r[2] for r in rows}
tot_digits = sum(len(dig[b]) for b in ids)
tot_syms = sum(len(dec[b]) for b in ids)
print(f"books=70 total_digits={tot_digits} total_symbols={tot_syms}")

prows = cur.execute("""SELECT bookid, reconstructed_code_stream, decodedbase
                       FROM row0_code_symbol_probe_books WHERE run_id=1""").fetchall()
print("ROWCOUNT probe_books:", len(prows))
assert len(prows) == 70
codes = {r[0]: r[1].split() for r in prows}
mismatch = [r[0] for r in prows if r[2] != dec[r[0]]]
print("decodedbase mismatch sheet vs probe:", mismatch)

# ---------------- (a0) containment ----------------
contained = set()
pairs = 0
for a in ids:
    for b in ids:
        if a != b and dig[a] in dig[b]:
            contained.add(a); pairs += 1
print(f"\n== (a0) CONTAINMENT: {len(contained)}/70 books are exact digit substrings of another book ({pairs} containment pairs)")

# ---------------- (a) greedy module tiling ----------------
def tile(strings, minL):
    """greedy longest-repeated-substring tiling. strings: dict id->str.
    returns modules [(modid, string, [(book,pos),...])], covered dict id->bytearray"""
    cov = {b: bytearray(len(strings[b])) for b in strings}
    modules = []
    cap = max(len(s) for s in strings.values())
    def segments():
        segs = []
        for b in strings:
            s, c = strings[b], cov[b]
            i = 0
            while i < len(s):
                if not c[i]:
                    j = i
                    while j < len(s) and not c[j]: j += 1
                    segs.append((b, i, s[i:j])); i = j
                else: i += 1
        return segs
    while True:
        segs = segments()
        if not segs: break
        maxseg = max(len(t) for _, _, t in segs)
        hi = min(cap, maxseg)
        lo = minL
        if hi < lo: break
        def repeat_at(L):
            d = {}
            for b, off, t in segs:
                for i in range(len(t) - L + 1):
                    k = t[i:i+L]
                    d.setdefault(k, []).append((b, off + i))
            best = None
            for k, occ in d.items():
                # need >=2 non-overlapping occurrences
                if len(occ) < 2: continue
                bb = set(o[0] for o in occ)
                if len(bb) >= 2 or (max(o[1] for o in occ) - min(o[1] for o in occ) >= L):
                    if best is None or len(occ) > len(d[best]):
                        best = k
            return best, d
        # binary search for largest L with a repeat
        bestL, bestkey = None, None
        a, z = lo, hi
        while a <= z:
            mid = (a + z) // 2
            k, _ = repeat_at(mid)
            if k is not None:
                bestL, a = mid, mid + 1
            else:
                z = mid - 1
        if bestL is None: break
        key, d = repeat_at(bestL)
        occ = sorted(d[key])
        # claim non-overlapping occurrences
        claimed = []
        last = {}
        for b, p in occ:
            if b in last and p < last[b] + bestL: continue
            claimed.append((b, p)); last[b] = p
        if len(claimed) < 2:
            # degenerate; shouldn't happen often
            cap = bestL - 1; continue
        mid_ = len(modules)
        modules.append((mid_, key, claimed))
        for b, p in claimed:
            for i in range(p, p + bestL): cov[b][i] = 1
        cap = bestL
    return modules, cov

for minL in (20, 10):
    modules, cov = tile(dig, minL)
    inv_len = sum(len(m[1]) for m in modules)
    covered = sum(sum(c) for c in cov.values())
    novel = tot_digits - covered
    occ_tot = sum(len(m[2]) for m in modules)
    full = sum(1 for b in ids if all(cov[b]))
    print(f"\n== (a) MODULE TILING minL={minL}: modules={len(modules)} "
          f"inventory_digits={inv_len} occurrences={occ_tot} covered={covered} "
          f"({100*covered/tot_digits:.1f}%) novel_residual={novel} "
          f"unique_content=inventory+novel={inv_len+novel} "
          f"compression={tot_digits/(inv_len+novel):.2f}x books_fully_covered={full}")
    if minL == 20:
        MOD20, COV20 = modules, cov
        print("   top modules (len x uses):")
        for mid_, s, occ in sorted(modules, key=lambda m: -len(m[1]) * len(m[2]))[:10]:
            print(f"     M{mid_:02d} len={len(s)} uses={len(occ)} books={len(set(o[0] for o in occ))} {s[:40]}...")
    if minL == 10:
        COV10 = cov

# per-book composition at minL=20
comp = {b: [] for b in ids}
for mid_, s, occ in MOD20:
    for b, p in occ:
        comp[b].append((p, mid_, len(s)))
for b in comp: comp[b].sort()
seqs = {b: [m for _, m, _ in comp[b]] for b in ids}
print("\n== per-book module composition (minL=20), first 15 books:")
for b in ids[:15]:
    gaps = len(dig[b]) - sum(L for _, _, L in comp[b])
    print(f"   book {b}: len={len(dig[b])} modules={seqs[b]} residual_digits={gaps}")

# ---------------- (c) dedup + headline stats ----------------
# LZ-style dedup at decoded-symbol level, min match 5 symbols (=10 digits), vs all earlier text
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

novel_dec = lz_novel(dec, ids, 5)
nov_syms = sum(sum(m) for m in novel_dec.values())
print(f"\n== (c) DEDUP decoded level (LZ, min match 5 symbols, bookid order): novel={nov_syms} of {tot_syms} ({100*nov_syms/tot_syms:.1f}%)")
novel_dig = lz_novel(dig, ids, 10)
nov_digs = sum(sum(m) for m in novel_dig.values())
print(f"   DEDUP digit level (LZ, min match 10 digits): novel={nov_digs} of {tot_digits} ({100*nov_digs/tot_digits:.1f}%)")

ENGLISH = dict(A=8.167,B=1.492,C=2.782,D=4.253,E=12.702,F=2.228,G=2.015,H=6.094,
    I=6.966,J=0.153,K=0.772,L=4.025,M=2.406,N=6.749,O=7.507,P=1.929,Q=0.095,
    R=5.987,S=6.327,T=9.056,U=2.758,V=0.978,W=2.360,X=0.150,Y=1.974,Z=0.074)
GERMAN = dict(A=6.516,B=1.886,C=2.732,D=5.076,E=16.396,F=1.656,G=3.009,H=4.577,
    I=6.550,J=0.268,K=1.417,L=3.437,M=2.534,N=9.776,O=2.594,P=0.670,Q=0.018,
    R=7.003,S=7.270,T=6.154,U=4.166,V=0.846,W=1.921,X=0.034,Y=0.039,Z=1.134)
SPANISH = dict(A=11.525,B=2.215,C=4.019,D=5.010,E=12.181,F=0.692,G=1.768,H=0.703,
    I=6.247,J=0.493,K=0.011,L=4.967,M=3.157,N=6.712,O=8.683,P=2.510,Q=0.877,
    R=6.871,S=7.977,T=4.632,U=2.927,V=1.138,W=0.017,X=0.215,Y=1.008,Z=0.467)
SYMS13 = sorted(set("".join(dec.values())) - {"*"})
print("   13 symbols:", "".join(SYMS13))

def chigate(cnt, label):
    obs = {s: cnt.get(s, 0) for s in SYMS13}
    N = sum(obs.values())
    def chisq(ref):
        tot = sum(ref[s] for s in SYMS13)
        return sum((obs[s] - N*ref[s]/tot)**2 / (N*ref[s]/tot) for s in SYMS13)
    uni = {s: 1.0 for s in SYMS13}
    res = {"UNIFORM": chisq(uni), "English": chisq(ENGLISH),
           "German": chisq(GERMAN), "Spanish": chisq(SPANISH)}
    order = sorted(res.items(), key=lambda kv: kv[1])
    print(f"   chi2 gate [{label}] N={N}: " + " < ".join(f"{k} {v:.0f}" for k, v in order))
    return res

cnt_full = Counter("".join(dec.values()))
cnt_ded = Counter()
for b in ids:
    for i, ch in enumerate(dec[b]):
        if novel_dec[b][i]: cnt_ded[ch] += 1
chigate(cnt_full, "FULL corpus 5729 syms")
chigate(cnt_ded, f"DEDUPED residual {nov_syms} syms")
print("   symbol freq full vs dedup (pct of non-star):")
nf = sum(v for k, v in cnt_full.items() if k != "*")
nd = sum(v for k, v in cnt_ded.items() if k != "*")
for s in SYMS13:
    print(f"     {s}: full {100*cnt_full[s]/nf:5.2f}%  dedup {100*cnt_ded[s]/nd:5.2f}%")
print(f"   star: full {cnt_full.get('*',0)} dedup {cnt_ded.get('*',0)}")

# code frequencies full vs dedup (map decoded positions -> codes; code i corresponds to symbol i)
cnt_code_full, cnt_code_ded = Counter(), Counter()
for b in ids:
    cs = codes[b]
    if len(cs) != len(dec[b]):
        print(f"   WARN book {b}: codes {len(cs)} vs syms {len(dec[b])}")
        continue
    cnt_code_full.update(cs)
    for i, c in enumerate(cs):
        if novel_dec[b][i]: cnt_code_ded[c] += 1
Nf, Nd = sum(cnt_code_full.values()), sum(cnt_code_ded.values())
print(f"\n   code stream: {Nf} codes full, {Nd} novel; distinct codes full={len(cnt_code_full)} dedup={len(cnt_code_ded)}")
print("   top 10 codes full vs dedup:")
for c, v in cnt_code_full.most_common(10):
    print(f"     {c}: full {v} ({100*v/Nf:.2f}%)  dedup {cnt_code_ded.get(c,0)} ({100*cnt_code_ded.get(c,0)/Nd:.2f}%)")
# chi2 of dedup code dist against full-corpus code dist
chi = 0.0; df = 0
for c, v in cnt_code_full.items():
    e = Nd * v / Nf
    if e >= 1:
        chi += (cnt_code_ded.get(c, 0) - e)**2 / e; df += 1
print(f"   chi2(dedup codes vs full-corpus code dist) = {chi:.1f} on ~{df-1} df")

# ---------------- (d) module-order syntax ----------------
print("\n== (d) MODULE ORDER SYNTAX (minL=20 modules) ==")
mseqs = [seqs[b] for b in ids if len(seqs[b]) >= 1]
print(f"   books with >=1 module: {len(mseqs)}; with >=2: {sum(1 for s in mseqs if len(s)>=2)}")
firsts = Counter(s[0] for s in mseqs if s)
lasts = Counter(s[-1] for s in mseqs if s)
print(f"   first-module counts (top5): {firsts.most_common(5)}")
print(f"   last-module counts (top5): {lasts.most_common(5)}")
obs_first = firsts.most_common(1)[0][1]
obs_last = lasts.most_common(1)[0][1]

def bigram_rep(seqlist):
    bg = Counter()
    for s in seqlist:
        for i in range(len(s) - 1): bg[(s[i], s[i+1])] += 1
    return sum(v for v in bg.values() if v >= 2), sum(bg.values())

obs_rep, tot_bg = bigram_rep(mseqs)
print(f"   bigrams: total={tot_bg} tokens in repeated(>=2) bigram types={obs_rep}")

rng = random.Random(469)
NPERM = 10000
ge_f = ge_l = ge_b = 0
rep_dist = []
for _ in range(NPERM):
    perm = [rng.sample(s, len(s)) for s in mseqs]
    f = Counter(s[0] for s in perm if s).most_common(1)[0][1]
    l = Counter(s[-1] for s in perm if s).most_common(1)[0][1]
    r, _ = bigram_rep(perm)
    rep_dist.append(r)
    if f >= obs_first: ge_f += 1
    if l >= obs_last: ge_l += 1
    if r >= obs_rep: ge_b += 1
mu = sum(rep_dist)/NPERM
sd = (sum((x-mu)**2 for x in rep_dist)/NPERM) ** 0.5
z = (obs_rep - mu)/sd if sd > 0 else float('nan')
print(f"   PERMUTATION CONTROL ({NPERM} within-book order shuffles):")
print(f"     first-module max count: obs={obs_first} p={ge_f/NPERM:.4f}")
print(f"     last-module max count:  obs={obs_last} p={ge_l/NPERM:.4f}")
print(f"     repeated-bigram tokens: obs={obs_rep} control mean={mu:.1f} sd={sd:.2f} z={z:.2f} p={ge_b/NPERM:.4f}")

# module position regularity: does each module prefer a position-in-book?
print("   module offset consistency (modules used in >=3 books):")
for mid_, s, occ in MOD20:
    bb = set(o[0] for o in occ)
    if len(bb) >= 5:
        offs = [p for _, p in occ]
        print(f"     M{mid_:02d} len={len(s)} uses={len(occ)} offsets min={min(offs)} max={max(offs)} distinct={len(set(offs))}")
print("\nDONE m1")
