#!/usr/bin/env python3
"""Claim 7: does letter ORDER in decodedbase carry an English/language signal?
Measure: conditional bigram log-prob under an English bigram model, observed vs
shuffles of the book's own letters (stars fixed as segment breaks).
Controls:
  (a) relabel control - random permutations of the 13 book letters before scoring
      under the SAME English model (destroys English identity, keeps order+skew)
  (b) leave-one-out corpus bigram model (trained on other 69 books) - measures
      internal/templated order structure directly.
"""
import sqlite3, math, random, statistics
from collections import Counter, defaultdict

random.seed(469)
URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("""SELECT bookid, MIN(decodedbase) FROM sheet__books GROUP BY bookid""").fetchall()
print("ROWCOUNT:", len(rows)); assert rows
books = dict(rows)

# ---------- English bigram model from embedded prose ----------
PROSE = """
The morning light came slowly over the hills, and the small town below began to
stir. Shopkeepers unlocked their doors and swept the steps, while the baker set
out loaves of warm bread that filled the street with a comfortable smell. A few
children hurried along the lane with their satchels, calling to one another and
laughing at some private joke. The river that ran through the middle of the town
moved quietly under the old stone bridge, carrying leaves and small branches
down toward the distant sea.

In those days people did not travel far from the places where they were born.
A journey to the next county was something to plan for weeks, and a voyage
across the water was the adventure of a lifetime. News arrived late and often
changed in the telling, so that by the time a story reached the far villages it
had grown strange and wonderful. Still, the farmers knew the weather and the
soil, the fishermen knew the tides, and the old women knew the history of every
family for three generations back. Knowledge of that kind does not appear in
books, but it held the place together more surely than any law.

When the war finally ended, the men who returned found the fields overgrown and
the fences fallen, and they set to work without much complaint because there
was nothing else to be done. Within a few years the orchards were bearing
again, and the market square filled every week with carts of vegetables, wool,
and cheese. People measured their lives by harvests and holidays rather than
by clocks. If you had asked them whether they were happy they would have
shrugged, but in the evenings there was singing in the public house, and on
summer nights the young people walked along the river until the stars came out.

Science in the modern sense had not yet touched the town. Illness was treated
with herbs and patience, and the doctor, when he came, often could do little
more than the herbs had done. Yet the people were curious about the world.
They watched the birds return each spring and argued about where they had
been. They noticed that the moon pulled the tides and that certain winds
brought rain. Their explanations were wrong as often as right, but the habit
of looking closely at things is the seed of all understanding, and that habit
they had in abundance.

The schoolmaster kept a shelf of books at the front of the room, and any child
who finished the day's work early was allowed to read them. There was a book
of maps with the countries colored like quilts, a history of ancient kings,
and a volume of natural philosophy that explained, with serious diagrams, why
the sky is blue and how a seed becomes a tree. More than one farmer's son sat
with that volume open long after the light had gone gray, and a few of them
left the valley in the end, carrying questions the village could not answer.
Those who stayed told their own children about the wider world with a mixture
of pride and regret, which is perhaps the oldest story there is.
"""

def train_bigram(text_words, alphabet, alpha=0.5):
    uni, bi = Counter(), Counter()
    for w in text_words:
        for a, b in zip(w, w[1:]):
            bi[(a, b)] += 1; uni[a] += 1
    V = len(alphabet)
    logp = {}
    for a in alphabet:
        den = uni[a] + alpha * V
        for b in alphabet:
            logp[(a, b)] = math.log((bi[(a, b)] + alpha) / den)
    return logp

import re
AZ = [chr(c) for c in range(97, 123)]
words = re.findall(r"[a-z]+", PROSE.lower())
EN = train_bigram(words, AZ)

def score(segments, logp):
    s = 0.0; n = 0
    for seg in segments:
        for a, b in zip(seg, seg[1:]):
            s += logp[(a, b)]; n += 1
    return s / max(n, 1)

def zscore(base, logp, nshuf, relabel=None):
    segs = [seg.lower() for seg in base.split("*") if len(seg) >= 2]
    if relabel:
        segs = [seg.translate(relabel) for seg in segs]
    obs = score(segs, logp)
    letters = list("".join(segs))
    lens = [len(s) for s in segs]
    sh = []
    for _ in range(nshuf):
        random.shuffle(letters)
        out, i = [], 0
        for L in lens:
            out.append("".join(letters[i:i+L])); i += L
        sh.append(score(out, logp))
    mu, sd = statistics.fmean(sh), statistics.stdev(sh)
    return (obs - mu) / sd if sd > 0 else float("nan")

# ---------- book selection: 10 longest + 2 median ----------
order = sorted(books, key=lambda b: -len(books[b]))
sel = order[:10] + [order[len(order)//2], order[len(order)//2 + 1]]
print("selected books (id,len):", [(b, len(books[b])) for b in sel])

# ---------- leave-one-out corpus model ----------
BOOK_AZ = sorted(set("abcefilnorstv"))
def corpus_model(exclude):
    segs = []
    for bid, t in books.items():
        if bid == exclude: continue
        segs += [s.lower() for s in t.split("*") if len(s) >= 2]
    return train_bigram(segs, BOOK_AZ)

# ---------- run ----------
NSHUF = 300; NRELAB = 30; NSHUF_RELAB = 200
print(f"\nbook  len   z_EN({NSHUF}sh)   relabel z: mean/min/max of {NRELAB} perms   z_corpusLOO")
zs_en, zs_rel_all, zs_corpus = [], [], []
for bid in sel:
    base = books[bid]
    z_en = zscore(base, EN, NSHUF)
    rel_zs = []
    for _ in range(NRELAB):
        perm = BOOK_AZ[:]
        random.shuffle(perm)
        table = str.maketrans(dict(zip(BOOK_AZ, perm)))
        rel_zs.append(zscore(base, EN, NSHUF_RELAB, relabel=table))
    zc = zscore(base, corpus_model(bid), NSHUF)
    zs_en.append(z_en); zs_rel_all.append(rel_zs); zs_corpus.append(zc)
    print(f"{bid:>4} {len(base):4d}   {z_en:+7.2f}      "
          f"{statistics.fmean(rel_zs):+6.2f} / {min(rel_zs):+6.2f} / {max(rel_zs):+6.2f}      {zc:+7.2f}")

flat = [z for zz in zs_rel_all for z in zz]
n_rel_ge = sum(1 for z in flat if z >= statistics.fmean(zs_en))
print(f"\nsummary: z_EN mean={statistics.fmean(zs_en):+.2f} range "
      f"[{min(zs_en):+.2f},{max(zs_en):+.2f}]")
print(f"relabel-control z: mean={statistics.fmean(flat):+.2f} "
      f"range [{min(flat):+.2f},{max(flat):+.2f}]; "
      f"{sum(1 for z in flat if z > 2):d}/{len(flat)} perms exceed z=+2")
print(f"corpus-LOO z: mean={statistics.fmean(zs_corpus):+.2f} "
      f"range [{min(zs_corpus):+.2f},{max(zs_corpus):+.2f}]")
# per-book: is z_EN an outlier among its own relabel distribution?
print("\nper-book percentile of z_EN within its relabel-control distribution:")
for bid, z_en, rel in zip(sel, zs_en, zs_rel_all):
    pct = 100 * sum(1 for r in rel if r < z_en) / len(rel)
    print(f"  book {bid:>4}: z_EN={z_en:+6.2f} is at {pct:5.1f}th pct of relabel z "
          f"(mean {statistics.fmean(rel):+5.2f})")
con.close()
