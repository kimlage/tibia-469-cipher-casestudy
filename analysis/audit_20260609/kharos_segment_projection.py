#!/usr/bin/env python3
"""Stage 2: decompose the Kharos 137-digit string into maximal chunks shared with
the 70 books, then project the books' OWN recorded row0 tokenizations onto those
chunks to get a consensus symbol decode (instead of an ambiguous free parse).

Also: greedy-cover statistics vs 100 shuffle controls.
"""
import sqlite3, json, math, random
from collections import defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
random.seed(469)

con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

books = {}
for bookid, digits, base in cur.execute(
        "SELECT bookid, MIN(digits), MIN(decodedbase) FROM sheet__books GROUP BY bookid"):
    books[bookid] = dict(digits=digits.strip(), base=base.strip())
print(f"[books] {len(books)}")

# probe parses: rebuild digit-position -> (symbol, token-start) maps
probe = {}
nrebuilt = 0
for bookid, stream, om_pos_j, valid in cur.execute(
        "SELECT bookid, reconstructed_code_stream, omitted_positions_json, valid "
        "FROM row0_code_symbol_probe_books WHERE run_id=1"):
    codes = stream.split()
    om = set(json.loads(om_pos_j))          # try 1-based symbol positions
    # rebuild digits two ways to detect base
    def rebuild(off):
        out = []
        for idx, c in enumerate(codes):
            if (idx + off) in om: out.append(c[1])   # omitted leading zero
            else: out.append(c)
        return "".join(out)
    d = books[bookid]["digits"]
    for off in (1, 0):
        if rebuild(off) == d:
            break
    else:
        print(f"  [warn] cannot rebuild digits for book {bookid}")
        continue
    nrebuilt += 1
    # map: digit position -> (token_index, is_token_start)
    pos2tok = []
    for idx, c in enumerate(codes):
        n = 1 if (idx + off) in om else 2
        for k in range(n):
            pos2tok.append((idx, k == 0))
    probe[bookid] = dict(codes=codes, pos2tok=pos2tok, off=off)
print(f"[probe] rebuilt digit<->token maps for {nrebuilt}/70 books")

# symbol map
code_sym = dict(cur.execute(
    "SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1"))

KH = cur.execute("SELECT sequence_digits FROM s2ward_corpus_audit_items "
                 "WHERE source_set='sorted_unique_with_kharos' AND source_index=22"
                 ).fetchone()[0].strip()
L = len(KH)

# ---- longest-match table: for each start, longest substring found in any book; record all hits ----
def longest_match_at(s, i, corpus):
    """returns (maxlen, [(bookid, offset)]) for longest substring of s starting at i found in corpus."""
    lo, hi = 0, len(s) - i
    def hits(n):
        if n == 0: return []
        sub = s[i:i+n]
        out = []
        for bid, b in corpus.items():
            start = b["digits"].find(sub)
            while start != -1:
                out.append((bid, start))
                start = b["digits"].find(sub, start+1)
        return out
    best_hits = []
    while lo < hi:
        mid = (lo+hi+1)//2
        h = hits(mid)
        if h: lo = mid; best_hits = h
        else: hi = mid-1
    return lo, best_hits

def greedy_cover(s, corpus, minlen=8):
    """greedy left-to-right cover with longest matches >= minlen; gaps marked."""
    segs = []; i = 0
    while i < len(s):
        n, h = longest_match_at(s, i, corpus)
        if n >= minlen:
            segs.append(("MATCH", i, n, h)); i += n
        else:
            if segs and segs[-1][0] == "GAP":
                t, st, ln, _ = segs[-1]; segs[-1] = ("GAP", st, ln+1, None)
            else:
                segs.append(("GAP", i, 1, None))
            i += 1
    return segs

segs = greedy_cover(KH, books)
print(f"\n[kharos cover] greedy maximal-match segmentation (minlen=8):")
match_total = 0; nmatch = 0
for t, st, ln, h in segs:
    if t == "MATCH":
        match_total += ln; nmatch += 1
        hs = h[:4]
        print(f"  pos {st:3d} len {ln:3d} MATCH {KH[st:st+ln][:40]}{'...' if ln>40 else ''} "
              f"-> {len(h)} hit(s) e.g. {hs}")
    else:
        print(f"  pos {st:3d} len {ln:3d} GAP   {KH[st:st+ln]}")
print(f"[kharos cover] {nmatch} match segments cover {match_total}/{L} = {match_total/L:.3f}")

# ---- shuffle control for greedy cover ----
NC = 100
cov_ctrl = []; nseg_ctrl = []
chars = list(KH)
for t in range(NC):
    random.shuffle(chars)
    cs = greedy_cover("".join(chars), books)
    cov = sum(ln for ty, st, ln, h in cs if ty == "MATCH")
    cov_ctrl.append(cov/L)
    nseg_ctrl.append(sum(1 for ty, *_ in cs if ty == "MATCH"))
mu = sum(cov_ctrl)/NC; sd = (sum((v-mu)**2 for v in cov_ctrl)/(NC-1))**0.5
z = (match_total/L - mu)/sd if sd else float("inf")
print(f"[control] greedy cover fraction: kharos={match_total/L:.3f} ctrl_mu={mu:.4f} "
      f"ctrl_sd={sd:.4f} z={z:+.2f} P(ctrl>=real)={sum(1 for v in cov_ctrl if v >= match_total/L)}/{NC}")

# ---- project book tokenizations onto matched segments ----
print("\n[projection] decode matched chunks via source-book recorded tokenizations:")
consensus = ["?"]*L          # symbol per kharos digit position (token spans)
conflict = 0; aligned_chunks = 0; misaligned = 0
chunk_decodes = []
for t, st, ln, h in segs:
    if t != "MATCH": continue
    # try each hit; require token-boundary alignment at chunk start in source book
    proj = None
    for bid, boff in h:
        if bid not in probe: continue
        p = probe[bid]
        # source book digit positions boff .. boff+ln-1
        toks = p["pos2tok"][boff:boff+ln]
        if not toks[0][1]:
            continue   # chunk does not start at a token boundary in this book
        syms = []
        ok = True
        j = 0
        while j < ln:
            ti, is_start = toks[j]
            if not is_start: ok = False; break
            code = p["codes"][ti]
            tlen = 1 if (j+1 >= ln or p["pos2tok"][boff+j+1][0] != ti) else 2
            # actual token length in book:
            real_tlen = sum(1 for x in p["pos2tok"] if x[0] == ti)
            if j + real_tlen > ln:
                # token straddles chunk end; stop cleanly
                break
            syms.append(code_sym[code]); j += real_tlen
        if ok and syms:
            proj = (bid, boff, j, "".join(syms))
            break
    if proj:
        bid, boff, used, symstr = proj
        aligned_chunks += 1
        chunk_decodes.append((st, used, bid, symstr))
        # fill consensus per digit pos
        p = probe[bid]
        j = 0; si = 0
        while j < used:
            ti, _ = p["pos2tok"][boff+j]
            real_tlen = sum(1 for x in p["pos2tok"] if x[0] == ti)
            for k in range(real_tlen):
                pos = st+j+k
                if consensus[pos] != "?" and consensus[pos] != symstr[si]:
                    conflict += 1
                consensus[pos] = symstr[si]
            j += real_tlen; si += 1
        print(f"  pos {st:3d} len {used:3d} via book {bid}@{boff}: {symstr}")
    else:
        misaligned += 1
        print(f"  pos {st:3d} len {ln:3d} NO token-aligned projection (hits: {[x[0] for x in h[:5]]})")

print(f"\n[projection] aligned chunks={aligned_chunks} misaligned={misaligned} conflicts={conflict}")
covered_syms = sum(1 for c in consensus if c != "?")
print(f"[projection] digit positions with projected symbol: {covered_syms}/{L} = {covered_syms/L:.3f}")
print(f"[projection] consensus per-digit symbol track:")
print("  " + "".join(consensus))

con.close()
print("\nDONE")
