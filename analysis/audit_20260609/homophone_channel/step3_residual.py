#!/usr/bin/env python3
"""STEP 3: residual information after best mechanical rules.

Residual stream: per-token rank r_i of the chosen code under the held-out
predictive distribution (0 = model's top choice), plus PIT u_i.
Controls: 200 corpora sampled from the SAME held-out predictive distributions
(token-wise independent given model), pushed through identical statistics.

Tests (each on ALL / NOVEL / XUNIQ token subsets, models M2R and M1):
  T1 lzma + zlib compressed size of rank byte stream
  T2 mean log-loss (sanity: obs vs control distribution)
  T3 autocorrelation of miss indicator (r>0) lags 1..10 (report max |z|)
  T4 per-book hit-rate heterogeneity (G-statistic)
  T5 PIT u_i: KS distance from uniform; lag-1 autocorr of u
Decision: structure requires |z|>=3 on FULL AND on NOVEL (dedupe).
"""
import json
import lzma
import math
import zlib
import numpy as np
from collections import defaultdict

HC = "./tmp/audit_20260609/homophone_channel"
data = json.load(open(f"{HC}/occ_streams.json"))
class_codes = {s: v for s, v in data["class_sizes"].items() if len(v) >= 2}

stream = defaultdict(list)
for s, lst in data["occ"].items():
    if s not in class_codes:
        continue
    for r in lst:
        stream[r["book"]].append((r["pos"], s, class_codes[s].index(r["code"]),
                                  r["novel"], r["xuniq"]))
tokens = []
for b in sorted(stream):
    for rec in sorted(stream[b]):
        tokens.append((b,) + rec)
N = len(tokens)
print(f"tokens: {N}")

p1 = np.load(f"{HC}/preds.npz", allow_pickle=True)
p2 = np.load(f"{HC}/preds2.npz", allow_pickle=True)
PREDS = {"M1": p1["E"], "M2R": p2["M2R"]}
for m, P in PREDS.items():
    assert len(P) == N, (m, len(P))

rng = np.random.default_rng(20260610)
NCTL = 200

def build_tables(P):
    """per token: rank_table[ci], u_table[ci], logp_table[ci], cum for sampling"""
    rank_t, u_t, lp_t, cum_t = [], [], [], []
    for i in range(N):
        p = np.asarray(P[i], dtype=float)
        p = p / p.sum()
        order = np.argsort(-p, kind="stable")
        rk = np.empty(len(p), dtype=np.int32)
        rk[order] = np.arange(len(p))
        u = np.array([p[p > p[ci]].sum() + 0.5 * p[ci] for ci in range(len(p))])
        rank_t.append(rk)
        u_t.append(u)
        lp_t.append(-np.log2(np.maximum(p, 1e-12)))
        cum_t.append(np.cumsum(p))
    return rank_t, u_t, lp_t, cum_t

def stats_suite(r, u, ll, idx):
    """compute test statistics on subset idx; r,u,ll are full-length arrays."""
    rr = r[idx]
    uu = u[idx]
    by = bytes(int(min(x, 255)) for x in rr)
    out = {}
    out["lzma"] = len(lzma.compress(by, preset=6))
    out["zlib"] = len(zlib.compress(by, 9))
    out["logloss"] = float(np.mean(ll[idx]))
    miss = (rr > 0).astype(float)
    mm = miss - miss.mean()
    denom = (mm * mm).sum()
    acs = []
    for lag in range(1, 11):
        acs.append((mm[:-lag] * mm[lag:]).sum() / denom if denom > 0 else 0.0)
    out["ac_max"] = float(max(abs(a) for a in acs))
    out["ac1"] = float(acs[0])
    # per-book G of hit rate
    books = defaultdict(list)
    for j, i in enumerate(idx):
        books[tokens[i][0]].append(miss[j])
    G = 0.0
    pbar = miss.mean()
    for b, v in books.items():
        n = len(v); k = sum(v)
        if n < 5:
            continue
        for kk, pp in ((k, pbar), (n - k, 1 - pbar)):
            if kk > 0 and pp > 0:
                G += 2 * kk * math.log(kk / (n * pp))
    out["bookG"] = G
    # PIT KS + lag1 autocorr
    us = np.sort(uu)
    grid = (np.arange(len(us)) + 1) / len(us)
    out["pit_ks"] = float(np.max(np.abs(us - grid)))
    uc = uu - uu.mean()
    out["pit_ac1"] = float((uc[:-1] * uc[1:]).sum() / (uc * uc).sum())
    return out

def run_model(mname):
    P = PREDS[mname]
    ci_arr = np.array([t[3] for t in tokens])
    rank_t, u_t, lp_t, cum_t = build_tables(P)

    def streams_for(ci_vec):
        r = np.array([rank_t[i][ci_vec[i]] for i in range(N)])
        u = np.array([u_t[i][ci_vec[i]] for i in range(N)])
        ll = np.array([lp_t[i][ci_vec[i]] for i in range(N)])
        return r, u, ll

    r_obs, u_obs, ll_obs = streams_for(ci_arr)
    subsets = {
        "ALL": list(range(N)),
        "NOVEL": [i for i in range(N) if tokens[i][4]],
        "XUNIQ": [i for i in range(N) if tokens[i][5]],
    }
    obs = {k: stats_suite(r_obs, u_obs, ll_obs, v) for k, v in subsets.items()}

    # controls: sample ci from P token-wise (independent given model)
    ctl = {k: defaultdict(list) for k in subsets}
    for c in range(NCTL):
        rnd = rng.random(N)
        ci_sim = np.array([int(np.searchsorted(cum_t[i], rnd[i])) for i in range(N)])
        ci_sim = np.minimum(ci_sim, [len(cum_t[i]) - 1 for i in range(N)])
        r_s, u_s, ll_s = streams_for(ci_sim)
        for k, v in subsets.items():
            st = stats_suite(r_s, u_s, ll_s, v)
            for key, val in st.items():
                ctl[k][key].append(val)
        if c % 50 == 0:
            print(f"  control {c}/{NCTL}")

    print(f"\n===== MODEL {mname} =====")
    results = {}
    for k in subsets:
        print(f"-- subset {k} (n={len(subsets[k])})")
        for key in obs[k]:
            vals = np.array(ctl[k][key])
            m, sd = vals.mean(), vals.std(ddof=1)
            z = (obs[k][key] - m) / sd if sd > 0 else float("nan")
            lo = np.percentile(vals, 0.5); hi = np.percentile(vals, 99.5)
            print(f"   {key:8} obs={obs[k][key]:10.4f} ctl={m:10.4f}+-{sd:8.4f} "
                  f"z={z:+7.2f} ctl99%[{lo:.3f},{hi:.3f}]")
            results[(k, key)] = z
    return results

resM1 = run_model("M1")
resM2R = run_model("M2R")

print("\n=== SUMMARY: tests with |z|>=3 on FULL and NOVEL (pre-registered) ===")
for mname, res in (("M1", resM1), ("M2R", resM2R)):
    for key in ["lzma", "zlib", "logloss", "ac_max", "ac1", "bookG", "pit_ks", "pit_ac1"]:
        za = res.get(("ALL", key)); zn = res.get(("NOVEL", key)); zx = res.get(("XUNIQ", key))
        flag = abs(za) >= 3 and abs(zn) >= 3
        print(f"{mname:4} {key:8} zALL={za:+6.2f} zNOVEL={zn:+6.2f} zXUNIQ={zx:+6.2f} "
              f"{'<-- SURVIVES' if flag else ''}")
