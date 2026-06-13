#!/usr/bin/env python3
"""Part 2: token maps, projection decode, ML parse identity, controls."""
import sqlite3, json, math, random
from collections import Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
q = lambda s, *a: cur.execute(s, a).fetchall()

books = {}
for bid, digits, iz, bl, db_ in q("SELECT bookid, MIN(digits), MIN(insertedzeros), MIN(baselen), MIN(decodedbase) FROM sheet__books GROUP BY bookid"):
    books[bid] = dict(digits=digits, iz=int(iz), baselen=int(bl), decodedbase=db_)

K = q("SELECT sequence_digits FROM s2ward_corpus_audit_items WHERE source_set='sorted_unique_with_kharos' AND source_index=22")[0][0]

inv = q("SELECT code, symbol, occurrence_count, omitted_count, written_count FROM row0_code_symbol_counts WHERE run_id=1")
occ = Counter(); om = Counter(); wr = Counter(); c2s = {}
for c, s, o, omc, wrc in inv:
    occ[c]+=o; om[c]+=omc; wr[c]+=wrc; c2s[c]=s
valid_written = {c for c in c2s if wr[c] > 0}        # codes that may appear written
valid_omit = {c for c in c2s if om[c] > 0}           # codes that may appear omitted (0d only)

# ---------- token maps (0-based vs 1-based omitted token index) ----------
pb = q("SELECT bookid, reconstructed_code_stream, omitted_positions_json FROM row0_code_symbol_probe_books WHERE run_id=1")
def build(offset):
    maps = {}; ok = 0
    for bid, rcs, opj in pb:
        cs = rcs.split()
        omitted = set(x - offset for x in json.loads(opj))
        toks = []; pos = 0; raws = []
        for ti, c in enumerate(cs):
            emit = c[1] if ti in omitted else c
            toks.append((pos, len(emit), c, ti in omitted))
            raws.append(emit); pos += len(emit)
        if bid in books and "".join(raws) == books[bid]['digits']:
            ok += 1; maps[bid] = toks
    return ok, maps
ok0, m0 = build(0)
ok1, m1 = build(1)
print(f"byte-exact: 0-based {ok0}/70, 1-based {ok1}/70 (claim 70/70)")
tokmaps = m0 if ok0 >= ok1 else m1

# also verify code stream decodes to decodedbase via c2s
dec_ok = 0
for bid, rcs, opj in pb:
    cs = rcs.split()
    dec = "".join(c2s.get(c, '?') for c in cs)
    if dec == books[bid]['decodedbase']: dec_ok += 1
print(f"code-stream -> decodedbase via inventory map: {dec_ok}/70")

# ---------- chunks (from part 1, recompute) ----------
allcat = [(bid, b['digits']) for bid, b in books.items()]
def longest_at(s, i, minlen=8):
    for L in range(len(s)-i, minlen-1, -1):
        sub = s[i:i+L]
        for bid, d in allcat:
            j = d.find(sub)
            if j >= 0: return L, bid, j
    return 0, None, None
chunks = []; i = 0
while i < len(K):
    L, bid, j = longest_at(K, i)
    if L >= 8: chunks.append((i, L, bid, j)); i += L
    else: i += 1

# ---------- projection of book tokenizations onto chunks ----------
# For chunk (kpos, L, bid, j): book digit positions j..j+L-1.
# Find all occurrences of the substring in ALL books and all token-aligned projections.
proj_symbols = {}   # kharos digit pos -> set of (symbol) candidates from projections
proj_tokens_unique = 0
total_proj_positions = set()
print("\nPROJECTION per chunk:")
for (kpos, L, bid0, j0) in chunks:
    sub = K[kpos:kpos+L]
    projs = []
    for bid, d in allcat:
        st = 0
        while True:
            j = d.find(sub, st)
            if j < 0: break
            st = j + 1
            if bid not in tokmaps: continue
            toks = tokmaps[bid]
            # token-aligned: every token overlapping [j, j+L) lies fully inside
            inside = [t for t in toks if t[0] >= j and t[0] + t[1] <= j + L]
            cov = sum(t[1] for t in inside)
            if cov == L:
                projs.append((bid, j, inside))
    # unique projection = unique token sequence
    seqs = set(tuple((t[2], t[3]) for t in inside) for (_,_,inside) in projs)
    print(f"  chunk@{kpos} len={L}: {len(projs)} token-aligned occurrence(s), {len(seqs)} distinct token-seq(s); srcs={[(b,j) for b,j,_ in projs]}")
    if len(seqs) == 1:
        proj_tokens_unique += 1
    if projs:
        # take first projection, map symbols onto kharos positions
        for seqtup in [list(seqs)[0]]:
            pass
        bid, j, inside = projs[0]
        off = kpos - j
        for (p, n, c, omf) in inside:
            for dp in range(p, p+n):
                proj_symbols.setdefault(dp + off, set()).add(c2s[c])
                total_proj_positions.add(dp + off)
        # check all projections agree on symbols
        base = {}
        conflict = False
        for bidx, jx, insx in projs:
            offx = kpos - jx
            for (p, n, c, omf) in insx:
                for dp in range(p, p+n):
                    key = dp + offx
                    if key in base and base[key] != c2s[c]: conflict = True
                    base[key] = c2s[c]
        if conflict: print(f"    !! SYMBOL CONFLICT among projections for chunk@{kpos}")
print(f"chunks with unique projection: {proj_tokens_unique}/7 (claim 6/7 unique)")
print(f"kharos digit positions decoded by projection: {len(total_proj_positions)}/137 (claim 109, 79.6%)")

# ---------- Viterbi ML parse (claim: 71 tokens, 5 omitted zeros) ----------
# scoring: log( freq(code) ) + log( omission prob given code ), Laplace 0.5
N = sum(occ.values())
def logp_written(c):
    if c not in c2s: return None
    pf = math.log(occ[c] / N)
    pw = math.log((wr[c] + 0.5) / (occ[c] + 1.0))
    return pf + pw
def logp_omitted(c):
    if c not in c2s: return None
    pf = math.log(occ[c] / N)
    po = math.log((om[c] + 0.5) / (occ[c] + 1.0))
    return pf + po

n = len(K)
NEG = float('-inf')
dp = [NEG]*(n+1); bk = [None]*(n+1)
dp[0] = 0.0
for i in range(n):
    if dp[i] == NEG: continue
    # 1-digit token: omitted leading zero, code '0'+K[i]
    c = '0' + K[i]
    lp = logp_omitted(c)
    if lp is not None and dp[i] + lp > dp[i+1]:
        dp[i+1] = dp[i] + lp; bk[i+1] = (i, c, True)
    if i+2 <= n:
        c = K[i:i+2]
        lp = logp_written(c)
        if lp is not None and dp[i] + lp > dp[i+2]:
            dp[i+2] = dp[i] + lp; bk[i+2] = (i, c, False)
print(f"\nML parse logprob total={dp[n]:.3f}")
toks = []
i = n
while i > 0:
    pi, c, omf = bk[i]
    toks.append((c, omf)); i = pi
toks.reverse()
nom = sum(1 for _, o in toks if o)
print(f"ML parse: {len(toks)} tokens (claim 71), {nom} omitted (claim 5), identity 137+{nom}=={2*len(toks)}: {137+nom==2*len(toks)}")
print(f"ML logprob/token = {dp[n]/len(toks):.4f} (claim -4.119)")
omitted_used = [c for c, o in toks if o]
print("omitted codes used:", sorted(omitted_used), "(claim 00x1,01,04,05,07... wait claim says 00,01,04,05,07x? -> '00x1w,01,04,05,07x3')")
viol39 = any(c == '39' for c, _ in toks)
viol_wr07 = any(c == '07' and not o for c, o in toks)
viol_om = any(o and om[c] == 0 for c, o in toks)
print(f"violations: code39={viol39}, written07={viol_wr07}, omit-of-never-omitted={viol_om} (claim all 0)")
ml_decode = "".join(c2s[c] for c, _ in toks)
print("ML decode:", ml_decode)

# ---------- constrained decode (forced to agree with projections) ----------
# constraint: at digit pos covered by projection, symbol fixed
CLAIM_DECODE = "TEINTAAETTEIVIFASTFNEVVTISETAFSETBASIESTIENFITFAIFVI*NIFATAEFTNESFEVIII"
print("\nclaimed decode len:", len(CLAIM_DECODE))
# constrained viterbi: state = digit pos; token symbol must match proj_symbols at all its positions if constrained
# We track token list; constraint applies per token: if any covered position constrains symbol, token's symbol must equal it,
# and token boundaries must be compatible (projection had token boundaries; enforce symbol only, as claim says "forced to agree with projections")
dp2 = [NEG]*(n+1); bk2 = [None]*(n+1); dp2[0] = 0.0
def sym_ok(c, i, ln):
    s = c2s[c]
    for p in range(i, i+ln):
        if p in proj_symbols and s not in proj_symbols[p]:
            return False
    return True
for i in range(n):
    if dp2[i] == NEG: continue
    c = '0' + K[i]
    lp = logp_omitted(c)
    if lp is not None and sym_ok(c, i, 1) and dp2[i] + lp > dp2[i+1]:
        dp2[i+1] = dp2[i] + lp; bk2[i+1] = (i, c, True)
    if i+2 <= n:
        c = K[i:i+2]
        lp = logp_written(c)
        if lp is not None and sym_ok(c, i, 2) and dp2[i] + lp > dp2[i+2]:
            dp2[i+2] = dp2[i] + lp; bk2[i+2] = (i, c, False)
toks2 = []
i = n
while i > 0:
    pi, c, omf = bk2[i]
    toks2.append((c, omf)); i = pi
toks2.reverse()
dec2 = "".join(c2s[c] for c, _ in toks2)
print(f"constrained decode: {len(toks2)} symbols")
print("mine :", dec2)
print("claim:", CLAIM_DECODE)
print("match:", dec2 == CLAIM_DECODE)
if dec2 != CLAIM_DECODE and len(dec2) == len(CLAIM_DECODE):
    diffs = [i for i in range(len(dec2)) if dec2[i] != CLAIM_DECODE[i]]
    print("diff positions:", diffs, [(dec2[i], CLAIM_DECODE[i]) for i in diffs])

# symbol 5-gram coverage of claimed decode vs book decodedbases
bases = [b['decodedbase'] for b in books.values()]
g5 = [CLAIM_DECODE[i:i+5] for i in range(len(CLAIM_DECODE)-4)]
hit5 = sum(1 for g in g5 if any(g in b for b in bases))
print(f"decode 5-gram coverage: {hit5}/{len(g5)} = {hit5/len(g5):.4f} (claim 31/67=.463)")
# longest decoded substring shared
bestL = 0
for i in range(len(CLAIM_DECODE)):
    for L in range(len(CLAIM_DECODE)-i, bestL, -1):
        sub = CLAIM_DECODE[i:i+L]
        if any(sub in b for b in bases):
            bestL = max(bestL, L); break
print(f"longest decoded-symbol shared substring: {bestL} (claim 12)")

con.close()
print("PART2 DONE")
