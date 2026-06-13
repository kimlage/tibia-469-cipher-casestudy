#!/usr/bin/env python3
"""Independent adversarial verification of module-decomposition claim.
Own implementations, fresh seed (rng 20260609)."""
import sqlite3, random, math, lzma
from collections import Counter

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, MIN(digits), MIN(decodedbase) FROM sheet__books GROUP BY bookid").fetchall()
print("rowcount:", len(rows)); assert len(rows)==70
def keyf(b):
    try: return (0,int(b))
    except: return (1,b)
rows.sort(key=lambda r: keyf(r[0]))
ids=[r[0] for r in rows]; dig={r[0]:r[1] for r in rows}; dec={r[0]:r[2] for r in rows}
print("digits:",sum(len(dig[b]) for b in ids),"symbols:",sum(len(dec[b]) for b in ids))

# probe_books cross-check
p = con.execute("SELECT bookid, decodedbase FROM row0_code_symbol_probe_books WHERE run_id=1").fetchall()
print("probe rows:", len(p), "mismatches:", sum(1 for b,d in p if dec.get(b)!=d))

# 1. containment (independent loop)
contained=set(); pairs=0
for a in ids:
    for b in ids:
        if a!=b and dig[a] in dig[b]:
            contained.add(a); pairs+=1
print(f"containment: distinct_contained={len(contained)} pairs={pairs}")
# how long are contained books? (chance probability check)
clens=sorted(len(dig[a]) for a in contained)
print("contained book lengths:", clens)

# 2. shared 10-gram coverage, own implementation
def cov10(texts):
    d={}
    for bi,t in enumerate(texts):
        for i in range(len(t)-9):
            d.setdefault(t[i:i+10],set()).add(bi)
    tot=0
    for bi,t in enumerate(texts):
        m=bytearray(len(t))
        for i in range(len(t)-9):
            if len(d[t[i:i+10]])>=2:
                for j in range(i,i+10): m[j]=1
        tot+=sum(m)
    return tot
texts=[dec[b] for b in ids]; N=sum(len(t) for t in texts)
real=cov10(texts)
print(f"shared10gram REAL: {real}/{N} = {100*real/N:.1f}%")

rng=random.Random(20260609)
sh=[]
for _ in range(10):
    sh.append(cov10(["".join(rng.sample(t,len(t))) for t in texts]))
print("shuffle x10:", sh, "max=",max(sh), f"({100*max(sh)/N:.2f}%)")

# order-2 markov surrogate, own implementation
tr={}
for t in texts:
    for i in range(len(t)-2):
        tr.setdefault(t[i:i+2],[]).append(t[i+2])
starts=[t[:2] for t in texts]
def mk2():
    out=[]
    for t in texts:
        cur=list(rng.choice(starts))[:len(t)]
        while len(cur)<len(t):
            c="".join(cur[-2:]); ch=tr.get(c)
            if not ch: c=rng.choice(list(tr)); ch=tr[c]
            cur.append(rng.choice(ch))
        out.append("".join(cur))
    return out
mk=[cov10(mk2()) for _ in range(10)]
print("order2-markov x10:", mk, "max=",max(mk), f"({100*max(mk)/N:.2f}%)")

# 3. LZ dedup novel symbols, own implementation
def lznovel(strs, order, minM):
    corpus=""; total=0; masks={}
    for b in order:
        s=strs[b]; m=bytearray(len(s)); i=0
        while i<len(s):
            lo,hi,best=minM,len(s)-i,0
            while lo<=hi:
                mid=(lo+hi)//2
                if s[i:i+mid] in corpus: best,lo=mid,mid+1
                else: hi=mid-1
            if best>=minM: i+=best
            else: m[i]=1; i+=1
        masks[b]=m; total+=sum(m); corpus+="#"+s
    return total,masks
nv,masks=lznovel(dec,ids,5)
print(f"LZ dedup decoded novel: {nv}/{N}")
nvd,_=lznovel(dig,ids,10)
print(f"LZ dedup digit novel: {nvd}/11263")

# 4. residual chi2 gate, own implementation
EN=dict(A=8.167,B=1.492,C=2.782,E=12.702,F=2.228,I=6.966,L=4.025,N=6.749,O=7.507,R=5.987,S=6.327,T=9.056,V=0.978)
DE=dict(A=6.516,B=1.886,C=2.732,E=16.396,F=1.656,I=6.550,L=3.437,N=9.776,O=2.594,R=7.003,S=7.270,T=6.154,V=0.846)
ES=dict(A=11.525,B=2.215,C=4.019,E=12.181,F=0.692,I=6.247,L=4.967,N=6.712,O=8.683,R=6.871,S=7.977,T=4.632,V=1.138)
S13="ABCEFILNORSTV"
cnt=Counter()
for b in ids:
    for i,ch in enumerate(dec[b]):
        if masks[b][i]: cnt[ch]+=1
def gate(c,label):
    obs={s:c.get(s,0) for s in S13}; n=sum(obs.values())
    def chi(ref):
        T=sum(ref[s] for s in S13)
        return sum((obs[s]-n*ref[s]/T)**2/(n*ref[s]/T) for s in S13)
    r={"UNIFORM":chi({s:1 for s in S13}),"EN":chi(EN),"DE":chi(DE),"ES":chi(ES)}
    print(label,f"N={n}:"," < ".join(f"{k} {v:.0f}" for k,v in sorted(r.items(),key=lambda kv:kv[1])))
gate(Counter("".join(texts)),"gate FULL")
gate(cnt,"gate RESIDUAL")
print("residual stars:", cnt.get("*",0))

# 5. lzma secondary
def lzb(ts):
    al=sorted(set("".join(texts)))
    ix={c:i for i,c in enumerate(al)}
    return len(lzma.compress(b"\xff".join(bytes(ix[c] for c in t) for t in ts),preset=9))
print("lzma REAL:",lzb(texts))
print("lzma shuffle x3:",[lzb(["".join(rng.sample(t,len(t))) for t in texts]) for _ in range(3)])
print("lzma mk2 x3:",[lzb(mk2()) for _ in range(3)])

# 6. spot check biggest module: find longest repeated digit substring across 2 books
best=0;arg=None
import sys
# check the claimed M00 len=279: longest common substring across any pair, quick suffix-set approach at L=279
L=279
d={}
for b in ids:
    t=dig[b]
    for i in range(len(t)-L+1):
        d.setdefault(t[i:i+L],set()).add(b)
hits={k:v for k,v in d.items() if len(v)>=2}
print(f"digit substrings of len 279 shared by >=2 books: {len(hits)}; books:",[sorted(v) for v in list(hits.values())[:3]])
L=280
d={}
for b in ids:
    t=dig[b]
    for i in range(len(t)-L+1):
        d.setdefault(t[i:i+L],set()).add(b)
print("len 280 shared:", sum(1 for v in d.values() if len(v)>=2))
