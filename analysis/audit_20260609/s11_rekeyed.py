#!/usr/bin/env python3
"""Pairs with high decoded-LCS but low digit-LCS = same plaintext, different code choices."""
import sqlite3, itertools

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, digits, decodedbase FROM sheet__books GROUP BY bookid").fetchall()
print("ROWCOUNT", len(rows)); assert len(rows)==70
dig={r[0]:r[1] for r in rows}; dec={r[0]:r[2] for r in rows}
ids=sorted(dig,key=int)

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

out=[]
for a,b in itertools.combinations(ids,2):
    dl = lcs_len(dec[a],dec[b])/min(len(dec[a]),len(dec[b]))
    if dl < 0.35: continue
    gl = lcs_len(dig[a],dig[b])/min(len(dig[a]),len(dig[b]))
    # decoded frac should ~ match digit frac if same digits; excess decoded similarity = rekeyed
    if dl - gl/1.0 > 0.15:
        out.append((dl-gl, dl, gl, a, b))
out.sort(reverse=True)
print("pairs: decodedLCSfrac - digitLCSfrac > 0.15 (decoded>=0.35):", len(out))
for d,dl,gl,a,b in out[:15]:
    print("  %s/%s decodedfrac=%.2f digitfrac=%.2f delta=%.2f" % (a,b,dl,gl,d))
con.close()
