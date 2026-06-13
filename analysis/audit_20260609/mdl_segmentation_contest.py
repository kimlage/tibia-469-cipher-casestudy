#!/usr/bin/env python3
"""
Insertion-free segmentation MDL contest vs canonical 2-digit + inserted-zeros model.

Models compared under ONE consistent two-part MDL framework:
  total bits = codebook bits + token-stream bits (KT sequential, alphabet = lexicon size)
               [+ for canonical only: omission-layer bits (which 0X tokens were written short)]

  codebook bits = log2 C(1110, K)   (lexicon = subset of all 10+100+1000 digit strings len 1-3)
  canonical additionally charged log2 C(100,10) for the 'omissible set = {00..09}' rule.

Models:
  FIX1      : lexicon {0..9}, trivial parse (11263 tokens)
  CANON     : 2-digit codes from probe table (5729 tokens, A=100) + insertion bits
  MIXA1     : insertion-free lexicon {00..99} u {1..9}  (K=109), EM + Viterbi
  MIXA2     : insertion-free lexicon {00..99} u {0..9}  (K=110), EM + Viterbi
  LEARNED   : unigram-lexicon EM over all observed 1-3 grams, MDL pruning sweep;
              best overall and best with K<=110. (Unrestricted unigram dominates any
              prefix-free code in achievable stream likelihood => valid upper bound.)

Secondary metric: cross-book token 10-gram reuse (fraction of 10-token windows whose
10-gram appears in >=1 other book).

Controls: per-book digit shuffles (N=20), full LEARNED pipeline + MIXA1 rerun.
Also rerun on substring-deduped book set.
"""
import sqlite3, math, random, json, sys
from collections import defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
LOG2 = math.log(2.0)
NEG = float("-inf")

def log2_comb(n, k):
    if k < 0 or k > n: return float("inf")
    return (math.lgamma(n+1) - math.lgamma(k+1) - math.lgamma(n-k+1)) / LOG2

def kt_cost(tokens, A):
    """KT sequential code length in bits, alphabet size A."""
    cost = 0.0
    counts = {}
    for t, x in enumerate(tokens):
        c = counts.get(x, 0)
        cost += -math.log2((c + 0.5) / (t + A / 2.0))
        counts[x] = c + 1
    return cost

CODEBOOK_UNIVERSE = 10 + 100 + 1000  # all digit strings length 1..3

def codebook_bits(K):
    return log2_comb(CODEBOOK_UNIVERSE, K)

# ---------- segmentation machinery ----------
def viterbi(s, logp):
    """Best segmentation of digit string s using lexicon logp {word: logprob}. Returns tokens or None."""
    n = len(s)
    best = [NEG] * (n + 1); best[0] = 0.0
    back = [None] * (n + 1)
    for i in range(1, n + 1):
        for L in (1, 2, 3):
            if i - L < 0: break
            w = s[i - L:i]
            lp = logp.get(w)
            if lp is None or best[i - L] == NEG: continue
            v = best[i - L] + lp
            if v > best[i]:
                best[i] = v; back[i] = L
    if best[n] == NEG: return None
    toks = []
    i = n
    while i > 0:
        L = back[i]; toks.append(s[i - L:i]); i -= L
    toks.reverse()
    return toks

def forward_backward_counts(s, logp, counts):
    """Accumulate expected token counts; returns log-likelihood or None if unparseable."""
    n = len(s)
    alpha = [NEG] * (n + 1); alpha[0] = 0.0
    for i in range(1, n + 1):
        acc = NEG
        for L in (1, 2, 3):
            if i - L < 0: break
            lp = logp.get(s[i - L:i])
            if lp is None or alpha[i - L] == NEG: continue
            v = alpha[i - L] + lp
            acc = v if acc == NEG else (max(acc, v) + math.log1p(math.exp(-abs(acc - v))))
        alpha[i] = acc
    if alpha[n] == NEG: return None
    beta = [NEG] * (n + 1); beta[n] = 0.0
    for i in range(n - 1, -1, -1):
        acc = NEG
        for L in (1, 2, 3):
            if i + L > n: break
            lp = logp.get(s[i:i + L])
            if lp is None or beta[i + L] == NEG: continue
            v = lp + beta[i + L]
            acc = v if acc == NEG else (max(acc, v) + math.log1p(math.exp(-abs(acc - v))))
        beta[i] = acc
    Z = alpha[n]
    for i in range(n):
        if alpha[i] == NEG: continue
        for L in (1, 2, 3):
            if i + L > n: break
            w = s[i:i + L]
            lp = logp.get(w)
            if lp is None or beta[i + L] == NEG: continue
            counts[w] += math.exp(alpha[i] + lp + beta[i + L] - Z)
    return Z

def em(strings, lexicon, iters=40, tol=0.05, init_logp=None):
    """EM for unigram segmentation model. Returns (logp, total_loglik) or (None,None) if unparseable."""
    if init_logp is None:
        u = -math.log(len(lexicon))
        logp = {w: u for w in lexicon}
    else:
        logp = {w: init_logp.get(w, -math.log(len(lexicon) * 100)) for w in lexicon}
        # renormalize
        m = max(logp.values()); tot = sum(math.exp(v - m) for v in logp.values())
        logc = m + math.log(tot)
        logp = {w: v - logc for w, v in logp.items()}
    prev = None
    for it in range(iters):
        counts = defaultdict(float)
        ll = 0.0
        for s in strings:
            z = forward_backward_counts(s, logp, counts)
            if z is None: return None, None
            ll += z
        tot = sum(counts.values())
        floor = 1e-10
        logp = {w: math.log(max(counts.get(w, 0.0), floor) / tot) for w in lexicon}
        if prev is not None and abs(ll - prev) < tol: break
        prev = ll
    return logp, prev if prev is not None else ll

def model_mdl(strings, lexicon, em_iters=40, init_logp=None):
    """EM-fit lexicon, Viterbi-tokenize, KT-cost. Returns dict or None."""
    logp, ll = em(strings, lexicon, iters=em_iters, init_logp=init_logp)
    if logp is None: return None
    all_toks = []
    per_book_toks = []
    for s in strings:
        t = viterbi(s, logp)
        if t is None: return None
        per_book_toks.append(t)
        all_toks.extend(t)
    K = len(lexicon)
    stream = kt_cost(all_toks, K)
    cb = codebook_bits(K)
    return {"K": K, "ntok": len(all_toks), "stream": stream, "codebook": cb,
            "total": stream + cb, "logp": logp, "per_book": per_book_toks}

def tengram_reuse(per_book_toks):
    """Fraction of 10-token windows whose 10-gram occurs in >= 1 other book."""
    grams = defaultdict(set)
    for bi, toks in enumerate(per_book_toks):
        for j in range(len(toks) - 9):
            grams[tuple(toks[j:j + 10])].add(bi)
    shared = tot = 0
    for bi, toks in enumerate(per_book_toks):
        for j in range(len(toks) - 9):
            tot += 1
            if len(grams[tuple(toks[j:j + 10])]) > 1: shared += 1
    return shared / tot if tot else 0.0, tot

# ---------- load data ----------
con = sqlite3.connect(DB, uri=True)
cur = con.cursor()
rows = cur.execute("SELECT bookid, digits, CAST(insertedzeros AS INT), CAST(baselen AS INT) "
                   "FROM sheet__books GROUP BY bookid").fetchall()
print(f"[load] sheet__books deduped rows: {len(rows)}", flush=True)
assert len(rows) == 70
books = {bid: d for bid, d, _, _ in rows}
inserted = {bid: iz for bid, _, iz, _ in rows}
ndigits = sum(len(d) for d in books.values())
print(f"[load] total digits: {ndigits}")

probe = cur.execute("SELECT bookid, reconstructed_code_stream, omitted_positions_json "
                    "FROM row0_code_symbol_probe_books WHERE run_id=1 AND valid=1").fetchall()
print(f"[load] probe books: {len(probe)}")
canon_stream = {bid: cs.split() for bid, cs, _ in probe}
canon_omit = {bid: json.loads(oj) for bid, _, oj in probe}
con.close()

book_ids = sorted(books, key=lambda b: int(b))
strings = [books[b] for b in book_ids]

# substring-dedup (item-1 style fragment dedup)
contained = set()
for a in book_ids:
    for b in book_ids:
        if a != b and books[a] in books[b] and a not in contained and b not in contained:
            # a is a fragment of b -> drop a (if identical impossible: all distinct)
            if len(books[a]) < len(books[b]):
                contained.add(a)
dedup_ids = [b for b in book_ids if b not in contained]
dedup_strings = [books[b] for b in dedup_ids]
print(f"[dedup] books contained in another book: {len(contained)}; deduped set: {len(dedup_ids)} books, "
      f"{sum(len(s) for s in dedup_strings)} digits")

def canonical_mdl(ids):
    toks_all = []; per_book = []
    ins_bits = 0.0
    for b in ids:
        toks = canon_stream[b]
        per_book.append(toks)
        toks_all.extend(toks)
        n_elig = sum(1 for t in toks if t[0] == '0')   # codes 00..09 eligible for zero-omission
        k = inserted[b]
        ins_bits += log2_comb(n_elig, k) + math.log2(n_elig + 1)
    stream = kt_cost(toks_all, 100)
    cb = codebook_bits(100) + log2_comb(100, 10)   # lexicon {00..99} + omissible-set rule
    return {"K": 100, "ntok": len(toks_all), "stream": stream, "codebook": cb,
            "ins": ins_bits, "total": stream + cb + ins_bits, "per_book": per_book}

def fixed1_mdl(strs):
    toks = [c for s in strs for c in s]
    stream = kt_cost(toks, 10)
    cb = codebook_bits(10)
    return {"K": 10, "ntok": len(toks), "stream": stream, "codebook": cb, "total": stream + cb}

def all_ngrams(strs):
    lex = set()
    for s in strs:
        for L in (1, 2, 3):
            for i in range(len(s) - L + 1):
                lex.add(s[i:i + L])
    return lex

def learned_sweep(strs, tag, em_iters=30, sizes=None, verbose=True):
    """Unigram lexicon EM + MDL pruning sweep. Returns (best, best_le110, table)."""
    full = all_ngrams(strs)
    logp, _ = em(strs, full, iters=em_iters)
    best = None; best110 = None; table = []
    if sizes is None:
        sizes = [len(full), 800, 600, 450, 350, 280, 220, 180, 150, 130, 110, 95, 80, 65, 50, 40, 30, 25, 20, 15, 12, 10]
    cur_logp = logp
    for K in sizes:
        ranked = sorted(cur_logp, key=lambda w: cur_logp[w], reverse=True)
        lex = set(ranked[:K])
        # guarantee parseability: add single digits present in corpus
        needed = {c for s in strs for c in s}
        lex |= needed
        res = model_mdl(strs, lex, em_iters=em_iters, init_logp=cur_logp)
        if res is None:
            table.append((K, None)); continue
        res["lex"] = lex
        table.append((len(lex), res["total"]))
        if verbose:
            print(f"  [{tag}] K={len(lex):4d} ntok={res['ntok']:5d} stream={res['stream']:9.1f} "
                  f"cb={res['codebook']:7.1f} total={res['total']:9.1f} b/d={res['total']/sum(len(s) for s in strs):.4f}", flush=True)
        cur_logp = res["logp"]
        if best is None or res["total"] < best["total"]: best = res
        if len(lex) <= 110 and (best110 is None or res["total"] < best110["total"]): best110 = res
    return best, best110, table

def is_prefix_free(lex):
    lex = sorted(lex)
    for i, w in enumerate(lex):
        for v in lex[i + 1:]:
            if v.startswith(w): return False
            if v[0] != w[0] and not v.startswith(w[0]): break
    return True

def report(name, res, nd):
    extra = f" ins={res['ins']:.1f}" if "ins" in res else ""
    print(f"{name:18s} K={res['K']:4d} ntok={res['ntok']:5d} stream={res['stream']:.1f} "
          f"cb={res['codebook']:.1f}{extra} TOTAL={res['total']:.1f} bits  ({res['total']/nd:.4f} b/d)", flush=True)

# ================= FULL 70-BOOK CORPUS =================
print("\n=== FULL CORPUS (70 books, %d digits) ===" % ndigits)
res_canon = canonical_mdl(book_ids)
report("CANON(2d+ins)", res_canon, ndigits)
res_f1 = fixed1_mdl(strings)
report("FIX1", res_f1, ndigits)

lexA1 = {f"{i:02d}" for i in range(100)} | {str(d) for d in range(1, 10)}
lexA2 = lexA1 | {"0"}
res_a1 = model_mdl(strings, lexA1)
if res_a1: report("MIXA1(00-99,1-9)", res_a1, ndigits)
else: print("MIXA1: PARSE FAILURE on some book")
res_a2 = model_mdl(strings, lexA2)
if res_a2: report("MIXA2(+'0')", res_a2, ndigits)
else: print("MIXA2: PARSE FAILURE")

print("[learned sweep, full corpus]")
best, best110, table = learned_sweep(strings, "full")
report("LEARNED best", best, ndigits)
report("LEARNED K<=110", best110, ndigits)
print(f"LEARNED best lexicon prefix-free: {is_prefix_free(best['lex'])}; "
      f"K<=110 lexicon prefix-free: {is_prefix_free(best110['lex'])}")
print("LEARNED best top-30 codewords by prob:",
      sorted(best["logp"], key=lambda w: best["logp"][w], reverse=True)[:30])

# 10-gram reuse
ru_canon, n_c = tengram_reuse(res_canon["per_book"])
ru_a1, n_a = tengram_reuse(res_a1["per_book"]) if res_a1 else (None, None)
ru_l, n_l = tengram_reuse(best["per_book"])
ru_l110, n_l110 = tengram_reuse(best110["per_book"])
print(f"10-gram reuse: CANON={ru_canon:.4f} (n={n_c})  MIXA1={ru_a1:.4f} (n={n_a})  "
      f"LEARNEDbest={ru_l:.4f} (n={n_l})  LEARNED<=110={ru_l110:.4f} (n={n_l110})")

# ================= DEDUPED CORPUS =================
nd2 = sum(len(s) for s in dedup_strings)
print(f"\n=== DEDUPED CORPUS ({len(dedup_ids)} books, {nd2} digits) ===")
res_canon_d = canonical_mdl(dedup_ids)
report("CANON(2d+ins)", res_canon_d, nd2)
res_f1_d = fixed1_mdl(dedup_strings)
report("FIX1", res_f1_d, nd2)
res_a1_d = model_mdl(dedup_strings, lexA1)
if res_a1_d: report("MIXA1", res_a1_d, nd2)
print("[learned sweep, deduped corpus]")
best_d, best110_d, _ = learned_sweep(dedup_strings, "dedup", verbose=False)
report("LEARNED best", best_d, nd2)
report("LEARNED K<=110", best110_d, nd2)
ru_canon_d, ncd = tengram_reuse(res_canon_d["per_book"])
ru_l_d, nld = tengram_reuse(best_d["per_book"])
print(f"10-gram reuse (dedup): CANON={ru_canon_d:.4f} (n={ncd})  LEARNEDbest={ru_l_d:.4f} (n={nld})")

# ================= SHUFFLE CONTROLS =================
print("\n=== SHUFFLE CONTROLS (per-book digit shuffles, full corpus) ===", flush=True)
NSHUF = 20
rng = random.Random(469)
shuf_best = []; shuf_a1 = []
sizes_light = [400, 250, 150, 110, 80, 50, 30, 20, 12]
for rep in range(NSHUF):
    sh = []
    for s in strings:
        l = list(s); rng.shuffle(l); sh.append("".join(l))
    ra1 = model_mdl(sh, lexA1, em_iters=25)
    b, b110, _ = learned_sweep(sh, f"shuf{rep}", em_iters=20, sizes=sizes_light, verbose=False)
    shuf_a1.append(ra1["total"] if ra1 else float("nan"))
    shuf_best.append(b["total"])
    print(f"  shuffle {rep:2d}: MIXA1={shuf_a1[-1]:.1f}  LEARNEDbest={b['total']:.1f} (K={b['K']})", flush=True)

import statistics as st
mu, sd = st.mean(shuf_best), st.stdev(shuf_best)
mu_a, sd_a = st.mean(shuf_a1), st.stdev(shuf_a1)
z_learn = (best["total"] - mu) / sd
z_a1 = (res_a1["total"] - mu_a) / sd_a
print(f"\nshuffle LEARNEDbest: mean={mu:.1f} sd={sd:.1f}; real={best['total']:.1f}; z={z_learn:+.2f}")
print(f"shuffle MIXA1:       mean={mu_a:.1f} sd={sd_a:.1f}; real={res_a1['total']:.1f}; z={z_a1:+.2f}")

# ================= VERDICT TABLE =================
print("\n=== SUMMARY (bits, bits/digit over full corpus) ===")
for nm, r in [("CANON", res_canon), ("FIX1", res_f1), ("MIXA1", res_a1), ("MIXA2", res_a2),
              ("LEARNED_best", best), ("LEARNED_K<=110", best110)]:
    if r: print(f"{nm:16s} {r['total']:10.1f}  {r['total']/ndigits:.4f}")
delta = best["total"] - res_canon["total"]
print(f"\nDELTA (LEARNED_best - CANON) = {delta:+.1f} bits ({delta/ndigits:+.4f} b/d)")
print("CANONICAL WINS" if delta > 0 else "COMPETITOR WINS -- INVESTIGATE")
