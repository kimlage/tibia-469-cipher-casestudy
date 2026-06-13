#!/usr/bin/env python3
"""Final: novel-only language test, row0 code map inventory check, iz correlations, run lengths."""
import sqlite3, collections, math, random

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, digits, insertedzeros, decodedbase FROM sheet__books GROUP BY bookid").fetchall()
print("ROWCOUNT", len(rows)); assert len(rows)==70
dig={r[0]:r[1] for r in rows}; iz={r[0]:int(r[2]) for r in rows}; dec={r[0]:r[3] for r in rows}
ids=sorted(dig,key=int)

# ---- novel-only decoded text (greedy, 12+ symbol repeats of earlier corpus masked) ----
seen=""
novel_spans=[]
for b in ids:
    t=dec[b]; flags=[True]*len(t)
    i=0
    while i<len(t):
        best=0
        hi=min(len(t)-i,200)
        # find longest match >=12
        lo=12
        if i+lo<=len(t) and t[i:i+lo] in seen:
            # extend
            L=lo
            while L<hi and i+L+1<=len(t) and t[i:i+L+1] in seen: L+=1
            for k in range(i,min(i+L,len(t))): flags[k]=False
            i+=L
        else:
            i+=1
    spans=[]; cur=""
    for k,fl in enumerate(flags):
        if fl: cur+=t[k]
        else:
            if len(cur)>=2: spans.append(cur)
            cur=""
    if len(cur)>=2: spans.append(cur)
    novel_spans+=spans
    seen+="#"+t
tot_novel=sum(len(s) for s in novel_spans)
print("novel decoded spans: %d spans, %d symbols (of 5729)" % (len(novel_spans), tot_novel))

EN_BIG = {"th":3.56,"he":3.07,"in":2.43,"er":2.05,"an":1.99,"re":1.85,"on":1.76,"at":1.49,"en":1.45,"nd":1.35,
"ti":1.34,"es":1.34,"or":1.28,"te":1.20,"of":1.17,"ed":1.17,"is":1.13,"it":1.12,"al":1.09,"ar":1.07,
"st":1.05,"to":1.05,"nt":1.04,"ng":0.95,"se":0.93,"ha":0.93,"as":0.87,"ou":0.87,"io":0.83,"le":0.83,
"ve":0.83,"co":0.79,"me":0.79,"de":0.76,"hi":0.76,"ri":0.73,"ro":0.73,"ic":0.70,"ne":0.69,"ea":0.69,
"ra":0.69,"ce":0.65,"li":0.62,"ch":0.60,"ll":0.58,"be":0.58,"ma":0.57,"si":0.55,"om":0.55,"ur":0.54}
DE_BIG = {"en":3.88,"er":3.75,"ch":2.75,"de":2.03,"ei":1.98,"nd":1.93,"te":1.93,"in":1.71,"ie":1.63,"ge":1.47,
"es":1.52,"ne":1.31,"un":1.32,"st":1.21,"re":1.17,"he":1.14,"an":1.07,"be":1.07,"se":1.07,"ng":1.06,
"di":1.05,"sc":1.06,"is":0.94,"it":0.96,"ic":1.0,"da":0.69,"el":0.87,"au":0.74,"li":0.65,
"ns":0.74,"al":0.66,"le":0.64,"si":0.63,"ra":0.62,"ar":0.61,"ht":0.58,"ti":0.58,"eh":0.55,"ru":0.46}
def mk_logp(tb):
    tot=sum(tb.values()); base=0.005
    return {a+b: math.log((tb.get(a+b,0)+base)/(tot+base*676))
            for a in "abcdefghijklmnopqrstuvwxyz" for b in "abcdefghijklmnopqrstuvwxyz"}
LPE=mk_logp(EN_BIG); LPD=mk_logp(DE_BIG)
def sc(spans,lp):
    s=n=0
    for sp in spans:
        t=sp.lower()
        for i in range(len(t)-1):
            bg=t[i:i+2]
            if bg[0].isalpha() and bg[1].isalpha():
                s+=lp.get(bg,math.log(0.005/1000)); n+=1
    return s,n
rng=random.Random(3)
for name,lp in [("EN",LPE),("DE",LPD)]:
    so,no=sc(novel_spans,lp); obs=so/no
    sims=[]
    for t in range(1000):
        sh=[]
        for sp in novel_spans:
            l=list(sp); rng.shuffle(l); sh.append("".join(l))
        s,n=sc(sh,lp); sims.append(s/n)
    mu=sum(sims)/1000; sd=(sum((x-mu)**2 for x in sims)/1000)**0.5
    print("NOVEL-ONLY %s: obs=%.4f mu=%.4f sd=%.4f z=%+.2f (n bigrams=%d)" % (name,obs,mu,sd,(obs-mu)/sd,no))

# ---- row0 code map: inventory ----
try:
    tabs=[t[0] for t in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'row0%'").fetchall()]
    print("\nrow0 tables:", tabs)
    for t in ["row0_code_symbol_counts"]:
        cols=[c[1] for c in con.execute("PRAGMA table_info(%s)"%t).fetchall()]
        print(t, "cols:", cols)
        r=con.execute("SELECT * FROM %s LIMIT 200"%t).fetchall()
        print("rows:", len(r))
        print(r[:40])
except Exception as e:
    print("row0 read error:", e)

# ---- iz vs zero-count ----
zc={b: dig[b].count("0") for b in ids}
import statistics
xs=[iz[b] for b in ids]; ys=[zc[b] for b in ids]; ls=[len(dig[b]) for b in ids]
# partial-ish: correlate iz with zeros and with length
def corr(x,y):
    mx=sum(x)/len(x); my=sum(y)/len(y)
    num=sum((a-mx)*(b-my) for a,b in zip(x,y))
    den=(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))**0.5
    return num/den
print("\niz distribution:", sorted(collections.Counter(xs).items()))
print("corr(iz, zerocount)=%.3f corr(iz,len)=%.3f corr(zerocount,len)=%.3f" % (corr(xs,ys),corr(xs,ls),corr(ys,ls)))

# ---- digit run lengths ----
runs=collections.Counter()
for b in ids:
    d=dig[b]; cur=1
    for i in range(1,len(d)):
        if d[i]==d[i-1]: cur+=1
        else: runs[cur]+=1; cur=1
    runs[cur]+=1
print("\ndigit run-length distribution:", sorted(runs.items()))
con.close()
