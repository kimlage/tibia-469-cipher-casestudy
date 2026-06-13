#!/usr/bin/env python3
"""Battery: metadata channels + segmentation tests + forbidden-bigram significance."""
import sqlite3, math, collections, random

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, digits, insertedzeros, baselen, decodedbase FROM sheet__books GROUP BY bookid").fetchall()
print("ROWCOUNT", len(rows)); assert len(rows)==70
books = {r[0]: dict(digits=r[1], iz=r[2], baselen=r[3], dec=r[4]) for r in rows}

# --- metadata semantics ---
print("\n--- metadata sample (5 books) ---")
for bid in list(sorted(books, key=lambda x: int(x) if x.isdigit() else 0))[:5]:
    b = books[bid]
    print(bid, "len(digits)=", len(b["digits"]), "iz=", repr(b["iz"])[:60], "baselen=", b["baselen"], "len(dec)=", len(b["dec"]) if b["dec"] else None)

print("\n--- length relations ---")
mismatch = 0
parity_odd = 0
for bid, b in books.items():
    L = len(b["digits"])
    if L % 2 == 1: parity_odd += 1
    try: bl = int(b["baselen"])
    except: bl = None
    izs = b["iz"]
    # count inserted zeros if it's a list-ish string
    if bl is not None:
        if L != bl: mismatch += 1
print("books with odd digit length:", parity_odd, "of 70")
print("books where len(digits)!=baselen:", mismatch)

# distribution of iz field
print("\niz field samples:", [books[b]["iz"] for b in list(books)[:8]])
print("baselen values:", sorted(collections.Counter(int(books[b]["baselen"]) for b in books).items())[:20])

# relation len(dec) vs len(digits)
ratios = []
for bid, b in books.items():
    if b["dec"]:
        ratios.append((bid, len(b["digits"]), int(b["baselen"]), len(b["dec"])))
print("\nbid, len(digits), baselen, len(dec) for 10 books:")
for t in ratios[:10]: print(t)
r = [t[2]/t[3] for t in ratios if t[3]]
print("baselen/len(dec) min %.3f max %.3f" % (min(r), max(r)))
r2 = [t[1]-t[2] for t in ratios]
print("len(digits)-baselen distribution:", sorted(collections.Counter(r2).items()))

# --- forbidden bigram significance via within-book shuffle ---
def count_bg(target):
    def f(seqs):
        tot = 0
        for d in seqs:
            for i in range(len(d)-1):
                if d[i:i+2] == target: tot += 1
        return tot
    return f

seqs = [b["digits"] for b in books.values()]
rng = random.Random(469)
NTRIAL = 300
for target in ["07","32","33","19","11"]:
    obs = count_bg(target)(seqs)
    sims = []
    for t in range(NTRIAL):
        sh = ["".join(rng.sample(d, len(d))) for d in seqs]
        sims.append(count_bg(target)(sh))
    mu = sum(sims)/NTRIAL; sd = (sum((x-mu)**2 for x in sims)/NTRIAL)**0.5
    print("bigram %s: obs=%d shuffle mu=%.1f sd=%.1f z=%+.2f" % (target, obs, mu, sd, (obs-mu)/sd if sd else float('nan')))

# --- segmentation: fixed-2 vs fixed-3 vs variable ---
import zlib
all_d = "".join(seqs)

def token_stats(tokens):
    c = collections.Counter(tokens); n = len(tokens)
    H = -sum(v/n*math.log2(v/n) for v in c.values())
    return len(c), n, H, H*n  # vocab, count, per-token entropy, total bits (order-0)

print("\n--- segmentation comparisons (per-book tokenization, order-0 MDL bits/digit) ---")
for k in [1,2,3,4]:
    toks = []
    for d in seqs:
        toks += [d[i:i+k] for i in range(0, len(d)-k+1, k)]
    v, n, H, bits = token_stats(toks)
    # MDL: model cost = vocab * k * log2(10) approx + data cost
    model = v * (k*math.log2(10) + math.log2(max(n,2)))
    print("fixed-%d: vocab=%d tokens=%d H=%.3f bits/digit=%.4f (+model=%.4f)" % (k, v, n, H, H/k, (bits+model)/len(all_d)))

# unique token growth: how fast does 2-gram aligned vocab saturate vs unaligned
c_aligned = set(); c_all = set()
for d in seqs:
    for i in range(0, len(d)-1, 2): c_aligned.add(d[i:i+2])
    for i in range(len(d)-1): c_all.add(d[i:i+2])
print("2-digit vocab aligned-even-start: %d ; all offsets: %d" % (len(c_aligned), len(c_all)))
# also aligned odd start
c_odd = set()
for d in seqs:
    for i in range(1, len(d)-1, 2): c_odd.add(d[i:i+2])
print("2-digit vocab aligned-odd-start: %d" % len(c_odd))

# zlib compressibility
print("\nzlib len(all)=%d  comp=%d ratio=%.4f" % (len(all_d), len(zlib.compress(all_d.encode(),9)), len(zlib.compress(all_d.encode(),9))/len(all_d)))
sh = "".join(rng.sample(all_d, len(all_d)))
print("shuffled comp=%d" % len(zlib.compress(sh.encode(),9)))
con.close()
