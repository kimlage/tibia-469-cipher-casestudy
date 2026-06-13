#!/usr/bin/env python3
"""Dedupe-aware retests + superstring assembly + arithmetic/mod probes on 2-digit codes."""
import sqlite3, collections, math, random, itertools

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, digits, decodedbase FROM sheet__books GROUP BY bookid").fetchall()
print("ROWCOUNT", len(rows)); assert len(rows)==70
books = {r[0]: r[1] for r in rows}
decmap = {r[0]: r[2] for r in rows}
ids = sorted(books, key=int)

# ---------- greedy superstring assembly ----------
# repeatedly merge the pair with max overlap (suffix-prefix or containment)
def max_overlap(a, b):
    # containment
    if b in a: return len(b), ("contain", a)
    if a in b: return len(a), ("contain", b)
    best = 0; merged = None
    m = min(len(a), len(b))
    for k in range(m, 19, -1):  # min overlap 20
        if a[-k:] == b[:k]: return k, ("merge", a + b[k:])
    for k in range(m, 19, -1):
        if b[-k:] == a[:k]: return k, ("merge", b + a[k:])
    return 0, None

frags = list(dict.fromkeys(books[i] for i in ids))
print("start fragments:", len(frags))
changed = True
while changed:
    changed = False
    bestov = 0; bi = bj = -1; bm = None
    for i in range(len(frags)):
        for j in range(i+1, len(frags)):
            ov, m = max_overlap(frags[i], frags[j])
            if ov > bestov:
                bestov, bi, bj, bm = ov, i, j, m
    if bestov >= 20:
        new = bm[1]
        frags = [f for k,f in enumerate(frags) if k not in (bi,bj)] + [new]
        changed = True
print("after greedy merge (overlap>=20):", len(frags), "fragments")
frags.sort(key=len, reverse=True)
for f in frags[:12]:
    print("  frag len", len(f))
print("  total assembled length:", sum(len(f) for f in frags))
with open("./tmp/audit_20260609/fragments.txt","w") as fh:
    for f in frags: fh.write(f+"\n")

# which books map into which fragment
frag_of = {}
for b in ids:
    hits = [fi for fi,f in enumerate(frags) if books[b] in f]
    frag_of[b] = hits
unplaced = [b for b in ids if not frag_of[b]]
print("books fully contained in an assembled fragment:", sum(1 for b in ids if frag_of[b]), "; unplaced:", unplaced)

# ---------- dedupe-aware digit stats on fragments ----------
all_f = "".join(frags)
n = len(all_f)
uni = collections.Counter(all_f)
print("\nDEDUPED corpus len=%d unigram=%s" % (n, dict(sorted(uni.items()))))
big = collections.Counter()
for f in frags:
    for i in range(len(f)-1): big[f[i:i+2]] += 1
print("deduped missing bigrams:", [f"{a}{b}" for a in "0123456789" for b in "0123456789" if f"{a}{b}" not in big])
print("deduped rare bigrams (<=2):", sorted((bg,c) for bg,c in big.items() if c<=2))
rng = random.Random(11)
for target in ["07","32","33","19"]:
    obs = big.get(target,0)
    sims=[]
    for t in range(300):
        sh=["".join(rng.sample(f,len(f))) for f in frags]
        c=0
        for s in sh:
            for i in range(len(s)-1):
                if s[i:i+2]==target: c+=1
        sims.append(c)
    mu=sum(sims)/300; sd=(sum((x-mu)**2 for x in sims)/300)**0.5
    print("bigram %s deduped: obs=%d mu=%.1f sd=%.1f z=%+.2f" % (target,obs,mu,sd,(obs-mu)/sd))

# autocorr on deduped
p2 = sum((c/n)**2 for c in uni.values())
print("\nDEDUPED autocorr (expect %.4f):" % p2)
for k in range(1,9):
    m=t=0
    for f in frags:
        for i in range(len(f)-k):
            t+=1
            if f[i]==f[i+k]: m+=1
    sd=math.sqrt(p2*(1-p2)/t)
    print("  k=%d %.4f z=%+.2f (n=%d)" % (k, m/t, (m/t-p2)/sd, t))

# ---------- arithmetic relations on 2-digit codes (aligned per project: use decodedbase length) ----------
# without trusting decode, use even-aligned pairs on fragments
print("\n--- consecutive 2-digit code diffs mod 10/odd patterns (even-aligned on fragments) ---")
diffs = collections.Counter(); dmod10 = collections.Counter()
codes_all = []
for f in frags:
    codes = [int(f[i:i+2]) for i in range(0, len(f)-1, 2)]
    codes_all.append(codes)
    for x,y in zip(codes, codes[1:]):
        diffs[y-x] += 1
        dmod10[(y-x)%10] += 1
print("diff mod 10 distribution:", dict(sorted(dmod10.items())))
tot = sum(dmod10.values())
exp = tot/10
chi2 = sum((c-exp)**2/exp for c in dmod10.values())
print("chi2 vs uniform mod10 = %.1f (df=9)" % chi2)
# control: same but on within-fragment shuffled codes
sims=[]
for t in range(200):
    c2 = 0
    dm = collections.Counter()
    for codes in codes_all:
        s = codes[:]; rng.shuffle(s)
        for x,y in zip(s,s[1:]): dm[(y-x)%10]+=1
    tt=sum(dm.values()); ee=tt/10
    sims.append(sum((c-ee)**2/ee for c in dm.values()))
mu=sum(sims)/200; sd=(sum((x-mu)**2 for x in sims)/200)**0.5
print("shuffle-control chi2 mu=%.1f sd=%.1f z=%+.2f" % (mu,sd,(chi2-mu)/sd))

# code value histogram (even-aligned)
cv = collections.Counter()
for codes in codes_all: cv.update(codes)
print("\ncode-value histogram (deduped, even-aligned), nonzero count=%d:" % len(cv))
print(sorted(cv.items()))
con.close()
