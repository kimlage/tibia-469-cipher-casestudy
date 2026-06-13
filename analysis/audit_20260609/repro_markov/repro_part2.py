#!/usr/bin/env python3
"""Independent reproduction, part 2: order-1 Markov envelope (own seed/impl).
Checks the claim's 'close' verdicts (triples, quads, chi2 inside) and the
residual (lag3 enriched, lag4/6 suppressed, code-lag2/3 same-code deficit,
units-lag2 / tens-lag3 deficits) against 200 synthetic corpora.
"""
import math, random, sqlite3
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
N = 200
rng = random.Random(987654321)

con = sqlite3.connect(DB, uri=True)
sl = [r[1].split() for r in sorted(con.execute(
    "SELECT bookid, reconstructed_code_stream FROM row0_code_symbol_probe_books WHERE run_id=1"))]
tbl = con.execute("SELECT code, SUM(occurrence_count), SUM(omitted_count) "
                  "FROM row0_code_symbol_counts WHERE run_id=1 GROUP BY code").fetchall()
bl_obs = [r[1] for r in sorted(con.execute(
    "SELECT bookid, digits FROM sheet__books GROUP BY bookid"))]
con.close()
orate = {c: om / occ for c, occ, om in tbl}
assert len(sl) == 70

# fit order-1
big = defaultdict(Counter); ini = Counter(); uni = Counter()
for s in sl:
    ini[s[0]] += 1
    uni.update(s)
    for a, b in zip(s, s[1:]):
        big[a][b] += 1
trans = {a: (list(c), list(c.values())) for a, c in big.items()}
ik, iw = list(ini), list(ini.values())
uk, uw = list(uni), list(uni.values())
lens = [len(s) for s in sl]
print("codes:", len(uni), "bigram types:", sum(len(c) for c in big.values()),
      "bigram tokens:", sum(sum(c.values()) for c in big.values()))

def gen():
    out = []
    for L in lens:
        t = rng.choices(ik, iw)[0]; s = [t]
        while len(s) < L:
            t = rng.choices(*trans[t])[0] if t in trans else rng.choices(uk, uw)[0]
            s.append(t)
        out.append(s)
    return out

def render(s):
    return "".join(c[1] if (orate.get(c, 0) > 0 and rng.random() < orate[c]) else c for c in s)

def stats(bs, ss):
    r = {}
    dc = Counter()
    for d in bs: dc.update(d)
    n_ = sum(dc.values()); p2 = sum((v / n_) ** 2 for v in dc.values())
    for k in range(1, 9):
        m = n = 0
        for d in bs:
            for i in range(len(d) - k):
                n += 1; m += d[i] == d[i + k]
        r[f"mp{k}"] = m / n
        r[f"z{k}"] = (m - n * p2) / math.sqrt(n * p2 * (1 - p2))
    t3 = t4 = 0
    for d in bs:
        i = 0
        while i < len(d):
            j = i
            while j < len(d) and d[j] == d[i]: j += 1
            if j - i == 3: t3 += 1
            elif j - i >= 4: t4 += 1
            i = j
    r["t3"], r["t4"] = t3, t4
    pairs = [(a, b) for s in ss for a, b in zip(s, s[1:])]
    cnt = Counter((int(b) - int(a)) % 10 for a, b in pairs)
    e = len(pairs) / 10
    r["chi"] = sum((cnt.get(x, 0) - e) ** 2 / e for x in range(10))
    top = {x for x, _ in Counter(pairs).most_common(10)}
    p2_ = [p for p in pairs if p not in top]
    cnt = Counter((int(b) - int(a)) % 10 for a, b in p2_)
    e = len(p2_) / 10
    r["chi10"] = sum((cnt.get(x, 0) - e) ** 2 / e for x in range(10))
    for k in (1, 2, 3):
        rep = te = un = n = 0
        for s in ss:
            for i in range(len(s) - k):
                n += 1
                rep += s[i] == s[i + k]
                te += s[i][0] == s[i + k][0]
                un += s[i][1] == s[i + k][1]
        r[f"rep{k}"] = rep / n; r[f"tens{k}"] = te / n; r[f"units{k}"] = un / n
    return r

obs = stats(bl_obs, sl)
acc = defaultdict(list)
for it in range(N):
    ss = gen()
    bs = [render(s) for s in ss]
    for k, v in stats(bs, ss).items():
        acc[k].append(v)

print(f"\nkey: obs vs order-1 envelope ({N} corpora, seed 987654321)")
for k in (["t3", "t4", "chi", "chi10"] + [f"mp{i}" for i in range(1, 9)]
          + [f"z{i}" for i in (1, 3, 4, 6)]
          + ["rep1", "rep2", "rep3", "tens1", "tens2", "tens3", "units1", "units2", "units3"]):
    v = acc[k]
    m = sum(v) / N
    sd = (sum((x - m) ** 2 for x in v) / (N - 1)) ** 0.5
    lo, hi = min(v), max(v)
    o = obs[k]
    z = (o - m) / sd if sd else float("nan")
    p = min(sum(1 for x in v if x <= o), sum(1 for x in v if x >= o)) / N
    print(f"{k:8s} obs={o:>9.4f} synth={m:.4f}+-{sd:.4f} range[{lo:.4f},{hi:.4f}] "
          f"z={z:+.2f} tail_p={p:.3f} inside={lo <= o <= hi}")
