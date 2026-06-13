#!/usr/bin/env python3
"""Direct test of homophone rotation: when the same symbol recurs at base
distance d, is the same code reused less often than chance?
Control: permute codes within (book, symbol) groups - preserves per-book
per-symbol code usage counts, destroys sequential order. 1000 permutations.
"""
import random
import sqlite3
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
NPERM = 1000
SEED = 471

con = sqlite3.connect(DB, uri=True)
rows = con.execute(
    "SELECT bookid, reconstructed_code_stream, decodedbase "
    "FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
con.close()
print(f"rows: {len(rows)}"); assert len(rows) == 70

books = []
for bid, stream, base in sorted(rows):
    codes = stream.split()
    assert len(codes) == len(base), (bid, len(codes), len(base))
    books.append((bid, codes, base))

# how many codes per symbol (homophone classes)
sym_codes = defaultdict(set)
for _, codes, base in books:
    for c, s in zip(codes, base):
        sym_codes[s].add(c)
print("homophone class sizes:", {s: len(v) for s, v in sorted(sym_codes.items())})

MAXD = 6
def reuse_counts(books_codes):
    """books_codes: list of (codes, base). Return per-d (same_code, n_pairs)
    over pairs of equal-symbol positions at base distance d."""
    same = Counter(); n = Counter()
    for codes, base in books_codes:
        L = len(base)
        for d in range(1, MAXD + 1):
            for i in range(L - d):
                if base[i] == base[i + d]:
                    n[d] += 1
                    if codes[i] == codes[i + d]:
                        same[d] += 1
    return same, n

obs_books = [(codes, base) for _, codes, base in books]
obs_same, obs_n = reuse_counts(obs_books)
print("\nobserved same-code reuse at equal-symbol pairs:")
for d in range(1, MAXD + 1):
    print(f"  d={d}: same={obs_same[d]}/{obs_n[d]} = {obs_same[d]/obs_n[d]:.4f}")

# permutation control
rng = random.Random(SEED)
perm_same = defaultdict(list)
# pre-index positions per (book, symbol)
groups = []
for _, codes, base in books:
    g = defaultdict(list)
    for i, s in enumerate(base):
        g[s].append(i)
    groups.append((codes, base, g))

for it in range(NPERM):
    pb = []
    for codes, base, g in groups:
        new = list(codes)
        for s, idxs in g.items():
            vals = [codes[i] for i in idxs]
            rng.shuffle(vals)
            for i, v in zip(idxs, vals):
                new[i] = v
        pb.append((new, base))
    s, _ = reuse_counts(pb)
    for d in range(1, MAXD + 1):
        perm_same[d].append(s[d])

print(f"\npermutation control ({NPERM} within-book within-symbol shuffles):")
for d in range(1, MAXD + 1):
    vals = perm_same[d]
    m = sum(vals) / len(vals)
    sd = (sum((x - m) ** 2 for x in vals) / (len(vals) - 1)) ** 0.5
    o = obs_same[d]
    z = (o - m) / sd if sd > 0 else float("nan")
    p_lo = sum(1 for v in vals if v <= o) / len(vals)
    print(f"  d={d}: obs={o} perm={m:.1f}+-{sd:.1f} z={z:+.2f} p(<=obs)={p_lo:.4f}")

# which symbols drive the d=1..3 suppression
print("\nper-symbol same-code reuse at d<=3 (obs vs single perm-mean):")
sym_obs = Counter(); sym_n = Counter()
for codes, base in obs_books:
    for d in (1, 2, 3):
        for i in range(len(base) - d):
            if base[i] == base[i + d]:
                sym_n[base[i]] += 1
                if codes[i] == codes[i + d]:
                    sym_obs[base[i]] += 1
# permutation mean per symbol (200 perms enough)
sym_perm = defaultdict(list)
for it in range(200):
    pb = []
    for codes, base, g in groups:
        new = list(codes)
        for s, idxs in g.items():
            vals = [codes[i] for i in idxs]
            rng.shuffle(vals)
            for i, v in zip(idxs, vals):
                new[i] = v
        cnt = Counter()
        for d in (1, 2, 3):
            for i in range(len(base) - d):
                if base[i] == base[i + d] and new[i] == new[i + d]:
                    cnt[base[i]] += 1
        pb.append(cnt)
    tot = Counter()
    for c in pb:
        tot.update(c)
    for s in sym_n:
        sym_perm[s].append(tot.get(s, 0))
for s in sorted(sym_n):
    vals = sym_perm[s]
    m = sum(vals) / len(vals)
    sd = (sum((x - m) ** 2 for x in vals) / (len(vals) - 1)) ** 0.5
    z = (sym_obs[s] - m) / sd if sd > 0 else float("nan")
    print(f"  {s}: pairs={sym_n[s]} obs_same={sym_obs[s]} perm={m:.1f}+-{sd:.1f} z={z:+.2f} (homophones={len(sym_codes[s])})")
