#!/usr/bin/env python3
"""Part 3: binary side-channel tests on omit/retain bitstrings (50 pathcount=1 books).
Controls: C1 = per-code marginal-matched Bernoulli (1000x);
          C2 = per-(x,prev,nxt) signature-matched Bernoulli (1000x).
Stats: per-book balance chi2, lag-1 autocorr, Bacon-5bit English score (both
polarities), corr(omitted count, bookid/baselen), ANOVA F across clusterid.
Also: do wider contexts (prev2/nxt2) resolve the 2 exceptions?
"""
import sqlite3, json, random, math
from collections import Counter, defaultdict
import statistics

random.seed(20260609)
TMP = './tmp/audit_20260609'
occ = json.load(open(f'{TMP}/occurrences.json'))
data = [o for o in occ if o['pc'] == 1]

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
cur.execute("""SELECT bookid, clusterid, CAST(baselen AS INT), digits FROM sheet__books GROUP BY bookid""")
meta = {b: (cl, bl, d) for b, cl, bl, d in cur.fetchall()}
print("meta rows:", len(meta))

# --- exception context check ---
print("\n-- exception wider-context check --")
for sig_target in [('0','8','3'), ('3','5','6')]:
    print("sig", sig_target)
    for o in data:
        if (o['x'], o['prev'], o['nxt']) == sig_target:
            d = meta[o['book']][2]
            # find written offset: recompute
            # o has t; rebuild written offset from occurrences.json absent -> recompute prev2/nxt2 via digits scan
            pass
    # recompute with offsets
# rebuild occurrences with offsets (pathcount=1 books)
cur.execute("SELECT bookid, omitted_positions_json, reconstructed_code_stream FROM row0_code_symbol_probe_books WHERE run_id=1")
probe = {b: (set(json.loads(o)), cs.split()) for b, o, cs in cur.fetchall()}
cur.execute("SELECT bookid, pathcount FROM row0_omission_probe_book_items WHERE run_id=1")
pathcount = dict(cur.fetchall())

occ2 = []
for b, (cl, bl, digits) in meta.items():
    if pathcount[b] != 1:
        continue
    omit, codes = probe[b]
    i = 0
    for t, c in enumerate(codes, start=1):
        omitted = t in omit
        wlen = 1 if omitted else 2
        if c[0] == '0':
            prev = digits[i-1] if i > 0 else 'S'
            prev2 = digits[i-2:i] if i > 1 else 'S'+digits[max(i-1,0):i]
            nxt = digits[i+wlen] if i+wlen < len(digits) else 'E'
            nxt2 = digits[i+wlen:i+wlen+2]
            occ2.append(dict(book=b, t=t, x=c[1], prev=prev, prev2=prev2,
                             nxt=nxt, nxt2=nxt2, omitted=int(omitted)))
        i += wlen
print("occ2:", len(occ2))
for sig_target in [('0','8','3'), ('3','5','6')]:
    grp = [o for o in occ2 if (o['x'], o['prev'], o['nxt']) == sig_target]
    print(f"\nsig {sig_target}: n={len(grp)}")
    for key2 in ('prev2', 'nxt2'):
        tab = defaultdict(Counter)
        for o in grp:
            tab[o[key2]][o['omitted']] += 1
        sep = all(len(c) == 1 for c in tab.values())
        print(f"  by {key2}: separable={sep} :: " +
              " ".join(f"{k}:{dict(c)}" for k, c in sorted(tab.items())))

# --- bitstring battery ---
books_sorted = sorted(set(o['book'] for o in data), key=lambda b: int(b))
seq = []  # in bookid order, occurrences in stream order
for b in books_sorted:
    bo = sorted([o for o in data if o['book'] == b], key=lambda o: o['t'])
    seq.extend(bo)
bits = [o['omitted'] for o in seq]
n = len(bits)
print(f"\nbitstring: {n} bits, ones={sum(bits)}")

# per-code and per-signature probabilities
pcode = {c: statistics.mean([o['omitted'] for o in data if o['x'] == c])
         for c in set(o['x'] for o in data)}
psig = {}
sigocc = defaultdict(list)
for o in data:
    sigocc[(o['x'], o['prev'], o['nxt'])].append(o['omitted'])
for k, v in sigocc.items():
    psig[k] = statistics.mean(v)

# stats
ENG = {'A':8.2,'B':1.5,'C':2.8,'D':4.3,'E':12.7,'F':2.2,'G':2.0,'H':6.1,'I':7.0,
       'J':0.15,'K':0.77,'L':4.0,'M':2.4,'N':6.7,'O':7.5,'P':1.9,'Q':0.095,'R':6.0,
       'S':6.3,'T':9.1,'U':2.8,'V':0.98,'W':2.4,'X':0.15,'Y':2.0,'Z':0.074}
LOGF = {k: math.log(v/100) for k, v in ENG.items()}
def bacon_score(bs):
    best = -1e18
    for pol in (0, 1):
        b2 = [x ^ pol for x in bs]
        sc = 0.0; cnt = 0
        for i in range(0, len(b2)-4, 5):
            v = 0
            for j in range(5):
                v = v*2 + b2[i+j]
            if v < 26:
                sc += LOGF[chr(65+v)]
                cnt += 1
            else:
                sc += math.log(1/26/4)  # penalty
                cnt += 1
        best = max(best, sc/cnt)
    return best

def stats_for(bits_):
    # per-book balance chi2 against expected from per-code probs
    chi2 = 0.0
    idx = 0
    counts = {}
    for b in books_sorted:
        bo = [o for o in seq if o['book'] == b]
        k = sum(bits_[idx+i] for i in range(len(bo)))
        mu = sum(pcode[o['x']] for o in bo)
        var = sum(pcode[o['x']]*(1-pcode[o['x']]) for o in bo)
        if var > 0:
            chi2 += (k-mu)**2/var
        counts[b] = k
        idx += len(bo)
    # lag-1 autocorr within books
    num = 0.0; den = 0.0
    mu_all = statistics.mean(bits_)
    idx = 0
    for b in books_sorted:
        m = sum(1 for o in seq if o['book'] == b)
        bb = bits_[idx:idx+m]
        for i in range(m-1):
            num += (bb[i]-mu_all)*(bb[i+1]-mu_all)
        den += sum((x-mu_all)**2 for x in bb)
        idx += m
    ac1 = num/den if den else 0.0
    bac = bacon_score(bits_)
    ks = [counts[b] for b in books_sorted]
    ids = [int(b) for b in books_sorted]
    bls = [meta[b][1] for b in books_sorted]
    def pearson(a, c):
        ma, mc = statistics.mean(a), statistics.mean(c)
        cov = sum((x-ma)*(y-mc) for x, y in zip(a, c))
        sa = math.sqrt(sum((x-ma)**2 for x in a)); sc = math.sqrt(sum((y-mc)**2 for y in c))
        return cov/(sa*sc) if sa*sc else 0.0
    r_id = pearson(ks, ids)
    # rate vs baselen: use rate to decouple length
    nb = [sum(1 for o in seq if o['book'] == b) for b in books_sorted]
    rates = [k/m for k, m in zip(ks, nb)]
    r_bl = pearson(rates, bls)
    # ANOVA F across clusterid on rates
    bycl = defaultdict(list)
    for b, r in zip(books_sorted, rates):
        bycl[meta[b][0]].append(r)
    gm = statistics.mean(rates)
    ssb = sum(len(v)*(statistics.mean(v)-gm)**2 for v in bycl.values())
    ssw = sum(sum((x-statistics.mean(v))**2 for x in v) for v in bycl.values())
    dfb = len(bycl)-1; dfw = len(rates)-len(bycl)
    F = (ssb/dfb)/(ssw/dfw) if ssw > 0 and dfw > 0 else 0.0
    return dict(chi2=chi2, ac1=ac1, bacon=bac, r_id=r_id, r_bl=r_bl, F=F)

obs = stats_for(bits)
print("clusters:", len(set(meta[b][0] for b in books_sorted)))
print("observed:", {k: round(v, 4) for k, v in obs.items()})

def run_controls(pfunc, label, N=1000):
    null = defaultdict(list)
    for _ in range(N):
        bs = [1 if random.random() < pfunc(o) else 0 for o in seq]
        st = stats_for(bs)
        for k, v in st.items():
            null[k].append(v)
    print(f"\ncontrol {label} ({N}x):")
    for k in obs:
        mu = statistics.mean(null[k]); sd = statistics.pstdev(null[k])
        z = (obs[k]-mu)/sd if sd else float('nan')
        # two-sided empirical p
        pge = sum(1 for v in null[k] if v >= obs[k])/N
        ple = sum(1 for v in null[k] if v <= obs[k])/N
        p2 = 2*min(pge, ple)
        print(f"  {k:6s}: obs={obs[k]:8.4f} null mean={mu:8.4f} sd={sd:7.4f} z={z:7.2f} p_two~{min(p2,1):.3f}")

run_controls(lambda o: pcode[o['x']], "C1 per-code marginal")
run_controls(lambda o: psig[(o['x'], o['prev'], o['nxt'])], "C2 per-(x,prev,nxt) signature")

# capacity estimate of residual channel
H = 0.0
for k, v in sigocc.items():
    p = statistics.mean(v)
    if 0 < p < 1:
        h = -(p*math.log2(p) + (1-p)*math.log2(1-p))
        H += h*len(v)
print(f"\nresidual channel capacity upper bound given (x,prev,nxt) contexts, 50 books: {H:.1f} bits over {n} occurrences")
H1 = 0.0
for c, p in pcode.items():
    m = sum(1 for o in data if o['x'] == c)
    if 0 < p < 1:
        H1 += -(p*math.log2(p)+(1-p)*math.log2(1-p))*m
print(f"naive capacity if only per-code marginals constrained: {H1:.1f} bits")
