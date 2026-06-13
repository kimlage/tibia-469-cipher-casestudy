#!/usr/bin/env python3
"""Adversarial statistical-null checks on the zero-omission claim."""
import sqlite3, json, random, math
from collections import Counter, defaultdict
import statistics

random.seed(424242)
TMP = './tmp/audit_20260609'
DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
cur.execute("SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1")
SYM = dict(cur.fetchall()); INV = set(SYM)
print("code rows:", len(SYM))
cur.execute("""SELECT bookid, digits, CAST(insertedzeros AS INT), decodedbase
               FROM sheet__books GROUP BY bookid""")
books = {b: (d, iz, base) for b, d, iz, base in cur.fetchall()}
print("books:", len(books))
cur.execute("SELECT bookid, pathcount FROM row0_omission_probe_book_items WHERE run_id=1")
pathcount = dict(cur.fetchall())
print("pathcount rows:", len(pathcount))
cur.execute("SELECT bookid, omitted_positions_json, reconstructed_code_stream FROM row0_code_symbol_probe_books WHERE run_id=1")
probe = {b: (set(json.loads(o)), cs.split()) for b, o, cs in cur.fetchall()}
print("probe rows:", len(probe))

# rebuild occurrences with prev2 for ALL books
occ = []
for b, (digits, iz, base) in books.items():
    omit, codes = probe[b]
    i = 0
    for t, c in enumerate(codes, start=1):
        omitted = t in omit
        wlen = 1 if omitted else 2
        if c[0] == '0':
            prev = digits[i-1] if i > 0 else 'S'
            prev2 = digits[i-2:i] if i > 1 else 'S'+digits[max(i-1,0):i]
            nxt = digits[i+wlen] if i+wlen < len(digits) else 'E'
            occ.append(dict(book=b, t=t, x=c[1], prev=prev, prev2=prev2, nxt=nxt,
                            omitted=int(omitted), pc=pathcount[b]))
        i += wlen
    assert i == len(digits)
print("occurrences all books:", len(occ), "omitted:", sum(o['omitted'] for o in occ))
data = [o for o in occ if o['pc'] == 1]
n = len(data)
print("occ on 50 single-path books:", n, "omitted:", sum(o['omitted'] for o in data))

def maxacc(labels, keyf):
    labs = defaultdict(Counter)
    for o, y in zip(data, labels):
        labs[keyf(o)][y] += 1
    return sum(max(c.values()) for c in labs.values()) / n, len(labs)

K3 = lambda o: (o['x'], o['prev'], o['nxt'])
KP2 = lambda o: (o['x'], o['prev2'], o['nxt'])
y0 = [o['omitted'] for o in data]

obs3, nsig3 = maxacc(y0, K3)
obsP2, nsigP2 = maxacc(y0, KP2)
print(f"\n(x,prev,nxt): maxacc={obs3:.4f} #sig={nsig3}")
print(f"(x,prev2,nxt): maxacc={obsP2:.4f} #sig={nsigP2}  -> errors={round((1-obsP2)*n)}")

# --- CHECK 1: permutation null for (x,prev2,nxt) with within-code shuffle ---
bycode = defaultdict(list)
for idx, o in enumerate(data):
    bycode[o['x']].append(idx)

def shuffled_within(groups):
    lab = [None]*n
    for c, idxs in groups.items():
        ys = [data[i]['omitted'] for i in idxs]
        random.shuffle(ys)
        for i, yy in zip(idxs, ys):
            lab[i] = yy
    return lab

nullP2 = []
for _ in range(1000):
    a, _ = maxacc(shuffled_within(bycode), KP2)
    nullP2.append(a)
mu, sd = statistics.mean(nullP2), statistics.pstdev(nullP2)
ge = sum(1 for v in nullP2 if v >= obsP2)
print(f"NULL (x,prev2,nxt) within-code shuffle: mean {mu:.4f} sd {sd:.4f} max {max(nullP2):.4f} z={(obsP2-mu)/sd:.2f} p={ge}/1000")

# --- CHECK 2: book-blocked null (shuffle within code AND book) for (x,prev,nxt) ---
bycb = defaultdict(list)
for idx, o in enumerate(data):
    bycb[(o['x'], o['book'])].append(idx)
nullB = []
for _ in range(1000):
    a, _ = maxacc(shuffled_within(bycb), K3)
    nullB.append(a)
mu, sd = statistics.mean(nullB), statistics.pstdev(nullB)
ge = sum(1 for v in nullB if v >= obs3)
print(f"NULL (x,prev,nxt) within-(code,book) shuffle: mean {mu:.4f} sd {sd:.4f} max {max(nullB):.4f} z={(obs3-mu)/sd:.2f} p={ge}/1000")

# --- CHECK 3: LOBO of the (x,prev2,nxt) lookup ---
booklist = sorted(set(o['book'] for o in data))
glob_major = int(sum(y0)*2 > n)
def lobo(keyf):
    corr = 0
    for b in booklist:
        tr = [o for o in data if o['book'] != b]
        te = [o for o in data if o['book'] == b]
        tab = defaultdict(Counter); ct = defaultdict(Counter)
        for o in tr:
            tab[keyf(o)][o['omitted']] += 1
            ct[o['x']][o['omitted']] += 1
        for o in te:
            k = keyf(o)
            if k in tab: pred = tab[k].most_common(1)[0][0]
            elif o['x'] in ct: pred = ct[o['x']].most_common(1)[0][0]
            else: pred = glob_major
            corr += pred == o['omitted']
    return corr/n
print(f"LOBO lookup (x,prev,nxt): {lobo(K3):.4f}")
print(f"LOBO lookup (x,prev2,nxt): {lobo(KP2):.4f}")

# --- CHECK 4: held-out errors vs ambiguous slots ---
def enum_parses(digits, base):
    out = []; n2, m = len(digits), len(base)
    stack = [(0, 0, ())]
    while stack:
        i, t, pat = stack.pop()
        if t == m:
            if i == n2: out.append(pat)
            continue
        if i+2 <= n2:
            c = digits[i:i+2]
            if c in INV and SYM[c] == base[t]: stack.append((i+2, t+1, pat))
        if i+1 <= n2:
            c = '0'+digits[i]
            if c in INV and SYM[c] == base[t]: stack.append((i+1, t+1, pat+(t+1,)))
    return out

labs3 = defaultdict(Counter)
for o in data:
    labs3[K3(o)][o['omitted']] += 1
table = {k: c.most_common(1)[0][0] for k, c in labs3.items()}

print("\nheld-out error localization (multipath books, probe parse as ref):")
err_amb = 0; err_fix = 0
for b, pc in sorted(pathcount.items()):
    if pc == 1: continue
    digits, iz, base = books[b]
    parses = enum_parses(digits, base)
    allpos = set().union(*[set(p) for p in parses])
    common = set(parses[0])
    for p in parses[1:]: common &= set(p)
    amb = allpos - common
    for o in [q for q in occ if q['book'] == b]:
        k = (o['x'], o['prev'], o['nxt'])
        if k in table and table[k] != o['omitted']:
            isamb = o['t'] in amb
            print(f"  book {b} t={o['t']} code 0{o['x']} pred={table[k]} ref={o['omitted']} ambiguous_slot={isamb}")
            if isamb: err_amb += 1
            else: err_fix += 1
print(f"errors on ambiguous slots: {err_amb}; on fixed slots: {err_fix}")

# --- CHECK 5: book 46 ambiguity adjacency ---
digits, iz, base = books['46']
parses = enum_parses(digits, base)
print("\nbook 46 omission patterns (1-based code idx):")
for p in sorted(parses):
    print("  ", p)

# --- CHECK 6: honest residual capacity ---
# (a) plug-in over ALL 634 occurrences with per-(x,prev,nxt) empirical rates
sigall = defaultdict(list)
for o in occ:
    sigall[(o['x'], o['prev'], o['nxt'])].append(o['omitted'])
H_all = 0.0
for k, v in sigall.items():
    p = statistics.mean(v)
    if 0 < p < 1:
        H_all += -(p*math.log2(p)+(1-p)*math.log2(1-p))*len(v)
print(f"\nplug-in residual capacity, all 634 occ, (x,prev,nxt) contexts: {H_all:.1f} bits")
# (b) deterministic-rule + exception-rate model: observed exceptions
# unambiguous 376: 2 exceptions under (x,prev,nxt) majority (1 under prev2)
# held-out covered: count fixed-slot errors from CHECK 4 -> err_fix
exc = 2 + err_fix
n_tested = 376 + 188
for ub_name, lam in [("point", float(exc)), ("Poisson 95% UB", None)]:
    if lam is None:
        # Poisson upper 95% bound for observed exc
        import math as _m
        # solve sum_{k<=exc} pois(k;lam)=0.05
        lo, hi = float(exc), exc+15.0
        for _ in range(60):
            mid = (lo+hi)/2
            s = sum(_m.exp(-mid)*mid**k/_m.factorial(k) for k in range(exc+1))
            if s > 0.05: lo = mid
            else: hi = mid
        lam = (lo+hi)/2
    eps = lam/n_tested
    h = -(eps*math.log2(eps)+(1-eps)*math.log2(1-eps)) if 0 < eps < 1 else 0
    print(f"exception model [{ub_name}]: lam={lam:.2f} eps={eps:.4f} capacity~{h*634:.1f} bits over 634 occ")
print(f"(claim asserted 'at most ~10 bits'; plug-in on 376 occ = 9.9)")
