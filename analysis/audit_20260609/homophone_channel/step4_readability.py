#!/usr/bin/env python3
"""STEP 4: try to READ the homophone-selection channel.

Streams tested (corpus order = book sorted, pos sorted):
  S1  merged binary of class-size-2 symbols (B,C,O,R,S): 0=lower code,1=higher
  S2a binary stream of B alone; S2b of S alone
  S3  all multi-class symbols: freq-rank choice index mod 2 -> bits
  S4  per-symbol choice-index distribution vs English letter profile (sorted chi2)
  S5  residual stream under best mechanical rule M2R: miss bits (rank>0), rank mod 2
  S6  digit re-expansion: rank%10 digits -> 2-digit codes -> symbol letters

Per bitstream: monobit bias, runs test, 5-bit Baconian -> letter chi2 vs
English+German letter freqs, IoC, 7-bit/8-bit printable ASCII fraction.
Controls: S1-S4,S6 -> 200 within-(book,symbol) code shuffles; S5 -> 200
model-sampled corpora. Positive needs |z|>=3 (right direction) on FULL and NOVEL.
"""
import json
import math
import numpy as np
from collections import Counter, defaultdict

HC = "./tmp/audit_20260609/homophone_channel"
data = json.load(open(f"{HC}/occ_streams.json"))
class_codes = {s: v for s, v in data["class_sizes"].items() if len(v) >= 2}
SYMS = sorted(class_codes)

# token table in corpus order
tokens = []
per_book_sym = defaultdict(list)  # (book, sym) -> token indices (for shuffling)
tmp = defaultdict(list)
for s, lst in data["occ"].items():
    if s not in class_codes:
        continue
    for r in lst:
        tmp[r["book"]].append((r["pos"], s, class_codes[s].index(r["code"]),
                               r["novel"], r["xuniq"]))
for b in sorted(tmp):
    for rec in sorted(tmp[b]):
        tokens.append((b,) + rec)
N = len(tokens)
for i, t in enumerate(tokens):
    per_book_sym[(t[0], t[2])].append(i)
print(f"tokens: {N}")

# frequency-rank maps (global)
freq_rank = {}
cnt = {s: Counter() for s in SYMS}
for t in tokens:
    cnt[t[2]][t[3]] += 1
for s in SYMS:
    order = sorted(range(len(class_codes[s])), key=lambda ci: -cnt[s][ci])
    fr = {ci: r for r, ci in enumerate(order)}
    freq_rank[s] = fr

ENG = {'E':12.70,'T':9.06,'A':8.17,'O':7.51,'I':6.97,'N':6.75,'S':6.33,'H':6.09,
 'R':5.99,'D':4.25,'L':4.03,'C':2.78,'U':2.76,'M':2.41,'W':2.36,'F':2.23,
 'G':2.02,'Y':1.97,'P':1.93,'B':1.49,'V':0.98,'K':0.77,'J':0.15,'X':0.15,
 'Q':0.10,'Z':0.07}
GER = {'E':16.40,'N':9.78,'S':7.27,'R':7.00,'I':6.55,'A':6.52,'T':6.15,'D':5.08,
 'H':4.58,'U':4.17,'L':3.44,'C':3.06,'G':3.01,'M':2.53,'O':2.51,'B':1.89,
 'W':1.92,'F':1.66,'K':1.21,'Z':1.13,'P':0.79,'V':0.67,'J':0.27,'Y':0.04,
 'X':0.03,'Q':0.02}
def norm(d):
    t = sum(d.values()); return {k: v / t for k, v in d.items()}
ENG, GER = norm(ENG), norm(GER)

def bit_battery(bits):
    """bits: np array of 0/1. Returns dict of stats."""
    n = len(bits)
    out = {}
    out["bias"] = abs(bits.mean() - 0.5)
    # runs test z
    n1 = bits.sum(); n0 = n - n1
    runs = 1 + int(np.sum(bits[1:] != bits[:-1])) if n > 1 else 1
    if n0 > 0 and n1 > 0:
        mu = 1 + 2 * n0 * n1 / n
        var = 2 * n0 * n1 * (2 * n0 * n1 - n) / (n * n * (n - 1))
        out["runs_z_abs"] = abs((runs - mu) / math.sqrt(var)) if var > 0 else 0.0
    else:
        out["runs_z_abs"] = 0.0
    # Baconian 5-bit (both bit orders)
    for tag, bb in (("fwd", bits), ("rev", bits[::-1])):
        letters = []
        for i in range(0, len(bb) - 4, 5):
            v = int("".join(str(int(x)) for x in bb[i:i+5]), 2)
            if v < 26:
                letters.append(chr(65 + v))
        if len(letters) >= 20:
            c = Counter(letters); L = len(letters)
            chiE = sum((c.get(k, 0) - L * p) ** 2 / (L * p) for k, p in ENG.items())
            chiG = sum((c.get(k, 0) - L * p) ** 2 / (L * p) for k, p in GER.items())
            ioc = sum(v * (v - 1) for v in c.values()) / (L * (L - 1)) if L > 1 else 0
            out[f"bacon_{tag}_chiE"] = chiE
            out[f"bacon_{tag}_chiG"] = chiG
            out[f"bacon_{tag}_ioc"] = ioc
            out[f"bacon_{tag}_valid"] = len(letters) / max(1, (len(bb) // 5))
    # 7/8-bit printable
    for w in (7, 8):
        chars = []
        for i in range(0, len(bits) - w + 1, w):
            v = int("".join(str(int(x)) for x in bits[i:i+w]), 2)
            chars.append(v)
        if len(chars) >= 10:
            out[f"print{w}"] = float(np.mean([32 <= v < 127 for v in chars]))
    return out

def letter_battery(letters):
    c = Counter(letters); L = len(letters)
    out = {}
    if L < 20:
        return out
    chiE = sum((c.get(k, 0) - L * p) ** 2 / (L * p) for k, p in ENG.items())
    chiG = sum((c.get(k, 0) - L * p) ** 2 / (L * p) for k, p in GER.items())
    ioc = sum(v * (v - 1) for v in c.values()) / (L * (L - 1))
    out["chiE"] = chiE; out["chiG"] = chiG; out["ioc"] = ioc
    return out

# ---- stream builders, given a ci-assignment vector (len N)
CODE2SYM = {}
for s, lst in data["class_sizes"].items():
    for c in lst:
        CODE2SYM[c] = s

def build_streams(ci_vec, mask=None):
    """returns dict name->stats computed via batteries."""
    use = [i for i in range(N) if mask is None or mask[i]]
    res = {}
    # S1
    bits = np.array([ci_vec[i] for i in use if len(class_codes[tokens[i][2]]) == 2])
    if len(bits) >= 30:
        for k, v in bit_battery(bits).items():
            res[f"S1_{k}"] = v
    # S2 B and S
    for s in ("B", "S"):
        bs = np.array([ci_vec[i] for i in use if tokens[i][2] == s])
        if len(bs) >= 30:
            for k, v in bit_battery(bs).items():
                res[f"S2{s}_{k}"] = v
    # S3 freq-rank mod 2
    bits = np.array([freq_rank[tokens[i][2]][ci_vec[i]] % 2 for i in use])
    for k, v in bit_battery(bits).items():
        res[f"S3_{k}"] = v
    # S4: per big symbol, sorted-profile chi2 vs English sorted profile
    for s in ("E", "I", "N", "T", "A"):
        v = [ci_vec[i] for i in use if tokens[i][2] == s]
        if len(v) < 50:
            continue
        c = Counter(v); L = len(v)
        prof = sorted((x / L for x in c.values()), reverse=True)
        eng = sorted(ENG.values(), reverse=True)[:len(class_codes[s])]
        eng = [x / sum(eng) for x in eng]
        prof += [0.0] * (len(eng) - len(prof))
        chi = sum((p - q) ** 2 / q for p, q in zip(prof, eng))
        res[f"S4_{s}_profchi"] = chi * L
    # S6 digit re-expansion: rank%10 -> digits -> 2-digit codes -> symbols
    digs = "".join(str(freq_rank[tokens[i][2]][ci_vec[i]] % 10) for i in use)
    letters = []
    for i in range(0, len(digs) - 1, 2):
        sym = CODE2SYM.get(digs[i:i+2])
        if sym and sym != "*":
            letters.append(sym)
    for k, v in letter_battery(letters).items():
        res[f"S6_{k}"] = v
    res["S6_mapfrac"] = len(letters) / max(1, len(digs) // 2)
    return res

ci_obs = np.array([t[3] for t in tokens])
novel_mask = np.array([t[4] for t in tokens])

rng = np.random.default_rng(46910)
NCTL = 200

def shuffle_ci():
    new = ci_obs.copy()
    for key, idxs in per_book_sym.items():
        vals = ci_obs[idxs].copy()
        rng.shuffle(vals)
        new[idxs] = vals
    return new

for label, mask in (("FULL", None), ("NOVEL", novel_mask)):
    obs = build_streams(ci_obs, mask)
    ctl = defaultdict(list)
    for c in range(NCTL):
        st = build_streams(shuffle_ci(), mask)
        for k, v in st.items():
            ctl[k].append(v)
    print(f"\n===== RAW-CHOICE READABILITY, {label} =====")
    hits = []
    for k in sorted(obs):
        vals = np.array(ctl[k])
        if len(vals) < 50:
            continue
        m, sd = vals.mean(), vals.std(ddof=1)
        z = (obs[k] - m) / sd if sd > 0 else float("nan")
        mark = ""
        # direction of interest: lower chi2 / higher ioc-toward-0.066 / extreme bias/runs/printable
        if abs(z) >= 3:
            mark = " ***"
            hits.append((k, z))
        print(f"  {k:22} obs={obs[k]:9.4f} ctl={m:9.4f}+-{sd:8.4f} z={z:+6.2f}{mark}")
    print(f"  |z|>=3 hits: {hits}")

# ---- S5: residual-rank streams under M2R with model-sampled controls
print("\n===== S5 RESIDUAL-RANK READABILITY (M2R, model-sampled controls) =====")
p2 = np.load(f"{HC}/preds2.npz", allow_pickle=True)
P = p2["M2R"]
rank_t, cum_t = [], []
for i in range(N):
    p = np.asarray(P[i], dtype=float); p = p / p.sum()
    order = np.argsort(-p, kind="stable")
    rk = np.empty(len(p), dtype=np.int32); rk[order] = np.arange(len(p))
    rank_t.append(rk); cum_t.append(np.cumsum(p))

def s5_stats(ci_vec, mask=None):
    use = [i for i in range(N) if mask is None or mask[i]]
    r = np.array([rank_t[i][ci_vec[i]] for i in use])
    res = {}
    for k, v in bit_battery((r > 0).astype(int)).items():
        res[f"miss_{k}"] = v
    for k, v in bit_battery((r % 2).astype(int)).items():
        res[f"rmod2_{k}"] = v
    # rank stream as letters (rank -> A+rank, capped 25)
    letters = [chr(65 + min(int(x), 25)) for x in r]
    for k, v in letter_battery(letters).items():
        res[f"rlet_{k}"] = v
    return res

for label, mask in (("FULL", None), ("NOVEL", novel_mask)):
    obs = s5_stats(ci_obs, mask)
    ctl = defaultdict(list)
    for c in range(NCTL):
        rnd = rng.random(N)
        ci_sim = np.array([min(int(np.searchsorted(cum_t[i], rnd[i])), len(cum_t[i]) - 1)
                           for i in range(N)])
        st = s5_stats(ci_sim, mask)
        for k, v in st.items():
            ctl[k].append(v)
    print(f"\n-- S5 {label}")
    hits = []
    for k in sorted(obs):
        vals = np.array(ctl[k])
        m, sd = vals.mean(), vals.std(ddof=1)
        z = (obs[k] - m) / sd if sd > 0 else float("nan")
        mark = ""
        if abs(z) >= 3:
            mark = " ***"
            hits.append((k, round(z, 2)))
        print(f"  {k:22} obs={obs[k]:9.4f} ctl={m:9.4f}+-{sd:8.4f} z={z:+6.2f}{mark}")
    print(f"  |z|>=3 hits: {hits}")
