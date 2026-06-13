#!/usr/bin/env python3
"""STEP 5: code 19 hyper-enrichment + dead codes 32/33/38.
Are they fully explained by (text-keyed lexicon + module copying + global
code-frequency preferences), or do they carry extra structure?

Tests:
  5.1 counts full vs novel-only (dedupe-corrected enrichment)
  5.2 cross-book homogeneity of 19-share within I, novel material only
      (G-test vs 1000 binomial sims with global novel share)
  5.3 within-segment positional preference of 19 (start/middle/end of segment),
      novel only, vs within-(book,I) shuffle
  5.4 dead codes: occurrence counts; expected count under fitted per-symbol
      frequencies is the parameter itself -> report lexicon-cell usage instead:
      how many of 145 distinct segments use each code (copy-corrected usage).
  5.5 lexicon-level channel: first-token choice index of each distinct segment
      (in order of first appearance) -> bitstream/letter tests vs 200 shuffles.
"""
import json
import math
import sqlite3
import numpy as np
from collections import Counter, defaultdict

HC = "./tmp/audit_20260609/homophone_channel"
data = json.load(open(f"{HC}/occ_streams.json"))
class_codes = {s: v for s, v in data["class_sizes"].items() if len(v) >= 2}

con = sqlite3.connect("file:./data/bonelord_operational.sqlite?mode=ro", uri=True)
cnts = con.execute("SELECT code, symbol, occurrence_count FROM row0_code_symbol_counts WHERE run_id=1").fetchall()
rows = con.execute("SELECT bookid, reconstructed_code_stream, decodedbase FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
con.close()
print(f"count rows: {len(cnts)}, book rows: {len(rows)}")

occ_full = Counter(); occ_novel = Counter()
book_I = defaultdict(lambda: [0, 0])  # bid -> [n_I_novel, n_19_novel]
for s, lst in data["occ"].items():
    for r in lst:
        occ_full[r["code"]] += 1
        if r["novel"]:
            occ_novel[r["code"]] += 1
            if s == "I":
                book_I[r["book"]][0] += 1
                if r["code"] == "19":
                    book_I[r["book"]][1] += 1

print("\n5.1 counts (full / novel):")
for c in ("19", "32", "33", "38"):
    s = next(sym for cc, sym, _ in cnts if cc == c)
    cls = class_codes[s]
    n_s_full = sum(occ_full[x] for x in cls)
    n_s_nov = sum(occ_novel[x] for x in cls)
    print(f"  code {c} (sym {s}, class {len(cls)}): full={occ_full[c]}/{n_s_full} "
          f"({occ_full[c]/n_s_full:.3f}) novel={occ_novel[c]}/{n_s_nov} "
          f"({occ_novel[c]/max(1,n_s_nov):.3f}) "
          f"[uniform would be {1/len(cls):.3f}]")

# 5.2 homogeneity of 19-share across books, novel I tokens
rng = np.random.default_rng(195)
books = {b: v for b, v in book_I.items() if v[0] >= 5}
n_tot = sum(v[0] for v in books.values()); k_tot = sum(v[1] for v in books.values())
p_glob = k_tot / n_tot
def gstat(obs):
    G = 0.0
    for n, k in obs:
        for kk, pp in ((k, p_glob), (n - k, 1 - p_glob)):
            if kk > 0 and pp > 0:
                G += 2 * kk * math.log(kk / (n * pp))
    return G
obs_pairs = [(v[0], v[1]) for v in books.values()]
G_obs = gstat(obs_pairs)
sims = []
for _ in range(1000):
    sims.append(gstat([(n, rng.binomial(n, p_glob)) for n, k in obs_pairs]))
sims = np.array(sims)
z = (G_obs - sims.mean()) / sims.std(ddof=1)
p_emp = (sims >= G_obs).mean()
print(f"\n5.2 19-share homogeneity across books (novel I, books w/ n>=5): "
      f"share={p_glob:.3f}, G={G_obs:.1f} sims={sims.mean():.1f}+-{sims.std(ddof=1):.1f} "
      f"z={z:+.2f} p={p_emp:.3f} (nbooks={len(books)})")

# 5.3 positional preference of 19 within segments, novel only
# rebuild segments
seg_positions = []  # (relpos_bucket, is19) for novel I tokens
flag = {}
for s, lst in data["occ"].items():
    for r in lst:
        flag[(r["book"], r["pos"])] = r["novel"]
pos19 = []; posI = []
for bid, stream, base in sorted(rows):
    codes = stream.split()
    L = len(base); i = 0
    while i < L:
        if base[i] == "*": i += 1; continue
        j = i
        while j < L and base[j] != "*": j += 1
        for k in range(i, j):
            if base[k] == "I" and flag.get((bid, k)):
                rel = (k - i) / max(1, j - i - 1)
                posI.append(rel)
                if codes[k] == "19":
                    pos19.append(rel)
        i = j
posI = np.array(posI); pos19 = np.array(pos19)
obs_d = pos19.mean() - posI.mean()
sims = []
for _ in range(2000):
    pick = rng.choice(posI, size=len(pos19), replace=False)
    sims.append(pick.mean() - posI.mean())
sims = np.array(sims)
print(f"\n5.3 19 positional preference (novel I): mean relpos 19={pos19.mean():.3f} "
      f"all-I={posI.mean():.3f} diff z={(obs_d-sims.mean())/sims.std(ddof=1):+.2f}")

# 5.4 lexicon-cell usage of focal codes: distinct segments using each code
seg_codes = {}
seen_segs = set()
code_seg_use = Counter()
for bid, stream, base in sorted(rows):
    codes = stream.split()
    L = len(base); i = 0
    while i < L:
        if base[i] == "*": i += 1; continue
        j = i
        while j < L and base[j] != "*": j += 1
        seg = base[i:j]
        if seg not in seen_segs:
            seen_segs.add(seg)
            for k in range(i, j):
                code_seg_use[codes[k]] += 1
        i = j
print(f"\n5.4 distinct segments: {len(seen_segs)}")
tot_cells = sum(code_seg_use.values())
for c in ("19", "32", "33", "38"):
    s = next(sym for cc, sym, _ in cnts if cc == c)
    cls = class_codes[s]
    cls_cells = sum(code_seg_use[x] for x in cls)
    print(f"  code {c}: used in {code_seg_use[c]} lexicon cells "
          f"(class {s}: {cls_cells} cells over {len(cls)} codes; "
          f"uniform exp {cls_cells/len(cls):.1f})")
# zero-prob under fitted class distribution (excl. focal code circularity):
for c in ("32", "33", "38"):
    s = next(sym for cc, sym, _ in cnts if cc == c)
    cls = class_codes[s]
    cls_cells = sum(code_seg_use[x] for x in cls)
    k = code_seg_use[c]
    # under uniform choice: P(usage <= k)
    from scipy.stats import binom
    p_le = binom.cdf(k, cls_cells, 1 / len(cls))
    print(f"  code {c}: P(usage<={k} | uniform within class, {cls_cells} cells) = {p_le:.2e}")

# 5.5 lexicon-level channel: first-token choice index per distinct segment
firsts = []
seen_segs = set()
for bid, stream, base in sorted(rows):
    codes = stream.split()
    L = len(base); i = 0
    while i < L:
        if base[i] == "*": i += 1; continue
        j = i
        while j < L and base[j] != "*": j += 1
        seg = base[i:j]
        if seg not in seen_segs:
            seen_segs.add(seg)
            for k in range(i, j):
                if base[k] in class_codes:
                    firsts.append((base[k], class_codes[base[k]].index(codes[k])))
                    break
        i = j
print(f"\n5.5 lexicon first-choice stream: n={len(firsts)}")
# freq-rank mod 2 bits
cntS = {s: Counter() for s in class_codes}
for s, lst in data["occ"].items():
    if s in class_codes:
        for r in lst:
            cntS[s][class_codes[s].index(r["code"])] += 1
frank = {s: {ci: r for r, ci in enumerate(sorted(range(len(class_codes[s])), key=lambda x: -cntS[s][x]))} for s in class_codes}
bits_obs = np.array([frank[s][ci] % 2 for s, ci in firsts])
def bstats(bits):
    n1 = bits.sum(); n = len(bits)
    runs = 1 + int(np.sum(bits[1:] != bits[:-1]))
    return n1 / n, runs
b_obs, r_obs = bstats(bits_obs)
sims_b, sims_r = [], []
for _ in range(2000):
    sb = np.array([frank[s][ci] % 2 for s, ci in firsts])
    # control: resample ci from that symbol's global distribution
    sim = []
    for s, ci in firsts:
        ks = list(cntS[s].keys()); ws = np.array([cntS[s][k] for k in ks], float)
        sim.append(frank[s][ks[rng.choice(len(ks), p=ws / ws.sum())]] % 2)
    bb, rr = bstats(np.array(sim))
    sims_b.append(bb); sims_r.append(rr)
sims_b = np.array(sims_b); sims_r = np.array(sims_r)
print(f"  bias: obs={b_obs:.3f} ctl={sims_b.mean():.3f}+-{sims_b.std(ddof=1):.3f} "
      f"z={(b_obs-sims_b.mean())/sims_b.std(ddof=1):+.2f}")
print(f"  runs: obs={r_obs} ctl={sims_r.mean():.1f}+-{sims_r.std(ddof=1):.1f} "
      f"z={(r_obs-sims_r.mean())/sims_r.std(ddof=1):+.2f}")
