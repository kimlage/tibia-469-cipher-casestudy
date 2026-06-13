#!/usr/bin/env python3
"""Holdout decode of the Kharos 71st sequence (137 digits) + 2012 'Your True Colour' prefix.

Pipeline (matches the 70-book row0 mechanical model):
  - tokenization: stream of tokens, each either a written 2-digit code (any code in the
    99-code inventory = 00..99 minus '39') or a 1-digit token d == code '0d' with the
    leading zero omitted.
  - length identity: digitslen + insertedzeros == 2*baselen.
  - strict book-conformance: omitted only codes with omitted_count>0 in books
    (00,01,03,04,05,06,07,08,09 ; NOT 02), written only codes with written_count>0
    (everything except 07; 39 absent entirely).
  - ML parse: maximize sum log P(code)+log P(flag|code) with book-derived rates.
  - decode ML parse with row0 code->symbol map; coverage metrics vs 70-book corpus.
  - control: 100 digit-preserving shuffles of the same string.
"""
import sqlite3, json, math, random
from functools import lru_cache

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

# ---------- load code map ----------
rows = cur.execute("SELECT code, symbol, occurrence_count, omitted_count, written_count FROM row0_code_symbol_counts").fetchall()
print("code map rows:", len(rows)); assert len(rows) == 99
code2sym, occ, omi, wri = {}, {}, {}, {}
for c, s, o, om, w in rows:
    code2sym[c] = s; occ[c] = o; omi[c] = om; wri[c] = w
TOT = sum(occ.values()); print("total symbol occurrences:", TOT)
INV = set(code2sym)                                   # structural inventory (no '39')
OMITTABLE = {c for c in INV if omi[c] > 0}            # strict omitted set
WRITABLE  = {c for c in INV if wri[c] > 0}            # strict written set (no '07')
print("omittable:", sorted(OMITTABLE), "| not writable:", sorted(INV - WRITABLE))

# log-probs (book ML rates, no smoothing -> strict)
def lp_written(c):
    if c not in INV or wri[c] == 0: return None
    return math.log(occ[c]/TOT) + math.log(wri[c]/occ[c])
def lp_omitted(c):
    if c not in INV or omi[c] == 0: return None
    return math.log(occ[c]/TOT) + math.log(omi[c]/occ[c])

# ---------- load 70 books (dedupe) ----------
books = cur.execute("SELECT bookid, MIN(digits), MIN(decodedbase) FROM sheet__books GROUP BY bookid").fetchall()
print("books:", len(books)); assert len(books) == 70
book_digits = [b[1] for b in books]; book_base = [b[2] for b in books]
print("total book digits:", sum(len(d) for d in book_digits), "| total base symbols:", sum(len(b) for b in book_base))

def ngrams(s, n):
    return {s[i:i+n] for i in range(len(s)-n+1)}
book_dig10 = set().union(*[ngrams(d,10) for d in book_digits])
book_sym10 = set().union(*[ngrams(b,10) for b in book_base])
print("book digit-10grams:", len(book_dig10), "| book symbol-10grams:", len(book_sym10))

# ---------- target strings ----------
KHAROS = cur.execute("SELECT sequence_digits FROM s2ward_corpus_audit_items WHERE source_set='sorted_unique_with_kharos' AND source_index=22").fetchone()[0]
print("kharos len:", len(KHAROS)); assert len(KHAROS) == 137
S2012 = "7856734334"   # only the prefix exists locally (docs/wiki/07-external-sources.md)

# ---------- DP machinery ----------
def parse_counts(s, strict=True):
    """#valid parses ending exactly at len(s); also min/max insertedzeros over valid parses."""
    n = len(s)
    cnt = [0]*(n+1); cnt[0] = 1
    minz = [None]*(n+1); maxz = [None]*(n+1); minz[0] = maxz[0] = 0
    for i in range(n):
        if cnt[i] == 0 and minz[i] is None: continue
        # 1-digit omitted token
        c1 = "0"+s[i]
        ok1 = (c1 in OMITTABLE) if strict else (c1 in INV)
        if ok1:
            cnt[i+1] += cnt[i]
            for arr, f in ((minz, min), (maxz, max)):
                v = arr[i]+1
                arr[i+1] = v if arr[i+1] is None else f(arr[i+1], v)
        # 2-digit written token
        if i+2 <= n:
            c2 = s[i:i+2]
            ok2 = (c2 in WRITABLE) if strict else (c2 in INV)
            if ok2:
                cnt[i+2] += cnt[i]
                for arr, f in ((minz, min), (maxz, max)):
                    v = arr[i]
                    arr[i+2] = v if arr[i+2] is None else f(arr[i+2], v)
    return cnt[n], minz[n], maxz[n]

def ml_parse(s):
    """Viterbi: best strict parse; returns (logprob, tokens) tokens=(code, omitted?)."""
    n = len(s)
    best = [None]*(n+1); back = [None]*(n+1); best[0] = 0.0
    for i in range(n):
        if best[i] is None: continue
        c1 = "0"+s[i]; lp1 = lp_omitted(c1)
        if lp1 is not None:
            v = best[i]+lp1
            if best[i+1] is None or v > best[i+1]:
                best[i+1] = v; back[i+1] = (i, c1, True)
        if i+2 <= n:
            c2 = s[i:i+2]; lp2 = lp_written(c2)
            if lp2 is not None:
                v = best[i]+lp2
                if best[i+2] is None or v > best[i+2]:
                    best[i+2] = v; back[i+2] = (i, c2, False)
    if best[n] is None: return None, None
    toks = []; i = n
    while i > 0:
        j, c, om = back[i]; toks.append((c, om)); i = j
    return best[n], toks[::-1]

def metrics(s):
    cnt_strict, minz_s, maxz_s = parse_counts(s, strict=True)
    cnt_struct, minz_x, maxz_x = parse_counts(s, strict=False)
    lp, toks = ml_parse(s)
    out = {"len": len(s), "n_parses_strict": cnt_strict, "n_parses_struct": cnt_struct,
           "minz_strict": minz_s, "maxz_strict": maxz_s}
    if toks is None:
        out.update({"ml_lp_per_sym": None, "z_ml": None, "sym10_cov": None, "dig10_cov": None, "decoded": None})
        return out
    decoded = "".join(code2sym[c] for c, _ in toks)
    z = sum(1 for _, om in toks if om)
    assert len(s) + z == 2*len(toks), "length identity violated"
    out["z_ml"] = z
    out["baselen_ml"] = len(toks)
    out["ml_lp_per_sym"] = lp/len(toks)
    out["omitted_codes_ml"] = sorted({c for c, om in toks if om})
    # decoded-symbol 10-gram coverage: fraction of symbol positions inside >=1 book-shared 10-gram
    def pos_cov(t, grams, n=10):
        cov = [False]*len(t)
        for i in range(len(t)-n+1):
            if t[i:i+n] in grams:
                for k in range(i, i+n): cov[k] = True
        return sum(cov)/len(t) if t else 0.0
    out["sym10_cov"] = pos_cov(decoded, book_sym10)
    out["dig10_cov"] = pos_cov(s, book_dig10)
    out["decoded"] = decoded
    return out

# ---------- run on Kharos ----------
print("\n=== KHAROS (137 digits, held out) ===")
mk = metrics(KHAROS)
for k, v in mk.items():
    if k == "decoded": continue
    print(f"  {k}: {v}")
print("  decoded(ML):", mk["decoded"])

print("\n=== 2012 prefix (10 digits only; full string NOT local) ===")
m2 = metrics(S2012)
for k, v in m2.items(): print(f"  {k}: {v}")

# ---------- longest-substring containment of Kharos in books ----------
def longest_match_cover(s, corpus, minlen=10):
    """greedy: per position, longest book substring starting there (cap 137)."""
    best_at = [0]*len(s)
    for i in range(len(s)):
        lo, hi = 0, len(s)-i
        # binary search longest L such that s[i:i+L] in some book
        while lo < hi:
            mid = (lo+hi+1)//2
            sub = s[i:i+mid]
            if any(sub in d for d in corpus): lo = mid
            else: hi = mid-1
        best_at[i] = lo
    cov = [False]*len(s)
    for i, L in enumerate(best_at):
        if L >= minlen:
            for k in range(i, i+L): cov[k] = True
    return max(best_at), sum(cov)/len(s)
lm, frac_cov = longest_match_cover(KHAROS, book_digits)
print(f"\nKharos: longest exact book substring = {lm} digits; fraction covered by book substrings >=10 = {frac_cov:.4f}")

# ---------- control: 100 digit-preserving shuffles ----------
print("\n=== CONTROL: 100 shuffles of Kharos ===")
random.seed(469)
ctrl = []
for t in range(100):
    sh = list(KHAROS); random.shuffle(sh); sh = "".join(sh)
    m = metrics(sh)
    lmc, fc = longest_match_cover(sh, book_digits)
    m["longest_book_sub"] = lmc; m["sub_cov"] = fc
    ctrl.append(m)

import statistics as st
def summ(key):
    vals = [c[key] for c in ctrl if c[key] is not None]
    return (len(vals), st.mean(vals), st.pstdev(vals)) if vals else (0, None, None)

n_parse_ok = sum(1 for c in ctrl if c["ml_lp_per_sym"] is not None)
print("controls with >=1 strict parse:", n_parse_ok, "/100")
for key in ("ml_lp_per_sym", "minz_strict", "z_ml", "sym10_cov", "dig10_cov", "longest_book_sub", "sub_cov"):
    n, mu, sd = summ(key)
    obs = mk[key] if key in mk else {"longest_book_sub": lm, "sub_cov": frac_cov}[key]
    zsc = (obs-mu)/sd if (mu is not None and sd and obs is not None) else None
    print(f"  {key}: kharos={obs} | ctrl mean={mu if mu is None else round(mu,4)} sd={sd if sd is None else round(sd,4)} n={n} z={zsc if zsc is None else round(zsc,2)}")

# log10 of parse counts
lk = math.log10(mk["n_parses_strict"]) if mk["n_parses_strict"] else None
lc = [math.log10(c["n_parses_strict"]) for c in ctrl if c["n_parses_strict"]]
print(f"  log10(n_parses_strict): kharos={lk:.2f} | ctrl mean={st.mean(lc):.2f} sd={st.pstdev(lc):.2f} z={(lk-st.mean(lc))/st.pstdev(lc):.2f}")

# empirical p-values for coverage metrics (one-sided, kharos > control)
for key, obs in (("sym10_cov", mk["sym10_cov"]), ("dig10_cov", mk["dig10_cov"]), ("sub_cov", frac_cov), ("longest_book_sub", lm)):
    vals = [c[key] for c in ctrl if c[key] is not None]
    ge = sum(1 for v in vals if v >= obs)
    print(f"  empirical p({key} >= obs) = {ge}/{len(vals)}")

# omission-consistency: are ML omitted codes all inside book omittable set? (true by construction in strict mode)
print("\nML omitted codes (kharos):", mk.get("omitted_codes_ml"))
# how many structural-only parses use a non-book-conformant token? ratio strict/structural
print("strict/structural parse ratio (kharos): {:.3e}".format(mk["n_parses_strict"]/mk["n_parses_struct"]))

# does '39' or written '07' actually appear as forced blockers in kharos?
print("'39' substring occurrences in kharos:", KHAROS.count("39"))

# save results
out = {"kharos": {k: v for k, v in mk.items()}, "prefix2012": m2,
       "kharos_longest_book_sub": lm, "kharos_subcov": frac_cov,
       "control_n": len(ctrl)}
with open("./tmp/audit_20260609/holdout_results.json", "w") as f:
    json.dump(out, f, default=str, indent=1)
print("\nsaved holdout_results.json")
