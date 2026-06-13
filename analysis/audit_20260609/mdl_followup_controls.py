#!/usr/bin/env python3
"""
Follow-up controls for the MDL segmentation contest.

Q: the learned variable-length lexicon beats canonical on order-0 MDL. Is that a rival
segmentation, or just dictionary compression of cross-token repetition that is fully
compatible with the canonical 2-digit frame?

Controls:
  B  WRITTEN-FIXED : canonical boundaries, written forms as token types (no insertion bits).
  C  SMART-CANON   : canonical + omission flags coded per-code (KT-Bernoulli given code id)
                     = the 'item-2 deterministic-ish rule' canonical.
  D  BOUNDARY ALIGNMENT : fraction of learned/MIXA1 Viterbi boundaries coinciding with
                     canonical written-token boundaries, vs chance density.
  E  TOKEN-SHUFFLE : per-book shuffle of canonical written tokens -> new digit strings.
                     Canonical KT cost is permutation-invariant (exchangeable), so canonical
                     MDL is IDENTICAL on this corpus. If learned-best collapses toward
                     canonical here, its win on real data = cross-token repetition only.
"""
import sqlite3, math, random, json
from collections import defaultdict
import importlib.util, sys

spec = importlib.util.spec_from_file_location(
    "mc", "./tmp/audit_20260609/mdl_segmentation_contest_lib.py")

# inline the needed machinery instead (copied from main script)
LOG2 = math.log(2.0); NEG = float("-inf")
def log2_comb(n, k):
    if k < 0 or k > n: return float("inf")
    return (math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1))/LOG2
def kt_cost(tokens, A):
    cost = 0.0; counts = {}
    for t, x in enumerate(tokens):
        c = counts.get(x, 0)
        cost += -math.log2((c+0.5)/(t+A/2.0)); counts[x] = c+1
    return cost
UNIV = 1110
def codebook_bits(K): return log2_comb(UNIV, K)

def viterbi(s, logp):
    n = len(s); best = [NEG]*(n+1); best[0] = 0.0; back = [None]*(n+1)
    for i in range(1, n+1):
        for L in (1,2,3):
            if i-L < 0: break
            lp = logp.get(s[i-L:i])
            if lp is None or best[i-L] == NEG: continue
            v = best[i-L]+lp
            if v > best[i]: best[i] = v; back[i] = L
    if best[n] == NEG: return None
    toks = []; i = n
    while i > 0:
        L = back[i]; toks.append(s[i-L:i]); i -= L
    toks.reverse(); return toks

def forward_backward_counts(s, logp, counts):
    n = len(s); alpha = [NEG]*(n+1); alpha[0] = 0.0
    for i in range(1, n+1):
        acc = NEG
        for L in (1,2,3):
            if i-L < 0: break
            lp = logp.get(s[i-L:i])
            if lp is None or alpha[i-L] == NEG: continue
            v = alpha[i-L]+lp
            acc = v if acc == NEG else (max(acc,v)+math.log1p(math.exp(-abs(acc-v))))
        alpha[i] = acc
    if alpha[n] == NEG: return None
    beta = [NEG]*(n+1); beta[n] = 0.0
    for i in range(n-1, -1, -1):
        acc = NEG
        for L in (1,2,3):
            if i+L > n: break
            lp = logp.get(s[i:i+L])
            if lp is None or beta[i+L] == NEG: continue
            v = lp+beta[i+L]
            acc = v if acc == NEG else (max(acc,v)+math.log1p(math.exp(-abs(acc-v))))
        beta[i] = acc
    Z = alpha[n]
    for i in range(n):
        if alpha[i] == NEG: continue
        for L in (1,2,3):
            if i+L > n: break
            w = s[i:i+L]; lp = logp.get(w)
            if lp is None or beta[i+L] == NEG: continue
            counts[w] += math.exp(alpha[i]+lp+beta[i+L]-Z)
    return Z

def em(strings, lexicon, iters=30, tol=0.05, init_logp=None):
    if init_logp is None:
        u = -math.log(len(lexicon)); logp = {w: u for w in lexicon}
    else:
        logp = {w: init_logp.get(w, -math.log(len(lexicon)*100)) for w in lexicon}
        m = max(logp.values()); tot = sum(math.exp(v-m) for v in logp.values())
        logc = m+math.log(tot); logp = {w: v-logc for w, v in logp.items()}
    prev = None; ll = None
    for it in range(iters):
        counts = defaultdict(float); ll = 0.0
        for s in strings:
            z = forward_backward_counts(s, logp, counts)
            if z is None: return None, None
            ll += z
        tot = sum(counts.values())
        logp = {w: math.log(max(counts.get(w,0.0),1e-10)/tot) for w in lexicon}
        if prev is not None and abs(ll-prev) < tol: break
        prev = ll
    return logp, ll

def model_mdl(strings, lexicon, em_iters=30, init_logp=None):
    logp, ll = em(strings, lexicon, iters=em_iters, init_logp=init_logp)
    if logp is None: return None
    all_toks = []; per_book = []
    for s in strings:
        t = viterbi(s, logp)
        if t is None: return None
        per_book.append(t); all_toks.extend(t)
    K = len(lexicon)
    stream = kt_cost(all_toks, K); cb = codebook_bits(K)
    return {"K": K, "ntok": len(all_toks), "stream": stream, "codebook": cb,
            "total": stream+cb, "logp": logp, "per_book": per_book}

def all_ngrams(strs):
    lex = set()
    for s in strs:
        for L in (1,2,3):
            for i in range(len(s)-L+1): lex.add(s[i:i+L])
    return lex

def learned_sweep(strs, em_iters=25, sizes=None):
    full = all_ngrams(strs)
    logp, _ = em(strs, full, iters=em_iters)
    best = None; best110 = None
    if sizes is None:
        sizes = [len(full), 600, 450, 350, 280, 220, 180, 150, 130, 110, 95, 80, 65, 50, 40, 30, 20, 12, 10]
    cur = logp
    for K in sizes:
        ranked = sorted(cur, key=lambda w: cur[w], reverse=True)
        lex = set(ranked[:K]) | {c for s in strs for c in s}
        res = model_mdl(strs, lex, em_iters=em_iters, init_logp=cur)
        if res is None: continue
        res["lex"] = lex; cur = res["logp"]
        if best is None or res["total"] < best["total"]: best = res
        if len(lex) <= 110 and (best110 is None or res["total"] < best110["total"]): best110 = res
    return best, best110

# ---------- load ----------
DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True); cur = con.cursor()
rows = cur.execute("SELECT bookid, digits, CAST(insertedzeros AS INT) FROM sheet__books GROUP BY bookid").fetchall()
books = {b: d for b, d, _ in rows}; inserted = {b: iz for b, _, iz in rows}
probe = cur.execute("SELECT bookid, reconstructed_code_stream, omitted_positions_json, omitted_codes_json "
                    "FROM row0_code_symbol_probe_books WHERE run_id=1 AND valid=1").fetchall()
con.close()
print(f"[load] books={len(books)} probe={len(probe)}")
book_ids = sorted(books, key=lambda b: int(b))
strings = [books[b] for b in book_ids]
ndigits = sum(len(s) for s in strings)

# canonical written tokens per book (verify exact reconstruction)
written = {}
for b, cs, oj, ocj in probe:
    codes = cs.split()
    pos = json.loads(oj); ocodes = json.loads(ocj)
    om = set(p - 1 for p in pos)  # positions are 1-based token indices
    for p, oc in zip(pos, ocodes):
        assert codes[p - 1] == oc, (b, p, codes[p - 1], oc)
    toks = []
    for i, c in enumerate(codes):
        if i in om:
            assert c[0] == '0', (b, i, c)
            toks.append(c[1:])
        else:
            toks.append(c)
    assert "".join(toks) == books[b], f"book {b} reconstruction mismatch"
    assert len(om) == inserted[b]
    written[b] = (codes, toks, om)
print(f"[verify] all {len(written)} books: written-token concatenation == digits EXACT")
tot_short = sum(len(om) for _, _, om in written.values())
print(f"[verify] total short-form (omitted-zero) tokens: {tot_short}")

# ---------- B: WRITTEN-FIXED ----------
all_written = [t for b in book_ids for t in written[b][1]]
K_B = 110  # lexicon {00..99} u {0..9}
mdl_B = kt_cost(all_written, K_B) + codebook_bits(K_B)
print(f"\n[B] WRITTEN-FIXED (canonical boundaries, written types, K=110): "
      f"ntok={len(all_written)} TOTAL={mdl_B:.1f} bits ({mdl_B/ndigits:.4f} b/d)")

# ---------- C: SMART-CANON (omission flag coded per-code, KT-Bernoulli) ----------
all_codes = [c for b in book_ids for c in written[b][0]]
stream_C = kt_cost(all_codes, 100)
flag_cost = 0.0; flag_counts = defaultdict(lambda: [0, 0])  # code -> [n_seen, n_omit]
for b in book_ids:
    codes, toks, om = written[b]
    for i, c in enumerate(codes):
        if c[0] != '0': continue
        nseen, nom = flag_counts[c]
        p_omit = (nom + 0.5) / (nseen + 1.0)
        bit = 1 if i in om else 0
        flag_cost += -math.log2(p_omit if bit else 1 - p_omit)
        flag_counts[c][0] += 1; flag_counts[c][1] += bit
cb_C = codebook_bits(100) + log2_comb(100, 10)
mdl_C = stream_C + flag_cost + cb_C
print(f"[C] SMART-CANON (per-code KT omission flags): stream={stream_C:.1f} flags={flag_cost:.1f} "
      f"cb={cb_C:.1f} TOTAL={mdl_C:.1f} bits ({mdl_C/ndigits:.4f} b/d)")
print("    per-code omission rates:",
      {c: f"{v[1]}/{v[0]}" for c, v in sorted(flag_counts.items())})

# ---------- D: boundary alignment ----------
def boundaries(toks):
    s = set(); p = 0
    for t in toks[:-1]:
        p += len(t); s.add(p)
    return s

canon_bounds = {b: boundaries(written[b][1]) for b in book_ids}
n_pos = sum(len(books[b]) - 1 for b in book_ids)
n_cb = sum(len(v) for v in canon_bounds.values())
chance = n_cb / n_pos
print(f"\n[D] canonical internal boundaries: {n_cb} of {n_pos} internal positions (chance rate {chance:.4f})")

def alignment(per_book_toks):
    hit = tot = 0; respect = inst = 0
    for b, toks in zip(book_ids, per_book_toks):
        cb = canon_bounds[b]
        p = 0
        for j, t in enumerate(toks):
            st = p; p += len(t)
            if j < len(toks) - 1:
                tot += 1
                if p in cb: hit += 1
            inst += 1
            ok_start = (st == 0) or (st in cb)
            ok_end = (p == len(books[b])) or (p in cb)
            inner = any((st + q) in cb for q in range(1, len(t)))
            if ok_start and ok_end and not inner: respect += 1
    return hit / tot, respect / inst

# rebuild the contest's key tokenizations fresh (deterministic given same pipeline)
lexA1 = {f"{i:02d}" for i in range(100)} | {str(d) for d in range(1, 10)}
res_a1 = model_mdl(strings, lexA1)
print(f"[rebuild] MIXA1 total={res_a1['total']:.1f}")
best, best110 = learned_sweep(strings)
print(f"[rebuild] LEARNED best K={best['K']} total={best['total']:.1f}; "
      f"K<=110 total={best110['total']:.1f}")

for name, r in [("MIXA1", res_a1), ("LEARNED_best", best), ("LEARNED_K<=110", best110)]:
    al, resp = alignment(r["per_book"])
    lens = defaultdict(int)
    for toks in r["per_book"]:
        for t in toks: lens[len(t)] += 1
    z = (al - chance) * math.sqrt(sum(len(t) for t in r["per_book"])) / math.sqrt(chance * (1 - chance))
    print(f"[D] {name:14s}: boundary-coincidence={al:.4f} (chance {chance:.4f}, z≈{z:+.1f}) "
          f"whole-token-respects-canon={resp:.4f} token-lengths={dict(lens)}")

# ---------- E: token-shuffle control ----------
print("\n[E] TOKEN-SHUFFLE control (canonical written tokens shuffled per book; "
      "canonical MDL invariant by exchangeability)")
rng = random.Random(4690)
NSH = 8
vals = []
for rep in range(NSH):
    sh = []
    for b in book_ids:
        t = list(written[b][1]); rng.shuffle(t); sh.append("".join(t))
    bsh, _ = learned_sweep(sh, em_iters=20,
                           sizes=[500, 350, 250, 180, 130, 110, 80, 50, 30, 20, 12])
    a1sh = model_mdl(sh, lexA1, em_iters=20)
    vals.append((bsh["total"], bsh["K"], a1sh["total"] if a1sh else float("nan")))
    print(f"    rep {rep}: LEARNEDbest={bsh['total']:.1f} (K={bsh['K']})  MIXA1={vals[-1][2]:.1f}", flush=True)
import statistics as st
lb = [v[0] for v in vals]; a1v = [v[2] for v in vals]
print(f"[E] token-shuffled LEARNEDbest: mean={st.mean(lb):.1f} sd={st.stdev(lb):.1f}  "
      f"(real LEARNEDbest=29757.1; CANON=36736.0 invariant)")
print(f"[E] token-shuffled MIXA1:      mean={st.mean(a1v):.1f} sd={st.stdev(a1v):.1f}  (real MIXA1=34777.3)")
zE = (29757.1 - st.mean(lb)) / st.stdev(lb)
print(f"[E] z(real learned vs token-shuffled learned) = {zE:+.2f}")
