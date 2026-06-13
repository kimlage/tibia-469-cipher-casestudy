#!/usr/bin/env python3
"""Independent reproduction, part 1: pipeline facts + observed statistics.
Fresh implementation, no code shared with the audited scripts.
"""
import json, math, sqlite3, random
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)

# --- books ---
books = dict(con.execute("SELECT bookid, digits FROM sheet__books GROUP BY bookid").fetchall())
print("books:", len(books), "| total digits:", sum(len(v) for v in books.values()))

# --- probe streams ---
probe = con.execute(
    "SELECT bookid, reconstructed_code_stream, decodedbase, omitted_positions_json, valid "
    "FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
print("probe rows:", len(probe), "| all valid:", all(r[4] == 1 for r in probe))

streams, bases, opos = {}, {}, {}
for bid, st, base, op, v in probe:
    streams[bid] = st.split()
    bases[bid] = base
    opos[bid] = set(json.loads(op))
print("total tokens:", sum(len(s) for s in streams.values()))
print("token==base length mismatches:", sum(1 for b in streams if len(streams[b]) != len(bases[b])))

# --- byte-exact render check + omission facts (independent: derive omissions from positions) ---
bad = 0
omit_by_code = Counter()
tot_omit = 0
for bid, s in streams.items():
    out = []
    for i, c in enumerate(s):
        if (i + 1) in opos[bid]:
            assert c[0] == '0', (bid, i, c)   # omission must be a leading-zero drop
            out.append(c[1])
            omit_by_code[c] += 1
            tot_omit += 1
        else:
            out.append(c)
    if "".join(out) != books[bid]:
        bad += 1
print("byte-exact failures:", bad)
print("total omissions:", tot_omit, "(11458-11263 =", 11458 - 11263, ")")
print("omitted codes:", dict(sorted(omit_by_code.items())))
occ_all = Counter()
for s in streams.values():
    occ_all.update(s)
print("code 07: occurrences", occ_all['07'], "omitted", omit_by_code['07'])
print("omissions on codes 10-99:", sum(v for c, v in omit_by_code.items() if c[0] != '0'))

# --- cross-check vs row0_code_symbol_counts table ---
tbl = con.execute("SELECT code, SUM(occurrence_count), SUM(omitted_count) "
                  "FROM row0_code_symbol_counts WHERE run_id=1 GROUP BY code").fetchall()
mism = [c for c, occ, om in tbl if occ_all.get(c, 0) != occ or omit_by_code.get(c, 0) != om]
print("counts-table rows:", len(tbl), "| mismatches vs stream-derived:", mism)

# --- code -> symbol determinism ---
code2sym = defaultdict(set)
for bid in streams:
    for c, s in zip(streams[bid], bases[bid]):
        code2sym[c].add(s)
nondet = {c: v for c, v in code2sym.items() if len(v) > 1}
print("codes mapping to >1 symbol:", nondet if nondet else "none (deterministic)")
sym2codes = defaultdict(set)
for c, v in code2sym.items():
    sym2codes[next(iter(v))].add(c)
print("homophone class sizes:", {s: len(v) for s, v in sorted(sym2codes.items())})

# --- observed digit stats ---
bl = [books[b] for b in sorted(books)]
dc = Counter()
for d in bl: dc.update(d)
N = sum(dc.values())
p2 = sum((v / N) ** 2 for v in dc.values())
print(f"\nsum p^2 = {p2:.4f}")
for k in range(1, 9):
    m = n = 0
    for d in bl:
        for i in range(len(d) - k):
            n += 1
            m += d[i] == d[i + k]
    z = (m - n * p2) / math.sqrt(n * p2 * (1 - p2))
    print(f"lag {k}: match={m/n:.4f} n={n} z_iid={z:+.2f}")

def runs(bs):
    t3 = t4 = 0
    for d in bs:
        i = 0
        while i < len(d):
            j = i
            while j < len(d) and d[j] == d[i]: j += 1
            if j - i == 3: t3 += 1
            elif j - i >= 4: t4 += 1
            i = j
    return t3, t4
print("runs len3, len>=4:", runs(bl))

sl = [streams[b] for b in sorted(streams)]
def chi2_mod10(ss, drop=0):
    pairs = [(a, b) for s in ss for a, b in zip(s, s[1:])]
    if drop:
        top = {x for x, _ in Counter(pairs).most_common(drop)}
        pairs = [p for p in pairs if p not in top]
    cnt = Counter((int(b) - int(a)) % 10 for a, b in pairs)
    e = len(pairs) / 10
    return sum((cnt.get(r, 0) - e) ** 2 / e for r in range(10)), len(pairs)
c0, n0 = chi2_mod10(sl)
c10, n10 = chi2_mod10(sl, 10)
print(f"diff-mod10 chi2: {c0:.1f} over {n0} pairs; after drop-top10: {c10:.1f} over {n10}")

# code-shuffle baseline for chi2 (my own seed)
rng = random.Random(20260610)
vals = []
for _ in range(200):
    ss = []
    for s in sl:
        t = list(s); rng.shuffle(t); ss.append(t)
    vals.append(chi2_mod10(ss)[0])
m = sum(vals) / len(vals)
sd = (sum((x - m) ** 2 for x in vals) / 199) ** 0.5
print(f"code-shuffle chi2 baseline: {m:.1f}+-{sd:.1f}; obs z={(c0-m)/sd:+.2f}")

# digit-shuffle baseline for runs
v3, v4 = [], []
for _ in range(200):
    bs = []
    for d in bl:
        t = list(d); rng.shuffle(t); bs.append("".join(t))
    a, b = runs(bs)
    v3.append(a); v4.append(b)
m3 = sum(v3)/200; s3 = (sum((x-m3)**2 for x in v3)/199)**0.5
m4 = sum(v4)/200; s4 = (sum((x-m4)**2 for x in v4)/199)**0.5
t3o, t4o = runs(bl)
print(f"digit-shuffle: triples {m3:.1f}+-{s3:.1f} (obs z={(t3o-m3)/s3:+.2f}), quads {m4:.1f}+-{s4:.1f} (obs z={(t4o-m4)/s4:+.2f})")

# observed code-level lag stats
for k in (1, 2, 3):
    rep = tens = units = n = 0
    for s in sl:
        for i in range(len(s) - k):
            n += 1
            rep += s[i] == s[i + k]
            tens += s[i][0] == s[i + k][0]
            units += s[i][1] == s[i + k][1]
    print(f"code lag {k}: same={rep/n:.4f} tens={tens/n:.4f} units={units/n:.4f} n={n}")
con.close()
