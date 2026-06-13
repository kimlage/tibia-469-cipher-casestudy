#!/usr/bin/env python3
"""Step 2: 10x10 occupancy heatmap. Step 3: table-generator tests with null controls."""
import sqlite3, json, math, random, itertools
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
cur.execute("""SELECT code, symbol, occurrence_count, written_count
               FROM row0_code_symbol_counts WHERE run_id=1""")
rows = cur.fetchall()
print(f"[rows] code_symbol_counts: {len(rows)}")
con.close()

occ = {c: o for c, _, o, _ in rows}          # occurrence incl omitted-zero writes
wr = {c: w for c, _, _, w in rows}           # written as 2 digits
sym = {c: s for c, s, _, _ in rows}
all_codes = [f"{i}{j}" for i in range(10) for j in range(10)]
for c in all_codes:
    occ.setdefault(c, 0); wr.setdefault(c, 0)
total = sum(occ.values())
print(f"total occurrences: {total}")

# ---------- STEP 2: heatmap ----------
exp = total / 100.0
print(f"\n=== 10x10 occupancy (occurrence_count), expected/cell={exp:.1f} ===")
print("     " + "  ".join(f"j={j}" for j in range(10)))
classes = {}
for i in range(10):
    cells = []
    for j in range(10):
        c = f"{i}{j}"
        o = occ[c]
        z = (o - exp) / math.sqrt(exp)
        if o == 0 or (wr[c] == 0):
            cls = "DEAD" if c != "07" else "DEAD*"  # 07 written 0, occurs via omission
        elif o <= 1:
            cls = "ONCE"
        elif o <= 2:
            cls = "TWICE"
        elif z >= 8:
            cls = "HOT"
        else:
            cls = "norm"
        classes[c] = cls
        cells.append(f"{o:4d}")
    print(f"i={i}: " + " ".join(cells) + f"   | rowsum={sum(occ[f'{i}{j}'] for j in range(10)):4d}")
print("colsum: " + " ".join(f"{sum(occ[f'{i}{j}'] for i in range(10)):4d}" for j in range(10)))

zline = []
for c in all_codes:
    z = (occ[c] - exp) / math.sqrt(exp)
    if abs(z) >= 4 or occ[c] <= 2:
        zline.append(f"{c}({sym.get(c,'-')})occ={occ[c]} z={z:+.2f} [{classes[c]}]")
print("\nextreme cells (|z|>=4 or occ<=2):")
for l in zline: print("  " + l)

dead_strict = sorted(c for c in all_codes if occ[c] == 0)            # never occurs at all
dead_written = sorted(c for c in all_codes if wr[c] == 0)            # never written as 2 digits
once = sorted(c for c in all_codes if occ[c] == 1)
twice = sorted(c for c in all_codes if occ[c] == 2)
hot = sorted(c for c in all_codes if (occ[c]-exp)/math.sqrt(exp) >= 8)
print(f"\ndead_strict (occ=0): {dead_strict}")
print(f"dead_written (written=0): {dead_written}")
print(f"once (occ=1): {once}")
print(f"twice (occ=2): {twice}")
print(f"hot (z>=8): {hot}  zs: {[f'{(occ[c]-exp)/math.sqrt(exp):+.1f}' for c in hot]}")

# within-symbol homophone null: is cell rare beyond its symbol's rarity?
groups = defaultdict(list)
for c in all_codes:
    if c in sym: groups[sym[c]].append(c)
print("\nwithin-symbol homophone skew (symbol: total, ncodes, min..max):")
for s, cs in sorted(groups.items()):
    tot = sum(occ[c] for c in cs)
    print(f"  {s}: total={tot} ncodes={len(cs)} counts={sorted((occ[c] for c in cs), reverse=True)}")

# ---------- row-confinement permutation control ----------
# fact: {32,33,38,39} = 4 of the 5 cells with occ<=1 (excl 07 written-0) share first digit 3
rng = random.Random(469)
counts_vec = [occ[c] for c in all_codes]
def low_cells_rowstat(assign):
    # assign: list of counts aligned to all_codes order
    lows = [all_codes[k] for k, v in enumerate(assign) if v <= 1 and all_codes[k] != "07"]
    if not lows: return 0
    rowc = Counter(c[0] for c in lows)
    return max(rowc.values())
obs_stat = low_cells_rowstat(counts_vec)
NTRIал = 200000
hits = 0
v = counts_vec[:]
for _ in range(NTRIал):
    rng.shuffle(v)
    if low_cells_rowstat(v) >= obs_stat:
        hits += 1
print(f"\n[control] max #(occ<=1 cells sharing a first digit): observed={obs_stat}")
print(f"[control] permutation null (shuffle counts over cells, {NTRIал} trials): P(stat>={obs_stat}) = {hits/NTRIал:.5f} ({hits} hits)")

# same for second digit (column confinement)
def low_cells_colstat(assign):
    lows = [all_codes[k] for k, v in enumerate(assign) if v <= 1 and all_codes[k] != "07"]
    if not lows: return 0
    colc = Counter(c[1] for c in lows)
    return max(colc.values())
obs_col = low_cells_colstat(counts_vec)
hits = 0
for _ in range(NTRIал):
    rng.shuffle(v)
    if low_cells_colstat(v) >= obs_col:
        hits += 1
print(f"[control] max #(occ<=1 cells sharing a second digit): observed={obs_col}, P={hits/NTRIал:.5f}")

# row-3 depletion: P(min row sum <= row3 sum) under count permutation
row3 = sum(occ[f"3{j}"] for j in range(10))
hits = 0
NT2 = 20000
for _ in range(NT2):
    rng.shuffle(v)
    sums = [sum(v[10*i:10*i+10]) for i in range(10)]
    if min(sums) <= row3:
        hits += 1
print(f"[control] row3 sum={row3} (uniform exp={total/10:.0f}); P(min rowsum <= {row3}) under count-permutation = {hits/NT2:.4f}")

# ---------- STEP 3: generator enumeration ----------
print("\n=== generator tests ===")
# candidate dead sets to explain
cand_sets = {
    "briefs {07,32,33,38}": {"07","32","33","38"},
    "strict {39}": {"39"},
    "written0 {07,39}": {"07","39"},
    "occ<=1 {32,33,38,39,69}": {"32","33","38","39","69"},
    "occ<=1 noomit+07 {07,32,33,38,39,69}": {"07","32","33","38","39","69"},
    "row3 cluster {32,33,38,39}": {"32","33","38","39"},
    "occ<=2 {32,33,38,39,41,66,69}": {"32","33","38","39","41","66","69"},
}

# fill orders over the 10x10 grid
def order_rowwise():   return [(i,j) for i in range(10) for j in range(10)]
def order_colwise():   return [(i,j) for j in range(10) for i in range(10)]
def order_boustro_r(): return [(i,j) for i in range(10) for j in (range(10) if i%2==0 else range(9,-1,-1))]
def order_boustro_c(): return [(i,j) for j in range(10) for i in (range(10) if j%2==0 else range(9,-1,-1))]
def order_diag():
    out=[]
    for s in range(19):
        for i in range(10):
            j=s-i
            if 0<=j<10: out.append((i,j))
    return out
def order_antidiag():
    out=[]
    for s in range(-9,10):
        for i in range(10):
            j=i-s
            if 0<=j<10: out.append((i,j))
    return out
def order_spiral():
    out=[]; top,bot,left,right=0,9,0,9
    while top<=bot and left<=right:
        for j in range(left,right+1): out.append((top,j))
        for i in range(top+1,bot+1): out.append((i,right))
        if top<bot:
            for j in range(right-1,left-1,-1): out.append((bot,j))
        if left<right:
            for i in range(bot-1,top,-1): out.append((i,left))
        top+=1; bot-=1; left+=1; right-=1
    return out
orders = {
    "rowwise": order_rowwise(), "colwise": order_colwise(),
    "boustro_row": order_boustro_r(), "boustro_col": order_boustro_c(),
    "diag": order_diag(), "antidiag": order_antidiag(), "spiral": order_spiral(),
}
orders.update({k+"_rev": list(reversed(v)) for k, v in list(orders.items())})

n_tests = 0
hits_found = []
# (a) contiguous run (incl tail/head) in fill order
for oname, o in orders.items():
    codestr = [f"{i}{j}" for i, j in o]
    pos = {c: k for k, c in enumerate(codestr)}
    for sname, S in cand_sets.items():
        ps = sorted(pos[c] for c in S)
        n_tests += 1
        if ps[-1] - ps[0] == len(ps) - 1:
            hits_found.append(f"CONTIGUOUS: {sname} contiguous in {oname} at positions {ps}")
print(f"(a) contiguous-run tests: {n_tests} order x set combos; hits: {len(hits_found)}")
for h in hits_found: print("   " + h)

# (b) skip rules
rules = []
for m in range(2, 11):
    for r in range(m):
        rules.append((f"(i+j)%{m}=={r}", lambda i,j,m=m,r=r: (i+j)%m==r))
        rules.append((f"(i*j)%{m}=={r}", lambda i,j,m=m,r=