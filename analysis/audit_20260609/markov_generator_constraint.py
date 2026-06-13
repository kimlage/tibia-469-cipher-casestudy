#!/usr/bin/env python3
"""Generator-constraint hunt: order-1 Markov model over code tokens.

Tests whether digit-level anomalies (lag-1/4/6 self-repulsion, triple-run
ceiling, consecutive-code diff-mod-10 chi-square) are fully downstream of
code-stream statistics (bigrams) + per-code leading-zero omission rates.
"""
import json
import math
import random
import sqlite3
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
N_SYNTH = 200
N_SHUFFLE = 200
SEED = 469

# ---------------------------------------------------------------- load data
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

rows = cur.execute(
    "SELECT bookid, digits FROM sheet__books GROUP BY bookid"
).fetchall()
print(f"sheet__books deduped rows: {len(rows)}")
assert len(rows) == 70
digits_by_book = {bid: d for bid, d in rows}
total_digits = sum(len(d) for d in digits_by_book.values())
print(f"total digits: {total_digits}")
assert total_digits == 11263

rows = cur.execute(
    "SELECT bookid, reconstructed_code_stream, omitted_positions_json, "
    "omitted_codes_json, valid FROM row0_code_symbol_probe_books WHERE run_id=1"
).fetchall()
print(f"probe_books rows: {len(rows)}")
assert len(rows) == 70
streams = {}
omitted_pos = {}
for bid, stream, opos, ocodes, valid in rows:
    assert valid == 1
    streams[bid] = stream.split()
    omitted_pos[bid] = json.loads(opos)
total_tokens = sum(len(s) for s in streams.values())
print(f"total code tokens: {total_tokens}")
assert total_tokens == 5729

rows = cur.execute(
    "SELECT code, SUM(occurrence_count), SUM(omitted_count) "
    "FROM row0_code_symbol_counts WHERE run_id=1 GROUP BY code"
).fetchall()
print(f"code count rows (distinct codes): {len(rows)}")
omit_rate = {c: om / occ for c, occ, om in rows}
print(f"codes with omission>0: {sorted(c for c in omit_rate if omit_rate[c] > 0)}")
con.close()

# ------------------------------------------- verify rendering model exactly
def render(stream, omitted_idx_set_1based=None, omit_rate_map=None, rng=None):
    out = []
    for i, code in enumerate(stream):
        if omitted_idx_set_1based is not None:
            omit = (i + 1) in omitted_idx_set_1based
        else:
            r = omit_rate_map.get(code, 0.0)
            omit = r > 0 and rng.random() < r
        out.append(code[1] if omit else code)
    return "".join(out)

mismatch = 0
for bid in streams:
    rec = render(streams[bid], omitted_idx_set_1based=set(omitted_pos[bid]))
    if rec != digits_by_book[bid]:
        mismatch += 1
print(f"books where render(stream, omitted positions) != digits: {mismatch}")
assert mismatch == 0, "rendering model does not reproduce raw digits"

# ------------------------------------------------------- statistic functions
def digit_freqs(books):
    c = Counter()
    for d in books:
        c.update(d)
    n = sum(c.values())
    return {k: v / n for k, v in c.items()}, n

def lag_match_stats(books, lags=range(1, 9)):
    """Return per-lag (match_prob, n_pairs, z vs iid sum p^2)."""
    p, _ = digit_freqs(books)
    p2 = sum(v * v for v in p.values())
    res = {}
    for k in lags:
        m = n = 0
        for d in books:
            for i in range(len(d) - k):
                n += 1
                if d[i] == d[i + k]:
                    m += 1
        mp = m / n
        z = (m - n * p2) / math.sqrt(n * p2 * (1 - p2))
        res[k] = (mp, n, z)
    return res, p2

def run_counts(books):
    """Count maximal runs of identical digits of length exactly 3 and >=4."""
    t3 = t4 = 0
    for d in books:
        i = 0
        while i < len(d):
            j = i
            while j < len(d) and d[j] == d[i]:
                j += 1
            L = j - i
            if L == 3:
                t3 += 1
            elif L >= 4:
                t4 += 1
            i = j
    return t3, t4

def diff_mod10_chi2(streams_list, drop_top_bigrams=0):
    """Chi-square (df 9) of (next-cur) mod 10 over within-book code pairs.
    Optionally remove pairs belonging to the corpus's own top-N bigrams."""
    pairs = []
    for s in streams_list:
        for a, b in zip(s, s[1:]):
            pairs.append((a, b))
    if drop_top_bigrams:
        top = set(x for x, _ in Counter(pairs).most_common(drop_top_bigrams))
        pairs = [p for p in pairs if p not in top]
    cnt = Counter((int(b) - int(a)) % 10 for a, b in pairs)
    n = len(pairs)
    exp = n / 10.0
    chi2 = sum((cnt.get(r, 0) - exp) ** 2 / exp for r in range(10))
    return chi2, n, cnt

# ------------------------------------------------------------ observed stats
books_obs = [digits_by_book[b] for b in sorted(digits_by_book)]
streams_obs = [streams[b] for b in sorted(streams)]

p_obs, _ = digit_freqs(books_obs)
lag_obs, p2_obs = lag_match_stats(books_obs)
t3_obs, t4_obs = run_counts(books_obs)
chi_obs, npairs_obs, cnt_obs = diff_mod10_chi2(streams_obs)
chi_obs_d10, npairs_d10, _ = diff_mod10_chi2(streams_obs, drop_top_bigrams=10)

print("\n=== OBSERVED ===")
print(f"sum p^2 = {p2_obs:.4f}")
for k in range(1, 9):
    mp, n, z = lag_obs[k]
    print(f"lag {k}: match={mp:.4f} n={n} z_iid={z:+.2f}")
print(f"runs len==3: {t3_obs}, len>=4: {t4_obs}")
print(f"diff mod10 chi2 (df9): {chi_obs:.1f} over {npairs_obs} pairs")
print(f"  mod10 counts: {[cnt_obs.get(r,0) for r in range(10)]}")
print(f"diff mod10 chi2 after dropping top-10 bigrams: {chi_obs_d10:.1f} over {npairs_d10} pairs")

# --------------------------------------------- baseline shuffle controls
rng = random.Random(SEED)

# (1) digit shuffle within books -> iid baseline for runs & lag matches
sh_t3, sh_t4 = [], []
for _ in range(N_SHUFFLE):
    sh_books = []
    for d in books_obs:
        l = list(d)
        rng.shuffle(l)
        sh_books.append("".join(l))
    a, b = run_counts(sh_books)
    sh_t3.append(a)
    sh_t4.append(b)
mean3 = sum(sh_t3) / len(sh_t3)
mean4 = sum(sh_t4) / len(sh_t4)
sd3 = (sum((x - mean3) ** 2 for x in sh_t3) / (len(sh_t3) - 1)) ** 0.5
sd4 = (sum((x - mean4) ** 2 for x in sh_t4) / (len(sh_t4) - 1)) ** 0.5
print(f"\ndigit-shuffle baseline: triples {mean3:.1f}+-{sd3:.1f}, quads+ {mean4:.1f}+-{sd4:.1f}")
print(f"observed triples z vs shuffle: {(t3_obs-mean3)/sd3:+.2f}, quads z: {(t4_obs-mean4)/sd4:+.2f}")

# (2) code-token shuffle within books -> baseline for diff-mod10 chi2 (reproduce z=+7)
sh_chi = []
for _ in range(N_SHUFFLE):
    ss = []
    for s in streams_obs:
        l = list(s)
        rng.shuffle(l)
        ss.append(l)
    c, _, _ = diff_mod10_chi2(ss)
    sh_chi.append(c)
mc = sum(sh_chi) / len(sh_chi)
sc = (sum((x - mc) ** 2 for x in sh_chi) / (len(sh_chi) - 1)) ** 0.5
print(f"code-shuffle baseline chi2: {mc:.1f}+-{sc:.1f}; observed z vs shuffle: {(chi_obs-mc)/sc:+.2f}")

# ------------------------------------------------- fit order-1 Markov model
bigram = defaultdict(Counter)
unigram = Counter()
initials = Counter()
for s in streams_obs:
    initials[s[0]] += 1
    for a, b in zip(s, s[1:]):
        bigram[a][b] += 1
    unigram.update(s)

vocab = sorted(unigram)
uni_tokens = list(unigram.keys())
uni_weights = list(unigram.values())
init_tokens = list(initials.keys())
init_weights = list(initials.values())
trans = {}
for a, c in bigram.items():
    trans[a] = (list(c.keys()), list(c.values()))
n_bigram_types = sum(len(c) for c in bigram.values())
print(f"\nMarkov fit: {len(vocab)} codes, {n_bigram_types} bigram types, "
      f"{sum(sum(c.values()) for c in bigram.values())} bigram tokens")

book_lens = [len(s) for s in streams_obs]

def sample_corpus(rng):
    corpus = []
    for L in book_lens:
        tok = rng.choices(init_tokens, init_weights)[0]
        s = [tok]
        for _ in range(L - 1):
            if tok in trans:
                ks, ws = trans[tok]
                tok = rng.choices(ks, ws)[0]
            else:
                tok = rng.choices(uni_tokens, uni_weights)[0]
            s.append(tok)
        corpus.append(s)
    return corpus

# ------------------------------------------------- simulate synthetic corpora
synth = {
    "lag_mp": defaultdict(list), "lag_z": defaultdict(list),
    "t3": [], "t4": [], "chi": [], "chi_d10": [],
}
rng = random.Random(SEED + 1)
for it in range(N_SYNTH):
    corpus = sample_corpus(rng)
    books = [render(s, omit_rate_map=omit_rate, rng=rng) for s in corpus]
    lag_s, _ = lag_match_stats(books)
    for k in range(1, 9):
        synth["lag_mp"][k].append(lag_s[k][0])
        synth["lag_z"][k].append(lag_s[k][2])
    a, b = run_counts(books)
    synth["t3"].append(a)
    synth["t4"].append(b)
    c, _, _ = diff_mod10_chi2(corpus)
    synth["chi"].append(c)
    c2, _, _ = diff_mod10_chi2(corpus, drop_top_bigrams=10)
    synth["chi_d10"].append(c2)

def env(vals, obs, label, fmt="{:.4f}"):
    m = sum(vals) / len(vals)
    sd = (sum((x - m) ** 2 for x in vals) / (len(vals) - 1)) ** 0.5
    lo, hi = min(vals), max(vals)
    z = (obs - m) / sd if sd > 0 else float("nan")
    n_le = sum(1 for v in vals if v <= obs)
    n_ge = sum(1 for v in vals if v >= obs)
    p_emp = min(n_le, n_ge) / len(vals)  # one-sided empirical tail
    inside = lo <= obs <= hi
    print(f"{label}: obs={fmt.format(obs)} synth={fmt.format(m)}+-{fmt.format(sd)} "
          f"range[{fmt.format(lo)},{fmt.format(hi)}] z={z:+.2f} "
          f"tail_p={p_emp:.3f} inside_envelope={inside}")
    return z, p_emp, inside

print(f"\n=== SYNTHETIC ENVELOPE ({N_SYNTH} corpora, order-1 Markov + omission rates) ===")
results = {}
for k in range(1, 9):
    results[f"lag{k}_mp"] = env(synth["lag_mp"][k], lag_obs[k][0], f"lag{k} match_prob")
print()
for k in range(1, 9):
    results[f"lag{k}_z"] = env(synth["lag_z"][k], lag_obs[k][2], f"lag{k} z_iid", fmt="{:+.2f}")
print()
results["t3"] = env(synth["t3"], t3_obs, "triple runs", fmt="{:.1f}")
results["t4"] = env(synth["t4"], t4_obs, "quad+ runs", fmt="{:.1f}")
results["chi"] = env(synth["chi"], chi_obs, "diff-mod10 chi2", fmt="{:.1f}")
results["chi_d10"] = env(synth["chi_d10"], chi_obs_d10, "diff-mod10 chi2 (top10 bigrams dropped)", fmt="{:.1f}")

n_out = sum(1 for v in results.values() if not v[2])
print(f"\nstatistics outside synthetic envelope: {n_out}/{len(results)}")
print("outside:", [k for k, v in results.items() if not v[2]])
