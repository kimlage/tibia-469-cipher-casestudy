#!/usr/bin/env python3
"""Part 2c:
1) Permutation control: is 99.47% (x,prev,nxt)-functionality on 50 books
   explainable by per-code marginal rates alone? 1000 within-code label shuffles.
2) List contradictory signatures.
3) True held-out test: apply 50-book (x,prev,nxt) table to the 20 multipath
   books, per constrained parse; does the rule select a unique parse?
"""
import sqlite3, json, random
from collections import Counter, defaultdict

random.seed(469)
TMP = './tmp/audit_20260609'
occ = json.load(open(f'{TMP}/occurrences.json'))
data = [o for o in occ if o['pc'] == 1]
n = len(data)
print("n(50 books) =", n)

def maxacc(labels):
    labs = defaultdict(Counter)
    for o, y in zip(data, labels):
        labs[(o['x'], o['prev'], o['nxt'])][y] += 1
    return sum(max(c.values()) for c in labs.values()) / n

obs = maxacc([o['omitted'] for o in data])
print(f"observed (x,prev,nxt) max in-sample accuracy: {obs:.4f}")

# permutation: shuffle labels within each code class (preserves per-code rates exactly)
bycode = defaultdict(list)
for idx, o in enumerate(data):
    bycode[o['x']].append(idx)
null = []
for _ in range(1000):
    lab = [None]*n
    for c, idxs in bycode.items():
        ys = [data[i]['omitted'] for i in idxs]
        random.shuffle(ys)
        for i, y in zip(idxs, ys):
            lab[i] = y
    null.append(maxacc(lab))
import statistics
mu, sd = statistics.mean(null), statistics.pstdev(null)
ge = sum(1 for v in null if v >= obs)
print(f"null (within-code shuffle, 1000x): mean {mu:.4f} sd {sd:.4f} max {max(null):.4f}")
print(f"empirical p(null >= obs) = {ge}/1000; z = {(obs-mu)/sd:.2f}")

# permutation 2: shuffle within (code, prev) classes — tests whether nxt adds determinism
byc2 = defaultdict(list)
for idx, o in enumerate(data):
    byc2[(o['x'], o['prev'])].append(idx)
null2 = []
for _ in range(1000):
    lab = [None]*n
    for c, idxs in byc2.items():
        ys = [data[i]['omitted'] for i in idxs]
        random.shuffle(ys)
        for i, y in zip(idxs, ys):
            lab[i] = y
    null2.append(maxacc(lab))
mu2, sd2 = statistics.mean(null2), statistics.pstdev(null2)
ge2 = sum(1 for v in null2 if v >= obs)
print(f"null2 (within code+prev shuffle): mean {mu2:.4f} sd {sd2:.4f} max {max(null2):.4f}")
print(f"empirical p = {ge2}/1000; z = {(obs-mu2)/sd2:.2f}")

# contradictory signatures
labs = defaultdict(list)
for o in data:
    labs[(o['x'], o['prev'], o['nxt'])].append(o)
print("\ncontradictory (x,prev,nxt) signatures on 50 books:")
for k, os_ in labs.items():
    cnt = Counter(o['omitted'] for o in os_)
    if len(cnt) == 2:
        print("  sig", k, dict(cnt), "errors under majority:", min(cnt.values()))
        for o in os_:
            print("     book", o['book'], "t", o['t'], "code", o['c'], "omitted", o['omitted'])

# --- held-out test on 20 multipath books ---
DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
cur.execute("SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1")
SYM = dict(cur.fetchall())
INV = set(SYM)
cur.execute("""SELECT bookid, digits, CAST(insertedzeros AS INT), decodedbase
               FROM sheet__books GROUP BY bookid""")
books = {b: (d, iz, base) for b, d, iz, base in cur.fetchall()}
cur.execute("SELECT bookid, pathcount FROM row0_omission_probe_book_items WHERE run_id=1")
pathcount = dict(cur.fetchall())
print("\nmultipath books:", sum(1 for v in pathcount.values() if v > 1))

# lookup table from the 50 books
table = {k: c.most_common(1)[0][0] for k, c in
         ((k, Counter(o['omitted'] for o in v)) for k, v in labs.items())}
codemaj = {c: Counter(o['omitted'] for o in data if o['x'] == c).most_common(1)[0][0]
           for c in set(o['x'] for o in data)}

def enum_parses(digits, base):
    out = []
    n2, m = len(digits), len(base)
    stack = [(0, 0, ())]
    while stack:
        i, t, pat = stack.pop()
        if t == m:
            if i == n2:
                out.append(pat)
            continue
        if i + 2 <= n2:
            c = digits[i:i+2]
            if c in INV and SYM[c] == base[t]:
                stack.append((i+2, t+1, pat))
        if i + 1 <= n2:
            c = '0' + digits[i]
            if c in INV and SYM[c] == base[t]:
                stack.append((i+1, t+1, pat + (t+1,)))
    return out

def occs_for_parse(digits, pat):
    """list of (x, prev, nxt, omitted) for 0X codes given omission pattern pat (1-based code idx)."""
    pat = set(pat)
    res = []
    i = 0; t = 1
    while i < len(digits):
        if t in pat:
            c = '0' + digits[i]; wlen = 1
        else:
            c = digits[i:i+2]; wlen = 2
        if c[0] == '0':
            prev = digits[i-1] if i > 0 else 'S'
            nxt = digits[i+wlen] if i + wlen < len(digits) else 'E'
            res.append((c[1], prev, nxt, int(t in pat)))
        i += wlen; t += 1
    return res

tot_held = 0; corr_held = 0; covered = 0; corr_covered = 0
unique_sel = 0; tie = 0; wrongsel = 0
cur.execute("SELECT bookid, omitted_positions_json FROM row0_code_symbol_probe_books WHERE run_id=1")
chosen = {b: tuple(json.loads(j)) for b, j in cur.fetchall()}

for b, pc in sorted(pathcount.items(), key=lambda kv: kv[0]):
    if pc == 1:
        continue
    digits, iz, base = books[b]
    parses = enum_parses(digits, base)
    assert len(parses) == pc
    scores = []
    for pat in parses:
        oc = occs_for_parse(digits, pat)
        sc = 0; cov = 0
        for x, p, nx, y in oc:
            k = (x, p, nx)
            if k in table:
                cov += 1
                sc += table[k] == y
        scores.append((sc, cov, pat))
    best = max(s[0] for s in scores)
    bests = [s for s in scores if s[0] == best]
    sel = 'UNIQUE' if len(bests) == 1 else f'TIE({len(bests)})'
    if len(bests) == 1:
        unique_sel += 1
        match_probe = set(bests[0][2]) == set(chosen[b])
        if not match_probe:
            wrongsel += 1
    else:
        tie += 1
        match_probe = any(set(s[2]) == set(chosen[b]) for s in bests)
    # held-out accuracy on the probe-chosen parse (treat as reference)
    oc = occs_for_parse(digits, chosen[b])
    for x, p, nx, y in oc:
        tot_held += 1
        k = (x, p, nx)
        if k in table:
            covered += 1
            ok = table[k] == y
            corr_covered += ok
            corr_held += ok
        else:
            corr_held += codemaj.get(x, 0) == y
    print(f"book {b}: paths={pc} scores={[ (s[0],s[1]) for s in scores ]} -> {sel} probe-parse-among-best={match_probe}")

print(f"\nheld-out (20 multipath books, probe-chosen parse as reference):")
print(f"  total 0X occurrences: {tot_held}")
print(f"  covered by (x,prev,nxt) table: {covered} ({covered/tot_held:.3f})")
print(f"  accuracy on covered: {corr_covered}/{covered} = {corr_covered/covered:.4f}")
print(f"  accuracy overall (fallback per-code majority): {corr_held}/{tot_held} = {corr_held/tot_held:.4f}")
print(f"  rule selects unique best parse: {unique_sel}/20 (ties: {tie}); unique-but-disagrees-with-probe: {wrongsel}")
