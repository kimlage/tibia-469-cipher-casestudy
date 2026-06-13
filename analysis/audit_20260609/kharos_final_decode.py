#!/usr/bin/env python3
"""Stage 3: maximal token-aligned projection for every matched chunk (allowing
chunk starts mid-token and trying every hit), consensus across hits, final
full-string decode with gaps filled by constrained ML parse, and symbol-level
n-gram coverage of the final decode vs the 70 decodedbase strings."""
import sqlite3, json, math
from collections import defaultdict, Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

books = {}
for bookid, digits, base in cur.execute(
        "SELECT bookid, MIN(digits), MIN(decodedbase) FROM sheet__books GROUP BY bookid"):
    books[bookid] = dict(digits=digits.strip(), base=base.strip())

probe = {}
for bookid, stream, om_pos_j in cur.execute(
        "SELECT bookid, reconstructed_code_stream, omitted_positions_json "
        "FROM row0_code_symbol_probe_books WHERE run_id=1"):
    codes = stream.split()
    om = set(json.loads(om_pos_j))
    for off in (1, 0):
        d = "".join(c[1] if (i+off) in om else c for i, c in enumerate(codes))
        if d == books[bookid]["digits"]:
            break
    else:
        continue
    pos2tok = []
    tok_digit_start = []
    p = 0
    for i, c in enumerate(codes):
        n = 1 if (i+off) in om else 2
        tok_digit_start.append(p)
        for k in range(n):
            pos2tok.append((i, k == 0))
        p += n
    probe[bookid] = dict(codes=codes, pos2tok=pos2tok, om=om, off=off)
print(f"[probe] maps for {len(probe)}/70 books")

code_sym = dict(cur.execute("SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1"))
crow = cur.execute("SELECT code, occurrence_count, omitted_count, written_count "
                   "FROM row0_code_symbol_counts WHERE run_id=1").fetchall()
occ = {c: o for c, o, om, w in crow}; omc = {c: om for c, o, om, w in crow}
wrc = {c: w for c, o, om, w in crow}; TOT = sum(occ.values()); AL = 0.5
def lp_w(c): return math.log((occ.get(c,0)+AL)/(TOT+100*AL)) + math.log((wrc.get(c,0)+AL)/(occ.get(c,0)+2*AL))
def lp_o(c): return math.log((occ.get(c,0)+AL)/(TOT+100*AL)) + math.log((omc.get(c,0)+AL)/(occ.get(c,0)+2*AL))
inv = set(code_sym)

KH = cur.execute("SELECT sequence_digits FROM s2ward_corpus_audit_items "
                 "WHERE source_set='sorted_unique_with_kharos' AND source_index=22").fetchone()[0].strip()
L = len(KH)

# all maximal matches (recompute segmentation as before)
def longest_match_at(s, i):
    lo, hi = 0, len(s)-i
    best = []
    while lo < hi:
        mid = (lo+hi+1)//2
        sub = s[i:i+mid]; h = []
        for bid, b in books.items():
            st = b["digits"].find(sub)
            while st != -1:
                h.append((bid, st)); st = b["digits"].find(sub, st+1)
        if h: lo = mid; best = h
        else: hi = mid-1
    return lo, best

segs = []; i = 0
while i < L:
    n, h = longest_match_at(KH, i)
    if n >= 8: segs.append(("MATCH", i, n, h)); i += n
    else:
        if segs and segs[-1][0] == "GAP":
            t, st, ln, _ = segs[-1]; segs[-1] = ("GAP", st, ln+1, None)
        else: segs.append(("GAP", i, 1, None))
        i += 1

# token-aligned projection: for a hit (bid,boff,len), find the maximal run of FULL
# tokens inside [boff, boff+ln) and its symbols + offsets relative to chunk
def project(bid, boff, ln):
    p = probe.get(bid)
    if p is None: return None
    toks = p["pos2tok"]
    j = 0
    while j < ln and not toks[boff+j][1]: j += 1   # skip partial first token
    out = []; start_in_chunk = j
    while j < ln:
        ti, is_start = toks[boff+j]
        tlen = sum(1 for x in toks if x[0] == ti)
        if j + tlen > ln: break
        out.append((j, tlen, p["codes"][ti]))
        j += tlen
    if not out: return None
    return start_in_chunk, out

consensus = ["?"]*L
chunk_report = []
n_alt = 0
for t, st, ln, hits in segs:
    if t != "MATCH": continue
    best = None
    agree = Counter()
    for bid, boff in hits:
        pr = project(bid, boff, ln)
        if pr is None: continue
        s0, out = pr
        covered = sum(tl for _, tl, _ in out)
        sym = "".join(code_sym[c] for _, _, c in out)
        agree[(s0, sym)] += 1
        if best is None or covered > best[2]:
            best = (bid, boff, covered, s0, out, sym)
    if best:
        bid, boff, covered, s0, out, sym = best
        chunk_report.append((st, ln, bid, boff, s0, sym, len(agree), covered))
        if len(agree) > 1: n_alt += 1
        # fill consensus from BEST projection only (token-consistent by construction)
        for j, tl, c in out:
            for k in range(tl):
                consensus[st+j+k] = code_sym[c]
        print(f"  chunk@{st:3d} len{ln:3d} best book {bid}@{boff} skip{s0} "
              f"covers {covered} -> {sym}  (distinct projections across hits: {len(agree)}"
              f"{' ALTS: '+str(dict(agree)) if len(agree)>1 else ''})")
    else:
        print(f"  chunk@{st:3d} len{ln:3d} NO projection at all")

ncov = sum(1 for x in consensus if x != "?")
print(f"\n[consensus] positions with projected symbol (best projections only): "
      f"{ncov}/{L} = {ncov/L:.3f}; chunks with alternate projections: {n_alt}")

# ---- final full decode: constrained Viterbi (match consensus where defined) ----
# state: position; token must produce symbols agreeing with consensus on its span where defined
def viterbi_constrained(s, cons):
    Ln = len(s)
    best = [None]*(Ln+1); best[Ln] = (0.0, None, None)
    for i in range(Ln-1, -1, -1):
        cands = []
        c1 = "0"+s[i]
        if best[i+1] is not None:
            sym = code_sym[c1]
            if cons[i] in ("?", sym):
                cands.append((best[i+1][0]+lp_o(c1), (c1, True), i+1))
        if i+1 < Ln and s[i:i+2] in inv and best[i+2] is not None:
            c2 = s[i:i+2]; sym = code_sym[c2]
            if all(cons[i+k] in ("?", sym) for k in range(2)):
                cands.append((best[i+2][0]+lp_w(c2), (c2, False), i+2))
        best[i] = max(cands) if cands else None
    if best[0] is None: return None, []
    toks = []; i = 0
    while i < Ln:
        _, tok, nxt = best[i]; toks.append(tok); i = nxt
    return best[0][0], toks

lpv, toks = viterbi_constrained(KH, consensus)
if toks:
    decoded = "".join(code_sym[c] for c, om in toks)
    nom = sum(1 for _, om in toks if om)
    print(f"\n[final] constrained ML decode: lp={lpv:.2f} tokens={len(toks)} omitted_zeros={nom} "
          f"identity 137+{nom}==2*{len(toks)}: {137+nom == 2*len(toks)}")
    print(f"[final] decoded({len(decoded)}): {decoded}")
    # symbol n-gram coverage of decode vs books, n=5..10
    for n in (5, 6, 8, 10):
        grams = set()
        for b in books.values():
            bs = b["base"]
            for i in range(len(bs)-n+1): grams.add(bs[i:i+n])
        tot = len(decoded)-n+1
        hits_n = sum(1 for i in range(tot) if decoded[i:i+n] in grams)
        print(f"[final] symbol {n}-gram coverage of decode: {hits_n}/{tot} = {hits_n/tot:.3f}")
else:
    print("[final] constrained decode infeasible")
    decoded = None

# does the full decoded string exist as symbol substring patchwork? longest symbol substring shared
if decoded:
    joined = "\x00".join(b["base"] for b in books.values())
    lo, hi = 0, len(decoded)
    while lo < hi:
        mid = (lo+hi+1)//2
        if any(decoded[i:i+mid] in joined for i in range(len(decoded)-mid+1)): lo = mid
        else: hi = mid-1
    print(f"[final] longest decoded-symbol substring shared with any book decodedbase: {lo}")
con.close()
print("DONE")
