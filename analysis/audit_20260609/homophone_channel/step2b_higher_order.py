#!/usr/bin/env python3
"""STEP 2b: tighten the residual-capacity bound with higher-order CAUSAL
context models over the code stream (order-2, order-3 token context, with
backoff to order-1 -> frequency). LOBO as in step2. Also a combined
order-2 + recency-bucket model. Saves best-model held-out preds -> preds_best.npz
"""
import json
import math
import numpy as np
from collections import Counter, defaultdict

HC = "./tmp/audit_20260609/homophone_channel"
data = json.load(open(f"{HC}/occ_streams.json"))
class_codes = {s: v for s, v in data["class_sizes"].items() if len(v) >= 2}
SYMS = sorted(class_codes)

all_book_stream = defaultdict(list)
sym_of = {}
flags = {}
for s, lst in data["occ"].items():
    for r in lst:
        all_book_stream[r["book"]].append((r["pos"], r["code"], s, r["novel"], r["xuniq"]))
for b in all_book_stream:
    all_book_stream[b].sort()
BIDS = sorted(all_book_stream)

NB = 7
def bucket(d):
    if d is None: return 6
    if d <= 4: return d - 1
    if d <= 8: return 4
    return 5

tokens = []
for b in BIDS:
    seq = all_book_stream[b]
    last_use = {}
    for j, (pos, code, s, novel, xuniq) in enumerate(seq):
        if s not in class_codes:
            last = None
        prev1 = seq[j-1][1] if j >= 1 else "^"
        prev2 = seq[j-2][1] if j >= 2 else "^"
        prev3 = seq[j-3][1] if j >= 3 else "^"
        if s in class_codes:
            cl = class_codes[s]
            bks = [bucket(pos - last_use[(s, c)] if (s, c) in last_use else None) for c in cl]
            tokens.append(dict(book=b, pos=pos, sym=s, ci=cl.index(code),
                               novel=novel, xuniq=xuniq, bks=bks,
                               p1=prev1, p2=prev2, p3=prev3))
        if s in class_codes:
            last_use[(s, code)] = pos
N = len(tokens)
print(f"token records: {N}")
book_to_idx = defaultdict(list)
for i, t in enumerate(tokens):
    book_to_idx[t["book"]].append(i)

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
        k = (t["sym"],) + key_fn(t)
        if k not in cnt:
            cnt[k] = np.zeros(len(class_codes[t["sym"]]))
        cnt[k][t["ci"]] += 1
    return cnt

A1, A2_, A3 = 2.0, 1.0, 1.0
MODELS = ["M1", "M2", "M3", "M2R"]
preds = {m: [None] * N for m in MODELS}

def fit_bucket_weights_vec(groups, iters=250, lr=1.0):
    w = np.zeros(NB)
    ntot = sum(g[0].shape[0] for g in groups)
    if ntot < 50:
        return w
    for it in range(iters):
        g = np.zeros(NB)
        for off, bks, ci in groups:
            z = off + w[bks]
            z -= z.max(axis=1, keepdims=True)
            p = np.exp(z); p /= p.sum(axis=1, keepdims=True)
            np.add.at(g, bks[np.arange(len(ci)), ci], 1.0)
            np.add.at(g, bks.ravel(), -p.ravel())
        w += lr * g / ntot
        w -= w.mean()
    return w

for fold_n, hb in enumerate(BIDS):
    test_idx = book_to_idx[hb]
    if not test_idx:
        continue
    train_idx = [i for b in BIDS if b != hb for i in book_to_idx[b]]
    f = freq_table(train_idx)
    c1 = fit_counts(train_idx, lambda t: (t["p1"],))
    c2 = fit_counts(train_idx, lambda t: (t["p1"], t["p2"]))
    c3 = fit_counts(train_idx, lambda t: (t["p1"], t["p2"], t["p3"]))

    def p1(t):
        c = c1.get((t["sym"], t["p1"]))
        fv = f[t["sym"]]
        if c is None: return fv
        return (c + A1 * fv) / (c.sum() + A1)
    def p2(t):
        c = c2.get((t["sym"], t["p1"], t["p2"]))
        b = p1(t)
        if c is None: return b
        return (c + A2_ * b) / (c.sum() + A2_)
    def p3(t):
        c = c3.get((t["sym"], t["p1"], t["p2"], t["p3"]))
        b = p2(t)
        if c is None: return b
        return (c + A3 * b) / (c.sum() + A3)

    # M2R: order-2 logits + recency bucket weights
    by_sym = defaultdict(list)
    for i in train_idx:
        by_sym[tokens[i]["sym"]].append(i)
    groups = []
    for s, idx in by_sym.items():
        off = np.array([np.log(np.maximum(p2(tokens[i]), 1e-12)) for i in idx])
        bks = np.array([tokens[i]["bks"] for i in idx])
        ci = np.array([tokens[i]["ci"] for i in idx])
        groups.append((off, bks, ci))
    w2 = fit_bucket_weights_vec(groups)

    for i in test_idx:
        t = tokens[i]
        preds["M1"][i] = p1(t)
        preds["M2"][i] = p2(t)
        preds["M3"][i] = p3(t)
        z = np.log(np.maximum(p2(t), 1e-12)) + w2[np.array(t["bks"])]
        z -= z.max(); p = np.exp(z)
        preds["M2R"][i] = p / p.sum()
    if fold_n % 20 == 0:
        print(f"fold {fold_n} done (book {hb}); bucket w2={np.round(w2,3)}")

def evaluate(mask_fn, label):
    idx = [i for i in range(N) if mask_fn(tokens[i])]
    print(f"\n=== {label} (n={len(idx)}) ===")
    print(f"{'model':5} {'bits/choice':>11} {'top1':>7} {'total bits':>11}")
    for m in MODELS:
        bits = acc = 0.0
        for i in idx:
            p = preds[m][i]; ci = tokens[i]["ci"]
            bits += -math.log2(max(p[ci], 1e-12))
            acc += (np.argmax(p) == ci)
        print(f"{m:5} {bits/len(idx):11.4f} {acc/len(idx):7.4f} {bits:11.1f}")

evaluate(lambda t: True, "ALL multi-class tokens")
evaluate(lambda t: t["novel"], "NOVEL only")
evaluate(lambda t: t["xuniq"], "XUNIQ only")

np.savez_compressed(f"{HC}/preds2.npz",
                    **{m: np.array(preds[m], dtype=object) for m in MODELS})
print("saved preds2.npz")
