#!/usr/bin/env python3
"""Adversarial audit of the markov/homophone-rotation claim.

A) Segmentation ambiguity: given digits + decodedbase + code->symbol map,
   how many valid parses exist per book? At how many token positions does
   the code identity differ across valid parses? (If many, the recorded
   reconstructed_code_stream is an algorithmic choice and the rotation
   statistic could be an artifact of the resolver = leakage.)
B) Independent reproduction of the rotation test (own code, new seed=20260610,
   2000 perms), plus robustness:
   - per-book sign consistency at d=2,3 (deficit direction)
   - excluding all omittable codes (00-09) from pair counting
   - d=5 enrichment: fraction of d=5 same-code pairs inside repeated code
     5-gram contexts (verbatim-copy confound)
"""
import json, random, sqlite3
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
rows = con.execute(
    "SELECT bookid, reconstructed_code_stream, decodedbase FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
sb = dict(con.execute("SELECT bookid, digits FROM sheet__books GROUP BY bookid").fetchall())
maprows = con.execute("SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1").fetchall()
con.close()
print(f"probe rows: {len(rows)}; sheet books: {len(sb)}; map rows: {len(maprows)}")
assert len(rows) == 70 and len(sb) == 70
code2sym = {}
for c, s in maprows:
    assert c not in code2sym or code2sym[c] == s
    code2sym[c] = s
print(f"distinct codes in map: {len(code2sym)}")

# ---------- A) parse-count DP and per-position code ambiguity ----------
def parse_info(digits, base, code2sym):
    m, n = len(base), len(digits)
    # f[i][j] = number of parses of base[i:] from digits[j:]
    from functools import lru_cache
    import sys
    sys.setrecursionlimit(100000)
    NP = {}
    def npar(i, j):
        if (i, j) in NP: return NP[(i, j)]
        if i == m:
            r = 1 if j == n else 0
        else:
            r = 0
            if j + 2 <= n:
                c = digits[j:j+2]
                if code2sym.get(c) == base[i]:
                    r += npar(i+1, j+2)
            if j + 1 <= n:
                c = "0" + digits[j]
                if code2sym.get(c) == base[i]:
                    r += npar(i+1, j+1)
        NP[(i, j)] = r
        return r
    total = npar(0, 0)
    # positions with >1 distinct code across valid parses
    amb_positions = 0
    if total > 0:
        # forward counts g[i][j]: parses of base[:i] ending at digit j
        G = defaultdict(int); G[(0, 0)] = 1
        # iterate i ascending over reachable states
        states = [(0, 0)]
        seen = {(0, 0)}
        per_pos_codes = defaultdict(set)
        frontier = {(0, 0): 1}
        for i in range(m):
            nf = defaultdict(int)
            for (ii, j), cnt in frontier.items():
                # 2-digit
                if j + 2 <= n:
                    c = digits[j:j+2]
                    if code2sym.get(c) == base[i] and npar(i+1, j+2) > 0:
                        per_pos_codes[i].add(c)
                        nf[(i+1, j+2)] += cnt
                if j + 1 <= n:
                    c = "0" + digits[j]
                    if code2sym.get(c) == base[i] and npar(i+1, j+1) > 0:
                        per_pos_codes[i].add(c)
                        nf[(i+1, j+1)] += cnt
            frontier = nf
        amb_positions = sum(1 for i in range(m) if len(per_pos_codes[i]) > 1)
    return total, amb_positions

tot_amb = 0; multi_parse_books = 0; tot_pos = 0
for bid, stream, base in sorted(rows):
    digits = sb[bid]
    t, a = parse_info(digits, base, code2sym)
    assert t >= 1, (bid, "no valid parse?!")
    tot_pos += len(base)
    tot_amb += a
    if t > 1:
        multi_parse_books += 1
print(f"\nA) books with >1 valid parse: {multi_parse_books}/70")
print(f"   token positions with ambiguous code identity: {tot_amb}/{tot_pos}")

# ---------- B) independent rotation reproduction ----------
books = []
for bid, stream, base in sorted(rows):
    codes = stream.split()
    assert len(codes) == len(base)
    books.append((bid, codes, base))

MAXD = 6
def reuse(codes, base, exclude_codes=None):
    same = Counter(); n = Counter()
    for d in range(1, MAXD+1):
        for i in range(len(base)-d):
            if base[i] == base[i+d]:
                if exclude_codes and (codes[i] in exclude_codes or codes[i+d] in exclude_codes):
                    continue
                n[d] += 1
                if codes[i] == codes[i+d]:
                    same[d] += 1
    return same, n

def perm_test(books, nperm, seed, exclude_codes=None):
    obs_s = Counter(); obs_n = Counter()
    groups = []
    for _, codes, base in books:
        s, n = reuse(codes, base, exclude_codes)
        obs_s.update(s); obs_n.update(n)
        g = defaultdict(list)
        for i, sym in enumerate(base):
            g[sym].append(i)
        groups.append((codes, base, g))
    rng = random.Random(seed)
    perm = defaultdict(list)
    for _ in range(nperm):
        tot = Counter()
        for codes, base, g in groups:
            new = list(codes)
            for sym, idxs in g.items():
                vals = [codes[i] for i in idxs]
                rng.shuffle(vals)
                for i, v in zip(idxs, vals):
                    new[i] = v
            s, _ = reuse(new, base, exclude_codes)
            tot.update(s)
        for d in range(1, MAXD+1):
            perm[d].append(tot[d])
    out = {}
    for d in range(1, MAXD+1):
        vals = perm[d]
        m = sum(vals)/len(vals)
        sd = (sum((x-m)**2 for x in vals)/(len(vals)-1))**0.5
        o = obs_s[d]
        z = (o-m)/sd if sd > 0 else float("nan")
        plo = sum(1 for v in vals if v <= o)/len(vals)
        phi = sum(1 for v in vals if v >= o)/len(vals)
        out[d] = (o, obs_n[d], m, sd, z, plo, phi)
    return out

print("\nB1) independent reproduction (2000 perms, seed 20260610):")
r = perm_test(books, 2000, 20260610)
for d in sorted(r):
    o, n, m, sd, z, plo, phi = r[d]
    print(f"  d={d}: obs={o}/{n} perm={m:.1f}+-{sd:.1f} z={z:+.2f} p_lo={plo:.4f} p_hi={phi:.4f}")

print("\nB2) excluding all omittable codes 00-09 (segmentation-ambiguity-proof):")
excl = {f"0{i}" for i in range(10)}
r = perm_test(books, 1000, 20260611, exclude_codes=excl)
for d in sorted(r):
    o, n, m, sd, z, plo, phi = r[d]
    print(f"  d={d}: obs={o}/{n} perm={m:.1f}+-{sd:.1f} z={z:+.2f} p_lo={plo:.4f} p_hi={phi:.4f}")

# per-book direction at d=2,3 (pooled d2+d3 deficit per book, vs its own 200 perms)
print("\nB3) per-book consistency at d in {2,3}:")
neg = pos = zero = 0
rngb = random.Random(99)
for bid, codes, base in books:
    s, n = reuse(codes, base)
    o = s[2] + s[3]
    g = defaultdict(list)
    for i, sym in enumerate(base):
        g[sym].append(i)
    vals = []
    for _ in range(200):
        new = list(codes)
        for sym, idxs in g.items():
            v = [codes[i] for i in idxs]
            rngb.shuffle(v)
            for i, x in zip(idxs, v):
                new[i] = x
        ss, _ = reuse(new, base)
        vals.append(ss[2] + ss[3])
    m = sum(vals)/len(vals)
    if o < m: neg += 1
    elif o > m: pos += 1
    else: zero += 1
print(f"   books below perm mean: {neg}, above: {pos}, equal: {zero} (of 70)")

# d=5 enrichment: how many same-code-at-d5 pairs sit inside a repeated code k-gram
print("\nB4) d=5 same-code pairs inside locally repeated code contexts:")
ctx = 0; tot5 = 0
for bid, codes, base in books:
    for i in range(len(base)-5):
        if base[i] == base[i+5] and codes[i] == codes[i+5]:
            tot5 += 1
            # is the neighboring code also equal (i.e., a >=2-token repeat at offset 5)?
            if (i+6 < len(codes) and codes[i+1] == codes[i+6]) or (i-1 >= 0 and i+4 < len(codes) and codes[i-1] == codes[i+4]):
                ctx += 1
print(f"   {ctx}/{tot5} d=5 same-code pairs have an adjacent code also repeating at offset 5")
# baseline: same fraction among ALL equal-symbol d=5 pairs (not just same-code)
ctx2 = 0; totp = 0
for bid, codes, base in books:
    for i in range(len(base)-5):
        if base[i] == base[i+5]:
            totp += 1
            if (i+6 < len(codes) and codes[i+1] == codes[i+6]) or (i-1 >= 0 and i+4 < len(codes) and codes[i-1] == codes[i+4]):
                ctx2 += 1
print(f"   baseline among all equal-symbol d=5 pairs: {ctx2}/{totp}")
