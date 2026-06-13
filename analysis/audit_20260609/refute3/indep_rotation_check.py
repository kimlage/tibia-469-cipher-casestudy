#!/usr/bin/env python3
"""Independent adversarial re-check of the homophone-rotation claim.
Different seed, independent implementation. Robustness slices:
  A. full data (replication)
  B. exclude '*' positions entirely
  C. exclude any pair where either code is in 00-09 (omission-affected)
  D. per-book contribution at d=2,3 (is signal concentrated in few books?)
  E. byte-exact pipeline re-verification (render stream + omissions -> digits)
"""
import json, random, sqlite3
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
rng = random.Random(98765)
NPERM = 2000

con = sqlite3.connect(DB, uri=True)
rows = con.execute(
    "SELECT bookid, reconstructed_code_stream, decodedbase, omitted_positions_json "
    "FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
print("probe rows:", len(rows))
assert len(rows) == 70

sheet = con.execute(
    "SELECT bookid, MIN(digits) FROM sheet__books GROUP BY bookid").fetchall()
digits_by_book = dict(sheet)
print("sheet books:", len(sheet))
con.close()

# E: pipeline re-verification (independent implementation)
bad = 0
total_omit = 0
omit_codes = Counter()
for bid, stream, base, omitpos in rows:
    codes = stream.split()
    assert len(codes) == len(base), bid
    omits = set(json.loads(omitpos) if omitpos else [])
    total_omit += len(omits)
    # omitted positions are TOKEN indices where the leading zero was dropped
    parts = []
    for i, c in enumerate(codes):
        if i in omits:
            omit_codes[c] += 1
            parts.append(c[1])  # leading zero dropped
        else:
            parts.append(c)
    rendered = "".join(parts)
    if rendered != digits_by_book[bid]:
        bad += 1
print("total omitted digits:", total_omit, "(claim: 195)")
print("books failing byte-exact render:", bad)
print("omitted-digit codes:", dict(sorted(omit_codes.items())))

books = []
for bid, stream, base, _ in sorted(rows):
    books.append((bid, stream.split(), base))

MAXD = 6

def reuse(books_codes, pair_filter):
    same = Counter(); n = Counter()
    for bid, codes, base in books_codes:
        L = len(base)
        for d in range(1, MAXD + 1):
            for i in range(L - d):
                if base[i] == base[i + d] and pair_filter(base[i], codes[i], codes[i + d]):
                    n[d] += 1
                    if codes[i] == codes[i + d]:
                        same[d] += 1
    return same, n

def perm_books(books_):
    out = []
    for bid, codes, base in books_:
        g = defaultdict(list)
        for i, s in enumerate(base):
            g[s].append(i)
        new = list(codes)
        for s, idxs in g.items():
            vals = [codes[i] for i in idxs]
            rng.shuffle(vals)
            for i, v in zip(idxs, vals):
                new[i] = v
        out.append((bid, new, base))
    return out

FILTERS = {
    "A_full": lambda s, c1, c2: True,
    "B_no_star": lambda s, c1, c2: s != "*",
    "C_no_star_no_0x": lambda s, c1, c2: s != "*" and c1[0] != "0" and c2[0] != "0",
}

for name, f in FILTERS.items():
    obs_same, obs_n = reuse(books, f)
    perm = defaultdict(list)
    rng.seed(13579)  # fresh deterministic seed per slice
    for _ in range(NPERM):
        pb = perm_books(books)
        s, _ = reuse(pb, f)
        for d in range(1, MAXD + 1):
            perm[d].append(s[d])
    print(f"\n=== slice {name} ({NPERM} perms) ===")
    for d in range(1, MAXD + 1):
        vals = perm[d]
        m = sum(vals) / len(vals)
        sd = (sum((x - m) ** 2 for x in vals) / (len(vals) - 1)) ** 0.5
        o = obs_same[d]
        z = (o - m) / sd if sd else float("nan")
        plo = sum(1 for v in vals if v <= o) / len(vals)
        phi = sum(1 for v in vals if v >= o) / len(vals)
        print(f"  d={d}: obs={o}/{obs_n[d]} perm={m:.1f}+-{sd:.1f} z={z:+.2f} p_lo={plo:.4f} p_hi={phi:.4f}")

# D: per-book contribution at d=2,3 (obs - perm_mean), 300 perms
print("\n=== per-book deficit at d in {2,3} (no star) ===")
obs_by_book = Counter(); n_by_book = Counter()
for bid, codes, base in books:
    for d in (2, 3):
        for i in range(len(base) - d):
            if base[i] == base[i + d] and base[i] != "*":
                n_by_book[bid] += 1
                if codes[i] == codes[i + d]:
                    obs_by_book[bid] += 1
rng.seed(2468)
pm = defaultdict(list)
for _ in range(300):
    pb = perm_books(books)
    for bid, codes, base in pb:
        c = 0
        for d in (2, 3):
            for i in range(len(base) - d):
                if base[i] == base[i + d] and base[i] != "*" and codes[i] == codes[i + d]:
                    c += 1
        pm[bid].append(c)
neg = pos = zero = 0
contribs = []
for bid in sorted(n_by_book):
    m = sum(pm[bid]) / len(pm[bid])
    diff = obs_by_book[bid] - m
    contribs.append((diff, bid, obs_by_book[bid], m, n_by_book[bid]))
    if diff < -0.5: neg += 1
    elif diff > 0.5: pos += 1
    else: zero += 1
contribs.sort()
print(f"books with deficit: {neg}, surplus: {pos}, ~zero: {zero} (of {len(n_by_book)})")
print("5 strongest deficits (diff, book, obs, perm_mean, npairs):")
for c in contribs[:5]:
    print("   %+.1f %s obs=%d perm=%.1f n=%d" % c)
total_diff = sum(c[0] for c in contribs)
top5 = sum(c[0] for c in contribs[:5])
print(f"total deficit={total_diff:.1f}; top-5 books share={top5/total_diff:.2%}")
# sign test
import math
nb = neg + pos
if nb:
    from math import comb
    p_sign = sum(comb(nb, k) for k in range(neg, nb + 1)) / 2 ** nb
    print(f"sign test (deficit books {neg}/{nb}): p={p_sign:.4g}")
