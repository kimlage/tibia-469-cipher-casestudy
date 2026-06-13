#!/usr/bin/env python3
"""Battery 1: digit-level statistics independent of segmentation."""
import sqlite3, math, collections, json, random

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, digits, insertedzeros, baselen, decodedbase FROM sheet__books GROUP BY bookid").fetchall()
print("ROWCOUNT", len(rows))
assert len(rows) == 70

books = {}
for bid, digits, iz, baselen, dec in rows:
    assert set(digits) <= set("0123456789"), bid
    books[bid] = dict(digits=digits, iz=iz, baselen=baselen, dec=dec)

all_digits = "".join(b["digits"] for b in books.values())
print("TOTAL DIGITS", len(all_digits))

# unigram
uni = collections.Counter(all_digits)
print("UNIGRAM:", dict(sorted(uni.items())))
n = len(all_digits)
H1 = -sum(c/n*math.log2(c/n) for c in uni.values())
print("H1 = %.4f bits (max 3.3219)" % H1)

# bigram / trigram within books (no cross-book concatenation artifacts)
big = collections.Counter()
tri = collections.Counter()
for b in books.values():
    d = b["digits"]
    for i in range(len(d)-1): big[d[i:i+2]] += 1
    for i in range(len(d)-2): tri[d[i:i+3]] += 1
nb = sum(big.values())
H2 = -sum(c/nb*math.log2(c/nb) for c in big.values())
print("H2(bigram joint) = %.4f, cond H = %.4f" % (H2, H2 - H1))
print("TOP15 BIGRAMS:", big.most_common(15))
print("BOTTOM bigrams (count<=2):", sorted([bg for bg,c in big.items() if c<=2]))
missing_bg = [f"{a}{b2}" for a in "0123456789" for b2 in "0123456789" if f"{a}{b2}" not in big]
print("MISSING BIGRAMS:", missing_bg)
print("TOP15 TRIGRAMS:", tri.most_common(15))

# positional: odd vs even index (per book, 0-based)
even = collections.Counter(); odd = collections.Counter()
for b in books.values():
    d = b["digits"]
    for i,ch in enumerate(d):
        (even if i%2==0 else odd)[ch] += 1
print("EVEN-IDX:", dict(sorted(even.items())))
print("ODD-IDX :", dict(sorted(odd.items())))
ne, no = sum(even.values()), sum(odd.values())
# chi2 of independence between parity and digit
chi2 = 0
for ch in "0123456789":
    tot = uni[ch]
    for cnt, N in ((even[ch], ne), (odd[ch], no)):
        exp = tot * N / n
        if exp>0: chi2 += (cnt-exp)**2/exp
print("parity-vs-digit chi2 = %.1f (df=9)" % chi2)

# parity test under 2-digit framing: first digit vs second digit distributions
first = collections.Counter(); second = collections.Counter()
for b in books.values():
    d = b["digits"]
    for i in range(0, len(d)-1, 2):
        first[d[i]] += 1; second[d[i+1]] += 1
print("2DIGIT FIRSTPOS:", dict(sorted(first.items())))
print("2DIGIT SECONDPOS:", dict(sorted(second.items())))

# per-book entropy + length
print("\nPERBOOK: bookid len H1 H2cond")
ent = []
for bid, b in sorted(books.items()):
    d = b["digits"]; c = collections.Counter(d); m = len(d)
    h1 = -sum(v/m*math.log2(v/m) for v in c.values())
    c2 = collections.Counter(d[i:i+2] for i in range(m-1)); m2 = m-1
    h2 = -sum(v/m2*math.log2(v/m2) for v in c2.values()) - h1
    ent.append((bid, m, h1, h2))
ent.sort(key=lambda t: t[2])
for bid, m, h1, h2 in ent[:5]: print("LOWH", bid, m, "%.3f %.3f" % (h1,h2))
for bid, m, h1, h2 in ent[-5:]: print("HIGHH", bid, m, "%.3f %.3f" % (h1,h2))

# autocorrelation: P(d[i]==d[i+k]) vs expected sum p^2
p2 = sum((c/n)**2 for c in uni.values())
print("\nAUTOCORR (match prob, expect %.4f):" % p2)
for k in range(1, 13):
    match = tot_k = 0
    for b in books.values():
        d = b["digits"]
        for i in range(len(d)-k):
            tot_k += 1
            if d[i]==d[i+k]: match += 1
    obs = match/tot_k
    # binomial sd
    sd = math.sqrt(p2*(1-p2)/tot_k)
    print("k=%2d  %.4f  z=%+.2f  (n=%d)" % (k, obs, (obs-p2)/sd, tot_k))

# digit-sum / mod patterns quick view
print("\nDigit mod2 counts:", sum(1 for ch in all_digits if int(ch)%2==0), "even of", n)
con.close()
