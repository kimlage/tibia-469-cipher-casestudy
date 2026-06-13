#!/usr/bin/env python3
"""Independent reproduction (refutation lens) of the zero-omission claim.
Written from scratch; only feature DEFINITIONS mirror the probe so numbers are comparable.
"""
import sqlite3, json, math, sys, random
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

cur.execute("SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1")
rows = cur.fetchall()
print(f"[check] code map rows = {len(rows)}")
SYM = dict(rows)
INV = set(SYM)

cur.execute("""SELECT bookid, digits, CAST(insertedzeros AS INT), CAST(baselen AS INT), decodedbase
               FROM sheet__books GROUP BY bookid""")
books = cur.fetchall()
print(f"[check] books = {len(books)}")
tot_digits = sum(len(b[1]) for b in books)
tot_base = sum(len(b[4]) for b in books)
tot_iz = sum(b[2] for b in books)
print(f"[check] total digits={tot_digits} total base symbols={tot_base} total insertedzeros={tot_iz}")

cur.execute("SELECT bookid, pathcount, omitidxs_1based FROM row0_omission_probe_book_items WHERE run_id=1")
stored = {b: (pc, oi) for b, pc, oi in cur.fetchall()}
print(f"[check] stored probe items = {len(stored)}")

cur.execute("""SELECT bookid, omitted_positions_json, reconstructed_code_stream
               FROM row0_code_symbol_probe_books WHERE run_id=1""")
probe = {r[0]: (json.loads(r[1]), r[2].split()) for r in cur.fetchall()}

# ---------- sanity: probe parse actually reproduces the written digits ----------
bad_recon = 0
for bookid, digits, iz, baselen, base in books:
    omitset, codes = set(probe[bookid][0]), probe[bookid][1]
    w = ''.join((c[1] if (t in omitset) else c) for t, c in enumerate(codes, start=1))
    dec = ''.join(SYM[c] for c in codes)
    if w != digits or dec != base or len(codes) != baselen or len(omitset) != iz:
        bad_recon += 1
        print(f"  RECON FAIL {bookid}")
print(f"[check] probe-parse reconstruction failures (1-based convention): {bad_recon}/70")

# ---------- DP-A: enumerate ALL parses constrained by inventory + decodedbase ----------
def enum_parses(digits, base):
    n, m = len(digits), len(base)
    from functools import lru_cache
    @lru_cache(maxsize=None)
    def cnt(i, t):
        if t == m:
            return 1 if i == n else 0
        s = 0
        if i+2 <= n:
            c = digits[i:i+2]
            if c in INV and SYM[c] == base[t]:
                s += cnt(i+2, t+1)
        c = '0'+digits[i] if i < n else None
        if c and c in INV and SYM[c] == base[t]:
            s += cnt(i+1, t+1)
        return s
    total = cnt(0, 0)
    pats = []
    def walk(i, t, pat):
        if t == m:
            if i == n: pats.append(tuple(pat))
            return
        if i+2 <= len(digits):
            c = digits[i:i+2]
            if c in INV and SYM[c] == base[t] and cnt(i+2, t+1):
                walk(i+2, t+1, pat)
        if i < len(digits):
            c = '0'+digits[i]
            if c in INV and SYM[c] == base[t] and cnt(i+1, t+1):
                pat.append(t+1); walk(i+1, t+1, pat); pat.pop()
    sys.setrecursionlimit(100000)
    walk(0, 0, [])
    assert len(pats) == total
    return total, pats

pc_dist = Counter()
pc_mismatch = pat_mismatch = 0
multipath = {}
adjacent_only = True
for bookid, digits, iz, baselen, base in books:
    total, pats = enum_parses(digits, base)
    pc_dist[total] += 1
    spc, soi = stored[bookid]
    if total != spc:
        pc_mismatch += 1
        print(f"  PATHCOUNT MISMATCH {bookid}: mine={total} stored={spc}")
    spat = tuple(int(x) for x in soi.split(',')) if soi else ()
    if spat not in pats:
        pat_mismatch += 1
        print(f"  PATTERN MISMATCH {bookid}: stored={spat}")
    ppat = tuple(sorted(probe[bookid][0]))
    if ppat not in pats:
        print(f"  PROBE PATTERN NOT A VALID PARSE {bookid}")
    if total > 1:
        multipath[bookid] = pats
        # check ambiguity is adjacent-slot only: differing slots across parses
        allp = set().union(*[set(p) for p in pats])
        common = set(pats[0])
        for p in pats[1:]: common &= set(p)
        diff = sorted(allp - common)
        # adjacency: differences come in pairs (t, t+1)?
        for a, b in zip(diff[::2], diff[1::2]):
            if b - a != 1:
                adjacent_only = False
                print(f"  NON-ADJACENT ambiguity {bookid}: {diff}")
print(f"[DP-A] pathcount distribution: {dict(sorted(pc_dist.items()))}")
print(f"[DP-A] pathcount mismatches: {pc_mismatch}/70  pattern mismatches: {pat_mismatch}/70")
print(f"[DP-A] ambiguity adjacent-only: {adjacent_only}")

# ---------- occurrence extraction (mirror probe feature defs) ----------
def occurrences(bookid, digits, codes, omitset):
    out = []
    i = 0
    for t, c in enumerate(codes, start=1):
        om = t in omitset
        wlen = 1 if om else 2
        if c[0] == '0':
            prev = digits[i-1] if i > 0 else 'S'
            prev2 = digits[max(0, i-2):i]
            if i == 0: prev2 = 'SS'
            elif i == 1: prev2 = 'S' + digits[0]
            nxt = digits[i+wlen] if i+wlen < len(digits) else 'E'
            out.append(dict(book=bookid, t=t, c=c, prev=prev, prev2=prev2, nxt=nxt,
                            start=int(t == 1), omitted=int(om)))
        i += wlen
    assert i == len(digits)
    return out

allocc = []
bookinfo = {b[0]: b for b in books}
for bookid, digits, iz, baselen, base in books:
    omitset, codes = set(probe[bookid][0]), probe[bookid][1]
    allocc += occurrences(bookid, digits, codes, omitset)
n_om = sum(o['omitted'] for o in allocc)
print(f"[occ] all-70-books 0X occurrences = {len(allocc)}, omitted = {n_om}")

def rate(sel):
    s = [o['omitted'] for o in sel]
    return f"{sum(s)}/{len(s)}" + (f" = {sum(s)/len(s)*100:.1f}%" if s else "")
print(f"[marg] prev='1': {rate([o for o in allocc if o['prev']=='1'])}")
print(f"[marg] prev='8': {rate([o for o in allocc if o['prev']=='8'])}")
print(f"[marg] book-start: {rate([o for o in allocc if o['start']==1])}")
print(f"[marg] code 07: {rate([o for o in allocc if o['c']=='07'])}")
print(f"[marg] code 02: {rate([o for o in allocc if o['c']=='02'])}")

single = set(b for b, (pc, _) in stored.items() if pc == 1)
data = [o for o in allocc if o['book'] in single]
print(f"[occ] 50-book subset: n={len(data)} omitted={sum(o['omitted'] for o in data)}")

# ---------- lookup-table functionality ----------
def max_lookup(data, keyfn):
    tab = defaultdict(Counter)
    for o in data:
        tab[keyfn(o)][o['omitted']] += 1
    correct = sum(max(c.values()) for c in tab.values())
    return correct, len(tab), tab

k_cpn  = lambda o: (o['c'], o['prev'], o['nxt'])
k_cp2n = lambda o: (o['c'], o['prev2'], o['nxt'])
c1, n1, _ = max_lookup(data, k_cpn)
c2, n2, tab2 = max_lookup(data, k_cp2n)
print(f"[rule] (code,prev,nxt): {c1}/{len(data)} = {c1/len(data)*100:.2f}% over {n1} signatures")
print(f"[rule] (code,prev2,nxt): {c2}/{len(data)} = {c2/len(data)*100:.2f}% over {n2} signatures")
for k, cnts in tab2.items():
    if len(cnts) == 2:
        print(f"  contradictory (code,prev2,nxt) signature: {k} counts={dict(cnts)}")
        for o in data:
            if k_cp2n(o) == k:
                print(f"    book={o['book']} t={o['t']} omitted={o['omitted']}")

# ---------- permutation nulls ----------
def perm_null(data, keyfn, groupfn, R=1000, seed=12345):
    rng = random.Random(seed)
    groups = defaultdict(list)
    for idx, o in enumerate(data):
        groups[groupfn(o)].append(idx)
    labels = [o['omitted'] for o in data]
    vals = []
    for _ in range(R):
        lab = labels[:]
        for g, idxs in groups.items():
            sub = [lab[i] for i in idxs]
            rng.shuffle(sub)
            for i, v in zip(idxs, sub): lab[i] = v
        tab = defaultdict(Counter)
        for i, o in enumerate(data):
            tab[keyfn(o)][lab[i]] += 1
        vals.append(sum(max(c.values()) for c in tab.values()) / len(data))
    mu = sum(vals)/len(vals)
    sd = (sum((v-mu)**2 for v in vals)/len(vals))**0.5
    return mu, sd

obs1 = c1/len(data)
mu_a, sd_a = perm_null(data, k_cpn, lambda o: o['c'])
print(f"[null] within-code shuffle, (code,prev,nxt) lookup: {mu_a*100:.2f}% +- {sd_a*100:.2f}%  z={(obs1-mu_a)/sd_a:.2f}")
mu_b, sd_b = perm_null(data, k_cpn, lambda o: (o['c'], o['prev']))
print(f"[null] within-(code,prev) shuffle: {mu_b*100:.2f}% +- {sd_b*100:.2f}%  z={(obs1-mu_b)/sd_b:.2f}")
obs2 = c2/len(data)
mu_c, sd_c = perm_null(data, k_cp2n, lambda o: o['c'])
print(f"[null] within-code shuffle, (code,prev2,nxt) lookup: {mu_c*100:.2f}% +- {sd_c*100:.2f}%  z={(obs2-mu_c)/sd_c:.2f}")

# ---------- held-out test on 20 multipath books (labels = stored probe parse) ----------
tab = defaultdict(Counter)
for o in data:
    tab[k_cp2n(o)][o['omitted']] += 1
rule = {k: c.most_common(1)[0][0] for k, c in tab.items()}
heldout = [o for o in allocc if o['book'] not in single]
print(f"[held-out] multipath occurrences = {len(heldout)}")
cov = [o for o in heldout if k_cp2n(o) in rule]
corr = sum(1 for o in cov if rule[k_cp2n(o)] == o['omitted'])
print(f"[held-out] coverage {len(cov)}/{len(heldout)} = {len(cov)/len(heldout)*100:.1f}%; correct {corr}/{len(cov)} = {corr/len(cov)*100:.2f}%")

# ---------- per-parse scoring of multipath books: unique disambiguation? ----------
print("[disambig] scoring each DP-A parse of each multipath book against 50-book rule")
uniq = ties = 0
conflicts = []
for bookid, pats in sorted(multipath.items(), key=lambda kv: kv[0]):
    digits = bookinfo[bookid][1]; codes = probe[bookid][1]
    scores = []
    for p in pats:
        occ_p = occurrences(bookid, digits, codes, set(p))
        sc = sum(1 for o in occ_p if k_cp2n(o) in rule and rule[k_cp2n(o)] == o['omitted'])
        ncov = sum(1 for o in occ_p if k_cp2n(o) in rule)
        scores.append((sc, ncov, p))
    best = max(s[0] for s in scores)
    winners = [s for s in scores if s[0] == best]
    stored_pat = tuple(sorted(probe[bookid][0]))
    if len(winners) == 1:
        uniq += 1
        if winners[0][2] != stored_pat:
            conflicts.append(bookid)
            print(f"  book {bookid}: rule-preferred parse != stored parse  scores={[(s[0],s[1]) for s in scores]}")
    else:
        ties += 1
print(f"[disambig] unique={uniq} ties={ties} (of {len(multipath)}); rule-vs-stored conflicts: {conflicts}")

# ---------- residual channel capacity ----------
def H2(p):
    if p <= 0 or p >= 1: return 0.0
    return -p*math.log2(p) - (1-p)*math.log2(1-p)
def capacity(data, keyfn):
    tab = defaultdict(Counter)
    for o in data:
        tab[keyfn(o)][o['omitted']] += 1
    bits = 0.0
    for c in tab.values():
        n = sum(c.values())
        bits += n * H2(c.get(1, 0)/n)
    return bits
cap_ctx = capacity(data, k_cpn)
cap_code = capacity(data, lambda o: o['c'])
cap_naive_376 = len(data) * H2(sum(o['omitted'] for o in data)/len(data))
cap_naive_all = len(allocc) * H2(n_om/len(allocc))
print(f"[capacity] (code,prev,nxt) residual: {cap_ctx:.1f} bits over {len(data)} occ")
print(f"[capacity] per-code only: {cap_code:.1f} bits; naive(376): {cap_naive_376:.1f}; naive(634, all books): {cap_naive_all:.1f}")
cap_ctx2 = capacity(data, k_cp2n)
print(f"[capacity] (code,prev2,nxt) residual: {cap_ctx2:.1f} bits")
print("DONE")
