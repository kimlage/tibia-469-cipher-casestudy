#!/usr/bin/env python3
"""Dedupe-corrected language test + bookid correlation + module inventory."""
import sqlite3, collections, math, random

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, digits, decodedbase FROM sheet__books GROUP BY bookid").fetchall()
print("ROWCOUNT", len(rows)); assert len(rows)==70
dig = {r[0]: r[1] for r in rows}
dec = {r[0]: r[2] for r in rows}
ids = sorted(dig, key=int)

# ---- assemble decoded fragments greedily (overlap >= 10 symbols) ----
def merge_all(strs, minov):
    frags = list(dict.fromkeys(strs))
    changed = True
    while changed:
        changed = False
        bestov=0; bi=bj=-1; bnew=None
        for i in range(len(frags)):
            for j in range(i+1,len(frags)):
                a,b = frags[i],frags[j]
                if b in a: ov,new = len(b),a
                elif a in b: ov,new = len(a),b
                else:
                    ov,new = 0,None
                    m=min(len(a),len(b))
                    for k in range(m, minov-1, -1):
                        if a[-k:]==b[:k]: ov,new=k,a+b[k:]; break
                    if not ov:
                        for k in range(m, minov-1, -1):
                            if b[-k:]==a[:k]: ov,new=k,b+a[k:]; break
                if ov>bestov: bestov,bi,bj,bnew=ov,i,j,new
        if bestov>=minov:
            frags=[f for k,f in enumerate(frags) if k not in (bi,bj)]+[bnew]; changed=True
    return frags

dfrags = merge_all([dec[i] for i in ids], 10)
print("decoded fragments:", len(dfrags), "total symbols:", sum(len(f) for f in dfrags))

EN_BIG = {"th":3.56,"he":3.07,"in":2.43,"er":2.05,"an":1.99,"re":1.85,"on":1.76,"at":1.49,"en":1.45,"nd":1.35,
"ti":1.34,"es":1.34,"or":1.28,"te":1.20,"of":1.17,"ed":1.17,"is":1.13,"it":1.12,"al":1.09,"ar":1.07,
"st":1.05,"to":1.05,"nt":1.04,"ng":0.95,"se":0.93,"ha":0.93,"as":0.87,"ou":0.87,"io":0.83,"le":0.83,
"ve":0.83,"co":0.79,"me":0.79,"de":0.76,"hi":0.76,"ri":0.73,"ro":0.73,"ic":0.70,"ne":0.69,"ea":0.69,
"ra":0.69,"ce":0.65,"li":0.62,"ch":0.60,"ll":0.58,"be":0.58,"ma":0.57,"si":0.55,"om":0.55,"ur":0.54}
DE_BIG = {"en":3.88,"er":3.75,"ch":2.75,"de":2.03,"ei":1.98,"nd":1.93,"te":1.93,"in":1.71,"ie":1.63,"ge":1.47,
"es":1.52,"ne":1.31,"un":1.32,"st":1.21,"re":1.17,"he":1.14,"an":1.07,"be":1.07,"se":1.07,"ng":1.06,
"di":1.05,"sc":1.06,"is":0.94,"it":0.96,"ic":1.0,"da":0.69,"el":0.87,"au":0.74,"li":0.65,
"ns":0.74,"al":0.66,"le":0.64,"si":0.63,"ra":0.62,"ar":0.61,"ht":0.58,"ti":0.58,"eh":0.55,"ru":0.46}
def mk_logp(table):
    tot=sum(table.values()); base=0.005
    return {a+b: math.log((table.get(a+b,0)+base)/(tot+base*676))
            for a in "abcdefghijklmnopqrstuvwxyz" for b in "abcdefghijklmnopqrstuvwxyz"}
LP_EN=mk_logp(EN_BIG); LP_DE=mk_logp(DE_BIG)
def score(txt, lp):
    t=txt.lower(); s=n=0
    for i in range(len(t)-1):
        bg=t[i:i+2]
        if bg[0].isalpha() and bg[1].isalpha():
            s+=lp.get(bg, math.log(0.005/1000)); n+=1
    return s,n

rng = random.Random(99)
NT=1000
for name,lp in [("EN",LP_EN),("DE",LP_DE)]:
    so,no = 0,0
    for f in dfrags:
        s,n = score(f,lp); so+=s; no+=n
    obs = so/no
    sims=[]
    for t in range(NT):
        ss=nn=0
        for f in dfrags:
            l=list(f); rng.shuffle(l)
            s,n=score("".join(l),lp); ss+=s; nn+=n
        sims.append(ss/nn)
    mu=sum(sims)/NT; sd=(sum((x-mu)**2 for x in sims)/NT)**0.5
    print("DEDUPED %s bigram: obs=%.4f mu=%.4f sd=%.4f z=%+.2f" % (name,obs,mu,sd,(obs-mu)/sd))

# decoded bigram-structure chi2 on deduped fragments
def big_chi2(texts):
    bg=collections.Counter(); un=collections.Counter()
    for t in texts:
        un.update(t)
        for i in range(len(t)-1): bg[t[i:i+2]]+=1
    n=sum(bg.values()); tu=sum(un.values()); chi=0
    for p,c in bg.items():
        e=un[p[0]]*un[p[1]]/tu/tu*n
        if e>0: chi+=(c-e)**2/e
    return chi
obs=big_chi2(dfrags)
sims=[]
for t in range(300):
    sh=[]
    for f in dfrags:
        l=list(f); rng.shuffle(l); sh.append("".join(l))
    sims.append(big_chi2(sh))
mu=sum(sims)/300; sd=(sum((x-mu)**2 for x in sims)/300)**0.5
print("DEDUPED decoded bigram chi2: obs=%.0f mu=%.0f sd=%.0f z=%+.2f" % (obs,mu,sd,(obs-mu)/sd))

# ---- bookid vs similarity ----
def lcs_len(a,b):
    la,lb=len(a),len(b)
    if la>lb: a,b,la,lb=b,a,lb,la
    prev=[0]*(lb+1); best=0
    for i in range(1,la+1):
        cur=[0]*(lb+1); ai=a[i-1]
        for j in range(1,lb+1):
            if ai==b[j-1]:
                cur[j]=prev[j-1]+1
                if cur[j]>best: best=cur[j]
        prev=cur
    return best
import itertools
sim={}
for a,b in itertools.combinations(ids,2):
    sim[(a,b)] = lcs_len(dig[a],dig[b])/min(len(dig[a]),len(dig[b]))
# correlation between id distance and similarity (Spearman-ish via permutation of ids)
pairs=list(sim.items())
def stat(idmap):
    # mean similarity of adjacent ids (distance 1..3) minus overall mean
    s=n=0
    for (a,b),v in pairs:
        if abs(idmap[a]-idmap[b])<=3: s+=v; n+=1
    return s/n
idmap={b:int(b) for b in ids}
obs=stat(idmap)
allmean=sum(v for _,v in pairs)/len(pairs)
sims=[]
perm=ids[:]
for t in range(2000):
    rng.shuffle(perm)
    pm={b:i for i,b in enumerate(perm)}
    sims.append(stat(pm))
mu=sum(sims)/2000; sd=(sum((x-mu)**2 for x in sims)/2000)**0.5
print("\nadjacent-bookid (|d|<=3) mean LCS-frac: obs=%.4f overall=%.4f permnull mu=%.4f sd=%.4f z=%+.2f" % (obs,allmean,mu,sd,(obs-mu)/sd))

# ---- module inventory: distinct maximal >=20-digit repeated substrings count ----
k=20
occ=collections.Counter()
for b in ids:
    d=dig[b]
    for i in range(len(d)-k+1): occ[d[i:i+k]]+=1
rep={g for g,c in occ.items() if c>=2}
# merge overlapping 20-mers into maximal modules (greedy chaining)
modset=set()
for g in sorted(rep):
    modset.add(g)
print("\nrepeated 20-mers (count>=2): %d distinct" % len(rep))
con.close()
