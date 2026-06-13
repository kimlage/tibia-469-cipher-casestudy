#!/usr/bin/env python3
"""Shuffle control: is the observed symbol->cell assignment more geometrically
structured than a random homophonic table with the same symbol multiset?"""
import sqlite3, random
from collections import Counter

DB="file:./data/bonelord_operational.sqlite?mode=ro"
con=sqlite3.connect(DB,uri=True);cur=con.cursor()
cur.execute("SELECT code,symbol FROM row0_code_symbol_counts WHERE run_id=1")
sym={c:s for c,s in cur.fetchall()}
con.close()
codes=sorted(sym)                      # 99 assigned codes
symbols=[sym[c] for c in codes]        # multiset of 99 symbols

def metrics(assign):
    """assign: dict code->symbol. Return (row_purity, colcoord_purity)."""
    grid={}
    for c,s in assign.items():
        grid[(int(c)//10,int(c)%10)]=s
    # max single-symbol fraction summed over rows (block structure)
    rowscore=0
    for i in range(10):
        cnt=Counter(grid[(i,j)] for j in range(10) if (i,j) in grid)
        if cnt: rowscore+=max(cnt.values())
    # i+j coordinate purity
    classes={}
    for (i,j),s in grid.items():
        classes.setdefault(i+j,set()).add(s)
    coordpure=sum(1 for v in classes.values() if len(v)==1)
    # residue%13 purity
    rc={}
    for c,s in assign.items():
        rc.setdefault(int(c)%13,set()).add(s)
    respure=sum(1 for v in rc.values() if len(v)==1)
    return rowscore,coordpure,respure

obs=metrics(sym)
print(f"[observed] rowblock_sum={obs[0]}  i+j_pure={obs[1]}  mod13_pure={obs[2]}")

N=20000
random.seed(469)
rb=[];cp=[];rp=[]
for _ in range(N):
    perm=symbols[:]
    random.shuffle(perm)
    a=dict(zip(codes,perm))
    m=metrics(a)
    rb.append(m[0]);cp.append(m[1]);rp.append(m[2])

def report(name,obsval,dist):
    import statistics
    mu=statistics.mean(dist);sd=statistics.pstdev(dist)
    ge=sum(1 for x in dist if x>=obsval)
    z=(obsval-mu)/sd if sd else 0
    print(f"  {name}: obs={obsval}  null mean={mu:.2f} sd={sd:.2f}  z={z:+.2f}  P(null>=obs)={ge/len(dist):.4f}")

print(f"\n[shuffle control, N={N}]")
report("rowblock_sum",obs[0],rb)
report("i+j coord purity",obs[1],cp)
report("mod13 residue purity",obs[2],rp)
print("\n(Interpretation: P>=~0.05 on every metric => observed table is NOT more")
print(" geometrically structured than a random homophonic assignment.)")
