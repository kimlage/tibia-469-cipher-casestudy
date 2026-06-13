#!/usr/bin/env python3
"""Follow-up: (1) order-2 Markov over codes - does it cover lag-3/4/6 residual?
(2) code-level diagnostics: same-code repetition at code-lags 1-3, tens/units
digit matches at code-lags 1-3, observed vs order-1 synthetic.
(3) digit-pair characterization of the lag-4/6 suppression and lag-3 enrichment.
"""
import json
import math
import random
import sqlite3
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
N_SYNTH = 200
SEED = 470

con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
rows = cur.execute(
    "SELECT bookid, reconstructed_code_stream FROM row0_code_symbol_probe_books "
    "WHERE run_id=1").fetchall()
print(f"probe rows: {len(rows)}"); assert len(rows) == 70
streams_obs = [r[1].split() for r in sorted(rows)]
rows = cur.execute(
    "SELECT code, SUM(occurrence_count), SUM(omitted_count) "
    "FROM row0_code_symbol_counts WHERE run_id=1 GROUP BY code").fetchall()
print(f"code rows: {len(rows)}"); assert len(rows) == 99
omit_rate = {c: om / occ for c, occ, om in rows}
con.close()

def render(stream, rng):
    out = []
    for code in stream:
        r = omit_rate.get(code, 0.0)
        out.append(code[1] if (r > 0 and rng.random() < r) else code)
    return "".join(out)

def digit_freqs(books):
    c = Counter()
    for d in books:
        c.update(d)
    n = sum(c.values())
    return {k: v / n for k, v in c.items()}

def lag_match(books, k):
    m = n = 0
    for d in books:
        for i in range(len(d) - k):
            n += 1
            if d[i] == d[i + k]:
                m += 1
    return m / n, m, n

def run_counts(books):
    t3 = t4 = 0
    for d in books:
        i = 0
        while i < len(d):
            j = i
            while j < len(d) and d[j] == d[i]:
                j += 1
            if j - i == 3: t3 += 1
            elif j - i >= 4: t4 += 1
            i = j
    return t3, t4

def code_lag_stats(streams_list, k):
    """(same-code rate, tens-digit match rate, units-digit match rate) at code lag k."""
    rep = tens = units = n = 0
    for s in streams_list:
        for i in range(len(s) - k):
            n += 1
            a, b = s[i], s[i + k]
            if a == b: rep += 1
            if a[0] == b[0]: tens += 1
            if a[1] == b[1]: units += 1
    return rep / n, tens / n, units / n, n

# ---------------- observed digit books (true omission positions) ----------
con = sqlite3.connect(DB, uri=True)
books_obs = [r[1] for r in sorted(con.execute(
    "SELECT bookid, digits FROM sheet__books GROUP BY bookid").fetchall())]
con.close()
assert sum(len(b) for b in books_obs) == 11263

print("\n=== observed code-level lag stats ===")
obs_code = {}
for k in (1, 2, 3):
    obs_code[k] = code_lag_stats(streams_obs, k)
    r, t, u, n = obs_code[k]
    print(f"code lag {k}: same-code={r:.4f} tens-match={t:.4f} units-match={u:.4f} n={n}")

# ---------------- order-1 model (for code-level + digit-pair residual) ----
big1 = defaultdict(Counter); uni = Counter(); init1 = Counter()
for s in streams_obs:
    init1[s[0]] += 1
    uni.update(s)
    for a, b in zip(s, s[1:]):
        big1[a][b] += 1
trans1 = {a: (list(c.keys()), list(c.values())) for a, c in big1.items()}
uk, uw = list(uni.keys()), list(uni.values())
i1k, i1w = list(init1.keys()), list(init1.values())
book_lens = [len(s) for s in streams_obs]

def sample1(rng):
    corpus = []
    for L in book_lens:
        t = rng.choices(i1k, i1w)[0]; s = [t]
        for _ in range(L - 1):
            if t in trans1:
                ks, ws = trans1[t]; t = rng.choices(ks, ws)[0]
            else:
                t = rng.choices(uk, uw)[0]
            s.append(t)
        corpus.append(s)
    return corpus

# ---------------- order-2 model ----------------
big2 = defaultdict(Counter); init2 = Counter()
for s in streams_obs:
    init2[(s[0], s[1])] += 1
    for i in range(len(s) - 2):
        big2[(s[i], s[i + 1])][s[i + 2]] += 1
trans2 = {ctx: (list(c.keys()), list(c.values())) for ctx, c in big2.items()}
i2k, i2w = list(init2.keys()), list(init2.values())
n_tri_types = sum(len(c) for c in big2.values())
n_tri_tokens = sum(sum(c.values()) for c in big2.values())
print(f"\norder-2 fit: {len(big2)} contexts, {n_tri_types} trigram types, {n_tri_tokens} trigram tokens")

def sample2(rng):
    corpus = []
    for L in book_lens:
        a, b = rng.choices(i2k, i2w)[0]
        s = [a, b]
        while len(s) < L:
            ctx = (s[-2], s[-1])
            if ctx in trans2:
                ks, ws = trans2[ctx]; nxt = rng.choices(ks, ws)[0]
            elif s[-1] in trans1:
                ks, ws = trans1[s[-1]]; nxt = rng.choices(ks, ws)[0]
            else:
                nxt = rng.choices(uk, uw)[0]
            s.append(nxt)
        corpus.append(s[:L])
    return corpus

# ---------------- simulate both models ----------------
def simulate(sampler, seed):
    rng = random.Random(seed)
    acc = defaultdict(list)
    pair_lag_counts = {3: Counter(), 4: Counter(), 6: Counter()}  # pooled synthetic digit pairs
    for it in range(N_SYNTH):
        corpus = sampler(rng)
        books = [render(s, rng) for s in corpus]
        for k in (1, 2, 3, 4, 5, 6, 7, 8):
            acc[f"mp{k}"].append(lag_match(books, k)[0])
        a, b = run_counts(books)
        acc["t3"].append(a); acc["t4"].append(b)
        for k in (1, 2, 3):
            r, t, u, n = code_lag_stats(corpus, k)
            acc[f"rep{k}"].append(r); acc[f"tens{k}"].append(t); acc[f"units{k}"].append(u)
        for k in (3, 4, 6):
            for d in books:
                for i in range(len(d) - k):
                    pair_lag_counts[k][(d[i], d[i + k])] += 1
    return acc, pair_lag_counts

def env(vals, obs, label, fmt="{:.4f}"):
    m = sum(vals) / len(vals)
    sd = (sum((x - m) ** 2 for x in vals) / (len(vals) - 1)) ** 0.5
    lo, hi = min(vals), max(vals)
    z = (obs - m) / sd if sd > 0 else float("nan")
    p = min(sum(1 for v in vals if v <= obs), sum(1 for v in vals if v >= obs)) / len(vals)
    print(f"{label}: obs={fmt.format(obs)} synth={fmt.format(m)}+-{fmt.format(sd)} "
          f"range[{fmt.format(lo)},{fmt.format(hi)}] z={z:+.2f} tail_p={p:.3f} inside={lo<=obs<=hi}")
    return lo <= obs <= hi

obs_mp = {k: lag_match(books_obs, k)[0] for k in range(1, 9)}
obs_t3, obs_t4 = run_counts(books_obs)

for name, sampler, seed in (("ORDER-1", sample1, SEED), ("ORDER-2", sample2, SEED + 1)):
    acc, plc = simulate(sampler, seed)
    print(f"\n=== {name} envelope ({N_SYNTH} corpora) ===")
    outside = []
    for k in range(1, 9):
        if not env(acc[f"mp{k}"], obs_mp[k], f"digit lag{k} match"): outside.append(f"mp{k}")
    if not env(acc["t3"], obs_t3, "triple runs", "{:.1f}"): outside.append("t3")
    if not env(acc["t4"], obs_t4, "quad+ runs", "{:.1f}"): outside.append("t4")
    for k in (1, 2, 3):
        r, t, u, n = obs_code[k]
        if not env(acc[f"rep{k}"], r, f"code lag{k} same-code"): outside.append(f"rep{k}")
        if not env(acc[f"tens{k}"], t, f"code lag{k} tens-match"): outside.append(f"tens{k}")
        if not env(acc[f"units{k}"], u, f"code lag{k} units-match"): outside.append(f"units{k}")
    print(f"{name} outside envelope: {outside}")
    if name == "ORDER-1":
        plc1 = plc  # keep for residual characterization

# ---------------- digit-pair residual characterization vs order-1 ----------
print("\n=== digit-pair residual vs ORDER-1 synthetic (per-pair z) ===")
for k in (3, 4, 6):
    obs_pairs = Counter()
    for d in books_obs:
        for i in range(len(d) - k):
            obs_pairs[(d[i], d[i + k])] += 1
    n_obs = sum(obs_pairs.values())
    n_syn = sum(plc1[k].values())
    zs = []
    for a in "0123456789":
        for b in "0123456789":
            e = plc1[k].get((a, b), 0) / N_SYNTH
            o = obs_pairs.get((a, b), 0)
            if e >= 5:
                z = (o - e) / math.sqrt(e)
                zs.append((z, a, b, o, e))
    zs.sort()
    diag = [(z, a, b, o, e) for (z, a, b, o, e) in zs if a == b]
    print(f"\nlag {k}: top-5 suppressed pairs (obs<exp):")
    for z, a, b, o, e in zs[:5]:
        print(f"  {a}->{b}: obs={o} exp={e:.1f} z={z:+.2f}")
    print(f"lag {k}: top-5 enriched pairs:")
    for z, a, b, o, e in zs[-5:]:
        print(f"  {a}->{b}: obs={o} exp={e:.1f} z={z:+.2f}")
    sdiag = sorted(diag)
    print(f"lag {k}: diagonal (d->d) z-scores: " +
          " ".join(f"{a}:{z:+.1f}" for z, a, b, o, e in sorted(diag, key=lambda x: x[1])))
