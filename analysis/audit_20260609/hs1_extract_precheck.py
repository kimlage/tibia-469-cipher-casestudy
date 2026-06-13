#!/usr/bin/env python3
"""Homophonic attack step 1: extract code streams, dedupe (fragment assembly
at code-token level), Jensen-Shannon clustering pre-check."""
import sqlite3, json, math, random
import numpy as np

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
OUT = "./tmp/audit_20260609"

con = sqlite3.connect(URI, uri=True)
rows = con.execute(
    "SELECT bookid, reconstructed_code_stream, valid FROM row0_code_symbol_probe_books "
    "WHERE run_id=1 ORDER BY CAST(bookid AS INTEGER)").fetchall()
print("ROWCOUNT", len(rows))
assert len(rows) == 70, "expected 70 books"
books = {}
for bid, stream, valid in rows:
    toks = stream.split()
    assert all(len(t) == 2 and t.isdigit() for t in toks), bid
    books[bid] = toks
total = sum(len(v) for v in books.values())
codes = sorted({t for v in books.values() for t in v})
print("TOTAL_CODE_TOKENS", total)
print("DISTINCT_CODES", len(codes))
missing = [f"{i:02d}" for i in range(100) if f"{i:02d}" not in codes]
print("MISSING_CODES", missing)

# ---------- fragment assembly dedupe (token level) ----------
# greedy: drop books contained in others, then merge with suffix/prefix overlap >= MINOV tokens
MINOV = 10
frags = [(bid, tuple(toks)) for bid, toks in books.items()]
frags.sort(key=lambda x: -len(x[1]))
kept = []
membership = {}  # bookid -> fragment index (post-merge resolved later)
def contains(big, small):
    n, m = len(big), len(small)
    for i in range(n - m + 1):
        if big[i:i+m] == small:
            return True
    return False
for bid, t in frags:
    placed = False
    for j, (ids, kt) in enumerate(kept):
        if contains(kt, t):
            kept[j][0].append(bid); placed = True; break
    if not placed:
        kept.append([[bid], t])
print("AFTER_CONTAINMENT_FRAGS", len(kept), "tokens", sum(len(k[1]) for k in kept))

def best_overlap(a, b):
    mx = min(len(a), len(b))
    for L in range(mx, MINOV - 1, -1):
        if a[-L:] == b[:L]:
            return L
    return 0
changed = True
while changed:
    changed = False
    n = len(kept)
    best = (0, -1, -1, 0)  # ov, i, j, dir
    for i in range(n):
        for j in range(n):
            if i == j: continue
            ov = best_overlap(kept[i][1], kept[j][1])
            if ov > best[0]:
                best = (ov, i, j, 0)
    if best[0] >= MINOV:
        ov, i, j, _ = best
        ids = kept[i][0] + kept[j][0]
        merged = kept[i][1] + kept[j][1][ov:]
        a, b = sorted((i, j), reverse=True)
        kept.pop(a); kept.pop(b)
        kept.append([ids, merged])
        changed = True
kept.sort(key=lambda k: -len(k[1]))
ded_total = sum(len(k[1]) for k in kept)
print("AFTER_MERGE_FRAGS", len(kept), "DEDUP_TOKENS", ded_total)
print("FRAG_SIZES", [len(k[1]) for k in kept])
for k in kept:
    print("FRAG", len(k[1]), "books:", sorted(k[0], key=int))

# ---------- JS clustering pre-check ----------
def dist(toks):
    d = np.zeros(100)
    for t in toks:
        d[int(t)] += 1
    return d / d.sum()
def jsd(p, q):
    m = 0.5 * (p + q)
    def kl(a, b):
        mask = a > 0
        return float(np.sum(a[mask] * np.log2(a[mask] / b[mask])))
    return 0.5 * kl(p, m) + 0.5 * kl(q, m)

bids = sorted(books, key=int)
dists = {b: dist(books[b]) for b in bids}
sizes = {b: len(books[b]) for b in bids}
obs = []
for i in range(len(bids)):
    for j in range(i + 1, len(bids)):
        obs.append(jsd(dists[bids[i]], dists[bids[j]]))
obs = np.array(obs)
print("JS_OBS mean=%.4f sd=%.4f min=%.4f max=%.4f" % (obs.mean(), obs.std(), obs.min(), obs.max()))

# null: multinomial samples from the GLOBAL distribution with matched book sizes
glob = np.zeros(100)
for b in bids: glob += dist(books[b]) * sizes[b]
glob /= glob.sum()
rng = np.random.default_rng(469)
NREP = 200
null_means, null_maxs = [], []
for r in range(NREP):
    samp = {b: rng.multinomial(sizes[b], glob).astype(float) / sizes[b] for b in bids}
    vals = []
    for i in range(len(bids)):
        for j in range(i + 1, len(bids)):
            vals.append(jsd(samp[bids[i]], samp[bids[j]]))
    vals = np.array(vals)
    null_means.append(vals.mean()); null_maxs.append(vals.max())
nm, ns = np.mean(null_means), np.std(null_means)
print("JS_NULL mean-of-means=%.4f sd=%.4f -> z(meanJS)=%.2f" % (nm, ns, (obs.mean() - nm) / ns))
print("JS_NULL max: mu=%.4f sd=%.4f obs_max=%.4f z=%.2f" % (
    np.mean(null_maxs), np.std(null_maxs), obs.max(),
    (obs.max() - np.mean(null_maxs)) / np.std(null_maxs)))

# crude 2-cluster check: split by top eigenvector of -JS matrix, compare mean within/between
M = np.zeros((len(bids), len(bids)))
k = 0
for i in range(len(bids)):
    for j in range(i + 1, len(bids)):
        M[i, j] = M[j, i] = obs[k]; k += 1
# spectral sign split
B = M - M.mean()
w, v = np.linalg.eigh(B)
lab = (v[:, -1] > 0).astype(int)
within = [M[i, j] for i in range(70) for j in range(i+1, 70) if lab[i] == lab[j]]
betw = [M[i, j] for i in range(70) for j in range(i+1, 70) if lab[i] != lab[j]]
print("SPECTRAL_SPLIT sizes", int(lab.sum()), 70 - int(lab.sum()),
      "within=%.4f between=%.4f ratio=%.3f" % (np.mean(within), np.mean(betw),
                                               np.mean(betw)/np.mean(within)))
# null for ratio
ratios = []
for r in range(100):
    samp = [rng.multinomial(sizes[b], glob).astype(float)/sizes[b] for b in bids]
    Mn = np.zeros((70, 70))
    for i in range(70):
        for j in range(i+1, 70):
            Mn[i, j] = Mn[j, i] = jsd(samp[i], samp[j])
    Bn = Mn - Mn.mean()
    wn, vn = np.linalg.eigh(Bn)
    ln = (vn[:, -1] > 0).astype(int)
    wi = [Mn[i, j] for i in range(70) for j in range(i+1, 70) if ln[i] == ln[j]]
    be = [Mn[i, j] for i in range(70) for j in range(i+1, 70) if ln[i] != ln[j]]
    ratios.append(np.mean(be)/np.mean(wi))
print("SPECTRAL_RATIO_NULL mu=%.3f sd=%.3f obs=%.3f z=%.2f" % (
    np.mean(ratios), np.std(ratios), np.mean(betw)/np.mean(within),
    (np.mean(betw)/np.mean(within) - np.mean(ratios)) / np.std(ratios)))

json.dump({"books": {b: books[b] for b in bids},
           "fragments": [{"books": k[0], "tokens": list(k[1])} for k in kept]},
          open(f"{OUT}/hs_corpus.json", "w"))
print("WROTE hs_corpus.json")
