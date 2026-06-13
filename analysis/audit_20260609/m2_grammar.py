#!/usr/bin/env python3
"""Module decomposition attack, part 2: generative positive proof on decoded layer.
(b) RePair grammar induction on 70 decodedbase strings; two-part MDL; % corpus from
    rules used in >=2 books. Controls: per-book unigram shuffles + order-1/2 Markov
    surrogates (matched lengths). Also shared-10gram coverage + lzma secondary metric.
"""
import sqlite3, random, math, lzma
from collections import Counter

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("""SELECT bookid, MIN(decodedbase) FROM sheet__books GROUP BY bookid""").fetchall()
print("ROWCOUNT:", len(rows)); assert len(rows) == 70
def keyf(b):
    try: return (0, int(b))
    except: return (1, b)
rows.sort(key=lambda r: keyf(r[0]))
texts = [r[1] for r in rows]
alpha = sorted(set("".join(texts)))
A0 = len(alpha)
idx = {c: i for i, c in enumerate(alpha)}
seqs_real = [[idx[c] for c in t] for t in texts]
N = sum(len(s) for s in seqs_real)
log2 = math.log2
print(f"books=70 symbols={N} alphabet={A0} ({''.join(alpha)})")
BASE_MDL = N * log2(A0)
print(f"baseline MDL = N*log2(A0) = {BASE_MDL:.0f} bits")

# ---------- shared k-gram coverage ----------
def shared_cov(seqs, k=10):
    d = {}
    for bi, s in enumerate(seqs):
        t = tuple(s)
        for i in range(len(s) - k + 1):
            d.setdefault(t[i:i+k], set()).add(bi)
    cov = 0
    for bi, s in enumerate(seqs):
        t = tuple(s); mask = bytearray(len(s))
        for i in range(len(s) - k + 1):
            if len(d[t[i:i+k]]) >= 2:
                for j in range(i, i + k): mask[j] = 1
        cov += sum(mask)
    return cov

cov_real = shared_cov(seqs_real)
print(f"\n== shared 10-gram coverage (symbols in 10-grams verbatim in >=2 books) ==")
print(f"REAL: {cov_real}/{N} = {100*cov_real/N:.1f}%")

rng = random.Random(469)
def shuffle_corpus():
    return [rng.sample(s, len(s)) for s in seqs_real]

# Markov surrogates (order m), pooled transitions, per-book lengths preserved
def fit_markov(m):
    trans = {}
    starts = []
    for s in seqs_real:
        starts.append(tuple(s[:m]))
        for i in range(len(s) - m):
            ctx = tuple(s[i:i+m])
            trans.setdefault(ctx, []).append(s[i+m])
    return starts, trans
def markov_corpus(m, starts, trans):
    out = []
    for s in seqs_real:
        L = len(s)
        cur = list(rng.choice(starts))[:L]
        while len(cur) < L:
            ctx = tuple(cur[-m:])
            choices = trans.get(ctx)
            if not choices:
                ctx = rng.choice(list(trans.keys())); choices = trans[ctx]
            cur.append(rng.choice(choices))
        out.append(cur)
    return out

NCOV = 100
cov_sh = []
for _ in range(NCOV):
    cov_sh.append(shared_cov(shuffle_corpus()))
mu = sum(cov_sh)/NCOV; sd = (sum((x-mu)**2 for x in cov_sh)/NCOV)**0.5
z = (cov_real-mu)/sd if sd > 0 else float("inf")
print(f"CONTROL unigram-shuffle x{NCOV}: mean={mu:.1f} ({100*mu/N:.2f}%) sd={sd:.1f} max={max(cov_sh)} -> z={z:.1f}")
st1, tr1 = fit_markov(1)
cov_mk = [shared_cov(markov_corpus(1, st1, tr1)) for _ in range(NCOV)]
mu1 = sum(cov_mk)/NCOV; sd1 = (sum((x-mu1)**2 for x in cov_mk)/NCOV)**0.5
z1 = (cov_real-mu1)/sd1 if sd1 > 0 else float("inf")
print(f"CONTROL order-1 Markov x{NCOV}: mean={mu1:.1f} ({100*mu1/N:.2f}%) sd={sd1:.1f} max={max(cov_mk)} -> z={z1:.1f}")
st2, tr2 = fit_markov(2)
cov_mk2 = [shared_cov(markov_corpus(2, st2, tr2)) for _ in range(NCOV)]
mu2 = sum(cov_mk2)/NCOV; sd2 = (sum((x-mu2)**2 for x in cov_mk2)/NCOV)**0.5
z2 = (cov_real-mu2)/sd2 if sd2 > 0 else float("inf")
print(f"CONTROL order-2 Markov x{NCOV}: mean={mu2:.1f} ({100*mu2/N:.2f}%) sd={sd2:.1f} max={max(cov_mk2)} -> z={z2:.1f}")

# ---------- RePair + two-part MDL ----------
def repair_mdl(seqs, keep_best=False):
    cur = [list(s) for s in seqs]
    rules = []
    best = (sum(len(s) for s in cur)) * log2(A0)
    best_state = None
    while True:
        cnt = Counter()
        for s in cur:
            for i in range(len(s) - 1):
                cnt[(s[i], s[i+1])] += 1
        if not cnt: break
        (a, b), c = cnt.most_common(1)[0]
        if c < 3: break
        new = A0 + len(rules)
        rules.append((a, b))
        for k2, s in enumerate(cur):
            out = []; i = 0; n = len(s)
            while i < n:
                if i + 1 < n and s[i] == a and s[i+1] == b:
                    out.append(new); i += 2
                else:
                    out.append(s[i]); i += 1
            cur[k2] = out
        T = sum(len(s) for s in cur); G = len(rules)
        mdl = (T + 2*G) * log2(A0 + G)
        if mdl < best:
            best = mdl
            if keep_best:
                best_state = ([list(s) for s in cur], list(rules))
    return best, best_state

mdl_real, state = repair_mdl(seqs_real, keep_best=True)
final_seqs, rules = state
T = sum(len(s) for s in final_seqs); G = len(rules)
print(f"\n== RePair two-part MDL (decoded corpus) ==")
print(f"REAL: best MDL={mdl_real:.0f} bits (rules={G}, residual tokens={T}, alphabet {A0}+{G})")
print(f"      vs baseline {BASE_MDL:.0f} bits -> ratio {mdl_real/BASE_MDL:.3f}")

# % of corpus emitted by rules used in >=2 books (at MDL-optimal grammar)
explen = {i: 1 for i in range(A0)}
for ri, (a, b) in enumerate(rules):
    explen[A0 + ri] = explen[a] + explen[b]
tok_books = {}
for bi, s in enumerate(final_seqs):
    for t in s:
        if t >= A0: tok_books.setdefault(t, set()).add(bi)
shared_toks = {t for t, bb in tok_books.items() if len(bb) >= 2}
em_shared = sum(explen[t] for s in final_seqs for t in s if t in shared_toks)
rules_used2 = len(shared_toks)
print(f"      rules whose nonterminal appears in >=2 books: {rules_used2}/{G}")
print(f"      symbols emitted by shared(>=2 books) nonterminals: {em_shared}/{N} = {100*em_shared/N:.1f}%")
longest = sorted(((explen[A0+i], i) for i in range(G)), reverse=True)[:5]
for L, i in longest:
    bb = tok_books.get(A0 + i, set())
    print(f"      rule R{i}: expands to {L} symbols, top-level in {len(bb)} books")

# controls for MDL
NM = 20
mdl_sh = [repair_mdl(shuffle_corpus())[0] for _ in range(NM)]
mu = sum(mdl_sh)/NM; sd = (sum((x-mu)**2 for x in mdl_sh)/NM)**0.5
print(f"CONTROL unigram-shuffle x{NM}: MDL mean={mu:.0f} sd={sd:.0f} min={min(mdl_sh):.0f} -> real z={(mdl_real-mu)/sd:.1f}")
mdl_m1 = [repair_mdl(markov_corpus(1, st1, tr1))[0] for _ in range(NM)]
mu = sum(mdl_m1)/NM; sd = (sum((x-mu)**2 for x in mdl_m1)/NM)**0.5
print(f"CONTROL order-1 Markov x{NM}: MDL mean={mu:.0f} sd={sd:.0f} min={min(mdl_m1):.0f} -> real z={(mdl_real-mu)/sd:.1f}")
mdl_m2 = [repair_mdl(markov_corpus(2, st2, tr2))[0] for _ in range(NM)]
mu = sum(mdl_m2)/NM; sd = (sum((x-mu)**2 for x in mdl_m2)/NM)**0.5
print(f"CONTROL order-2 Markov x{NM}: MDL mean={mu:.0f} sd={sd:.0f} min={min(mdl_m2):.0f} -> real z={(mdl_real-mu)/sd:.1f}")

# lzma secondary
def lz_bytes(seqs):
    blob = b"\xff".join(bytes(s) for s in seqs)
    return len(lzma.compress(blob, preset=9))
lz_real = lz_bytes(seqs_real)
lz_sh = [lz_bytes(shuffle_corpus()) for _ in range(NM)]
lz_m2 = [lz_bytes(markov_corpus(2, st2, tr2)) for _ in range(NM)]
mu_s = sum(lz_sh)/NM; sd_s = (sum((x-mu_s)**2 for x in lz_sh)/NM)**0.5
mu_m = sum(lz_m2)/NM; sd_m = (sum((x-mu_m)**2 for x in lz_m2)/NM)**0.5
print(f"\nlzma bytes: REAL={lz_real}  shuffle mean={mu_s:.0f} sd={sd_s:.1f} (z={(lz_real-mu_s)/sd_s:.1f})  order2-Markov mean={mu_m:.0f} sd={sd_m:.1f} (z={(lz_real-mu_m)/sd_m:.1f})")
print("\nDONE m2")
