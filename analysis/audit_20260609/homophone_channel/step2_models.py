#!/usr/bin/env python3
"""STEP 2: Fit candidate homophone-selection rules, rank by leave-one-book-out
(LOBO) predictive performance (bits/choice, top-1 acc).

Models (all produce P(code | symbol, history) over the symbol's class):
  F  null: per-symbol train code frequencies
  A  recency-bucket: P ∝ f_c * exp(w[bucket(dist-since-last-use of c)])
  A2 recency-bucket per-symbol weights (big symbols), global fallback
  B  cyclic rotation (numeric / freq order) with fitted slip prob
  C  LRU deterministic with fitted slip prob
  D  position-keyed Gronsfeld: P(c | s, pos mod k), k chosen by inner CV
  E  prev-token Markov: P(c | s, prev code token) with backoff to f
  E2 same-symbol Markov: P(c | s, prev same-symbol code) with backoff
  AE Markov(E) x recency bucket weights

Saves held-out per-token predictions of every model -> preds.npz for step 3/4.
Metrics reported on: ALL multi-class tokens, NOVEL only, XUNIQ only.
"""
import json
import math
import numpy as np
from collections import Counter, defaultdict

HC = "./tmp/audit_20260609/homophone_channel"
data = json.load(open(f"{HC}/occ_streams.json"))
class_codes = {s: v for s, v in data["class_sizes"].items() if len(v) >= 2}
SYMS = sorted(class_codes)

# ---- flatten tokens (multi-class only), per book ordered by pos
# token record: (book, pos, sym, code_idx_in_class, occ_idx_within_book_sym,
#                novel, xuniq, prev_token_code(any sym) or None,
#                buckets per candidate, prev_same_sym_code_idx or -1)
books_tokens = defaultdict(list)  # bid -> [(pos, sym, code)] all multi tokens
all_book_stream = defaultdict(list)  # bid -> [(pos, code)] ALL tokens incl '*'
for s, lst in data["occ"].items():
    for r in lst:
        all_book_stream[r["book"]].append((r["pos"], r["code"]))
        if s in class_codes:
            books_tokens[r["book"]].append((r["pos"], s, r["code"], r["novel"], r["xuniq"]))
for b in all_book_stream:
    all_book_stream[b].sort()
    books_tokens[b].sort()

BIDS = sorted(all_book_stream)
print(f"books: {len(BIDS)}; multi-class tokens: {sum(len(v) for v in books_tokens.values())}")

NB = 7  # buckets: d=1,2,3,4,5-8,9+,never
def bucket(d):
    if d is None: return 6
    if d <= 4: return d - 1
    if d <= 8: return 4
    return 5

tokens = []  # global list of dicts
for b in BIDS:
    pos2code = dict(all_book_stream[b])
    last_use = {}   # (sym, code) -> pos
    last_sym_code = {}  # sym -> last code used
    occ_ix = Counter()
    for (pos, s, code, novel, xuniq) in books_tokens[b]:
        cl = class_codes[s]
        bks = [bucket(pos - last_use[(s, c)] if (s, c) in last_use else None) for c in cl]
        dists = [(pos - last_use[(s, c)]) if (s, c) in last_use else 10**9 for c in cl]
        prev_tok = pos2code.get(pos - 1)  # immediately preceding token code (any symbol)
        tokens.append(dict(book=b, pos=pos, sym=s, ci=cl.index(code),
                           novel=novel, xuniq=xuniq, bks=bks, dists=dists,
                           prev=prev_tok, prev_ss=last_sym_code.get(s, None),
                           occ=occ_ix[s]))
        occ_ix[s] += 1
        last_use[(s, code)] = pos
        last_sym_code[s] = code
N = len(tokens)
print(f"token records: {N}")
n_novel = sum(t["novel"] for t in tokens); n_xu = sum(t["xuniq"] for t in tokens)
print(f"novel: {n_novel}, xuniq: {n_xu}")

# ---------------------------------------------------------------- model fits
def freq_table(train_idx, alpha=0.5):
    cnt = {s: np.full(len(class_codes[s]), alpha) for s in SYMS}
    for i in train_idx:
        t = tokens[i]
        cnt[t["sym"]][t["ci"]] += 1
    return {s: v / v.sum() for s, v in cnt.items()}

def fit_bucket_weights_vec(groups, iters=250, lr=1.0):
    """ML fit of w[NB]. groups: list of (offset_logits[n,K], bks[n,K], ci[n]).
    Vectorized gradient ascent."""
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

def make_groups(train_idx, offset_fn, per_sym=None):
    """Group train tokens by symbol into arrays for fit_bucket_weights_vec.
    offset_fn(t) -> offset logit vector for token t."""
    by_sym = defaultdict(list)
    for i in train_idx:
        t = tokens[i]
        if per_sym is None or t["sym"] == per_sym:
            by_sym[t["sym"]].append(i)
    groups = []
    for s, idx in by_sym.items():
        off = np.array([offset_fn(tokens[i]) for i in idx])
        bks = np.array([tokens[i]["bks"] for i in idx])
        ci = np.array([tokens[i]["ci"] for i in idx])
        groups.append((off, bks, ci))
    return groups

def softmax_pred(lf, w, bks):
    z = lf + w[bks]; z -= z.max()
    p = np.exp(z); return p / p.sum()

def fit_markov(train_idx, key_fn, alpha=2.0):
    """counts[(sym, key)] -> array over class; predict (cnt + alpha*f)/(tot+alpha)."""
    cnt = defaultdict(lambda: None)
    for i in train_idx:
        t = tokens[i]
        k = (t["sym"], key_fn(t))
        if cnt[k] is None:
            cnt[k] = np.zeros(len(class_codes[t["sym"]]))
        cnt[k][t["ci"]] += 1
    return dict(cnt)

def markov_pred(cnt, f, t, key, alpha=2.0):
    c = cnt.get((t["sym"], key))
    fv = f[t["sym"]]
    if c is None:
        return fv
    return (c + alpha * fv) / (c.sum() + alpha)

def fit_gronsfeld(train_idx, f, k, alpha=0.5):
    cnt = {}
    for i in train_idx:
        t = tokens[i]
        kk = (t["sym"], t["pos"] % k)
        if kk not in cnt:
            cnt[kk] = np.full(len(class_codes[t["sym"]]), alpha)
        cnt[kk][t["ci"]] += 1
    return cnt

def grons_pred(cnt, f, t, k):
    c = cnt.get((t["sym"], t["pos"] % k))
    return (c / c.sum()) if c is not None else f[t["sym"]]

def fit_slip(train_idx, pred_fn):
    """accuracy of deterministic predictor on train, per symbol."""
    hit = Counter(); tot = Counter()
    for i in train_idx:
        t = tokens[i]
        p = pred_fn(t)
        tot[t["sym"]] += 1
        if p == t["ci"]:
            hit[t["sym"]] += 1
    return {s: (hit[s] + 1) / (tot[s] + 2) for s in SYMS}

def det_to_prob(pred_ci, acc, f_s):
    n = len(f_s)
    p = np.array(f_s) * (1 - acc)
    rest = p.sum() - p[pred_ci]
    out = np.empty(n)
    for j in range(n):
        out[j] = acc if j == pred_ci else (1 - acc) * f_s[j] / (f_s.sum() - f_s[pred_ci] + 1e-12) * (1 - 0)  # renorm below
    out[pred_ci] = acc
    mask = np.ones(n, bool); mask[pred_ci] = False
    out[mask] = (1 - acc) * (np.array(f_s)[mask] / np.array(f_s)[mask].sum())
    return out

def cyclic_pred(t, order_map):
    cl = class_codes[t["sym"]]
    order = order_map[t["sym"]]  # list of ci in rotation order
    if t["prev_ss"] is None:
        return None
    prev_ci = cl.index(t["prev_ss"])
    j = order.index(prev_ci)
    return order[(j + 1) % len(order)]

def lru_pred(t, f):
    dists = t["dists"]
    fv = f[t["sym"]]
    best = max(range(len(dists)), key=lambda j: (dists[j], fv[j]))
    return best

# ---------------------------------------------------------------- LOBO loop
MODELS = ["F", "A", "A2", "Bnum", "Bfreq", "C", "D", "E", "E2", "AE"]
preds = {m: np.zeros((N,), dtype=object) for m in MODELS}  # prob vectors
rng = np.random.default_rng(469)

book_to_idx = defaultdict(list)
for i, t in enumerate(tokens):
    book_to_idx[t["book"]].append(i)

BIG_SYMS = [s for s in SYMS if sum(1 for t in tokens if t["sym"] == s) >= 300]
print(f"per-symbol-weight symbols (A2): {BIG_SYMS}")

for fold_n, hb in enumerate(BIDS):
    test_idx = book_to_idx[hb]
    if not test_idx:
        continue
    train_idx = [i for b in BIDS if b != hb for i in book_to_idx[b]]
    f = freq_table(train_idx)
    lf = {s: np.log(f[s]) for s in SYMS}

    # A global bucket weights
    wA = fit_bucket_weights_vec(make_groups(train_idx, lambda t: lf[t["sym"]]))
    # A2 per-symbol for big syms
    wA2 = {s: fit_bucket_weights_vec(make_groups(train_idx, lambda t: lf[t["sym"]], per_sym=s))
           for s in BIG_SYMS}

    # E / E2 markov
    mkE = fit_markov(train_idx, lambda t: t["prev"])
    mkE2 = fit_markov(train_idx, lambda t: t["prev_ss"])

    # D: choose k by 5-fold CV over train books
    tb = [b for b in BIDS if b != hb]
    folds = [tb[j::5] for j in range(5)]
    best_k, best_loss = None, None
    for k in range(2, 27):
        loss = cnt_n = 0
        for fo in folds:
            tr = [i for b in tb if b not in fo for i in book_to_idx[b]]
            te = [i for b in fo for i in book_to_idx[b]]
            ftr = freq_table(tr)
            g = fit_gronsfeld(tr, ftr, k)
            for i in te:
                t = tokens[i]
                p = grons_pred(g, ftr, t, k)
                loss += -math.log2(max(p[t["ci"]], 1e-12)); cnt_n += 1
        loss /= cnt_n
        if best_loss is None or loss < best_loss:
            best_loss, best_k = loss, k
    gtab = fit_gronsfeld(train_idx, f, best_k)

    # B rotation orders
    order_num = {s: list(range(len(class_codes[s]))) for s in SYMS}
    order_freq = {s: list(np.argsort(-f[s])) for s in SYMS}
    accBn = fit_slip(train_idx, lambda t: cyclic_pred(t, order_num))
    accBf = fit_slip(train_idx, lambda t: cyclic_pred(t, order_freq))
    accC = fit_slip(train_idx, lambda t: lru_pred(t, f))

    # AE: markov base + bucket weights fitted on markov logits
    wAE = fit_bucket_weights_vec(make_groups(
        train_idx,
        lambda t: np.log(np.maximum(markov_pred(mkE, f, t, t["prev"]), 1e-12))))

    for i in test_idx:
        t = tokens[i]
        s = t["sym"]; fv = f[s]
        bks = np.array(t["bks"])
        preds["F"][i] = fv
        preds["A"][i] = softmax_pred(lf[s], wA, bks)
        wuse = wA2[s] if s in BIG_SYMS else wA
        preds["A2"][i] = softmax_pred(lf[s], wuse, bks)
        pc = cyclic_pred(t, order_num)
        preds["Bnum"][i] = fv if pc is None else det_to_prob(pc, accBn[s], fv)
        pc = cyclic_pred(t, order_freq)
        preds["Bfreq"][i] = fv if pc is None else det_to_prob(pc, accBf[s], fv)
        preds["C"][i] = det_to_prob(lru_pred(t, f), accC[s], fv)
        preds["D"][i] = grons_pred(gtab, f, t, best_k)
        mp = markov_pred(mkE, f, t, t["prev"])
        preds["E"][i] = mp
        preds["E2"][i] = markov_pred(mkE2, f, t, t["prev_ss"])
        z = np.log(np.maximum(mp, 1e-12)) + wAE[bks]; z -= z.max()
        p = np.exp(z); preds["AE"][i] = p / p.sum()
    if fold_n % 10 == 0:
        print(f"fold {fold_n}/{len(BIDS)} (book {hb}) done, D best_k={best_k}")

# ---------------------------------------------------------------- evaluate
def evaluate(mask_fn, label):
    idx = [i for i in range(N) if mask_fn(tokens[i])]
    print(f"\n=== {label} (n={len(idx)}) ===")
    print(f"{'model':6} {'bits/choice':>11} {'top1 acc':>9} {'total bits':>11}")
    res = {}
    for m in MODELS:
        bits = acc = 0.0
        for i in idx:
            p = preds[m][i]; ci = tokens[i]["ci"]
            bits += -math.log2(max(p[ci], 1e-12))
            acc += (np.argmax(p) == ci)
        res[m] = (bits / len(idx), acc / len(idx), bits)
        print(f"{m:6} {bits/len(idx):11.4f} {acc/len(idx):9.4f} {bits:11.1f}")
    return res

res_all = evaluate(lambda t: True, "ALL multi-class tokens")
res_nov = evaluate(lambda t: t["novel"], "NOVEL only")
res_xu = evaluate(lambda t: t["xuniq"], "XUNIQ only (cross-book-unique)")

# chance baseline: uniform over class
for label, mask_fn in [("ALL", lambda t: True), ("NOVEL", lambda t: t["novel"]),
                       ("XUNIQ", lambda t: t["xuniq"])]:
    idx = [i for i in range(N) if mask_fn(tokens[i])]
    ub = sum(math.log2(len(class_codes[tokens[i]["sym"]])) for i in idx)
    print(f"uniform-baseline {label}: {ub/len(idx):.4f} bits/choice, total {ub:.1f}")

# save held-out predictions + token table
np.savez_compressed(f"{HC}/preds.npz",
                    **{m: np.array([preds[m][i] for i in range(N)], dtype=object) for m in MODELS},
                    allow_pickle=True)
json.dump([{k: t[k] for k in ("book", "pos", "sym", "ci", "novel", "xuniq", "bks", "occ")}
           for t in tokens], open(f"{HC}/tokens.json", "w"))
print(f"\nsaved preds.npz + tokens.json; rows={N}")
