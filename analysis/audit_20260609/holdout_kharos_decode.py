#!/usr/bin/env python3
"""Holdout decode attack: Kharos 71st sequence (137 digits).

Pipeline:
  1. Load 70 books (dedup) + row0 99-code map from bonelord_operational.sqlite (read-only).
  2. Verify length identity digitslen + insertedzeros == 2*baselen on the 70 books.
  3. DP zero-reinsertion parse of the Kharos string over the 99-code inventory:
     - token A: 2 digits = written code c (must be in inventory, i.e. != '39')
     - token B: 1 digit d = code '0'+d with leading zero omitted (codes 00..09)
  4. Count parse paths exactly; ML (Viterbi) parse with per-code freq x omission probs
     estimated from the 70-book row0 counts.
  5. Cross-corpus template coverage: digit-level 10-gram coverage vs the 70 books,
     symbol-level 10-gram coverage of the ML-decoded stream vs the 70 decodedbase,
     longest common substring (digits) vs corpus.
  6. Control: 100 random shuffles of the Kharos string (exact same digit distribution,
     same length) through the identical pipeline -> z-scores.
"""
import sqlite3, math, random, json
from collections import Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
random.seed(469)

con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

# ---------- 1. load books ----------
rows = cur.execute("""
    SELECT bookid, MIN(digits), MIN(insertedzeros), MIN(baselen), MIN(decodedbase), MIN(digitslen)
    FROM sheet__books GROUP BY bookid
""").fetchall()
print(f"[books] deduped rows: {len(rows)}")
assert len(rows) == 70, "expected 70 books"
books = []
for bookid, digits, iz, bl, base, dl in rows:
    digits = digits.strip()
    books.append(dict(bookid=bookid, digits=digits, iz=int(iz), bl=int(bl),
                      base=base.strip(), dl=int(dl)))
tot_digits = sum(len(b["digits"]) for b in books)
tot_syms = sum(b["bl"] for b in books)
print(f"[books] total digits={tot_digits} total baselen={tot_syms}")

# length identity on all 70
bad = [b["bookid"] for b in books
       if len(b["digits"]) != b["dl"] or b["dl"] + b["iz"] != 2*b["bl"] or len(b["base"]) != b["bl"]]
print(f"[identity] books violating digitslen+insertedzeros==2*baselen or len mismatches: {len(bad)} {bad}")

# ---------- 2. code map ----------
code_rows = cur.execute("""
    SELECT code, symbol, occurrence_count, omitted_count, written_count
    FROM row0_code_symbol_counts WHERE run_id=1
""").fetchall()
print(f"[codes] inventory size: {len(code_rows)}")
code_sym = {c: s for c, s, *_ in code_rows}
occ = {c: o for c, s, o, om, w in code_rows}
omitted = {c: om for c, s, o, om, w in code_rows}
written = {c: w for c, s, o, om, w in code_rows}
inv = set(code_sym)
missing = sorted(set(f"{i:02d}" for i in range(100)) - inv)
print(f"[codes] codes absent from inventory: {missing}")

TOTOCC = sum(occ.values())
# token log-probs from corpus stats (Laplace alpha for robustness)
ALPHA = 0.5
def lp_written(c):
    # P(code) * P(written|code)
    o = occ.get(c, 0); w = written.get(c, 0)
    pc = (o + ALPHA) / (TOTOCC + 100*ALPHA)
    pw = (w + ALPHA) / (o + 2*ALPHA)
    return math.log(pc) + math.log(pw)
def lp_omit(c):
    o = occ.get(c, 0); om = omitted.get(c, 0)
    pc = (o + ALPHA) / (TOTOCC + 100*ALPHA)
    po = (om + ALPHA) / (o + 2*ALPHA)
    return math.log(pc) + math.log(po)

# ---------- 3. DP machinery ----------
def count_paths(s):
    """exact number of valid tokenizations (big int)."""
    L = len(s)
    dp = [0]*(L+1); dp[L] = 1
    for i in range(L-1, -1, -1):
        n = 0
        n += dp[i+1]                      # omitted-zero token '0'+s[i] (00..09 all in inv)
        if i+1 < L and s[i:i+2] in inv:
            n += dp[i+2]                  # written 2-digit code
        dp[i] = n
    return dp[0]

def viterbi(s):
    """ML parse. returns (logprob, tokens) tokens=(code, omitted_bool)."""
    L = len(s)
    best = [None]*(L+1); best[L] = (0.0, None, None)
    for i in range(L-1, -1, -1):
        cands = []
        c1 = "0" + s[i]
        if best[i+1] is not None:
            cands.append((best[i+1][0] + lp_omit(c1), (c1, True), i+1))
        if i+1 < L and s[i:i+2] in inv and best[i+2] is not None:
            c2 = s[i:i+2]
            cands.append((best[i+2][0] + lp_written(c2), (c2, False), i+2))
        best[i] = max(cands) if cands else None
    if best[0] is None:
        return None, []
    toks = []; i = 0
    while i < L:
        lpv, tok, nxt = best[i]
        toks.append(tok); i = nxt
    return best[0][0], toks

def k_range(s):
    """min/max number of omitted-zero insertions over valid parses."""
    L = len(s)
    mn = [None]*(L+1); mx = [None]*(L+1); mn[L] = mx[L] = 0
    for i in range(L-1, -1, -1):
        opts_mn, opts_mx = [], []
        if mn[i+1] is not None:
            opts_mn.append(mn[i+1]+1); opts_mx.append(mx[i+1]+1)
        if i+1 < L and s[i:i+2] in inv and mn[i+2] is not None:
            opts_mn.append(mn[i+2]); opts_mx.append(mx[i+2])
        mn[i] = min(opts_mn) if opts_mn else None
        mx[i] = max(opts_mx) if opts_mx else None
    return mn[0], mx[0]

# sanity: does the DP admit the books' recorded parses? check stored probe streams
probe = cur.execute("""
    SELECT bookid, reconstructed_code_stream, insertedzeros, valid
    FROM row0_code_symbol_probe_books WHERE run_id=1
""").fetchall()
print(f"[probe] probe books: {len(probe)}, valid={sum(r[3] for r in probe)}")

# ---------- 4. corpus templates ----------
NG = 10
book_digit_ngrams = set()
book_sym_ngrams = set()
all_digits_concat = []
for b in books:
    d = b["digits"]; bs = b["base"]
    all_digits_concat.append(d)
    for i in range(len(d)-NG+1):
        book_digit_ngrams.add(d[i:i+NG])
    for i in range(len(bs)-NG+1):
        book_sym_ngrams.add(bs[i:i+NG])
print(f"[templates] distinct digit {NG}-grams in 70 books: {len(book_digit_ngrams)}")
print(f"[templates] distinct symbol {NG}-grams in 70 books: {len(book_sym_ngrams)}")

def ngram_cov(s, grams, n=NG):
    """(fraction of n-grams present, fraction of positions covered)"""
    L = len(s)
    if L < n: return 0.0, 0.0
    hits = 0; covered = [False]*L
    for i in range(L-n+1):
        if s[i:i+n] in grams:
            hits += 1
            for j in range(i, i+n): covered[j] = True
    return hits/(L-n+1), sum(covered)/L

def longest_shared(s, corpus_list):
    """longest substring of s present in any corpus string (binary search)."""
    lo, hi = 0, len(s)
    joined = "\x00".join(corpus_list)
    def has(n):
        if n == 0: return True
        subs = {s[i:i+n] for i in range(len(s)-n+1)}
        return any(x in joined for x in subs)
    while lo < hi:
        mid = (lo+hi+1)//2
        if has(mid): lo = mid
        else: hi = mid-1
    return lo

def omission_consistency(toks):
    """flags: uses of code 39; omitted use of never-omitted codes; written use of always-omitted codes."""
    flags = Counter()
    for c, om in toks:
        if c not in inv: flags["invalid_code"] += 1
        if om and omitted.get(c, 0) == 0: flags["omit_never_omitted"] += 1
        if (not om) and c in inv and written.get(c, 0) == 0: flags["write_never_written"] += 1
    return dict(flags)

# ---------- 5. run on Kharos ----------
KH = cur.execute("""
    SELECT sequence_digits FROM s2ward_corpus_audit_items
    WHERE source_set='sorted_unique_with_kharos' AND source_index=22
""").fetchone()[0].strip()
print(f"\n[kharos] len={len(KH)}")
assert len(KH) == 137

def full_metrics(s, label, do_print=True):
    paths = count_paths(s)
    kmin, kmax = k_range(s)
    lpv, toks = viterbi(s)
    decoded = "".join(code_sym[c] for c, om in toks)
    n_omit = sum(1 for _, om in toks if om)
    flags = omission_consistency(toks)
    dcov_g, dcov_p = ngram_cov(s, book_digit_ngrams)
    scov_g, scov_p = ngram_cov(decoded, book_sym_ngrams)
    lss = longest_shared(s, [b["digits"] for b in books])
    m = dict(label=label, length=len(s), n_paths_log10=math.log10(paths) if paths else float("-inf"),
             k_min=kmin, k_max=kmax, ml_logprob=lpv, ml_logprob_per_token=lpv/len(toks) if toks else None,
             n_tokens=len(toks), n_omitted=n_omit, baselen_implied=len(toks),
             identity_holds=(len(s)+n_omit == 2*len(toks)),
             flags=flags, digit10_gramcov=dcov_g, digit10_poscov=dcov_p,
             sym10_gramcov=scov_g, sym10_poscov=scov_p, longest_shared_digit_substr=lss,
             decoded=decoded)
    if do_print:
        print(json.dumps({k: v for k, v in m.items() if k != "decoded"}, indent=2))
        print(f"[{label}] decoded({len(decoded)}): {decoded}")
    return m

kh = full_metrics(KH, "KHAROS")

# per-code omission consistency vs 70-book rates for the ML parse
print("\n[kharos] ML-parse code usage vs corpus omission rates (0x codes):")
use = Counter()
for c, om in [(c, om) for c, om in viterbi(KH)[1]]:
    use[(c, om)] += 1
for c in sorted(set(c for (c, _o) in use) | {f"0{i}" for i in range(10)}):
    if c.startswith("0") and len(c) == 2:
        o_k = use.get((c, True), 0); w_k = use.get((c, False), 0)
        corp = f"corpus omit {omitted.get(c,0)}/{occ.get(c,0)}"
        if o_k or w_k:
            print(f"  code {c}: kharos omitted={o_k} written={w_k} | {corp}")

# ---------- 6. controls ----------
NCTRL = 100
ctrl = []
chars = list(KH)
for t in range(NCTRL):
    random.shuffle(chars)
    ctrl.append(full_metrics("".join(chars), f"ctrl{t}", do_print=False))

def zstat(name, real, ctrls):
    vals = [c[name] for c in ctrls]
    mu = sum(vals)/len(vals)
    sd = (sum((v-mu)**2 for v in vals)/(len(vals)-1)) ** 0.5
    z = (real - mu)/sd if sd > 0 else float("inf") if real != mu else 0.0
    n_ge = sum(1 for v in vals if v >= real)
    return mu, sd, z, n_ge

print(f"\n[controls] n={NCTRL} shuffles of the Kharos string itself (same digit multiset)")
for name in ["n_paths_log10", "ml_logprob_per_token", "digit10_gramcov", "digit10_poscov",
             "sym10_gramcov", "sym10_poscov", "longest_shared_digit_substr"]:
    mu, sd, z, n_ge = zstat(name, kh[name], ctrl)
    print(f"  {name}: kharos={kh[name]:.4f} ctrl_mu={mu:.4f} ctrl_sd={sd:.4f} z={z:+.2f} "
          f"P(ctrl>=real)={n_ge}/{NCTRL}")

# ---------- 7. book-level benchmark: same metrics for each real book (leave-one-out templates) ----------
print("\n[benchmark] real-book metrics (in-sample, with leave-one-out templates for coverage):")
book_dcov, book_scov, book_lss = [], [], []
for b in books:
    d = b["digits"]
    # LOO digit ngrams
    loo = set()
    for ob in books:
        if ob["bookid"] == b["bookid"]: continue
        od = ob["digits"]
        for i in range(len(od)-NG+1): loo.add(od[i:i+NG])
    g, p = ngram_cov(d, loo)
    lss = longest_shared(d, [ob["digits"] for ob in books if ob["bookid"] != b["bookid"]])
    book_dcov.append(g); book_scov.append(p); book_lss.append(lss)
print(f"  LOO digit10 gramcov over 70 books: mean={sum(book_dcov)/70:.4f} "
      f"min={min(book_dcov):.4f} max={max(book_dcov):.4f}")
print(f"  LOO digit10 poscov  over 70 books: mean={sum(book_scov)/70:.4f} "
      f"min={min(book_scov):.4f} max={max(book_scov):.4f}")
print(f"  LOO longest shared digit substr: mean={sum(book_lss)/70:.1f} "
      f"min={min(book_lss)} max={max(book_lss)}")
print(f"  KHAROS (fully out-of-sample): digit10 gramcov={kh['digit10_gramcov']:.4f} "
      f"poscov={kh['digit10_poscov']:.4f} lss={kh['longest_shared_digit_substr']}")

con.close()
print("\nDONE")
