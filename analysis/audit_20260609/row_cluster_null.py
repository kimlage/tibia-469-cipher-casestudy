#!/usr/bin/env python3
import sqlite3, random, math
from collections import Counter
from math import comb

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True); cur = con.cursor()
cur.execute("SELECT code,occurrence_count FROM row0_code_symbol_counts WHERE run_id=1")
occ = {c:o for c,o in cur.fetchall()}
con.close()
cells = [f"{i:02d}" for i in range(100)]
for c in cells: occ.setdefault(c,0)   # 39 absent

# dead-ish thresholds
for thr in [0,1,2,4]:
    dead = [c for c in cells if occ[c] <= thr]
    rows = Counter(int(c[0]) for c in dead)
    cols = Counter(int(c[1]) for c in dead)
    k = len(dead)
    if k==0:
        print(f"thr<= {thr}: no cells"); continue
    maxrow_obs = max(rows.values())
    maxcol_obs = max(cols.values())
    # exact null via Monte Carlo: place k dead cells at random among 100, max-in-any-row
    N=200000; ge_row=0; ge_col=0
    allc=list(range(100))
    for _ in range(N):
        s=random.sample(allc,k)
        r=Counter(x//10 for x in s); c2=Counter(x%10 for x in s)
        if max(r.values())>=maxrow_obs: ge_row+=1
        if max(c2.values())>=maxcol_obs: ge_col+=1
    print(f"thr<= {thr}: k={k} dead={sorted(dead)}")
    print(f"    rows dist={dict(sorted(rows.items()))}  max_in_row={maxrow_obs}  P(>=that under null,any row)={ge_row/N:.4f}")
    print(f"    cols dist={dict(sorted(cols.items()))}  max_in_col={maxcol_obs}  P(>=that under null,any col)={ge_col/N:.4f}")
