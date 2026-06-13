#!/usr/bin/env python3
"""Claim 7 follow-up: corpus-AGGREGATE anagram-beat z over all 70 books,
to test whether the docs' 'z 8-15 robust beat' is the aggregate of weak,
template-duplicated per-book signals; plus a global relabel control and a
de-templated (deduplicated-fragment) variant."""
import sqlite3, math, random, statistics, re
from collections import Counter

random.seed(4690)
URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, MIN(decodedbase) FROM sheet__books GROUP BY bookid").fetchall()
print("ROWCOUNT:", len(rows)); assert rows
books = dict(rows)

exec(open("./tmp/audit_20260609/claim7_bigram.py").read().split("# ---------- book selection")[0].split('PROSE = """')[0])
# (re-import the trainer cheaply: redefine here instead)
PROSE = open("./tmp/audit_20260609/claim7_bigram.py").read()
PROSE = PROSE.split('PROSE = """')[1].split('"""')[0]

def train_bigram(text_words, alphabet, alpha=0.5):
    uni, bi = Counter(), Counter()
    for w in text_words:
        for a, b in zip(w, w[1:]):
            bi[(a, b)] += 1; uni[a] += 1
    V = len(alphabet)
    return {(a, b): math.log((bi[(a, b)] + alpha) / (uni[a] + alpha * V))
            for a in alphabet for b in alphabet}

AZ = [chr(c) for c in range(97, 123)]
EN = train_bigram(re.findall(r"[a-z]+", PROSE.lower()), AZ)
BOOK_AZ = sorted(set("abcefilnorstv"))

def segs_of(base):
    return [s.lower() for s in base.split("*") if len(s) >= 2]

def total_logp(segs, logp):
    return sum(logp[(a, b)] for seg in segs for a, b in zip(seg, seg[1:]))

def aggregate_z(book_segs, logp, nshuf, relabel=None):
    if relabel:
        book_segs = [[s.translate(relabel) for s in segs] for segs in book_segs]
    obs = sum(total_logp(segs, logp) for segs in book_segs)
    reps = []
    for _ in range(nshuf):
        tot = 0.0
        for segs in book_segs:
            letters = list("".join(segs))
            random.shuffle(letters)
            i = 0; sh = []
            for s in segs:
                sh.append("".join(letters[i:i+len(s)])); i += len(s)
            tot += total_logp(sh, logp)
        reps.append(tot)
    mu, sd = statistics.fmean(reps), statistics.stdev(reps)
    return (obs - mu) / sd

allsegs = [segs_of(b) for b in books.values()]
zagg = aggregate_z(allsegs, EN, 300)
print(f"AGGREGATE anagram-beat z over all 70 books, English bigram model: {zagg:+.2f}")

# global relabel control: one permutation applied to whole corpus
rel = []
for _ in range(60):
    perm = BOOK_AZ[:]; random.shuffle(perm)
    t = str.maketrans(dict(zip(BOOK_AZ, perm)))
    rel.append(aggregate_z(allsegs, EN, 120, relabel=t))
rel.sort()
print(f"global relabel control (60 perms): mean {statistics.fmean(rel):+.2f} "
      f"min {rel[0]:+.2f} max {rel[-1]:+.2f}; n_perms >= observed: "
      f"{sum(1 for r in rel if r >= zagg)}")

# de-templated corpus: greedily drop books that share a >=19-char fragment with
# an already-kept book, then recompute aggregate z
kept = []
def shares_long(a, b, L=19):
    frs = {a[i:i+L] for i in range(len(a) - L + 1)}
    return any(b[i:i+L] in frs for i in range(len(b) - L + 1))
for bid, base in books.items():
    if not any(shares_long(base, books[k]) for k in kept):
        kept.append(bid)
print(f"\nde-templated subset (no two books share a 19-char fragment): {len(kept)} books")
dt = [segs_of(books[k]) for k in kept]
zdt = aggregate_z(dt, EN, 300)
nb = sum(len(s) - 1 for segs in dt for s in segs)
print(f"aggregate z on de-templated subset: {zdt:+.2f}  (bigrams={nb})")
# scale comparison: aggregate z of a random subset of same size, full templating kept
import itertools
sizes = len(kept)
rand_zs = []
for _ in range(8):
    sub = random.sample(list(books), sizes)
    rand_zs.append(aggregate_z([segs_of(books[k]) for k in sub], EN, 150))
print(f"aggregate z of random same-size subsets (templates retained): "
      f"{[f'{z:+.2f}' for z in rand_zs]}")
con.close()
