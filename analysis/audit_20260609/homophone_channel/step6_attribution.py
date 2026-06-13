#!/usr/bin/env python3
"""STEP 6: attribute surviving NOVEL residual structure (miss ac1, bookG).

H_mech: misses cluster only at SEGMENT granularity (some novel segments are
bigram-conventional, others fresh) -> no token-level ordering info.
Test: compare observed ac1/bookG against controls that PERMUTE misses within
each segment (preserves per-segment miss rates, destroys within-segment order)
and against controls permuting across segments within book.
If within-segment permutation reproduces observed ac1/bookG (|z|<3), the
structure is segment-level, i.e., lexicon composition - mechanical.
Also: sub-chunk reuse check - novel-token miss rate vs whether its digit
8-gram context appeared earlier in the corpus.
"""
import json
import math
import sqlite3
import numpy as np
from collections import defaultdict

HC = "./tmp/audit_20260609/homophone_channel"
data = json.load(open(f"{HC}/occ_streams.json"))
class_codes = {s: v for s, v in data["class_sizes"].items() if len(v) >= 2}

# tokens aligned with preds (book sorted, pos sorted, multi-class only)
tmp = defaultdict(list)
for s, lst in data["occ"].items():
    if s not in class_codes:
        continue
    for r in lst:
        tmp[r["book"]].append((r["pos"], s, class_codes[s].index(r["code"]),
                               r["novel"], r["xuniq"]))
tokens = []
for b in sorted(tmp):
    for rec in sorted(tmp[b]):
        tokens.append((b,) + rec)
N = len(tokens)

# segment id per (book,pos)
con = sqlite3.connect("file:./data/bonelord_operational.sqlite?mode=ro", uri=True)
rows = con.execute("SELECT bookid, decodedbase FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
con.close()
print(f"rows: {len(rows)}")
segid = {}
sid = 0
for bid, base in sorted(rows):
    L = len(base); i = 0
    while i < L:
        if base[i] == "*": i += 1; continue
        j = i
        while j < L and base[j] != "*": j += 1
        for k in range(i, j):
            segid[(bid, k)] = sid
        sid += 1
        i = j

p2 = np.load(f"{HC}/preds2.npz", allow_pickle=True)
P = p2["M2R"]
miss = np.array([int(np.argmax(P[i]) != tokens[i][3]) for i in range(N)], float)
nov_idx = [i for i in range(N) if tokens[i][4]]
print(f"novel tokens: {len(nov_idx)}, miss rate: {miss[nov_idx].mean():.3f}")

def ac1(v):
    m = v - v.mean()
    den = (m * m).sum()
    return (m[:-1] * m[1:]).sum() / den if den > 0 else 0.0

def bookG(idx, mv):
    bb = defaultdict(list)
    for j, i in enumerate(idx):
        bb[tokens[i][0]].append(mv[j])
    G = 0.0; pbar = mv.mean()
    for b, v in bb.items():
        n = len(v); k = sum(v)
        if n < 5: continue
        for kk, pp in ((k, pbar), (n - k, 1 - pbar)):
            if kk > 0 and pp > 0:
                G += 2 * kk * math.log(kk / (n * pp))
    return G

mv_obs = miss[nov_idx]
obs_ac, obs_G = ac1(mv_obs), bookG(nov_idx, mv_obs)
print(f"observed NOVEL: ac1={obs_ac:.4f} bookG={obs_G:.1f}")

rng = np.random.default_rng(606)
seg_groups = defaultdict(list)   # segid -> positions in nov_idx vector
book_groups = defaultdict(list)
for j, i in enumerate(nov_idx):
    seg_groups[segid[(tokens[i][0], tokens[i][1])]].append(j)
    book_groups[tokens[i][0]].append(j)
print(f"novel segments touched: {len(seg_groups)}")

def perm_test(groups, label):
    acs, Gs = [], []
    for _ in range(500):
        mv = mv_obs.copy()
        for g in groups.values():
            vals = mv[g].copy()
            rng.shuffle(vals)
            mv[g] = vals
        acs.append(ac1(mv)); Gs.append(bookG(nov_idx, mv))
    acs = np.array(acs); Gs = np.array(Gs)
    za = (obs_ac - acs.mean()) / acs.std(ddof=1)
    zg = (obs_G - Gs.mean()) / Gs.std(ddof=1)
    print(f"{label}: ac1 ctl={acs.mean():.4f}+-{acs.std(ddof=1):.4f} z={za:+.2f} | "
          f"bookG ctl={Gs.mean():.1f}+-{Gs.std(ddof=1):.1f} z={zg:+.2f}")
    return za, zg

za_seg, zg_seg = perm_test(seg_groups, "within-SEGMENT permute")
za_book, zg_book = perm_test(book_groups, "within-BOOK permute  ")

# sub-chunk reuse: digit 8-gram context seen earlier?
con = sqlite3.connect("file:./data/bonelord_operational.sqlite?mode=ro", uri=True)
drows = con.execute("SELECT bookid, digits FROM sheet__books GROUP BY bookid").fetchall()
brows = con.execute("SELECT bookid, reconstructed_code_stream, omitted_positions_json FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
con.close()
digits = {b: d for b, d in drows}
SUBL = 8
seen = set()
sub_seen = {}  # (book,pos) -> bool seen-before
for bid, stream, opos in sorted(brows):
    codes = stream.split()
    omit = set(json.loads(opos))
    d = digits[bid]
    dp = 0
    spans = []
    for i, c in enumerate(codes):
        w = 1 if (i + 1) in omit else len(c)
        spans.append((dp, dp + w))
        dp += w
    local = set()
    for i, c in enumerate(codes):
        a, b_ = spans[i]
        ctx = d[max(0, a - 4):min(len(d), b_ + 4)]
        key = ctx
        sub_seen[(bid, i)] = key in seen or key in local
        local.add(key)
    seen |= local

hit_seen = [1 - miss[j] for j in range(N) if tokens[j][4] and sub_seen.get((tokens[j][0], tokens[j][1]))]
hit_fresh = [1 - miss[j] for j in range(N) if tokens[j][4] and not sub_seen.get((tokens[j][0], tokens[j][1]))]
print(f"\nsub-chunk reuse attribution (novel tokens, +-4-digit context seen before):")
print(f"  reused-context: hit={np.mean(hit_seen):.3f} (n={len(hit_seen)})")
print(f"  fresh-context:  hit={np.mean(hit_fresh):.3f} (n={len(hit_fresh)})")
