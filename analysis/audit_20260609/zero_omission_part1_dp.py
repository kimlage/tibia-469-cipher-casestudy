#!/usr/bin/env python3
"""Part 1: Independent DP over zero-omission placements.

DP-B: constraint = 99-code inventory + code->symbol map must reproduce the known
      decodedbase (sheet__books). Verify stored pathcount + altomitpatterns.
DP-A: constraint = 99-code inventory only (no decodedbase). Quantifies how
      underdetermined the parse/decode is from digits alone.
Also: extract per-occurrence omit/retain dataset from canonical parse and save it.
"""
import sqlite3, json, sys
from collections import defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
OUT = "./tmp/audit_20260609"

con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

# ---- load code->symbol map
rows = cur.execute("SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1").fetchall()
print(f"[load] code_symbol_counts rows = {len(rows)}")
assert len(rows) == 99, "expected 99 codes"
CMAP = {c: s for c, s in rows}
INV = set(CMAP)  # valid codes

# ---- load books (dedupe)
rows = cur.execute("""
  SELECT bookid, clusterid, digits, insertedzeros, baselen, decodedbase
  FROM sheet__books GROUP BY bookid""").fetchall()
print(f"[load] sheet__books deduped rows = {len(rows)}")
assert len(rows) == 70
# check duplicates agree
dup = cur.execute("""SELECT bookid, COUNT(DISTINCT digits||'|'||insertedzeros||'|'||decodedbase)
                     FROM sheet__books GROUP BY bookid HAVING COUNT(DISTINCT digits||'|'||insertedzeros||'|'||decodedbase)>1""").fetchall()
print(f"[check] books with disagreeing duplicate rows = {len(dup)}")

books = {}
for bid, clu, dig, iz, bl, db in rows:
    books[bid] = dict(clusterid=clu.strip(), digits=dig.strip(), k=int(iz), B=int(bl), base=db.strip())

# ---- stored probe results
stored = {}
for bid, pc, omitidx, omitcodes, alts in cur.execute(
        "SELECT bookid, pathcount, omitidxs_1based, omitcodes, altomitpatterns_1based FROM row0_omission_probe_book_items WHERE run_id=1"):
    stored[bid] = dict(pathcount=pc, omitidx=omitidx, omitcodes=omitcodes, alts=alts)
print(f"[load] omission_probe_book_items rows = {len(stored)}")

canon = {}
for bid, opos, ocodes, rcs, db in cur.execute(
        "SELECT bookid, omitted_positions_json, omitted_codes_json, reconstructed_code_stream, decodedbase FROM row0_code_symbol_probe_books WHERE run_id=1"):
    canon[bid] = dict(opos=json.loads(opos), ocodes=json.loads(ocodes), codes=rcs.split(), base=db.strip())
print(f"[load] code_symbol_probe_books rows = {len(canon)}")

# ---- sanity: canonical parse reproduces digits and decodedbase
bad = 0
for bid, b in books.items():
    c = canon[bid]
    omit = set(c["opos"])  # 1-based code idx
    written = "".join(code[1] if (i + 1) in omit else code for i, code in enumerate(c["codes"]))
    sym = "".join(CMAP[code] for code in c["codes"])
    if written != b["digits"] or sym != b["base"] or c["base"] != b["base"] or len(c["codes"]) != b["B"]:
        bad += 1
        print(f"[FAIL] canonical parse mismatch book {bid}")
print(f"[check] canonical parse consistency failures = {bad}/70")

# ---- DP machinery -------------------------------------------------------
def dp_count(digits, B, k, base=None):
    """Forward DP. State at code boundary i: omissions used o (digits consumed p = 2i-o).
    Returns F (list of dicts o->count) and total paths F[B].get(k,0)."""
    L = len(digits)
    F = [defaultdict(int) for _ in range(B + 1)]
    F[0][0] = 1
    for i in range(B):
        tgt = base[i] if base else None
        for o, cnt in F[i].items():
            p = 2 * i - o
            # retained 2-digit code
            if p + 2 <= L:
                c2 = digits[p:p + 2]
                if c2 in INV and (tgt is None or CMAP[c2] == tgt):
                    F[i + 1][o] += cnt
            # omitted 0X code (1 written digit)
            if o < k and p + 1 <= L:
                c1 = "0" + digits[p]
                if c1 in INV and (tgt is None or CMAP[c1] == tgt):
                    F[i + 1][o + 1] += cnt
    return F

def dp_backward(digits, B, k, base=None):
    L = len(digits)
    Bk = [defaultdict(int) for _ in range(B + 1)]
    Bk[B][k] = 1
    for i in range(B - 1, -1, -1):
        tgt = base[i] if base else None
        for o in range(0, k + 1):
            p = 2 * i - o
            if p < 0 or p > L:
                continue
            tot = 0
            if p + 2 <= L:
                c2 = digits[p:p + 2]
                if c2 in INV and (tgt is None or CMAP[c2] == tgt):
                    tot += Bk[i + 1].get(o, 0)
            if o < k and p + 1 <= L:
                c1 = "0" + digits[p]
                if c1 in INV and (tgt is None or CMAP[c1] == tgt):
                    tot += Bk[i + 1].get(o + 1, 0)
            if tot:
                Bk[i][o] = tot
    return Bk

def enumerate_paths(digits, B, k, base, cap=2000):
    """Enumerate omission position sets (1-based code idx) under DP-B."""
    L = len(digits)
    Bk = dp_backward(digits, B, k, base)
    out = []
    def rec(i, o, acc):
        if len(out) >= cap:
            return
        if i == B:
            if o == k:
                out.append(tuple(acc))
            return
        p = 2 * i - o
        tgt = base[i]
        if p + 2 <= L:
            c2 = digits[p:p + 2]
            if c2 in INV and CMAP[c2] == tgt and Bk[i + 1].get(o, 0) > 0:
                rec(i + 1, o, acc)
        if o < k and p + 1 <= L:
            c1 = "0" + digits[p]
            if c1 in INV and CMAP[c1] == tgt and Bk[i + 1].get(o + 1, 0) > 0:
                acc.append(i + 1)
                rec(i + 1, o + 1, acc)
                acc.pop()
    rec(0, 0, [])
    return out

# ---- run per book -------------------------------------------------------
import math
res = []
mismatch_pc = 0
mismatch_alt = 0
flip_books = []
for bid in sorted(books, key=lambda x: int(x)):
    b = books[bid]
    FB = dp_count(b["digits"], b["B"], b["k"], base=b["base"])
    nB = FB[b["B"]].get(b["k"], 0)
    FA = dp_count(b["digits"], b["B"], b["k"], base=None)
    nA = FA[b["B"]].get(b["k"], 0)
    spc = stored[bid]["pathcount"]
    if nB != spc:
        mismatch_pc += 1
        print(f"[MISMATCH pathcount] book {bid}: DP-B={nB} stored={spc}")
    # enumerate DP-B paths, compare with altomitpatterns
    paths = enumerate_paths(b["digits"], b["B"], b["k"], b["base"])
    stored_alts = stored[bid]["alts"]
    if stored_alts:
        sa = set(tuple(int(x) for x in p.strip().split(",")) for p in stored_alts.split("|"))
    else:
        sa = {tuple(int(x) for x in stored[bid]["omitidx"].split(","))} if stored[bid]["omitidx"] else {tuple()}
    if set(paths) != sa:
        mismatch_alt += 1
        print(f"[MISMATCH altpatterns] book {bid}: DP-B={sorted(paths)} stored={sorted(sa)}")
    # which occurrence labels flip across parses (multipath)?
    flips = set()
    if len(paths) > 1:
        union = set().union(*[set(p) for p in paths])
        inter = set(paths[0]).intersection(*[set(p) for p in paths[1:]])
        flips = union - inter
        flip_books.append((bid, len(paths), sorted(flips)))
    # DP-A symbol ambiguity: possible symbols per position
    BkA = dp_backward(b["digits"], b["B"], b["k"], base=None)
    ambig = 0
    L = len(b["digits"])
    for i in range(b["B"]):
        syms = set()
        for o, cnt in FA[i].items():
            p = 2 * i - o
            if p + 2 <= L:
                c2 = b["digits"][p:p + 2]
                if c2 in INV and BkA[i + 1].get(o, 0) > 0:
                    syms.add(CMAP[c2])
            if o < b["k"] and p + 1 <= L:
                c1 = "0" + b["digits"][p]
                if c1 in INV and BkA[i + 1].get(o + 1, 0) > 0:
                    syms.add(CMAP[c1])
        if len(syms) > 1:
            ambig += 1
    res.append(dict(bookid=bid, k=b["k"], B=b["B"], dpB=nB, stored=spc, dpA_log10=math.log10(nA) if nA else None,
                    ambig_frac=ambig / b["B"]))

print(f"\n[RESULT] pathcount mismatches DP-B vs stored: {mismatch_pc}/70")
print(f"[RESULT] altpattern set mismatches: {mismatch_alt}/70")
import statistics as st
pcs = [r["dpB"] for r in res]
print(f"[RESULT] DP-B pathcount distribution: " + str(sorted(set((p, pcs.count(p)) for p in pcs))))
print(f"[RESULT] median DP-B parses per book = {st.median(pcs)}")
la = [r["dpA_log10"] for r in res]
print(f"[RESULT] DP-A (inventory-only) log10(pathcount): min={min(la):.1f} median={st.median(la):.1f} max={max(la):.1f}")
af = [r["ambig_frac"] for r in res]
print(f"[RESULT] DP-A fraction of symbol positions ambiguous: min={min(af):.3f} median={st.median(af):.3f} max={max(af):.3f}")
print(f"[RESULT] multipath books label-flip positions: {flip_books}")
nflip = sum(len(f[2]) for f in flip_books)
print(f"[RESULT] total occurrence labels that flip across DP-B parses = {nflip}")

# DP-B symbol divergence across parses is 0 by construction (decodedbase fixed); verify code-stream-only divergence
print("[note] DP-B alternative parses all reproduce identical decodedbase by construction (constraint).")

# ---- extract per-occurrence dataset from canonical parse ----------------
occ = []
for bid in sorted(books, key=lambda x: int(x)):
    b, c = books[bid], canon[bid]
    omit = set(c["opos"])
    codes = c["codes"]
    p = 0
    flip_set = set()
    for fb, np_, fl in flip_books:
        if fb == bid:
            flip_set = set(fl)
    for i, code in enumerate(codes):
        idx1 = i + 1
        is_omit = idx1 in omit
        if code.startswith("0"):
            prev_digit = b["digits"][p - 1] if p > 0 else "S"
            nxt_code = codes[i + 1] if i + 1 < len(codes) else "EE"
            occ.append(dict(bookid=bid, cluster=b["clusterid"], idx1=idx1, B=b["B"], code=code,
                            label=int(is_omit), prev=prev_digit, next_first=nxt_code[0],
                            next_is0X=int(nxt_code.startswith("0")), imod2=idx1 % 2, imod3=idx1 % 3,
                            pmod2=p % 2, bookstart=int(idx1 == 1), relpos=idx1 / b["B"],
                            pathcount=stored[bid]["pathcount"], label_ambiguous=int(idx1 in flip_set)))
        p += 1 if is_omit else 2
print(f"\n[RESULT] total 0X occurrences = {len(occ)}; omitted = {sum(o['label'] for o in occ)}; retained = {sum(1 - o['label'] for o in occ)}")
print(f"[RESULT] occurrences in pathcount=1 books = {sum(1 for o in occ if o['pathcount'] == 1)}")
print(f"[RESULT] occurrences with parse-ambiguous label = {sum(o['label_ambiguous'] for o in occ)}")

with open(f"{OUT}/occurrences.json", "w") as f:
    json.dump(occ, f)
with open(f"{OUT}/dp_results.json", "w") as f:
    json.dump(res, f)
print("[saved] occurrences.json, dp_results.json")
