#!/usr/bin/env python3
"""Follow-ups: book 46 ambiguity structure, held-out conventions, parse-invariant
held-out subset (circularity-proof), side-channel spot checks."""
import sqlite3, json, math, sys, random
from collections import Counter, defaultdict
from functools import lru_cache

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
cur.execute("SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1")
SYM = dict(cur.fetchall()); INV = set(SYM)
cur.execute("""SELECT bookid, digits, CAST(insertedzeros AS INT), CAST(baselen AS INT), decodedbase
               FROM sheet__books GROUP BY bookid""")
books = cur.fetchall(); bookinfo = {b[0]: b for b in books}
cur.execute("SELECT bookid, pathcount FROM row0_omission_probe_book_items WHERE run_id=1")
stored_pc = dict(cur.fetchall())
cur.execute("SELECT bookid, omitted_positions_json, reconstructed_code_stream FROM row0_code_symbol_probe_books WHERE run_id=1")
probe = {r[0]: (json.loads(r[1]), r[2].split()) for r in cur.fetchall()}
cur.execute("SELECT bookid, clusterid FROM sheet__books GROUP BY bookid")
clus = dict(cur.fetchall())

def enum_parses(digits, base):
    n, m = len(digits), len(base)
    @lru_cache(maxsize=None)
    def cnt(i, t):
        if t == m: return 1 if i == n else 0
        s = 0
        if i+2 <= n:
            c = digits[i:i+2]
            if c in INV and SYM[c] == base[t]: s += cnt(i+2, t+1)
        if i < n:
            c = '0'+digits[i]
            if c in INV and SYM[c] == base[t]: s += cnt(i+1, t+1)
        return s
    pats = []
    def walk(i, t, pat):
        if t == m:
            if i == n: pats.append(tuple(pat))
            return
        if i+2 <= n:
            c = digits[i:i+2]
            if c in INV and SYM[c] == base[t] and cnt(i+2, t+1): walk(i+2, t+1, pat)
        if i < n:
            c = '0'+digits[i]
            if c in INV and SYM[c] == base[t] and cnt(i+1, t+1):
                pat.append(t+1); walk(i+1, t+1, pat); pat.pop()
    sys.setrecursionlimit(100000)
    walk(0, 0, [])
    return pats

# ---- book 46 ambiguity ----
b46 = bookinfo['46']
pats46 = enum_parses(b46[1], b46[4])
print(f"[46] pathcount={len(pats46)} stored_pc={stored_pc['46']}")
for p in pats46:
    print(f"  pattern: {p}  (stored={'*' if tuple(sorted(probe['46'][0]))==p else ''})")

# ---- occurrence extraction ----
def occurrences(bookid, digits, codes, omitset):
    out = []; i = 0
    for t, c in enumerate(codes, start=1):
        om = t in omitset; wlen = 1 if om else 2
        if c[0] == '0':
            prev = digits[i-1] if i > 0 else 'S'
            prev2 = ('SS' if i == 0 else ('S'+digits[0] if i == 1 else digits[i-2:i]))
            nxt = digits[i+wlen] if i+wlen < len(digits) else 'E'
            out.append(dict(book=bookid, t=t, c=c, prev=prev, prev2=prev2, nxt=nxt,
                            start=int(t==1), omitted=int(om)))
        i += wlen
    return out

single = set(b for b, pc in stored_pc.items() if pc == 1)
data, heldout = [], []
allpats = {}
for bookid, digits, iz, baselen, base in books:
    occ = occurrences(bookid, digits, probe[bookid][1], set(probe[bookid][0]))
    if bookid in single: data += occ
    else:
        heldout += occ
        allpats[bookid] = enum_parses(digits, base)

k_cpn  = lambda o: (o['c'], o['prev'], o['nxt'])
k_cp2n = lambda o: (o['c'], o['prev2'], o['nxt'])
def build(keyfn):
    tab = defaultdict(Counter)
    for o in data: tab[keyfn(o)][o['omitted']] += 1
    return {k: c.most_common(1)[0][0] for k, c in tab.items()}
rule3 = build(k_cpn); rule4 = build(k_cp2n)

for name, rule, kf in (("(code,prev,nxt)", rule3, k_cpn), ("(code,prev2,nxt)", rule4, k_cp2n)):
    cov = [o for o in heldout if kf(o) in rule]
    corr = sum(1 for o in cov if rule[kf(o)] == o['omitted'])
    print(f"[held-out {name}] coverage {len(cov)}/{len(heldout)}; correct {corr}/{len(cov)} = {corr/len(cov)*100:.2f}%")

# ---- parse-invariant held-out subset (labels independent of stored-parse convention) ----
inv_occ = []
amb_occ = []
for bookid, pats in allpats.items():
    omit_sets = [set(p) for p in pats]
    digits = bookinfo[bookid][1]; codes = probe[bookid][1]
    stored_set = set(probe[bookid][0])
    occ = occurrences(bookid, digits, codes, stored_set)
    always = set.intersection(*omit_sets); never_om = set()
    union = set.union(*omit_sets)
    for o in occ:
        t = o['t']
        if t in always or t not in union:
            # also features must be parse-invariant: check prev/prev2/nxt same under every parse
            feats = set()
            for p in pats:
                for o2 in occurrences(bookid, digits, codes, set(p)):
                    if o2['t'] == t:
                        feats.add((o2['prev'], o2['prev2'], o2['nxt'], o2['omitted']))
            if len(feats) == 1:
                inv_occ.append(o)
            else:
                amb_occ.append(o)
        else:
            amb_occ.append(o)
print(f"[invariant] parse-invariant held-out occurrences: {len(inv_occ)}; parse-dependent: {len(amb_occ)}")
for name, rule, kf in (("(code,prev,nxt)", rule3, k_cpn), ("(code,prev2,nxt)", rule4, k_cp2n)):
    cov = [o for o in inv_occ if kf(o) in rule]
    corr = sum(1 for o in cov if rule[kf(o)] == o['omitted'])
    print(f"[invariant held-out {name}] coverage {len(cov)}/{len(inv_occ)}; correct {corr}/{len(cov)} = {corr/len(cov)*100:.2f}%")

# ---- disambiguation with (code,prev,nxt) rule and tie conventions ----
for name, rule, kf in (("(code,prev,nxt)", rule3, k_cpn), ("(code,prev2,nxt)", rule4, k_cp2n)):
    uniq = ties = 0; conf = []
    for bookid, pats in sorted(allpats.items()):
        digits = bookinfo[bookid][1]; codes = probe[bookid][1]
        scores = []
        for p in pats:
            occ_p = occurrences(bookid, digits, codes, set(p))
            sc = sum(1 for o in occ_p if kf(o) in rule and rule[kf(o)] == o['omitted'])
            scores.append((sc, p))
        best = max(s[0] for s in scores)
        winners = [s for s in scores if s[0] == best]
        if len(winners) == 1:
            uniq += 1
            if winners[0][1] != tuple(sorted(probe[bookid][0])): conf.append(bookid)
        else: ties += 1
    print(f"[disambig {name}] unique={uniq} ties={ties} conflicts={conf}")

# ---- side-channel spot checks on the 376-bit string ----
# order: books sorted as in `books` list (GROUP BY bookid), occurrences in stream order
seq = [o for o in data]
bits = [o['omitted'] for o in seq]
bybook = defaultdict(list)
for o in seq: bybook[o['book']].append(o['omitted'])

def stat_balance(bb):
    # chi2 across books for omit counts vs expected from global rate
    p = sum(sum(v) for v in bb.values()) / sum(len(v) for v in bb.values())
    x2 = 0.0
    for v in bb.values():
        n = len(v); e = n*p
        if 0 < e < n: x2 += (sum(v)-e)**2/(e*(1-p))
    return x2
def stat_lag1(bb):
    num = den = 0
    for v in bb.values():
        for a, b in zip(v, v[1:]):
            num += (a == b); den += 1
    return num/den
def stat_rbaselen(bb):
    xs, ys = [], []
    for b, v in bb.items():
        xs.append(int(bookinfo[b][3])); ys.append(sum(v)/len(v))
    mx, my = sum(xs)/len(xs), sum(ys)/len(ys)
    cov = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    sx = math.sqrt(sum((x-mx)**2 for x in xs)); sy = math.sqrt(sum((y-my)**2 for y in ys))
    return cov/(sx*sy)
BACON = {tuple(int(c) for c in format(i, '05b')): chr(65+i) for i in range(26)}
ENG = {'E':12.7,'T':9.1,'A':8.2,'O':7.5,'I':7.0,'N':6.7,'S':6.3,'H':6.1,'R':6.0,'D':4.3,'L':4.0,'C':2.8,'U':2.8,'M':2.4,'W':2.4,'F':2.2,'G':2.0,'Y':2.0,'P':1.9,'B':1.5,'V':1.0,'K':0.8,'J':0.15,'X':0.15,'Q':0.1,'Z':0.07}
def stat_bacon(bits):
    best = -1e9
    for pol in (0, 1):
        bs = [b ^ pol for b in bits]
        sc = 0.0; n = 0
        for i in range(0, len(bs)-4, 5):
            ch = BACON.get(tuple(bs[i:i+5]))
            if ch: sc += math.log(ENG.get(ch, 0.05)/100); n += 1
        best = max(best, sc/n if n else -1e9)
    return best

obs = dict(bal=stat_balance(bybook), lag1=stat_lag1(bybook), rbl=stat_rbaselen(bybook), bacon=stat_bacon(bits))
# C1: permute labels within code class
rng = random.Random(777)
groups = defaultdict(list)
for idx, o in enumerate(seq): groups[o['c']].append(idx)
nulls = defaultdict(list)
labels = [o['omitted'] for o in seq]
for _ in range(1000):
    lab = labels[:]
    for g, idxs in groups.items():
        sub = [lab[i] for i in idxs]; rng.shuffle(sub)
        for i, v in zip(idxs, sub): lab[i] = v
    bb = defaultdict(list)
    for i, o in enumerate(seq): bb[o['book']].append(lab[i])
    nulls['bal'].append(stat_balance(bb)); nulls['lag1'].append(stat_lag1(bb))
    nulls['rbl'].append(stat_rbaselen(bb)); nulls['bacon'].append(stat_bacon(lab))
print("[side-channel vs C1 (within-code shuffle)]")
for k, v in obs.items():
    arr = nulls[k]; mu = sum(arr)/len(arr); sd = (sum((x-mu)**2 for x in arr)/len(arr))**0.5
    print(f"  {k}: obs={v:.4f} null={mu:.4f}+-{sd:.4f} z={(v-mu)/sd:+.2f}")
print("DONE")
