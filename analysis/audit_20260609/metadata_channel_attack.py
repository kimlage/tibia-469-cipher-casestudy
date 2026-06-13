#!/usr/bin/env python3
"""
Attack: book metadata as a covert channel (lengths, ordering, clusterid letterings).
Tibia 469 Bonelord cipher. Read-only DB access. Permutation-null discipline.
"""
import sqlite3, random, math, sys
from collections import Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
N_PERM = 1000
random.seed(469)

# ---------------- data ----------------
con = sqlite3.connect(DB, uri=True)
rows = con.execute(
    "SELECT bookid, clusterid, baselen, digitslen, insertedzeros "
    "FROM sheet__books GROUP BY bookid ORDER BY CAST(bookid AS INTEGER)"
).fetchall()
con.close()
print(f"[data] rows fetched: {len(rows)}")
assert len(rows) == 70, "expected 70 deduped books"

bookid   = [int(r[0]) for r in rows]
clusterid= [int(r[1]) for r in rows]
baselen  = [int(r[2]) for r in rows]
digitslen= [int(r[3]) for r in rows]
inszeros = [int(r[4]) for r in rows]
print(f"[data] baselen sum={sum(baselen)} digitslen sum={sum(digitslen)} "
      f"insertedzeros sum={sum(inszeros)} cluster0 count={clusterid.count(0)} "
      f"n_clusters={len(set(clusterid))}")

# cluster-then-bookid ordering (stable: clusterid asc, then bookid asc)
order_cluster = sorted(range(70), key=lambda i: (clusterid[i], bookid[i]))

# ---------------- dictionary + trigram LM ----------------
ENG_EXTRA = set()
GERMAN = """aber alle allem allen aller alles also andere anderen auch
auf aus bei bin bist dann das dass dein deine dem den der des dich die
dies diese diesem diesen dieser dieses doch dort durch eine einem einen
einer eines euch euer eure fuer gegen gewesen habe haben hast hatte
hatten hier hinter ich ihre ihrem ihren ihrer ihres immer kann kein
keine konnte machen mein meine meinem meinen meiner mich mir mit muss
nach nicht noch nur oder ohne sehr sein seine seinem seinen seiner sich
sie sind soll sondern uber unter viel vom von vor wann warum weil
welche wenn werden wieder wird wirst wurde zwischen geheim schatz
schluessel buch insel drachen tempel toten gott".split()"""
german_words = set(w for w in GERMAN.replace('"""','').replace(".split()","").split() if w.isalpha())

words = set()
with open("/usr/share/dict/words") as f:
    for w in f:
        w = w.strip().lower()
        if len(w) >= 4 and w.isalpha():
            words.add(w)
words |= {w for w in german_words if len(w) >= 4}
print(f"[dict] {len(words)} words len>=4 loaded")
MAXW = 12

# trigram LM built from dictionary words (relative scoring only; identical for null)
tri = Counter()
with open("/usr/share/dict/words") as f:
    for w in f:
        w = w.strip().lower()
        if len(w) >= 3 and w.isalpha():
            for i in range(len(w) - 2):
                tri[w[i:i+3]] += 1
tri_total = sum(tri.values())
V = 26**3
def tri_logp(t):
    return math.log((tri.get(t, 0) + 1) / (tri_total + V))

def letter_runs(s):
    runs, cur = [], []
    for ch in s.lower():
        if ch.isalpha():
            cur.append(ch)
        else:
            if cur: runs.append(''.join(cur)); cur = []
    if cur: runs.append(''.join(cur))
    return runs

def score_words(s):
    """count of (start,len) substring dictionary hits, len 4..12, over letter runs"""
    n = 0
    for run in letter_runs(s):
        L = len(run)
        for i in range(L):
            for j in range(i+4, min(i+MAXW, L)+1):
                if run[i:j] in words:
                    n += 1
    return n

def score_tri(s):
    tot, cnt = 0.0, 0
    for run in letter_runs(s):
        for i in range(len(run)-2):
            tot += tri_logp(run[i:i+3]); cnt += 1
    return tot/cnt if cnt else -999.0

# ---------------- decodings ----------------
def dec_a1z26_1(seq):  # 1=A..26=Z, 0->Z
    return ''.join(chr(ord('A') + (v-1) % 26) for v in seq)
def dec_a1z26_0(seq):  # 0=A..25=Z
    return ''.join(chr(ord('A') + v % 26) for v in seq)
def dec_ascii(seq):
    return ''.join(chr(v) if 32 <= v <= 126 else '.' for v in seq)
def dec_pair_ascii(seq):
    d = ''.join(str(abs(v)) for v in seq)
    out = []
    for i in range(0, len(d)-1, 2):
        c = int(d[i:i+2])
        out.append(chr(c) if 32 <= c <= 126 else '.')
    return ''.join(out)

DECODINGS = [("a1z26_1based", dec_a1z26_1), ("a1z26_0based", dec_a1z26_0),
             ("ascii_direct", dec_ascii), ("digitpair_ascii", dec_pair_ascii)]

def dsum(v):
    return sum(int(c) for c in str(v))

# sequence builders: take a base value list (in a given order) -> derived numeric seq
SEQ_BUILDERS = [
    ("baselen",        lambda b, d, z, c: b),
    ("digitslen",      lambda b, d, z, c: d),
    ("insertedzeros",  lambda b, d, z, c: z),
    ("clusterid",      lambda b, d, z, c: c),
    ("diff_baselen",   lambda b, d, z, c: [b[i+1]-b[i] for i in range(len(b)-1)]),
    ("diff_digitslen", lambda b, d, z, c: [d[i+1]-d[i] for i in range(len(d)-1)]),
    ("digitsum_baselen",   lambda b, d, z, c: [dsum(v) for v in b]),
    ("digitsum_digitslen", lambda b, d, z, c: [dsum(v) for v in d]),
]
ORDERINGS = [("bookid_order", list(range(70))), ("cluster_then_bookid", order_cluster)]

results = []
for oname, idx in ORDERINGS:
    b = [baselen[i] for i in idx]; d = [digitslen[i] for i in idx]
    z = [inszeros[i] for i in idx]; c = [clusterid[i] for i in idx]
    for sname, build in SEQ_BUILDERS:
        obs_seq = build(b, d, z, c)
        for dname, dec in DECODINGS:
            obs_str = dec(obs_seq)
            ow, ot = score_words(obs_str), score_tri(obs_str)
            # null: permute the PARENT vectors jointly (same multiset of books), rebuild
            pw, pt = [], []
            for _ in range(N_PERM):
                perm = list(range(70)); random.shuffle(perm)
                pb = [b[i] for i in perm]; pd = [d[i] for i in perm]
                pz = [z[i] for i in perm]; pc = [c[i] for i in perm]
                s = dec(build(pb, pd, pz, pc))
                pw.append(score_words(s)); pt.append(score_tri(s))
            def stats(obs, null):
                mu = sum(null)/len(null)
                sd = (sum((x-mu)**2 for x in null)/len(null))**0.5
                zsc = (obs-mu)/sd if sd > 0 else 0.0
                p = (1 + sum(1 for x in null if x >= obs)) / (1 + len(null))
                return mu, sd, zsc, p, max(null)
            wmu, wsd, wz, wp, wmax = stats(ow, pw)
            tmu, tsd, tz, tp, tmax = stats(ot, pt)
            flag = (ow > wmax) or (ot > tmax)
            results.append((oname, sname, dname, ow, wmu, wsd, wz, wp, wmax,
                            ot, tmu, tsd, tz, tp, tmax, flag, obs_str))

# ---------------- cluster-0 membership binary channel ----------------
bits = [1 if clusterid[i] == 0 else 0 for i in range(70)]
def bacon(bts, one='B'):
    out = []
    for i in range(0, len(bts)-4, 5):
        v = 0
        for bb in bts[i:i+5]:
            v = v*2 + (bb if one == 'B' else 1-bb)
        out.append(chr(ord('A')+v) if v < 26 else '?')
    return ''.join(out)
def ascii7(bts, inv=False):
    out = []
    for i in range(0, len(bts)-6, 7):
        v = 0
        for bb in bts[i:i+7]:
            v = v*2 + (bb if not inv else 1-bb)
        out.append(chr(v) if 32 <= v <= 126 else '.')
    return ''.join(out)

bin_decs = [("bacon_1isB", lambda x: bacon(x,'B')), ("bacon_0isB", lambda x: bacon(x,'A')),
            ("ascii7", lambda x: ascii7(x,False)), ("ascii7_inv", lambda x: ascii7(x,True))]
bin_results = []
for dname, dec in bin_decs:
    obs_str = dec(bits)
    ow, ot = score_words(obs_str), score_tri(obs_str)
    pw, pt = [], []
    for _ in range(N_PERM):
        pb = bits[:]; random.shuffle(pb)
        s = dec(pb)
        pw.append(score_words(s)); pt.append(score_tri(s))
    wmax, tmax = max(pw), max(pt)
    wp = (1+sum(1 for x in pw if x >= ow))/(1+N_PERM)
    tp = (1+sum(1 for x in pt if x >= ot))/(1+N_PERM)
    bin_results.append((dname, obs_str, ow, wmax, wp, ot, tmax, tp, ow > wmax or ot > tmax))

# ---------------- report ----------------
print("\n=== sequence-channel results (ordering | sequence | decoding) ===")
print(f"{'ordering':<20} {'sequence':<20} {'decoding':<16} "
      f"{'wHit':>4} {'wMax':>4} {'w_p':>7} {'w_z':>6}  {'triZ':>6} {'tri_p':>7} flag")
n_flag = 0
for r in results:
    (oname, sname, dname, ow, wmu, wsd, wz, wp, wmax,
     ot, tmu, tsd, tz, tp, tmax, flag, obs_str) = r
    if flag: n_flag += 1
    print(f"{oname:<20} {sname:<20} {dname:<16} "
          f"{ow:>4} {wmax:>4} {wp:>7.4f} {wz:>6.2f}  {tz:>6.2f} {tp:>7.4f} {'<<<' if flag else ''}")
print(f"\n[summary] {len(results)} sequence tests, {n_flag} exceeded permutation max")

print("\n=== cluster-0 membership binary channel ===")
print("bits:", ''.join(str(x) for x in bits))
for dname, obs_str, ow, wmax, wp, ot, tmax, tp, flag in bin_results:
    print(f"{dname:<12} '{obs_str}'  wHit={ow} (permMax={wmax}, p={wp:.4f}) "
          f"tri_p={tp:.4f} {'<<<' if flag else ''}")

print("\n=== decoded strings for any flagged tests (manual inspection) ===")
for r in results:
    if r[15]:
        print(f"{r[0]} | {r[1]} | {r[2]} -> '{r[16]}'  wHits={r[3]} permMax={r[8]} "
              f"w_p={r[7]:.4f} tri_p={r[13]:.4f}")
if n_flag == 0:
    print("(none)")

# always show a few observed strings for the record
print("\n=== sample observed decodings (bookid order) ===")
for r in results:
    if r[0] == "bookid_order" and r[2] in ("a1z26_1based", "ascii_direct"):
        print(f"{r[1]:<20} {r[2]:<14} '{r[16]}'")
