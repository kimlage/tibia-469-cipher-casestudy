#!/usr/bin/env python3
"""STEP 3b: is homophone selection TEXT-KEYED (lexicon: word + index -> code)?

A) Determinism test: pairs of occurrences with IDENTICAL (word, index-in-word,
   symbol) but NON-IDENTICAL local digit context (so not verbatim module copies):
   how often do they agree on the code, vs within-(book,symbol) shuffle control?
B) LOBO predictive models with text features:
   MS1: P(c | s, prev_sym, next_sym)
   MS2: + 2-symbol context each side (backoff to MS1)
   MSW: P(c | word, idx) with backoff to order-2 code Markov (M2) -> the
        lexicon model. Plus residual diagnostics (miss autocorr, bookG) under MSW.
"""
import json
import math
import numpy as np
from collections import Counter, defaultdict

HC = "./tmp/audit_20260609/homophone_channel"
DBP = "./data/bonelord_operational.sqlite"
import sqlite3
con = sqlite3.connect(f"file:{DBP}?mode=ro", uri=True)
rows = con.execute("SELECT bookid, reconstructed_code_stream, decodedbase "
                   "FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
con.close()
print(f"rows: {len(rows)}"); assert len(rows) == 70

data = json.load(open(f"{HC}/occ_streams.json"))
class_codes = {s: v for s, v in data["class_sizes"].items() if len(v) >= 2}
SYMS = sorted(class_codes)

# flags from step1
flag = {}
for s, lst in data["occ"].items():
    for r in lst:
        flag[(r["book"], r["pos"])] = (r["novel"], r["xuniq"])

books = {}
for bid, stream, base in sorted(rows):
    books[bid] = (stream.split(), base)

# ---- build word structure per book
tokens = []
for bid in sorted(books):
    codes, base = books[bid]
    L = len(base)
    # word id and index within word ('*' = separator)
    words = []  # (start, end) exclusive of '*'
    i = 0
    while i < L:
        if base[i] == "*":
            i += 1; continue
        j = i
        while j < L and base[j] != "*":
            j += 1
        words.append((i, j))
        i = j
    for (a, b) in words:
        w = base[a:b]
        for k in range(a, b):
            s = base[k]
            if s not in class_codes:
                continue
            novel, xuniq = flag[(bid, k)]
            tokens.append(dict(book=bid, pos=k, sym=s, code=codes[k],
                               ci=class_codes[s].index(codes[k]),
                               word=w, widx=k - a, novel=novel, xuniq=xuniq,
                               p1=codes[k-1] if k >= 1 else "^",
                               p2=codes[k-2] if k >= 2 else "^",
                               ps=base[k-1] if k >= 1 else "^",
                               ns=base[k+1] if k+1 < L else "$",
                               ps2=base[max(0,k-2):k] or "^",
                               ns2=base[k+1:k+3] or "$",
                               dctx=None))
    # digit-free local code context for determinism test: surrounding codes
for t in tokens:
    codes, base = books[t["book"]]
    k = t["pos"]
    t["dctx"] = " ".join(codes[max(0, k-3):k] + ["_"] + codes[k+1:k+4])
N = len(tokens)
print(f"tokens: {N}")

# ================= A) determinism among non-copy repeats =================
rng = np.random.default_rng(4690)
key_groups = defaultdict(list)
for i, t in enumerate(tokens):
    key_groups[(t["word"], t["widx"])].append(i)

def agreement(get_code):
    agree = tot = 0
    agree_xb = tot_xb = 0
    for key, idxs in key_groups.items():
        if len(idxs) < 2:
            continue
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                ta, tb = tokens[idxs[a]], tokens[idxs[b]]
                if ta["dctx"] == tb["dctx"]:
                    continue  # likely verbatim copy context; exclude
                tot += 1
                if get_code(idxs[a]) == get_code(idxs[b]):
                    agree += 1
                if ta["book"] != tb["book"]:
                    tot_xb += 1
                    if get_code(idxs[a]) == get_code(idxs[b]):
                        agree_xb += 1
    return agree, tot, agree_xb, tot_xb

a_obs, t_obs, axb_obs, txb_obs = agreement(lambda i: tokens[i]["code"])
print(f"\nA) same-(word,idx) non-identical-context pairs: agree={a_obs}/{t_obs} "
      f"= {a_obs/max(1,t_obs):.4f}")
print(f"   cross-book only: agree={axb_obs}/{txb_obs} = {axb_obs/max(1,txb_obs):.4f}")

# shuffle control: permute codes within (book, symbol)
per_bs = defaultdict(list)
for i, t in enumerate(tokens):
    per_bs[(t["book"], t["sym"])].append(i)
ctl_a, ctl_axb = [], []
for c in range(200):
    perm_code = {}
    for key, idxs in per_bs.items():
        vals = [tokens[i]["code"] for i in idxs]
        rng.shuffle(vals)
        for i, v in zip(idxs, vals):
            perm_code[i] = v
    a, t_, axb, txb = agreement(lambda i: perm_code[i])
    ctl_a.append(a / max(1, t_)); ctl_axb.append(axb / max(1, txb))
for label, obs, ctl in (("all-pairs", a_obs / max(1, t_obs), ctl_a),
                        ("cross-book", axb_obs / max(1, txb_obs), ctl_axb)):
    v = np.array(ctl); m, sd = v.mean(), v.std(ddof=1)
    print(f"   {label}: obs={obs:.4f} ctl={m:.4f}+-{sd:.4f} z={(obs-m)/sd:+.2f}")

# ================= B) LOBO predictive with text features =================
book_to_idx = defaultdict(list)
for i, t in enumerate(tokens):
    book_to_idx[t["book"]].append(i)
BIDS = sorted(book_to_idx)

def freq_table(train_idx, alpha=0.5):
    cnt = {s: np.full(len(class_codes[s]), alpha) for s in SYMS}
    for i in train_idx:
        t = tokens[i]
        cnt[t["sym"]][t["ci"]] += 1
    return {s: v / v.sum() for s, v in cnt.items()}

def fit_counts(train_idx, key_fn):
    cnt = {}
    for i in train_idx:
        t = tokens[i]
        k = key_fn(t)
        if k not in cnt:
            cnt[k] = np.zeros(len(class_codes[t["sym"]]))
        cnt[k][t["ci"]] += 1
    return cnt

MODELS = ["MS1", "MS2", "MSW", "MSWM"]
preds = {m: [None] * N for m in MODELS}
for hb in BIDS:
    test_idx = book_to_idx[hb]
    train_idx = [i for b in BIDS if b != hb for i in book_to_idx[b]]
    f = freq_table(train_idx)
    cM1 = fit_counts(train_idx, lambda t: (t["sym"], t["p1"]))
    cM2 = fit_counts(train_idx, lambda t: (t["sym"], t["p1"], t["p2"]))
    cS1 = fit_counts(train_idx, lambda t: (t["sym"], t["ps"], t["ns"]))
    cS2 = fit_counts(train_idx, lambda t: (t["sym"], t["ps2"], t["ns2"]))
    cW = fit_counts(train_idx, lambda t: (t["word"], t["widx"]))

    def bk(cnt, key, base, a=1.0):
        c = cnt.get(key)
        if c is None:
            return base
        return (c + a * base) / (c.sum() + a)
    for i in test_idx:
        t = tokens[i]
        fv = f[t["sym"]]
        pm1 = bk(cM1, (t["sym"], t["p1"]), fv, 2.0)
        pm2 = bk(cM2, (t["sym"], t["p1"], t["p2"]), pm1, 1.0)
        ps1 = bk(cS1, (t["sym"], t["ps"], t["ns"]), fv, 2.0)
        ps2 = bk(cS2, (t["sym"], t["ps2"], t["ns2"]), ps1, 1.0)
        pw_f = bk(cW, (t["word"], t["widx"]), fv, 1.0)       # lexicon w/ freq backoff
        pw_m = bk(cW, (t["word"], t["widx"]), pm2, 1.0)      # lexicon w/ M2 backoff
        preds["MS1"][i] = ps1
        preds["MS2"][i] = ps2
        preds["MSW"][i] = pw_f
        preds["MSWM"][i] = pw_m

def evaluate(mask_fn, label):
    idx = [i for i in range(N) if mask_fn(tokens[i])]
    print(f"\n=== {label} (n={len(idx)}) ===")
    print(f"{'model':5} {'bits/choice':>11} {'top1':>7} {'total bits':>11}")
    out = {}
    for m in MODELS:
        bits = acc = 0.0
        for i in idx:
            p = preds[m][i]; ci = tokens[i]["ci"]
            bits += -math.log2(max(p[ci], 1e-12))
            acc += (np.argmax(p) == ci)
        out[m] = bits
        print(f"{m:5} {bits/len(idx):11.4f} {acc/len(idx):7.4f} {bits:11.1f}")
    return out

evaluate(lambda t: True, "ALL")
evaluate(lambda t: t["novel"], "NOVEL")
evaluate(lambda t: t["xuniq"], "XUNIQ")

# residual diagnostics under best lexicon model (MSWM): miss autocorr + bookG
best = "MSWM"
P = preds[best]
ci_arr = [t["ci"] for t in tokens]
miss = np.array([int(np.argmax(P[i]) != ci_arr[i]) for i in range(N)], float)
cum = [np.cumsum(np.asarray(P[i]) / np.asarray(P[i]).sum()) for i in range(N)]

def diag(miss_vec, idx):
    mv = miss_vec[idx]
    mm = mv - mv.mean()
    den = (mm * mm).sum()
    ac1 = (mm[:-1] * mm[1:]).sum() / den if den > 0 else 0
    bb = defaultdict(list)
    for j, i in enumerate(idx):
        bb[tokens[i]["book"]].append(mv[j])
    G = 0.0; pbar = mv.mean()
    for b, v in bb.items():
        n = len(v); k = sum(v)
        if n < 5: continue
        for kk, pp in ((k, pbar), (n - k, 1 - pbar)):
            if kk > 0 and pp > 0:
                G += 2 * kk * math.log(kk / (n * pp))
    return ac1, G

subsets = {"ALL": list(range(N)),
           "NOVEL": [i for i in range(N) if tokens[i]["novel"]],
           "XUNIQ": [i for i in range(N) if tokens[i]["xuniq"]]}
print(f"\nresidual diagnostics under {best} (200 model-sampled controls):")
for lab, idx in subsets.items():
    o_ac, o_G = diag(miss, idx)
    cs = []
    for c in range(200):
        rnd = rng.random(N)
        sim_miss = np.empty(N)
        for i in range(N):
            ci = min(int(np.searchsorted(cum[i], rnd[i])), len(cum[i]) - 1)
            sim_miss[i] = int(np.argmax(P[i]) != ci)
        cs.append(diag(sim_miss, idx))
    a = np.array([x[0] for x in cs]); g = np.array([x[1] for x in cs])
    print(f"  {lab}: ac1 obs={o_ac:.4f} ctl={a.mean():.4f}+-{a.std(ddof=1):.4f} "
          f"z={(o_ac-a.mean())/a.std(ddof=1):+.2f} | bookG obs={o_G:.1f} "
          f"ctl={g.mean():.1f}+-{g.std(ddof=1):.1f} z={(o_G-g.mean())/g.std(ddof=1):+.2f}")
