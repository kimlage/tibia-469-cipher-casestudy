#!/usr/bin/env python3
"""Book families: containment, overlap graph, alignment of shared chunks."""
import sqlite3, collections, itertools

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, digits, decodedbase FROM sheet__books GROUP BY bookid").fetchall()
print("ROWCOUNT", len(rows)); assert len(rows)==70
books = {r[0]: r[1] for r in rows}
dec = {r[0]: r[2] for r in rows}
ids = sorted(books, key=int)

# containment: book A substring of book B
print("--- full containment ---")
cont = []
for a,b in itertools.permutations(ids,2):
    if books[a] in books[b]:
        cont.append((a,b))
        print("book %s (len %d) is a SUBSTRING of book %s (len %d) at offset %d" %
              (a, len(books[a]), b, len(books[b]), books[b].find(books[a])))
print("containment count:", len(cont))

# near-containment via LCS fraction
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

print("\n--- overlap graph: edges where LCS >= 50%% of shorter book ---")
edges = []
for a,b in itertools.combinations(ids,2):
    L = lcs_len(books[a], books[b])
    frac = L/min(len(books[a]),len(books[b]))
    if frac >= 0.5:
        edges.append((a,b,L,frac))
edges.sort(key=lambda e:-e[3])
for a,b,L,f in edges:
    print("  %s-%s LCS=%d frac=%.2f" % (a,b,L,f))

# connected components with threshold 50%
parent = {i:i for i in ids}
def find(x):
    while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
    return x
for a,b,L,f in edges:
    ra,rb=find(a),find(b)
    if ra!=rb: parent[ra]=rb
comps = collections.defaultdict(list)
for i in ids: comps[find(i)].append(i)
fams = sorted((sorted(v,key=int) for v in comps.values()), key=len, reverse=True)
print("\n--- families (>=50%% LCS components) ---")
for f in fams:
    if len(f)>1: print("  family size %d: %s" % (len(f), f))
singles = [f[0] for f in fams if len(f)==1]
print("  singletons (%d): %s" % (len(singles), singles))

# the 60-digit chunk shared by 11 books: where does it sit in each?
k=60
seen = collections.defaultdict(set)
for b in ids:
    d = books[b]
    for i in range(len(d)-k+1):
        seen[d[i:i+k]].add(b)
top = sorted(((len(bs),g) for g,bs in seen.items()), reverse=True)[0]
g = top[1]
print("\nmost-shared 60-mer (in %d books): %s" % (top[0], g))
for b in ids:
    p = books[b].find(g)
    if p>=0: print("  book %s len=%d offset=%d" % (b, len(books[b]), p))

# what does decodedbase render this chunk as? find decoded alignment roughly: offset/2
b0 = [b for b in ids if books[b].find(g)>=0][0]
p = books[b0].find(g)
print("\nbook %s decodedbase around offset//2: %s" % (b0, dec[b0][max(0,p//2-2):p//2+35]))

# effective distinct content: greedy dedupe — total digits minus digits covered by >=30-length repeats of earlier text
corpus = ""
new_digits = 0
for b in ids:
    d = books[b]
    i = 0
    while i < len(d):
        # longest match of d[i:] in corpus (binary search on length)
        lo, hi = 0, len(d)-i
        best = 0
        for Ltry in range(min(hi, 300), 9, -10):
            if d[i:i+Ltry] in corpus: best = Ltry; break
        if best >= 10:
            i += best
        else:
            new_digits += 1
            i += 1
    corpus += "#" + d
print("\nrough novel-digit estimate (10+ repeats deduped, greedy): %d of 11263" % new_digits)
con.close()
