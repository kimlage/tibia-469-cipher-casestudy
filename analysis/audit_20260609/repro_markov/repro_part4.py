#!/usr/bin/env python3
"""Robustness: rotation test restricted to pairs where NEITHER position is an
omitted (single-digit-rendered) token — removes any parse-ambiguity channel."""
import json, random, sqlite3
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
rng = random.Random(24680)
NPERM = 1000
MAXD = 6

con = sqlite3.connect(DB, uri=True)
rows = sorted(con.execute(
    "SELECT bookid, reconstructed_code_stream, decodedbase, omitted_positions_json "
    "FROM row0_code_symbol_probe_books WHERE run_id=1"))
con.close()
books = []
for bid, st, base, op in rows:
    codes = st.split()
    om = set(json.loads(op))          # 1-based token positions
    keep = [i + 1 not in om for i in range(len(codes))]
    books.append((codes, base, keep))
print("books:", len(books), "| excluded tokens:", sum(k.count(False) for _, _, k in books))

def profile(bks):
    same = Counter(); n = Counter()
    for codes, base, keep in bks:
        L = len(base)
        for d in range(1, MAXD + 1):
            for i in range(L - d):
                if base[i] == base[i + d] and keep[i] and keep[i + d]:
                    n[d] += 1
                    same[d] += codes[i] == codes[i + d]
    return same, n

obs_s, obs_n = profile(books)
pacc = defaultdict(list)
for _ in range(NPERM):
    pb = []
    for codes, base, keep in books:
        idx = defaultdict(list)
        for i, s in enumerate(base):
            idx[s].append(i)
        new = list(codes)
        for s, ii in idx.items():
            vv = [codes[i] for i in ii]
            rng.shuffle(vv)
            for i, v in zip(ii, vv):
                new[i] = v
        pb.append((new, base, keep))
    ps, _ = profile(pb)
    for d in range(1, MAXD + 1):
        pacc[d].append(ps[d])

print(f"rotation test, omitted-token pairs excluded (NPERM={NPERM}):")
for d in range(1, MAXD + 1):
    v = pacc[d]
    m = sum(v) / NPERM
    sd = (sum((x - m) ** 2 for x in v) / (NPERM - 1)) ** 0.5
    o = obs_s[d]
    z = (o - m) / sd if sd else float("nan")
    print(f"d={d}: obs={o}/{obs_n[d]} perm={m:.1f}+-{sd:.1f} z={z:+.2f}")
