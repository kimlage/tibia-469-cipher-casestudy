#!/usr/bin/env python3
"""Re-derive claims 1-6 and 8 for the 469 book-layer non-linguistic verdict.
Reads ONLY raw per-book columns (digits, insertedzeros, decodedbase) plus
omitted-zero positions from row0_code_symbol_probe_books. Recomputes everything.
"""
import sqlite3, json, sys
from collections import Counter, defaultdict

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
cur = con.cursor()

# ---------- load raw books (dedupe) ----------
rows = cur.execute("""
    SELECT bookid, MIN(digits), MIN(insertedzeros), MIN(baselen), MIN(decodedbase),
           COUNT(*), COUNT(DISTINCT digits), COUNT(DISTINCT decodedbase)
    FROM sheet__books GROUP BY bookid
""").fetchall()
print("ROWCOUNT sheet__books grouped:", len(rows))
assert len(rows) > 0, "EMPTY QUERY - red flag"
dup_mismatch = [r[0] for r in rows if r[6] != 1 or r[7] != 1]
print("books whose duplicated export rows disagree on digits/decodedbase:", dup_mismatch)

books = {}
for bid, digits, iz, baselen, base, _, _, _ in rows:
    books[bid] = dict(digits=digits, iz=int(iz), baselen=int(baselen), base=base)

n_books = len(books)
tot_digits = sum(len(b["digits"]) for b in books.values())
tot_syms = sum(len(b["base"]) for b in books.values())
alphabet = sorted(set("".join(b["base"] for b in books.values())))
print(f"CORPUS: books={n_books} total_digits={tot_digits} total_symbols={tot_syms}")
print("alphabet:", "".join(alphabet))
for bid, b in books.items():
    assert len(b["base"]) == b["baselen"], (bid, "baselen mismatch")
    assert len(b["digits"]) == 2*b["baselen"] - b["iz"], (bid, "digit count mismatch")
print("per-book invariant len(digits)==2*baselen-insertedzeros holds for all", n_books)

# ---------- CLAIM 1 & 3: symbol frequencies ----------
cnt = Counter()
for b in books.values():
    cnt.update(b["base"])
print("\n== CLAIM 1: symbol frequencies (pct of all", tot_syms, "chars incl '*') ==")
for s, c in cnt.most_common():
    print(f"  {s}: {c:5d}  {100*c/tot_syms:6.2f}%")
nonstar = tot_syms - cnt.get("*", 0)
print("non-star total:", nonstar)
print("pct excluding star:")
for s, c in cnt.most_common():
    if s != "*":
        print(f"  {s}: {100*c/nonstar:6.2f}%")

# ---------- CLAIM 2: chi-square vs renormalized references ----------
# standard published letter-frequency tables (percent)
ENGLISH = dict(A=8.167,B=1.492,C=2.782,D=4.253,E=12.702,F=2.228,G=2.015,H=6.094,
    I=6.966,J=0.153,K=0.772,L=4.025,M=2.406,N=6.749,O=7.507,P=1.929,Q=0.095,
    R=5.987,S=6.327,T=9.056,U=2.758,V=0.978,W=2.360,X=0.150,Y=1.974,Z=0.074)
GERMAN = dict(A=6.516,B=1.886,C=2.732,D=5.076,E=16.396,F=1.656,G=3.009,H=4.577,
    I=6.550,J=0.268,K=1.417,L=3.437,M=2.534,N=9.776,O=2.594,P=0.670,Q=0.018,
    R=7.003,S=7.270,T=6.154,U=4.166,V=0.846,W=1.921,X=0.034,Y=0.039,Z=1.134)
SPANISH = dict(A=11.525,B=2.215,C=4.019,D=5.010,E=12.181,F=0.692,G=1.768,H=0.703,
    I=6.247,J=0.493,K=0.011,L=4.967,M=3.157,N=6.712,O=8.683,P=2.510,Q=0.877,
    R=6.871,S=7.977,T=4.632,U=2.927,V=1.138,W=0.017,X=0.215,Y=1.008,Z=0.467)
SYMS13 = [s for s in alphabet if s != "*"]
print("\n== CLAIM 2: chi-square (book counts vs renormalized 13-letter refs) ==")
print("13 real symbols:", "".join(SYMS13))
obs = {s: cnt[s] for s in SYMS13}
N = sum(obs.values())
def chisq(ref):
    tot = sum(ref[s] for s in SYMS13)
    out = 0.0
    for s in SYMS13:
        e = N * ref[s] / tot
        out += (obs[s] - e) ** 2 / e
    return out
uni = {s: 1.0 for s in SYMS13}
results = {"UNIFORM": chisq(uni), "English": chisq(ENGLISH),
           "German": chisq(GERMAN), "Spanish": chisq(SPANISH)}
for k, v in sorted(results.items(), key=lambda kv: kv[1]):
    print(f"  {k:8s} chi2 = {v:9.1f}")
print("claimed: UNIFORM 3691 < English 4292 < German 4656 < Spanish 9817")

print("\n== CLAIM 3: per-symbol disqualifiers ==")
for s in "FVRO":
    print(f"  book {s} = {100*cnt[s]/tot_syms:5.2f}% (incl *) / {100*cnt[s]/N:5.2f}% (excl *)"
          f"   refs: EN {ENGLISH[s]}%, DE {GERMAN[s]}%, ES {SPANISH[s]}%")

# ---------- CLAIM 4: verbatim cross-book templating ----------
print("\n== CLAIM 4: cross-book identical fragments ==")
texts = {bid: b["base"] for bid, b in books.items()}
maxlen = max(len(t) for t in texts.values())
def books_sharing(L):
    """max #books sharing one identical length-L substring; return (count, frag)."""
    d = defaultdict(set)
    for bid, t in texts.items():
        for i in range(len(t) - L + 1):
            d[t[i:i+L]].add(bid)
    if not d:
        return 0, ""
    frag, s = max(d.items(), key=lambda kv: len(kv[1]))
    return len(s), frag
for L in (19, 29, 49):
    c, frag = books_sharing(L)
    print(f"  L={L}: best fragment shared by {c} books: {frag!r}")
# full curve: for each L, max books sharing a fragment; and for given k, longest frag
print("  curve (L -> max books sharing):")
prev = None
for L in range(5, maxlen + 1):
    c, frag = books_sharing(L)
    if c != prev:
        print(f"    L={L:3d} -> {c} books   e.g. {frag[:60]!r}")
        prev = c
    if c <= 1:
        break

# ---------- CLAIM 8 (tautology) + CLAIM 6 (functional map) ----------
print("\n== CLAIM 8/6: rebuild code streams, global map, consistency ==")
prows = cur.execute("""SELECT bookid, omitted_positions_json FROM row0_code_symbol_probe_books
                       WHERE run_id=1""").fetchall()
print("ROWCOUNT probe_books:", len(prows))
assert len(prows) == n_books
omits = {bid: json.loads(j) for bid, j in prows}
pairs = defaultdict(Counter)   # code -> Counter(symbol)
streams = {}
for bid, b in books.items():
    om = set(omits[bid])       # 1-indexed code positions with omitted leading zero
    digits, base = b["digits"], b["base"]
    i, codes = 0, []
    for k in range(1, b["baselen"] + 1):
        if k in om:
            codes.append("0" + digits[i]); i += 1
        else:
            codes.append(digits[i:i+2]); i += 2
    assert i == len(digits), (bid, "did not consume all digits")
    assert len(codes) == len(base), (bid, "stream/base length mismatch")
    assert len(om) == b["iz"], (bid, "insertedzeros count mismatch")
    streams[bid] = codes
    for c, s in zip(codes, base):
        pairs[c][s] += 1

codes_all = sorted(pairs)
symbols_all = sorted({s for c in pairs for s in pairs[c]})
ambiguous = {c: dict(pairs[c]) for c in pairs if len(pairs[c]) > 1}
total_positions = sum(sum(pairs[c].values()) for c in pairs)
print(f"distinct codes: {len(codes_all)}  distinct symbols: {len(symbols_all)} ({''.join(symbols_all)})")
print(f"ambiguous codes (map to >1 symbol): {len(ambiguous)} {ambiguous}")
print(f"total aligned positions: {total_positions}")
missing = sorted(set(f"{i:02d}" for i in range(100)) - set(codes_all))
print("codes never used:", missing)
gmap = {c: pairs[c].most_common(1)[0][0] for c in pairs}
mismatch_books = [bid for bid in books
                  if "".join(gmap[c] for c in streams[bid]) != books[bid]["base"]]
print("books whose decodedbase != global-map(reconstructed stream):", mismatch_books)
omitted_all = Counter(streams[bid][k-1] for bid in books for k in omits[bid])
print("omitted-zero codes observed (should all be 0d):", dict(omitted_all))

# DP: is the parse unique given digits + #insertedzeros + global code SET?
codeset = set(codes_all)
amb_parse = []
for bid, b in books.items():
    digits, iz, L = b["digits"], b["iz"], b["baselen"]
    # dp[(i,j)] = set of output strings (cap at 5) reaching end from digit i with j omitted left
    from functools import lru_cache
    sys.setrecursionlimit(100000)
    @lru_cache(maxsize=None)
    def dp(i, j):
        if i == len(digits):
            return frozenset([""]) if j == 0 else frozenset()
        out = set()
        c2 = digits[i:i+2]
        if len(c2) == 2 and c2 in codeset:
            out |= {gmap[c2] + t for t in dp(i + 2, j)}
        c1 = "0" + digits[i]
        if j > 0 and c1 in codeset:
            out |= {gmap[c1] + t for t in dp(i + 1, j - 1)}
        return frozenset(sorted(out)[:5])
    outs = dp(0, iz)
    dp.cache_clear()
    if len(outs) != 1 or next(iter(outs)) != b["base"]:
        amb_parse.append((bid, len(outs), b["base"] in outs))
print("books where parse from digits+count+global table is NOT unique-and-correct:",
      len(amb_parse))
for x in amb_parse[:10]:
    print("   ", x)

# ---------- CLAIM 5: reversal invariance + digit-sum ----------
print("\n== CLAIM 5: reversal invariance of recomputed map ==")
pal = [c for c in codes_all if c[0] == c[1]]
nonpal = [c for c in codes_all if c[0] != c[1]]
print(f"palindrome codes present: {len(pal)}  non-palindrome: {len(nonpal)}")
same = diff = norev = 0
diffs = []
for c in nonpal:
    r = c[::-1]
    if r not in gmap:
        norev += 1
    elif gmap[r] == gmap[c]:
        same += 1
    else:
        diff += 1; diffs.append((c, gmap[c], r, gmap[r]))
print(f"non-palindrome codes whose reverse maps to SAME symbol: {same}")
print(f"...different symbol: {diff} -> {diffs}")
print(f"...reverse code absent from corpus: {norev}")
classes = defaultdict(set)
for c in codes_all:
    classes[frozenset(c) if c[0] != c[1] else c].add(gmap[c])
pure = sum(1 for v in classes.values() if len(v) == 1)
print(f"unordered-pair classes: {len(classes)}  pure: {pure}  impure: "
      f"{[ (sorted(k) if isinstance(k, frozenset) else k, sorted(v)) for k, v in classes.items() if len(v)>1 ]}")
ds = defaultdict(set)
for c in codes_all:
    ds[int(c[0]) + int(c[1])].add(gmap[c])
multi = {k: sorted(v) for k, v in sorted(ds.items()) if len(v) > 1}
print(f"digit-sums with >1 symbol: {len(multi)} of {len(ds)}")
for k, v in sorted(ds.items()):
    print(f"   ds={k:2d}: {sorted(v)}")
con.close()
print("\nDONE")
