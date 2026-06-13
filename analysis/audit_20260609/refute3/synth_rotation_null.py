#!/usr/bin/env python3
"""Does an order-1 code Markov generator (no rotation rule) already produce
large |z| on the equal-symbol-pair rotation permutation test?
Generate 40 synthetic corpora (order-1 fit on pooled codes, matching book
lengths), decode codes->symbols, run the within-(book,symbol) permutation
test (200 perms each), collect z at d=1..6.
"""
import random, sqlite3
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
rows = con.execute(
    "SELECT bookid, reconstructed_code_stream, decodedbase "
    "FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
sym_rows = con.execute(
    "SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1 GROUP BY code, symbol").fetchall()
con.close()
print("probe rows:", len(rows), "| code->symbol rows:", len(sym_rows))
code2sym = {}
for c, s in sym_rows:
    assert code2sym.setdefault(c, s) == s, ("ambiguous", c)

books = [(bid, stream.split(), base) for bid, stream, base in sorted(rows)]
# cross-check decode map against decodedbase
mism = sum(1 for _, codes, base in books for c, s in zip(codes, base) if code2sym[c] != s)
print("decode map mismatches vs decodedbase:", mism)

# order-1 fit, pooled
start = Counter(); trans = defaultdict(Counter)
for _, codes, _ in books:
    start[codes[0]] += 1
    for a, b in zip(codes, codes[1:]):
        trans[a][b] += 1
lengths = [len(codes) for _, codes, _ in books]

def gen_book(L, rng):
    keys = list(start); wts = [start[k] for k in keys]
    cur = rng.choices(keys, wts)[0]
    out = [cur]
    for _ in range(L - 1):
        t = trans[cur]
        if not t:
            cur = rng.choices(keys, wts)[0]
        else:
            ks = list(t); cur = rng.choices(ks, [t[k] for k in ks])[0]
        out.append(cur)
    return out

MAXD = 6
def rotation_z(corpus, rng, nperm=200):
    """corpus: list of (codes, base). Return dict d-> (z, obs)."""
    def reuse(cs):
        same = Counter()
        for codes, base in cs:
            for d in range(1, MAXD + 1):
                for i in range(len(base) - d):
                    if base[i] == base[i + d] and codes[i] == codes[i + d]:
                        same[d] += 1
        return same
    obs = reuse(corpus)
    groups = []
    for codes, base in corpus:
        g = defaultdict(list)
        for i, s in enumerate(base):
            g[s].append(i)
        groups.append((codes, base, g))
    perm = defaultdict(list)
    for _ in range(nperm):
        pb = []
        for codes, base, g in groups:
            new = list(codes)
            for s, idxs in g.items():
                vals = [codes[i] for i in idxs]
                rng.shuffle(vals)
                for i, v in zip(idxs, vals):
                    new[i] = v
            pb.append((new, base))
        s = reuse(pb)
        for d in range(1, MAXD + 1):
            perm[d].append(s[d])
    out = {}
    for d in range(1, MAXD + 1):
        vals = perm[d]; m = sum(vals) / len(vals)
        sd = (sum((x - m) ** 2 for x in vals) / (len(vals) - 1)) ** 0.5
        out[d] = ((obs[d] - m) / sd if sd else float("nan"), obs[d])
    return out

rng = random.Random(31337)
NS = 40
zs = defaultdict(list)
for it in range(NS):
    corpus = []
    for L in lengths:
        codes = gen_book(L, rng)
        corpus.append((codes, [code2sym[c] for c in codes]))
    res = rotation_z(corpus, rng)
    for d, (z, _) in res.items():
        zs[d].append(z)

print(f"\nrotation-test z on {NS} order-1 synthetic corpora (200 perms each):")
for d in range(1, MAXD + 1):
    v = zs[d]; m = sum(v) / len(v)
    sd = (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5
    print(f"  d={d}: synth z mean={m:+.2f} sd={sd:.2f} min={min(v):+.2f} max={max(v):+.2f}")
print("\nobserved (real corpus) z for reference: d2=-6.2 d3=-6.6 d5=+6.0")
