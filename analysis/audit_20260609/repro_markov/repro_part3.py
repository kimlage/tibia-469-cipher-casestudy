#!/usr/bin/env python3
"""Independent reproduction, part 3: homophone-rotation permutation test
(own implementation, seed 13579), per-symbol breakdown, robustness variant
excluding '*'/N/B, and occurrence-gap control.
"""
import random, sqlite3
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
NPERM = 1000
rng = random.Random(13579)
MAXD = 6

con = sqlite3.connect(DB, uri=True)
rows = sorted(con.execute(
    "SELECT bookid, reconstructed_code_stream, decodedbase "
    "FROM row0_code_symbol_probe_books WHERE run_id=1"))
con.close()
assert len(rows) == 70

books = [(r[1].split(), r[2]) for r in rows]

def profile(bks, exclude=frozenset()):
    same = Counter(); n = Counter()
    for codes, base in bks:
        L = len(base)
        for d in range(1, MAXD + 1):
            for i in range(L - d):
                s = base[i]
                if s == base[i + d] and s not in exclude:
                    n[d] += 1
                    same[d] += codes[i] == codes[i + d]
    return same, n

def permute(bks):
    out = []
    for codes, base in bks:
        idx = defaultdict(list)
        for i, s in enumerate(base):
            idx[s].append(i)
        new = list(codes)
        for s, ii in idx.items():
            vv = [codes[i] for i in ii]
            rng.shuffle(vv)
            for i, v in zip(ii, vv):
                new[i] = v
        out.append((new, base))
    return out

for label, excl in (("ALL SYMBOLS", frozenset()), ("EXCL *,N,B", frozenset("*NB"))):
    obs_s, obs_n = profile(books, excl)
    perm_acc = defaultdict(list)
    for _ in range(NPERM):
        ps, _ = profile(permute(books), excl)
        for d in range(1, MAXD + 1):
            perm_acc[d].append(ps[d])
    print(f"\n=== rotation test [{label}] (NPERM={NPERM}, seed 13579) ===")
    for d in range(1, MAXD + 1):
        v = perm_acc[d]
        m = sum(v) / NPERM
        sd = (sum((x - m) ** 2 for x in v) / (NPERM - 1)) ** 0.5
        o = obs_s[d]
        z = (o - m) / sd if sd else float("nan")
        plo = sum(1 for x in v if x <= o) / NPERM
        phi = sum(1 for x in v if x >= o) / NPERM
        print(f"d={d}: obs={o}/{obs_n[d]} perm={m:.1f}+-{sd:.1f} z={z:+.2f} "
              f"p(<=)={plo:.4f} p(>=)={phi:.4f}")

# per-symbol d<=3 (500 perms)
obs_sym = Counter(); n_sym = Counter()
for codes, base in books:
    for d in (1, 2, 3):
        for i in range(len(base) - d):
            if base[i] == base[i + d]:
                n_sym[base[i]] += 1
                obs_sym[base[i]] += codes[i] == codes[i + d]
perm_sym = defaultdict(list)
for _ in range(500):
    pb = permute(books)
    c = Counter()
    for codes, base in pb:
        for d in (1, 2, 3):
            for i in range(len(base) - d):
                if base[i] == base[i + d] and codes[i] == codes[i + d]:
                    c[base[i]] += 1
    for s in n_sym:
        perm_sym[s].append(c.get(s, 0))
print("\n=== per-symbol d<=3 (500 perms) ===")
for s in sorted(n_sym):
    v = perm_sym[s]
    m = sum(v) / len(v)
    sd = (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5
    z = (obs_sym[s] - m) / sd if sd else float("nan")
    print(f"{s}: pairs={n_sym[s]} obs={obs_sym[s]} perm={m:.1f}+-{sd:.1f} z={z:+.2f}")

# occurrence-gap control
seqs = []
for codes, base in books:
    g = defaultdict(list)
    for c, s in zip(codes, base):
        g[s].append(c)
    for s, lst in g.items():
        if len(lst) >= 2 and s != '*':
            seqs.append(lst)
def gapstat(sq):
    same = Counter(); n = Counter()
    for lst in sq:
        for g in range(1, 6):
            for i in range(len(lst) - g):
                n[g] += 1
                same[g] += lst[i] == lst[i + g]
    return same, n
o_s, o_n = gapstat(seqs)
pacc = defaultdict(list)
for _ in range(NPERM):
    sq = []
    for lst in seqs:
        t = list(lst); rng.shuffle(t); sq.append(t)
    ps, _ = gapstat(sq)
    for g in range(1, 6):
        pacc[g].append(ps[g])
print("\n=== occurrence-gap control (NPERM=1000) ===")
for g in range(1, 6):
    v = pacc[g]
    m = sum(v) / NPERM
    sd = (sum((x - m) ** 2 for x in v) / (NPERM - 1)) ** 0.5
    z = (o_s[g] - m) / sd if sd else float("nan")
    print(f"g={g}: obs={o_s[g]}/{o_n[g]}={o_s[g]/o_n[g]:.4f} perm={m:.1f}+-{sd:.1f} z={z:+.2f}")
