#!/usr/bin/env python3
"""
PRE-REGISTERED split-half language-residual test on the deduplicated novel corpus.
Bonelord 469 audit, 2026-06-10. All rules below were fixed BEFORE any half-specific
statistic was computed (full-corpus values for EN/DE order were already public from
the fresh-eyes lane: EN +2.71 / DE +4.45 on novel-only; those are the claims under test).

--- PRE-REGISTRATION ---

OBJECT (novel-content corpus), exactly the fresh-eyes (s8_final.py) rule:
  * Books: SELECT bookid, decodedbase FROM sheet__books GROUP BY bookid (70 rows,
    asserted), processed in ascending int(bookid) order.
  * Greedy left-to-right scan per book: at position i, if the 12-symbol window
    t[i:i+12] occurs anywhere in 'seen' (the '#'-joined concatenation of all PRIOR
    books), extend the match maximally (cap 200) and mask those symbols; else keep
    t[i] and advance 1. Within-book repeats are NOT masked (only cross-book), and
    masking is first-occurrence-keeps: the first book containing a span keeps it.
  * Kept runs of length>=2 become spans. Expected: 100 spans, 1772 symbols.
  * DEVIATION from s8 (declared now): each span is further split at '*' (the
    omission/space symbol; excluded from all statistics) and resulting subsegments
    of length<2 are dropped. Subsegments are the analysis units; bigrams never
    cross a subsegment boundary.

SPLIT (mechanical, no peeking): subsegments enumerated in extraction order
  (book order, then position). Even index -> HALF A, odd index -> HALF B.

FOUR STATISTICS, computed identically and independently on each half
  (and on the combined corpus for reference). Symbols read as letters by
  IDENTITY (A=a ... V=v); seeds fixed (numpy-free, random.Random(20260610)).
  (a) EN-IDENTITY: mean unigram log-prob under English letter frequencies
      (Lewand 1999, standard published table). Null = 1000 random relabelings:
      a uniform random permutation of the 13 letters assigned to the 13 symbols
      (preserves the corpus frequency profile exactly).
  (b) EN-ORDER: mean bigram log-prob under the English bigram table used by the
      fresh-eyes lane (top-50 published English bigram percentages, Practical-
      Cryptography/Cornell-style, +0.005 smoothing over 26x26) -- SAME table as
      the claim under test. Null = 1000 within-subsegment symbol shuffles.
  (c) DE-ORDER: same with the German bigram table (top-39 published German
      bigram percentages, Beutelspacher-style, same smoothing) -- same table the
      DE claim was made with. Same 1000 shuffles.
  (d) DE-vs-EN CONTRAST: observed (mean DE logp - mean EN logp); null = the same
      1000 shuffle replicates' (DE-EN) differences. Tests whether the German
      preference over English survives shuffling (i.e., is an ORDER property).

DECISION RULE (fixed now): a signal is REAL only if z >= +3.00 in BOTH halves
  independently with the same sign. 2.0 <= z < 3.0 in both halves = WEAK/UNRESOLVED.
  Failing in either half = NOT_REPLICABLE at this sample size.

POWER SIMULATION: encode genuine German and genuine English prose through the
  actual 13-symbol merge and measure the z each statistic yields at matched n.
  Merge rule (declared; Latin-orthography motivated -- the corpus alphabet has V
  but no U, I but no J): identity on abcefilnorstv; u->v, j->i (Latin); d->t,
  g->c, k->c, q->c, p->b (voicing/place merge to nearest in-set stop);
  h->f (fricative), m->n (nasal), w->v, y->i, x->s, z->s (sibilant);
  umlauts a"->a, o"->o, u"->v, ss->s. Non-letters dropped.
  The merged text is cut into consecutive chunks matching HALF A's exact
  subsegment-length profile (same n symbols, same segmentation), at 3 different
  text offsets; all four statistics run identically; report each offset + mean.
  Interpretation rule (fixed now): if injected-real-language mean z exceeds the
  observed corpus z by a factor >=2 at matched n, the observed signal is
  quantitatively too weak to be straight-encoded language.

RECONCILIATION TESTS (explain DE-order vs failed 99-code homophonic split-half):
  (R1) MOTIF NULL: hypothesis = DE-order signal is sub-12-symbol repeated-motif
       structure surviving the dedupe, not language. Tokenize each subsegment
       greedily (longest-first, length 4..11) into motifs that occur >=2 times
       across the whole novel corpus; remaining symbols are singleton tokens.
       Null = 1000 within-subsegment TOKEN-order shuffles (preserves motif
       interiors). If DE z under the motif null < 2 while < the symbol-shuffle z,
       the signal lives INSIDE repeated motifs -> generic structure, not language.
       Run on combined corpus and per half.
  (R2) EDGE CONCENTRATION: bigrams within 3 symbols of a subsegment boundary
       (= adjacent to masked module-covered text or '*') vs interior bigrams.
       Observed mean DE logp per class, z per class under the same within-
       subsegment symbol shuffles (positions fixed). If the DE signal sits in
       edge bigrams, it is module-boundary leakage, not running text.

--- END PRE-REGISTRATION ---
"""
import sqlite3, math, random, collections

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
SEED = 20260610
NSHUF = 1000
SYMS = "ABCEFILNORSTV"

# ---------- data ----------
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, decodedbase FROM sheet__books GROUP BY bookid").fetchall()
print("ROWCOUNT", len(rows)); assert len(rows) == 70, "silent-empty guard"
dec = {r[0]: r[1] for r in rows}
ids = sorted(dec, key=int)
con.close()

# ---------- novel extraction (s8 rule, verbatim logic) ----------
seen = ""
novel_spans = []
for b in ids:
    t = dec[b]
    flags = [True] * len(t)
    i = 0
    while i < len(t):
        hi = min(len(t) - i, 200)
        lo = 12
        if i + lo <= len(t) and t[i:i+lo] in seen:
            L = lo
            while L < hi and i + L + 1 <= len(t) and t[i:i+L+1] in seen:
                L += 1
            for k in range(i, min(i + L, len(t))):
                flags[k] = False
            i += L
        else:
            i += 1
    cur = ""
    spans = []
    for k, fl in enumerate(flags):
        if fl:
            cur += t[k]
        else:
            if len(cur) >= 2: spans.append(cur)
            cur = ""
    if len(cur) >= 2: spans.append(cur)
    novel_spans += spans
    seen += "#" + t
print("novel spans: %d, symbols: %d (expect 100 / 1772)" % (len(novel_spans), sum(map(len, novel_spans))))

# split at '*'
segs = []
for sp in novel_spans:
    for part in sp.split("*"):
        if len(part) >= 2:
            segs.append(part)
print("subsegments after '*' split: %d, symbols: %d, bigrams: %d" %
      (len(segs), sum(map(len, segs)), sum(len(s) - 1 for s in segs)))

halfA = [s for i, s in enumerate(segs) if i % 2 == 0]
halfB = [s for i, s in enumerate(segs) if i % 2 == 1]
for nm, h in [("A", halfA), ("B", halfB)]:
    print("half %s: %d segs, %d symbols, %d bigrams" % (nm, len(h), sum(map(len, h)), sum(len(s)-1 for s in h)))

# ---------- language tables ----------
EN_UNI = {'e':12.702,'t':9.056,'a':8.167,'o':7.507,'i':6.966,'n':6.749,'s':6.327,'h':6.094,
          'r':5.987,'d':4.253,'l':4.025,'c':2.782,'u':2.758,'m':2.406,'w':2.360,'f':2.228,
          'g':2.015,'y':1.974,'p':1.929,'b':1.492,'v':0.978,'k':0.772,'j':0.153,'x':0.150,
          'q':0.095,'z':0.074}
EN_BIG = {"th":3.56,"he":3.07,"in":2.43,"er":2.05,"an":1.99,"re":1.85,"on":1.76,"at":1.49,"en":1.45,"nd":1.35,
"ti":1.34,"es":1.34,"or":1.28,"te":1.20,"of":1.17,"ed":1.17,"is":1.13,"it":1.12,"al":1.09,"ar":1.07,
"st":1.05,"to":1.05,"nt":1.04,"ng":0.95,"se":0.93,"ha":0.93,"as":0.87,"ou":0.87,"io":0.83,"le":0.83,
"ve":0.83,"co":0.79,"me":0.79,"de":0.76,"hi":0.76,"ri":0.73,"ro":0.73,"ic":0.70,"ne":0.69,"ea":0.69,
"ra":0.69,"ce":0.65,"li":0.62,"ch":0.60,"ll":0.58,"be":0.58,"ma":0.57,"si":0.55,"om":0.55,"ur":0.54}
DE_BIG = {"en":3.88,"er":3.75,"ch":2.75,"de":2.03,"ei":1.98,"nd":1.93,"te":1.93,"in":1.71,"ie":1.63,"ge":1.47,
"es":1.52,"ne":1.31,"un":1.32,"st":1.21,"re":1.17,"he":1.14,"an":1.07,"be":1.07,"se":1.07,"ng":1.06,
"di":1.05,"sc":1.06,"is":0.94,"it":0.96,"ic":1.0,"da":0.69,"el":0.87,"au":0.74,"li":0.65,
"ns":0.74,"al":0.66,"le":0.64,"si":0.63,"ra":0.62,"ar":0.61,"ht":0.58,"ti":0.58,"eh":0.55,"ru":0.46}
def mk_logp(tb):
    tot = sum(tb.values()); base = 0.005
    return {a+b: math.log((tb.get(a+b,0)+base)/(tot+base*676))
            for a in "abcdefghijklmnopqrstuvwxyz" for b in "abcdefghijklmnopqrstuvwxyz"}
LPE, LPD = mk_logp(EN_BIG), mk_logp(DE_BIG)
LU_EN = {c: math.log(v/100.0) for c, v in EN_UNI.items()}

def biscore(seglist, lp):
    s = n = 0
    for sp in seglist:
        t = sp.lower()
        for i in range(len(t)-1):
            s += lp[t[i:i+2]]; n += 1
    return s, n

def uniscore(seglist, mapping):
    # mapping: SYM(upper) -> letter(lower)
    s = n = 0
    for sp in seglist:
        for ch in sp:
            s += LU_EN[mapping[ch]]; n += 1
    return s, n

def zval(obs, sims):
    mu = sum(sims)/len(sims)
    sd = (sum((x-mu)**2 for x in sims)/len(sims))**0.5
    return (obs-mu)/sd, mu, sd

# ---------- the four statistics ----------
def run_stats(seglist, label, rng):
    out = {}
    # (a) EN-identity unigram, relabel null
    ident = {c: c.lower() for c in SYMS}
    so, n = uniscore(seglist, ident); obs = so/n
    letters = [c.lower() for c in SYMS]
    sims = []
    for _ in range(NSHUF):
        perm = letters[:]; rng.shuffle(perm)
        m = {c: perm[k] for k, c in enumerate(SYMS)}
        s, _ = uniscore(seglist, m); sims.append(s/n)
    z, mu, sd = zval(obs, sims)
    out['a_EN_identity'] = (obs, mu, sd, z, n)
    # (b)(c)(d) shared shuffle replicates
    se, ne = biscore(seglist, LPE); obs_e = se/ne
    sd_, nd_ = biscore(seglist, LPD); obs_d = sd_/nd_
    obs_c = obs_d - obs_e
    sims_e, sims_d, sims_c = [], [], []
    for _ in range(NSHUF):
        sh = []
        for sp in seglist:
            l = list(sp); rng.shuffle(l); sh.append("".join(l))
        e, _ = biscore(sh, LPE); d, _ = biscore(sh, LPD)
        sims_e.append(e/ne); sims_d.append(d/nd_); sims_c.append(d/nd_ - e/ne)
    for key, obsv, sims, nn in [('b_EN_order', obs_e, sims_e, ne),
                                ('c_DE_order', obs_d, sims_d, nd_),
                                ('d_DEminusEN', obs_c, sims_c, ne)]:
        z, mu, sd2 = zval(obsv, sims)
        out[key] = (obsv, mu, sd2, z, nn)
    print("\n== %s ==" % label)
    for k in ['a_EN_identity','b_EN_order','c_DE_order','d_DEminusEN']:
        o, mu, sd2, z, nn = out[k]
        print("  %-13s obs=%+.4f null mu=%+.4f sd=%.4f  z=%+.2f  (n=%d)" % (k, o, mu, sd2, z, nn))
    return out

rng = random.Random(SEED)
resA = run_stats(halfA, "HALF A (even segs)", rng)
resB = run_stats(halfB, "HALF B (odd segs)", rng)
resF = run_stats(segs,  "COMBINED (all novel)", rng)

# ---------- power simulation ----------
DE_TEXT = """
Der alte Bibliothekar stieg jeden Morgen die schmale Treppe hinauf und oeffnete die
schweren Laeden, damit das Licht auf die Regale fallen konnte. Seit vielen Jahren
ordnete er die Buecher nach einem System, das nur er selbst verstand, und niemand
in der Stadt haette gewagt, ihn danach zu fragen. Die Menschen brachten ihm ihre
alten Schriften, zerfallene Hefte und vergilbte Briefe, und er nahm alles entgegen,
als waere es ein kostbarer Schatz. In den langen Wintern sass er am Fenster und las,
waehrend der Schnee leise gegen die Scheiben fiel und die Strassen unter einer
weissen Decke verschwanden. Manchmal kamen Kinder in die Bibliothek und wollten
Geschichten hoeren, und dann erzaehlte er ihnen von fernen Laendern, von Schiffen
auf dem Meer und von Staedten, deren Namen laengst vergessen waren. Er sprach
langsam und deutlich, und seine Stimme fuellte den ganzen Raum, sodass selbst die
unruhigsten Kinder still wurden und zuhoerten. Am Abend, wenn die letzten Besucher
gegangen waren, loeschte er die Lampen und ging durch die dunklen Gaenge, um zu
pruefen, ob alle Buecher an ihrem Platz standen. Es war ihm wichtig, dass die
Ordnung erhalten blieb, denn er glaubte, dass jedes Buch seinen bestimmten Ort
habe und dass die Welt ein wenig besser werde, wenn man die Dinge dort liesse, wo
sie hingehoerten. Eines Tages fand er zwischen den Seiten eines alten Woerterbuchs
einen Brief, der nie abgeschickt worden war. Die Schrift war fein und sorgfaeltig,
und die Worte erzaehlten von einer Reise, die jemand vor langer Zeit geplant und
niemals angetreten hatte. Der Bibliothekar las den Brief wieder und wieder, und in
der Nacht traeumte er von Bahnhoefen und Haefen, von Koffern und von Wegen, die er
selbst nie gegangen war. Am naechsten Morgen legte er den Brief zurueck an seinen
Platz und beschloss, dass auch ungeschriebene Geschichten ihren Ort in der Welt
haben muessen, und dass es seine Aufgabe sei, diesen Ort zu bewahren, solange er
die Treppe noch hinaufsteigen konnte und seine Augen das Licht ertrugen.
"""
EN_TEXT = """
The old librarian climbed the narrow staircase every morning and opened the heavy
shutters so that the light could fall across the shelves. For many years he had
arranged the books according to a system that only he understood, and nobody in
the town would have dared to question him about it. People brought him their old
papers, crumbling notebooks and yellowed letters, and he accepted everything as
though it were a precious treasure. In the long winters he sat by the window and
read while the snow fell softly against the panes and the streets disappeared
under a white blanket. Sometimes children came into the library and asked for
stories, and then he told them about distant countries, about ships on the sea
and about cities whose names had long been forgotten. He spoke slowly and
clearly, and his voice filled the whole room, so that even the most restless
children grew quiet and listened. In the evening, when the last visitors had
gone, he put out the lamps and walked through the dark aisles to make sure that
every book stood in its proper place. It mattered to him that the order should
be preserved, for he believed that every book had its appointed place and that
the world became a little better when things were left where they belonged. One
day he found, between the pages of an old dictionary, a letter that had never
been sent. The handwriting was fine and careful, and the words told of a journey
that someone had planned long ago and never taken. The librarian read the letter
again and again, and that night he dreamed of stations and harbours, of trunks
and suitcases and of roads he himself had never travelled. The next morning he
put the letter back in its place and decided that unwritten stories too must
have their place in the world, and that it was his task to guard that place for
as long as he could still climb the stairs and his eyes could bear the light.
"""
MERGE = {c: c for c in "abcefilnorstv"}
MERGE.update({'u':'v','j':'i','d':'t','g':'c','k':'c','q':'c','p':'b',
              'h':'f','m':'n','w':'v','y':'i','x':'s','z':'s'})
def merge_text(txt):
    out = []
    for ch in txt.lower():
        if ch in MERGE: out.append(MERGE[ch].upper())
    return "".join(out)

def inject_and_test(raw, lab, lengths, rng):
    enc = merge_text(raw)
    need = sum(lengths)
    print("\n-- POWER: injected %s (merged length %d, need %d/offset) --" % (lab, len(enc), need))
    zs = {'a': [], 'b': [], 'c': [], 'd': []}
    for off_i, off in enumerate([0, (len(enc)-need)//2, len(enc)-need]):
        pos = off; chunks = []
        for L in lengths:
            chunks.append(enc[pos:pos+L]); pos += L
        r = run_stats(chunks, "%s offset %d" % (lab, off), rng)
        zs['a'].append(r['a_EN_identity'][3]); zs['b'].append(r['b_EN_order'][3])
        zs['c'].append(r['c_DE_order'][3]);    zs['d'].append(r['d_DEminusEN'][3])
    print("POWER %s mean z: a=%+.2f b=%+.2f c=%+.2f d=%+.2f" %
          (lab, sum(zs['a'])/3, sum(zs['b'])/3, sum(zs['c'])/3, sum(zs['d'])/3))
    return zs

lensA = [len(s) for s in halfA]
pw_de = inject_and_test(DE_TEXT, "GERMAN", lensA, rng)
pw_en = inject_and_test(EN_TEXT, "ENGLISH", lensA, rng)

# ---------- R1: motif-token null ----------
def motif_set(seglist):
    cnt = collections.Counter()
    for sp in seglist:
        for k in range(4, 12):
            for i in range(len(sp)-k+1):
                cnt[sp[i:i+k]] += 1
    return {m for m, c in cnt.items() if c >= 2}

def tokenize(sp, motifs):
    toks = []; i = 0
    while i < len(sp):
        for k in range(min(11, len(sp)-i), 3, -1):
            if sp[i:i+k] in motifs:
                toks.append(sp[i:i+k]); i += k; break
        else:
            toks.append(sp[i]); i += 1
    return toks

def motif_null(seglist, label, rng):
    motifs = motif_set(segs)   # motif inventory always from FULL novel corpus
    tok = [tokenize(sp, motifs) for sp in seglist]
    ntok = sum(len(t) for t in tok)
    nmot = sum(1 for t in tok for x in t if len(x) > 1)
    symin = sum(len(x) for t in tok for x in t if len(x) > 1)
    sd_, nd_ = biscore(seglist, LPD); obs = sd_/nd_
    sims = []
    for _ in range(NSHUF):
        sh = []
        for t in tok:
            l = t[:]; rng.shuffle(l); sh.append("".join(l))
        d, n = biscore(sh, LPD); sims.append(d/n)
    z, mu, sd2 = zval(obs, sims)
    print("MOTIF-NULL DE %s: obs=%+.4f mu=%+.4f sd=%.4f z=%+.2f | tokens=%d multi-sym motifs=%d (%d syms, %.0f%% of half)" %
          (label, obs, mu, sd2, z, ntok, nmot, symin, 100*symin/sum(map(len, seglist))))
    return z

print("\n-- R1: motif-token-order null (DE) --")
zm_F = motif_null(segs, "COMBINED", rng)
zm_A = motif_null(halfA, "HALF A", rng)
zm_B = motif_null(halfB, "HALF B", rng)

# ---------- R2: edge vs interior ----------
def edge_split(seglist, rng):
    def classify(sp):
        # bigram i is edge if within 3 symbols of either end
        return [(i < 3 or i > len(sp) - 5) for i in range(len(sp)-1)]
    cls = [classify(sp) for sp in seglist]
    def means(lst):
        se = si = ne = ni = 0
        for sp, cl in zip(lst, cls):
            t = sp.lower()
            for i in range(len(t)-1):
                v = LPD[t[i:i+2]]
                if cl[i]: se += v; ne += 1
                else: si += v; ni += 1
        return (se/ne if ne else 0, ne), (si/ni if ni else 0, ni)
    (oe, ne_), (oi, ni_) = means(seglist)
    sims_e, sims_i = [], []
    for _ in range(NSHUF):
        sh = []
        for sp in seglist:
            l = list(sp); rng.shuffle(l); sh.append("".join(l))
        (e, _), (i_, _) = means(sh)
        sims_e.append(e); sims_i.append(i_)
    ze, mue, sde = zval(oe, sims_e)
    zi, mui, sdi = zval(oi, sims_i)
    print("EDGE   (n=%4d): obs=%+.4f mu=%+.4f z=%+.2f" % (ne_, oe, mue, ze))
    print("INTERIOR(n=%4d): obs=%+.4f mu=%+.4f z=%+.2f" % (ni_, oi, mui, zi))

print("\n-- R2: DE-order edge (<=3 syms from segment boundary) vs interior, combined corpus --")
edge_split(segs, rng)

# ---------- verdict table ----------
print("\n==== DECISION (pre-registered rule: REAL iff z>=+3.00 in BOTH halves) ====")
for k in ['a_EN_identity','b_EN_order','c_DE_order','d_DEminusEN']:
    za, zb, zf = resA[k][3], resB[k][3], resF[k][3]
    real = "PASS" if (za >= 3 and zb >= 3) else "FAIL"
    print("  %-13s halfA z=%+.2f  halfB z=%+.2f  combined z=%+.2f  -> %s" % (k, za, zb, zf, real))
