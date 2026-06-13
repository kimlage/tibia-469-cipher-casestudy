#!/usr/bin/env python3
"""Battery: cross-book structure, duplicates, shared substrings, per-book compressibility."""
import sqlite3, math, collections, zlib, random, itertools

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, digits, insertedzeros, baselen, decodedbase FROM sheet__books GROUP BY bookid").fetchall()
print("ROWCOUNT", len(rows)); assert len(rows)==70
books = {r[0]: dict(digits=r[1], iz=int(r[2]), baselen=int(r[3]), dec=r[4]) for r in rows}

# verify length identity
bad = [(b, len(v["digits"]), v["iz"], v["baselen"]) for b,v in books.items() if len(v["digits"])+v["iz"] != 2*v["baselen"]]
print("identity len+iz==2*baselen violations:", bad if bad else "NONE (holds for all 70)")

# exact duplicate digit strings
byd = collections.defaultdict(list)
for b,v in books.items(): byd[v["digits"]].append(b)
dups = {k[:30]: v for k,v in byd.items() if len(v)>1}
print("exact duplicate digit-strings:", {tuple(v): None for v in byd.values() if len(v)>1})

# exact duplicate decodedbase
byd2 = collections.defaultdict(list)
for b,v in books.items(): byd2[v["dec"]].append(b)
print("exact duplicate decodedbase:", [tuple(v) for v in byd2.values() if len(v)>1])

# per-book self-compression (book alone vs shuffled book)
rng = random.Random(7)
print("\nper-book zlib ratio (sorted):")
pb = []
for b,v in books.items():
    d = v["digits"]
    c = len(zlib.compress(d.encode(),9))/len(d)
    sh = "".join(rng.sample(d,len(d)))
    cs = len(zlib.compress(sh.encode(),9))/len(d)
    pb.append((c, cs, b, len(d)))
pb.sort()
for c,cs,b,L in pb[:8]: print("  most-compressible book %s len=%d ratio=%.3f (shuf %.3f)" % (b,L,c,cs))
for c,cs,b,L in pb[-3:]: print("  least: book %s len=%d ratio=%.3f (shuf %.3f)" % (b,L,c,cs))

# cross-book: conditional compression gain. comp(A+B)-comp(A) vs comp(B)
ids = sorted(books, key=lambda x:int(x))
comp = {b: len(zlib.compress(books[b]["digits"].encode(),9)) for b in ids}
pairs = []
for a,b in itertools.combinations(ids,2):
    ab = len(zlib.compress((books[a]["digits"]+books[b]["digits"]).encode(),9))
    gain = comp[a]+comp[b]-ab  # bytes saved by knowing A when compressing B
    pairs.append((gain, a, b))
pairs.sort(reverse=True)
print("\ntop 20 cross-book compression-gain pairs (bytes saved):")
for g,a,b in pairs[:20]:
    print("  %s+%s gain=%d (lenA=%d lenB=%d)" % (a,b,g,len(books[a]["digits"]),len(books[b]["digits"])))
print("median gain:", sorted(p[0] for p in pairs)[len(pairs)//2])

# longest common substring between each top pair via suffix automaton-ish brute force
def lcs(a,b):
    # dp over shorter
    best = 0; besta=0
    la, lb = len(a), len(b)
    prev = [0]*(lb+1)
    for i in range(1,la+1):
        cur = [0]*(lb+1)
        ai = a[i-1]
        for j in range(1,lb+1):
            if ai == b[j-1]:
                cur[j] = prev[j-1]+1
                if cur[j]>best: best=cur[j]; besta=i
        prev = cur
    return best, a[besta-best:besta]

print("\nLCS for top gain pairs:")
for g,a,b in pairs[:8]:
    L, s = lcs(books[a]["digits"], books[b]["digits"])
    print("  %s/%s LCS=%d  %s%s" % (a,b,L,s[:60],"..." if L>60 else ""))

# global repeated substrings: longest substring appearing in >=2 books, and in many books
# build n-gram presence for lengths
from collections import Counter
def ngram_books(k):
    seen = collections.defaultdict(set)
    for b,v in books.items():
        d = v["digits"]
        for i in range(len(d)-k+1):
            seen[d[i:i+k]].add(b)
    return seen

for k in [10, 15, 20, 30, 40, 60]:
    s = ngram_books(k)
    multi = {g:len(bs) for g,bs in s.items() if len(bs)>1}
    if multi:
        top = sorted(multi.items(), key=lambda t:-t[1])[:3]
        print("k=%d: %d substrings shared by >=2 books; top shared-by counts %s" % (k, len(multi), [(g[:25]+'..',c) for g,c in top]))
    else:
        print("k=%d: none shared" % k)

# within-book longest internal repeat
def longest_repeat(d):
    best = 0
    # binary search with set
    lo, hi = 1, len(d)//2+1
    while lo<hi:
        mid=(lo+hi)//2
        seen=set(); found=False
        for i in range(len(d)-mid+1):
            g=d[i:i+mid]
            if g in seen: found=True; break
            seen.add(g)
        if found: lo=mid+1
        else: hi=mid
    return lo-1
print("\nwithin-book longest internal repeat (top 8):")
lr = sorted(((longest_repeat(v["digits"]), b, len(v["digits"])) for b,v in books.items()), reverse=True)
for L,b,n in lr[:8]: print("  book %s len=%d longest-repeat=%d" % (b,n,L))
print("  median:", lr[len(lr)//2][0])
con.close()
