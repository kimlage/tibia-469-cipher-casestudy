#!/usr/bin/env python3
import sqlite3, math, itertools
from collections import Counter

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True); cur = con.cursor()
cur.execute("SELECT code,symbol,occurrence_count,omitted_count,written_count FROM row0_code_symbol_counts WHERE run_id=1")
info = {c: dict(symbol=s, occ=o, om=om, wr=w) for c,s,o,om,w in cur.fetchall()}
con.close()

cells = [f"{i:02d}" for i in range(100)]
occ = {c: info.get(c,{}).get('occ',0) for c in cells}      # 0 for absent (39)
wr  = {c: info.get(c,{}).get('wr',0) for c in cells}        # written count
sym = {c: info.get(c,{}).get('symbol','.') for c in cells}
sym['39'] = '?'  # absent

# ---------- occupancy heatmap (first digit rows, second digit cols) ----------
print("=== OCCURRENCE HEATMAP (rows=d1, cols=d2) ===")
print("    " + "".join(f"{d:>5}" for d in range(10)))
for d1 in range(10):
    row = []
    for d2 in range(10):
        c = f"{d1}{d2}"
        row.append(f"{occ[c]:>5}")
    print(f" {d1}: " + "".join(row))

print("\n=== WRITTEN-COUNT HEATMAP (scribe-written only) ===")
print("    " + "".join(f"{d:>5}" for d in range(10)))
for d1 in range(10):
    print(f" {d1}: " + "".join(f"{wr[f'{d1}{d2}']:>5}" for d2 in range(10)))

# ---------- classify ----------
absent   = [c for c in cells if occ[c]==0]                 # truly absent
wzero    = [c for c in cells if wr[c]==0]                  # never written (incl absent)
wzero_only = [c for c in wzero if c not in absent]         # written=0 but occurs as omitted zero
occ1     = [c for c in cells if occ[c]==1]                 # occurs exactly once
hot      = sorted(cells, key=lambda c: -occ[c])[:6]
print("\nabsent (occ=0):", absent)
print("written=0 (never scribe-written):", wzero)
print("  of which occur only as inserted zero:", wzero_only)
print("occ==1 (rare):", occ1)
print("hot (top6 occ):", [(c, occ[c]) for c in hot])

# z-scores for occupancy (dedupe note: counts already per-token across 70 books)
vals = [occ[c] for c in cells]
mu = sum(vals)/len(vals); sd = (sum((v-mu)**2 for v in vals)/len(vals))**0.5
print(f"\nocc mean={mu:.2f} sd={sd:.2f}")
for c in ['19','51','11','45','07','32','33','38','39','69','66','41']:
    print(f"  {c}: occ={occ[c]:>3} z={(occ[c]-mu)/sd:+.2f}  sym={sym[c]}")

# ============================================================
# STEP 3: generator enumeration
# Candidate "dead set" interpretations to test a generator against:
#   D_absent  = {39}                      (1 cell)
#   D_wzero   = {07}                       (1 cell, written=0)
#   D_occ1    = {32,33,38,69} ∪ {39}       (rare/dead)
#   D_combo   = {07,32,33,38,39}           (original hypothesis-ish)
# A "construction fingerprint" generator must reproduce one of these EXACTLY
# from a simple rule, beating the random-occupancy null.
# ============================================================
ALPHABET = "ABCEFILNORSTV"  # 13 symbols + star mask
star = '*'

def keyword_mix(keyword, alpha):
    seen, out = set(), []
    for ch in keyword + alpha:
        if ch not in seen:
            seen.add(ch); out.append(ch)
    return out

# The symbol grid we OBSERVE (code -> symbol). Test: is there a 10x10 fill
# (row-wise or column-wise) of some keyword-mixed sequence that reproduces it?
# 100 cells, only 14 distinct symbols -> homophonic; a single keyword fill of a
# 14-letter alphabet into 100 cells repeats the alphabet ~7x. Check periodicity.
obs_syms = [sym[c] for c in cells]   # in code order 00..99
print("\n=== symbol sequence in code order (00..99) ===")
print("".join(obs_syms))

# Test for periodic structure: does sym[code] depend on code mod k for small k?
print("\n=== periodicity test: H(symbol | code mod k) ===")
def cond_entropy_mod(k):
    groups = {}
    for i,c in enumerate(cells):
        groups.setdefault(i%k, Counter())[sym[c]] += 1
    # weighted conditional entropy
    H=0.0; N=len(cells)
    for r,cnt in groups.items():
        tot=sum(cnt.values())
        h=-sum((v/tot)*math.log2(v/tot) for v in cnt.values())
        H += (tot/N)*h
    return H
base_counts = Counter(sym[c] for c in cells)
H0 = -sum((v/100)*math.log2(v/100) for v in base_counts.values())
print(f"  H(symbol) unconditional = {H0:.3f} bits")
for k in [2,3,4,5,7,10,13,14]:
    print(f"  k={k:>2}: H(sym|code%k)={cond_entropy_mod(k):.3f} bits  (drop={H0-cond_entropy_mod(k):+.3f})")

# Polybius / coordinate test: does sym depend separably on d1 and d2?
# Fit best symbol per (d1) and per (d2); measure how separable.
print("\n=== separability test (Polybius-style d1/d2 coordinates) ===")
d1_sym = {d1: Counter(sym[f'{d1}{d2}'] for d2 in range(10)) for d1 in range(10)}
d2_sym = {d2: Counter(sym[f'{d1}{d2}'] for d1 in range(10)) for d2 in range(10)}
for d1 in range(10):
    top = d1_sym[d1].most_common(1)[0]
    print(f"  row d1={d1}: top_sym={top[0]} count={top[1]}/10  dist={dict(d1_sym[d1])}")

# ---------- null model: dead-set match probability ----------
# Random occupancy null: place the OBSERVED number of zero/dead cells at random
# among 100 cells. Probability a specific generator predicts the exact set.
import math as m
def exact_prob(k_dead):
    return 1.0 / m.comb(100, k_dead)
print("\n=== null-model exact-match probabilities ===")
for label,k in [("|absent|=1",1),("|wzero|=1",1),("4 dead cells",4),("5 dead cells",5)]:
    print(f"  {label}: 1 in {m.comb(100,k):,}  (p={exact_prob(k):.3e})")

# ---------- Does ANY simple generator reproduce the absent/dead cells? ----------
# Generator family A: arithmetic skip - dead cells = {c : c mod g == r}
print("\n=== generator A: dead = codes with code%g==r reproducing absent set {39}? ===")
absent_ints = sorted(int(c) for c in absent)
print("  absent ints:", absent_ints, "-> single cell, no modulus signature (trivially any g with one residue).")

# Generator family B: keyword grid leaves trailing cells blank (e.g. fill 96 then stop)
# Observed: 99 present + 1 absent(39). If table filled 00..98 and 39 special - not contiguous.
print("\n=== generator B: contiguous trailing-blank fill? ===")
print("  absent code 39 is INTERIOR (not trailing) -> not a trailing-blank artifact.")

# Generator family C: 07 special because it's the inserted-zero token (structural, not table)
print("\n=== generator C: 07 written=0 ===")
print(f"  07 occ={occ['07']} written={wr['07']} omitted={info['07']['om']} -> 07 is the INSERTED-ZERO code by construction, not a dead table cell.")
