#!/usr/bin/env python3
"""Occurrence-index view: for the k-th and (k+g)-th occurrence of a symbol
within a book, P(same code) vs within-(book,symbol) permutation, by gap g.
Also: immediate-repeat rate on consecutive occurrences per symbol.
"""
import random
import sqlite3
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
NPERM = 1000
SEED = 472
MAXG = 5

con = sqlite3.connect(DB, uri=True)
rows = con.execute(
    "SELECT bookid, reconstructed_code_stream, decodedbase "
    "FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
con.close()
assert len(rows) == 70

# per (book,symbol): ordered list of codes used
seqs = []
for bid, stream, base in sorted(rows):
    codes = stream.split()
    g = defaultdict(list)
    for c, s in zip(codes, base):
        g[s].append(c)
    for s, lst in g.items():
        if len(lst) >= 2 and s != '*':
            seqs.append((s, lst))
print(f"(book,symbol) sequences with >=2 occurrences: {len(seqs)}")

def gap_same(seq_list):
    same = Counter(); n = Counter()
    for s, lst in seq_list:
        for g in range(1, MAXG + 1):
            for i in range(len(lst) - g):
                n[(s, g)] += 1
                if lst[i] == lst[i + g]:
                    same[(s, g)] += 1
    return same, n

obs_same, obs_n = gap_same(seqs)

rng = random.Random(SEED)
perm = defaultdict(list)
for it in range(NPERM):
    pl = []
    for s, lst in seqs:
        l2 = list(lst)
        rng.shuffle(l2)
        pl.append((s, l2))
    ps, _ = gap_same(pl)
    for key in obs_n:
        perm[key].append(ps.get(key, 0))

# pooled by gap
print("\npooled same-code rate by occurrence gap g (within book,symbol):")
for g in range(1, MAXG + 1):
    o = sum(obs_same.get((s, gg), 0) for (s, gg) in obs_n if gg == g)
    n = sum(v for (s, gg), v in obs_n.items() if gg == g)
    pv = [sum(perm[(s, gg)][it] for (s, gg) in obs_n if gg == g) for it in range(NPERM)]
    m = sum(pv) / len(pv)
    sd = (sum((x - m) ** 2 for x in pv) / (len(pv) - 1)) ** 0.5
    z = (o - m) / sd if sd > 0 else float("nan")
    print(f"  g={g}: obs={o}/{n}={o/n:.4f} perm={m:.1f}+-{sd:.1f} z={z:+.2f}")

# per-symbol consecutive-occurrence (g=1) repeat
print("\nper-symbol g=1 same-code repeat:")
for s in sorted(set(s for s, _ in obs_n)):
    if (s, 1) not in obs_n:
        continue
    o = obs_same.get((s, 1), 0); n = obs_n[(s, 1)]
    pv = perm[(s, 1)]
    m = sum(pv) / len(pv)
    sd = (sum((x - m) ** 2 for x in pv) / (len(pv) - 1)) ** 0.5
    z = (o - m) / sd if sd > 0 else float("nan")
    print(f"  {s}: obs={o}/{n}={o/n:.3f} perm_rate={m/n:.3f} z={z:+.2f}")
