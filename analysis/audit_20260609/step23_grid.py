#!/usr/bin/env python3
"""Step 2 + 3: 10x10 occupancy grid, dead-cell classification, generator tests."""
import sqlite3, json, itertools, math
from collections import Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True); cur = con.cursor()
cur.execute("""SELECT code, symbol, occurrence_count, omitted_count, written_count
               FROM row0_code_symbol_counts WHERE run_id=1""")
rows = cur.fetchall()
print(f"[rows] code_symbol_counts: {len(rows)}")
occ = {c:o for c,s,o,om,w in rows}
omt = {c:om for c,s,o,om,w in rows}
wrt = {c:w for c,s,o,om,w in rows}
sym = {c:s for c,s,o,om,w in rows}

allcodes = [f"{i:02d}" for i in range(100)]
absent   = [c for c in allcodes if c not in occ]            # never occur at all
never_written = [c for c in allcodes if occ.get(c,0)>0 and wrt.get(c,0)==0]
singletons = [c for c in allcodes if occ.get(c,0)==1]
doubles = [c for c in allcodes if occ.get(c,0)==2]
print(f"\n[CELL INVENTORY of 100-cell grid]")
print(f"absent (occurrence_count=0, NO symbol):    {absent}")
print(f"never_written (occ>0 but written=0):       {never_written}")
print(f"singletons (occurrence_count=1):           {singletons}")
print(f"doubles (occurrence_count=2):              {doubles}")
print(f"distinct symbols used: {sorted(set(sym.values()))}  (n={len(set(sym.values()))})")

# effective inventory
eff_dead = set(absent) | set(never_written)
print(f"\neffective dead-as-written cells (absent OR never literally written): {sorted(eff_dead)}  n={len(eff_dead)}")
eff_live = 100 - len(eff_dead)
print(f"effective written-code inventory: {eff_live}")

# ---- z-scores for occurrence (deduped not needed; use raw occ as in prior work) ----
vals = [occ.get(c,0) for c in allcodes]
import statistics
mu = statistics.mean(vals); sd = statistics.pstdev(vals)
print(f"\nocc mean={mu:.2f} sd={sd:.2f}")
for c in ["19","51","45","11","21","46","32","33","38","69","07","39","41","66"]:
    o = occ.get(c,0)
    print(f"  code {c}: occ={o:4d}  z={(o-mu)/sd:+.2f}  sym={sym.get(c,'-')}")

# ===== STEP 2: occupancy heatmap, first digit (row) x second digit (col) =====
print("\n=== 10x10 grid: symbol (occurrence) ; '.'=absent  ===")
print("     " + "  ".join(f"c{j}" for j in range(10)))
for i in range(10):
    cells=[]
    for j in range(10):
        c=f"{i}{j}"
        if c in absent: cells.append(" . ")
        else:
            s=sym[c]
            tag=s
            if c in never_written: tag=s+"*"   # never written
            elif occ[c]==1: tag=s.lower()       # singleton
            cells.append(f"{tag:>3}")
    print(f"r{i}: " + "  ".join(cells))

print("\n=== 10x10 grid: occurrence counts ===")
print("     " + "".join(f"{j:5d}" for j in range(10)))
for i in range(10):
    print(f"r{i}: " + "".join(f"{occ.get(f'{i}{j}',0):5d}" for j in range(10)))

# ===== STEP 3: generator tests =====
print("\n\n========== STEP 3: TABLE GENERATOR TESTS ==========")
# The map is HOMOPHONIC: 99 codes -> 13 symbols. Test geometric structure.
# Build symbol-by-cell as a 10x10 of symbols (None for absent).
grid = [[sym.get(f"{i}{j}") for j in range(10)] for i in range(10)]

# Test A: does each ROW have a dominant symbol? (row-keyed homophone blocks)
print("\n[A] row-major dominant symbol (would indicate row=plaintext-letter blocks):")
for i in range(10):
    cnt=Counter(grid[i][j] for j in range(10) if grid[i][j])
    top=cnt.most_common(3)
    print(f"  row {i}: {dict(cnt)}  top={top}")
print("\n[A'] col-major dominant symbol:")
for j in range(10):
    cnt=Counter(grid[i][j] for i in range(10) if grid[i][j])
    print(f"  col {j}: {dict(cnt)}  top={cnt.most_common(3)}")

# Test B: keyword-mixed alphabet read row-wise -> does the sequence of symbols
#         (skipping repeats) spell the 13-letter alphabet in any rotation/order?
seq=[grid[i][j] for i in range(10) for j in range(10) if grid[i][j]]
# collapse consecutive duplicates
collapsed=[]
for s in seq:
    if not collapsed or collapsed[-1]!=s: collapsed.append(s)
print(f"\n[B] row-wise symbol sequence, consecutive-dedup (len {len(collapsed)}):")
print("   " + "".join(collapsed))
# first appearance order of each symbol
firstapp=[]
seen=set()
for s in seq:
    if s not in seen: seen.add(s); firstapp.append(s)
print(f"[B] first-appearance order row-wise: {''.join(firstapp)}")
seq_c=[grid[i][j] for j in range(10) for i in range(10) if grid[i][j]]
seen=set(); firstapp_c=[]
for s in seq_c:
    if s not in seen: seen.add(s); firstapp_c.append(s)
print(f"[B] first-appearance order col-wise: {''.join(firstapp_c)}")

# Test C: is the symbol a function of (code mod 13) or (code // 13) etc.? (arithmetic keystream)
print("\n[C] symbol as arithmetic function of code value:")
ALPHA="ABCEFILNORSTV"
for mod in [13,10,7,5,26]:
    # check if sym is constant within residue class
    classes={}
    consistent=True
    for c,s in sym.items():
        r=int(c)%mod
        classes.setdefault(r,set()).add(s)
    pure=sum(1 for r,ss in classes.items() if len(ss)==1)
    print(f"  code%{mod}: {pure}/{len(classes)} residue classes map to a single symbol")

# Test D: Polybius coordinate — does (row,col) decompose so symbol depends only on
#         a derived coordinate? Check sym vs (i+j), (i*j), |i-j|.
print("\n[D] symbol vs derived coordinate purity:")
for name,f in [("i+j",lambda i,j:i+j),("i-j",lambda i,j:i-j),
               ("i^j(xor)",lambda i,j:i^j),("(i+j)%13",lambda i,j:(i+j)%13)]:
    classes={}
    for i in range(10):
        for j in range(10):
            c=f"{i}{j}"
            if c in sym:
                classes.setdefault(f(i,j),set()).add(sym[c])
    pure=sum(1 for k,ss in classes.items() if len(ss)==1)
    print(f"  {name}: {pure}/{len(classes)} coordinate classes single-symbol")

# Test E: null model for the absent/dead cells. The dead set is {39 absent, 07 never-written}.
# Probability under random model that exactly these specific cells are the dead ones.
print("\n[E] null model for dead-cell positions:")
n_absent=len(absent); n_nw=len(never_written)
print(f"  observed: {n_absent} absent cell(s) {absent}, {n_nw} never-written {never_written}")
# If k cells are dead out of 100, prob that a SPECIFIC set of k is the dead set = 1/C(100,k)
for k in [1,2,3,4]:
    print(f"  P(specific set of {k} cells is the dead set) = 1/C(100,{k}) = {1/math.comb(100,k):.3e}")
con.close()
