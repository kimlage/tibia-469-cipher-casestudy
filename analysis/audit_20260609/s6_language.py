#!/usr/bin/env python3
"""Battery 6: language sanity check on decodedbase (English + German bigram log-prob)
with within-book shuffle controls. Also symbol-layer stats."""
import sqlite3, collections, math, random

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, digits, decodedbase FROM sheet__books GROUP BY bookid").fetchall()
print("ROWCOUNT", len(rows)); assert len(rows)==70
dec = {r[0]: r[2] for r in rows}
ids = sorted(dec, key=int)

# symbol stats
alltxt = "".join(dec[i] for i in ids)
print("total decoded symbols:", len(alltxt))
cnt = collections.Counter(alltxt)
print("symbol counts:", dict(sorted(cnt.items(), key=lambda t:-t[1])))
star = cnt.get("*",0)
print("star fraction: %.3f" % (star/len(alltxt)))

# English & German letter-bigram log frequencies (from standard corpus tables, per mille).
# Source: Norvig ngram counts (English) and Beutelspacher/typical German tables; coarse but fine for ranking.
EN_BIG = {"th":3.56,"he":3.07,"in":2.43,"er":2.05,"an":1.99,"re":1.85,"on":1.76,"at":1.49,"en":1.45,"nd":1.35,
"ti":1.34,"es":1.34,"or":1.28,"te":1.20,"of":1.17,"ed":1.17,"is":1.13,"it":1.12,"al":1.09,"ar":1.07,
"st":1.05,"to":1.05,"nt":1.04,"ng":0.95,"se":0.93,"ha":0.93,"as":0.87,"ou":0.87,"io":0.83,"le":0.83,
"ve":0.83,"co":0.79,"me":0.79,"de":0.76,"hi":0.76,"ri":0.73,"ro":0.73,"ic":0.70,"ne":0.69,"ea":0.69,
"ra":0.69,"ce":0.65,"li":0.62,"ch":0.60,"ll":0.58,"be":0.58,"ma":0.57,"si":0.55,"om":0.55,"ur":0.54}
DE_BIG = {"en":3.88,"er":3.75,"ch":2.75,"de":2.03,"ei":1.98,"nd":1.93,"te":1.93,"in":1.71,"ie":1.63,"ge":1.47,
"es":1.52,"ne":1.31,"un":1.32,"st":1.21,"re":1.17,"he":1.14,"an":1.07,"be":1.07,"se":1.07,"ng":1.06,
"di":1.05,"sc":1.06,"sd":0.2,"is":0.94,"it":0.96,"ic":1.0,"da":0.69,"el":0.87,"au":0.74,"li":0.65,
"ns":0.74,"al":0.66,"le":0.64,"si":0.63,"ra":0.62,"ar":0.61,"ht":0.58,"ti":0.58,"eh":0.55,"ru":0.46}

def mk_logp(table):
    # build smoothed bigram logprob over a-z
    tot = sum(table.values())
    base = 0.005  # floor per mille
    lp = {}
    for a in "abcdefghijklmnopqrstuvwxyz":
        for b in "abcdefghijklmnopqrstuvwxyz":
            lp[a+b] = math.log((table.get(a+b, 0)+base)/ (tot+base*676))
    return lp
LP_EN = mk_logp(EN_BIG); LP_DE = mk_logp(DE_BIG)

def score(txt, lp):
    t = txt.lower()
    s = n = 0
    for i in range(len(t)-1):
        bg = t[i:i+2]
        if bg[0].isalpha() and bg[1].isalpha():
            s += lp.get(bg, math.log(0.005/1000)); n += 1
    return s/n if n else 0

rng = random.Random(469)
NT = 1000
for name, lp in [("EN", LP_EN), ("DE", LP_DE)]:
    obs = sum(score(dec[i], lp) for i in ids)/len(ids)
    sims = []
    for t in range(NT):
        tot = 0
        for i in ids:
            s = list(dec[i]); rng.shuffle(s)
            tot += score("".join(s), lp)
        sims.append(tot/len(ids))
    mu = sum(sims)/NT; sd = (sum((x-mu)**2 for x in sims)/NT)**0.5
    print("%s bigram score: obs=%.4f shuffle mu=%.4f sd=%.4f z=%+.2f" % (name, obs, mu, sd, (obs-mu)/sd))

# also: decoded-symbol bigram structure strength (language-agnostic): bigram chi2 vs shuffle
def big_chi2(texts):
    bg = collections.Counter(); un = collections.Counter()
    for t in texts:
        un.update(t)
        for i in range(len(t)-1): bg[t[i:i+2]] += 1
    n = sum(bg.values())
    chi = 0
    tot_u = sum(un.values())
    for (pair),c in bg.items():
        e = un[pair[0]]*un[pair[1]]/tot_u/tot_u*n
        if e>0: chi += (c-e)**2/e
    return chi
obs = big_chi2([dec[i] for i in ids])
sims=[]
for t in range(300):
    sh=[]
    for i in ids:
        s=list(dec[i]); rng.shuffle(s); sh.append("".join(s))
    sims.append(big_chi2(sh))
mu=sum(sims)/300; sd=(sum((x-mu)**2 for x in sims)/300)**0.5
print("decoded bigram-structure chi2: obs=%.0f shuffle mu=%.0f sd=%.0f z=%+.2f" % (obs,mu,sd,(obs-mu)/sd))

# top decoded bigrams/trigrams vs expectation
bg = collections.Counter(); un = collections.Counter(); tri = collections.Counter()
for i in ids:
    t = dec[i]; un.update(t)
    for j in range(len(t)-1): bg[t[j:j+2]] += 1
    for j in range(len(t)-2): tri[t[j:j+3]] += 1
print("top 15 decoded bigrams:", bg.most_common(15))
print("top 15 decoded trigrams:", tri.most_common(15))

# vowel/consonant alternation test (A E I O are vowels in alphabet ABCEFILNORSTV)
vow = set("AEIO")
trans = collections.Counter()
for i in ids:
    t = dec[i].replace("*","")
    for j in range(len(t)-1):
        trans[(t[j] in vow, t[j+1] in vow)] += 1
n = sum(trans.values())
pv = (trans[(True,True)]+trans[(True,False)])/n
print("vowel fraction %.3f ; VV %.3f VC %.3f CV %.3f CC %.3f (expect VV %.3f)" % (
    pv, trans[(True,True)]/n, trans[(True,False)]/n, trans[(False,True)]/n, trans[(False,False)]/n, pv*pv))

# word-like structure: does '*' or any letter act as separator? check inter-arrival of each symbol
print("\nrun-length / spacing check for top symbols:")
for sym,_ in cnt.most_common(6):
    gaps = collections.Counter()
    for i in ids:
        t = dec[i]
        pos = [k for k,c in enumerate(t) if c==sym]
        for a,b in zip(pos,pos[1:]): gaps[b-a]+=1
    com = gaps.most_common(5)
    print("  %s gaps top: %s" % (sym, com))
con.close()
