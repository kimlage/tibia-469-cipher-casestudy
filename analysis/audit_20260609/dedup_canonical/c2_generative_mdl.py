#!/usr/bin/env python3
"""GENERATIVE MDL VERDICT for the 469 book layer.

Two-part code G (digit level, fully explicit, lossless for the 11263-digit corpus):
  MODEL  = gamma(M+1) + sum_m [ gamma(len_m) + len_m*log2(10) ]      (module inventory)
  DATA   = gamma(B+1) + sum_b [ gamma(items_b+1)
                                + sum_items ( 1 flag bit
                                  + module ref: log2(M)
                                  + literal:   gamma(len)+len*log2(10) ) ]
Modules from the greedy longest-repeated-substring tiling, minL=20 digits
(same algorithm as ../m1_modules.py -> 62 modules, 81.5% digit coverage).
Decoder: read inventory; per book read items left-to-right and concatenate.
Conservative literal/content coding: flat log2(10) per digit (no digit model).
Secondary variant: single adaptive KT digit model over inventory+literals.

Also: LZ77 self-referential two-part code (tighter generative upper bound),
benchmarks, controls (English-through-the-same-code, shuffled symbols),
and residual-payload entropy of the novel material.
Read-only DB.
"""
import sqlite3, math, random
from collections import Counter

log2 = math.log2
URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
cur = con.cursor()

rows = cur.execute("""SELECT bookid, MIN(digits), MIN(decodedbase), COUNT(*)
                      FROM sheet__books GROUP BY bookid""").fetchall()
print("ROWCOUNT sheet__books grouped:", len(rows))
assert len(rows) == 70
def keyf(b):
    try: return (0, int(b))
    except: return (1, b)
ids = sorted([r[0] for r in rows], key=keyf)
dig = {r[0]: r[1] for r in rows}
dec = {r[0]: r[2] for r in rows}
tot_digits = sum(len(dig[b]) for b in ids)
tot_syms = sum(len(dec[b]) for b in ids)
print(f"books=70 total_digits={tot_digits} total_symbols={tot_syms}")

prows = cur.execute("""SELECT bookid, reconstructed_code_stream FROM row0_code_symbol_probe_books
                       WHERE run_id=1""").fetchall()
print("ROWCOUNT probe_books:", len(prows)); assert len(prows) == 70
codes = {r[0]: r[1].split() for r in prows}

mrows = cur.execute("SELECT code, symbol, occurrence_count FROM row0_code_symbol_counts WHERE run_id=1").fetchall()
print("ROWCOUNT map rows:", len(mrows)); assert len(mrows) > 0
sym2codes = {}
for c, s, n in mrows:
    sym2codes.setdefault(s, []).append((c, n))

# ---------------- module tiling (identical algorithm to m1_modules.py) ----------------
def tile(strings, minL):
    cov = {b: bytearray(len(strings[b])) for b in strings}
    modules = []
    cap = max(len(s) for s in strings.values())
    def segments():
        segs = []
        for b in strings:
            s, c = strings[b], cov[b]
            i = 0
            while i < len(s):
                if not c[i]:
                    j = i
                    while j < len(s) and not c[j]: j += 1
                    segs.append((b, i, s[i:j])); i = j
                else: i += 1
        return segs
    while True:
        segs = segments()
        if not segs: break
        maxseg = max(len(t) for _, _, t in segs)
        hi = min(cap, maxseg); lo = minL
        if hi < lo: break
        def repeat_at(L):
            d = {}
            for b, off, t in segs:
                for i in range(len(t) - L + 1):
                    d.setdefault(t[i:i+L], []).append((b, off + i))
            best = None
            for k, occ in d.items():
                if len(occ) < 2: continue
                bb = set(o[0] for o in occ)
                if len(bb) >= 2 or (max(o[1] for o in occ) - min(o[1] for o in occ) >= L):
                    if best is None or len(occ) > len(d[best]): best = k
            return best, d
        bestL = None
        a, z = lo, hi
        while a <= z:
            mid = (a + z) // 2
            k, _ = repeat_at(mid)
            if k is not None: bestL, a = mid, mid + 1
            else: z = mid - 1
        if bestL is None: break
        key, d = repeat_at(bestL)
        occ = sorted(d[key]); claimed = []; last = {}
        for b, p in occ:
            if b in last and p < last[b] + bestL: continue
            claimed.append((b, p)); last[b] = p
        if len(claimed) < 2:
            cap = bestL - 1; continue
        modules.append((len(modules), key, claimed))
        for b, p in claimed:
            for i in range(p, p + bestL): cov[b][i] = 1
        cap = bestL
    return modules, cov

def gamma_bits(n):  # Elias gamma for n>=1
    return 2 * int(math.floor(log2(n))) + 1

def two_part_module_code(strings, order, minL, alpha):
    """Returns dict of all bit terms. alpha = base alphabet size (10 digits / 14 symbols)."""
    modules, cov = tile({b: strings[b] for b in order}, minL)
    M = len(modules)
    inv_len = sum(len(m[1]) for m in modules)
    model = gamma_bits(M + 1) + sum(gamma_bits(len(m[1])) + len(m[1]) * log2(alpha) for m in modules)
    # per-book item lists
    occ_by_book = {b: [] for b in order}
    for mid_, s, occ in modules:
        for b, p in occ: occ_by_book[b].append((p, mid_, len(s)))
    data = gamma_bits(len(order) + 1)
    n_items = n_mod_items = n_lit_items = lit_digits = 0
    flag = ref = lit_len_bits = lit_content = 0.0
    book_hdr = 0.0
    for b in order:
        items = []
        occs = sorted(occ_by_book[b]); pos = 0
        for p, mid_, L in occs:
            if p > pos: items.append(("lit", strings[b][pos:p]))
            items.append(("mod", mid_)); pos = p + L
        if pos < len(strings[b]): items.append(("lit", strings[b][pos:]))
        book_hdr += gamma_bits(len(items) + 1)
        for kind, v in items:
            n_items += 1; flag += 1.0
            if kind == "mod":
                n_mod_items += 1; ref += log2(M) if M > 1 else 0.0
            else:
                n_lit_items += 1; lit_digits += len(v)
                lit_len_bits += gamma_bits(len(v)); lit_content += len(v) * log2(alpha)
    data += book_hdr + flag + ref + lit_len_bits + lit_content
    total = model + data
    # KT variant: inventory digits + literal digits through one adaptive KT over alpha
    def kt_cost(seq, A):
        cnt = Counter(); bits = 0.0
        for i, ch in enumerate(seq):
            bits += -log2((cnt[ch] + 0.5) / (i + A / 2)); cnt[ch] += 1
        return bits
    stream = "".join(m[1] for m in modules)
    for b in order:
        occs = sorted(occ_by_book[b]); pos = 0
        for p, mid_, L in occs:
            if p > pos: stream += strings[b][pos:p]
            pos = p + L
        if pos < len(strings[b]): stream += strings[b][pos:]
    kt_content = kt_cost(stream, alpha)
    total_kt = total - (sum(len(m[1]) for m in modules) + lit_digits) * log2(alpha) + kt_content
    return dict(M=M, inv_len=inv_len, model=model, book_hdr=book_hdr, flags=flag, refs=ref,
                lit_items=n_lit_items, mod_items=n_mod_items, lit_digits=lit_digits,
                lit_len_bits=lit_len_bits, lit_content=lit_content, data=data,
                TOTAL=total, TOTAL_KT=total_kt)

def lz77_code(strings, order, alpha, minM=8):
    """Self-referential LZ77 two-part code: per book ops; copy=(1+log2(hist)+gamma(L-minM+1)), lit=(1+log2(alpha))."""
    hist = ""
    total = gamma_bits(len(order) + 1)
    nlit = ncopy = 0
    for b in order:
        s = strings[b]; i = 0
        ops = 0; bits = 0.0
        while i < len(s):
            ref_text = hist + s[:i]
            lo, hi_, best = minM, len(s) - i, 0
            while lo <= hi_:
                mid = (lo + hi_) // 2
                if s[i:i+mid] in ref_text: best, lo = mid, mid + 1
                else: hi_ = mid - 1
            if best >= minM and len(ref_text) > 1:
                bits += 1 + log2(len(ref_text)) + gamma_bits(best - minM + 1)
                i += best; ncopy += 1
            else:
                bits += 1 + log2(alpha); i += 1; nlit += 1
            ops += 1
        total += gamma_bits(len(s) + 1) + bits
        hist += "#" + s
    return total, nlit, ncopy

def kt_tokens(streams, A):
    cnt = Counter(); bits = 0.0; i = 0
    for st in streams:
        for t in st:
            bits += -log2((cnt[t] + 0.5) / (i + A / 2)); cnt[t] += 1; i += 1
    return bits

RAW = tot_digits * log2(10)
print(f"\n== REAL CORPUS, digit level ==")
print(f"RAW digit baseline: {tot_digits} * log2(10) = {RAW:.1f} bits")

g = two_part_module_code(dig, ids, 20, 10)
print(f"\nGENERATIVE TWO-PART CODE G (modules minL=20):")
print(f"  modules M={g['M']} inventory_digits={g['inv_len']}")
print(f"  MODEL  = {g['model']:.1f} bits  [gamma(M+1)={gamma_bits(g['M']+1)}; per-module length gammas + {g['inv_len']}*log2(10)={g['inv_len']*log2(10):.1f}]")
print(f"  DATA   = {g['data']:.1f} bits:")
print(f"    book count+item counts: {gamma_bits(71) + g['book_hdr']:.1f}")
print(f"    item flags ({int(g['flags'])} items): {g['flags']:.1f}")
print(f"    module refs ({g['mod_items']} x log2({g['M']})={log2(g['M']):.2f}): {g['refs']:.1f}")
print(f"    literal lengths ({g['lit_items']} literals): {g['lit_len_bits']:.1f}")
print(f"    literal content ({g['lit_digits']} digits x log2(10)): {g['lit_content']:.1f}")
print(f"  TOTAL  = {g['TOTAL']:.1f} bits ({g['TOTAL']/tot_digits:.4f} b/d)")
print(f"  TOTAL (KT digit model variant) = {g['TOTAL_KT']:.1f} bits")

lz_total, nlit, ncopy = lz77_code(dig, ids, 10)
print(f"\nGENERATIVE LZ77 SELF-REFERENTIAL CODE (minM=8): TOTAL = {lz_total:.1f} bits "
      f"({lz_total/tot_digits:.4f} b/d) [literal digits={nlit}, copies={ncopy}]")

# internal token benchmark (message-bearing: digits = stream of 2-digit cipher tokens)
tok_streams = [codes[b] for b in ids]
ntok = sum(len(t) for t in tok_streams)
tokbits = kt_tokens(tok_streams, 100) + gamma_bits(71) + sum(gamma_bits(len(t) + 1) for t in tok_streams)
print(f"\nMESSAGE-BEARING BENCHMARKS (digit level):")
print(f"  internal token-KT on reconstructed code stream ({ntok} tokens, 100-token KT): {tokbits:.1f} bits "
      f"(caveat: ignores inserted-zero reconstruction flags ~600 bits)")
print(f"  CANON  (verified ../mdl_contest_run1.log): 36736.0 bits (3.2616 b/d, incl codebook+insertion flags)")
print(f"  MIXA1  (verified ../mdl_contest_run1.log): 34777.3 bits (3.0877 b/d, incl codebook) <- best message-bearing")
print(f"  RAW: {RAW:.1f}")
print(f"  [symbol-level, different object (5729-symbol stream, lossy wrt digits):")
print(f"   baseline 21812; RePair grammar 13125 (../m2_out.txt) - generative grammar already wins there]")

best_msg = 34777.3
print(f"\nMARGINS: G vs MIXA1 = {best_msg - g['TOTAL']:+.1f} bits; G vs CANON = {36736.0 - g['TOTAL']:+.1f}; "
      f"G vs RAW = {RAW - g['TOTAL']:+.1f}")
print(f"         LZ77 vs MIXA1 = {best_msg - lz_total:+.1f} bits")

# ---------------- residual payload entropy ----------------
def lz_novel(strings, order, minM):
    corpus = ""; out = {}
    for b in order:
        s = strings[b]; mask = bytearray(len(s)); i = 0
        while i < len(s):
            lo, hi_, best = minM, len(s) - i, 0
            while lo <= hi_:
                mid = (lo + hi_) // 2
                if s[i:i+mid] in corpus: best, lo = mid, mid + 1
                else: hi_ = mid - 1
            if best >= minM: i += best
            else: mask[i] = 1; i += 1
        out[b] = mask; corpus += "#" + s
    return out

nov_sym_mask = lz_novel(dec, ids, 5)
nov_syms = sum(sum(m) for m in nov_sym_mask.values())
cnt_nov = Counter()
for b in ids:
    for i, ch in enumerate(dec[b]):
        if nov_sym_mask[b][i]: cnt_nov[ch] += 1
H1 = -sum((v/nov_syms) * log2(v/nov_syms) for v in cnt_nov.values())
print(f"\nRESIDUAL ATTACK SURFACE (the novel payload, whatever wins):")
print(f"  novel symbols = {nov_syms}; flat bound {nov_syms}*log2(14) = {nov_syms*log2(14):.0f} bits; "
      f"unigram entropy H1={H1:.3f} -> {nov_syms*H1:.0f} bits")
print(f"  module-code literal digits = {g['lit_digits']} -> flat {g['lit_content']:.0f} bits")
print(f"  at ~10 bits/English-word this caps any hidden message at ~{int(nov_syms*H1/10)}-{int(g['lit_content']/10)} words IF the novel material were a channel")

# ---------------- controls ----------------
print(f"\n== CONTROLS (same two-part coding; does the generative code win on genuinely linguistic data?) ==")
import json
en = json.load(open("./tmp/audit_20260609/hs_control_plaintexts.json"))["en"].upper()
SYMS13 = sorted(set("".join(dec.values())) - {"*"})
# 26 -> 13 merge: pair English freq-rank i with rank 25-i, assign pairs to symbols
ENFREQ = "ETAOINSHRDLCUMWFGYPBVKJXQZ"
merge = {}
for i in range(13):
    merge[ENFREQ[i]] = SYMS13[i]; merge[ENFREQ[25 - i]] = SYMS13[i]
lens = [len(dec[b]) for b in ids]
assert sum(lens) <= len(en), (sum(lens), len(en))
en_books = {}
pos = 0
for b, L in zip(ids, lens):
    en_books[b] = "".join(merge[c] for c in en[pos:pos+L]); pos += L

rng = random.Random(469)
def run_control(name, sym_books, det=False):
    dg = {}
    toks = {}
    argmax = {s: max(cands, key=lambda cn: cn[1])[0] for s, cands in sym2codes.items()}
    for b, s in sym_books.items():
        parts = []
        for ch in s:
            if det:
                parts.append(argmax[ch]); continue
            cands = sym2codes[ch]
            tot = sum(n for _, n in cands)
            r = rng.random() * tot; acc = 0
            for c, n in cands:
                acc += n
                if r <= acc: parts.append(c); break
        dg[b] = "".join(parts); toks[b] = parts
    nd = sum(len(v) for v in dg.values())
    raw = nd * log2(10)
    gc = two_part_module_code(dg, ids, 20, 10)
    lzc, _, _ = lz77_code(dg, ids, 10)
    tb = kt_tokens([toks[b] for b in ids], 100) + gamma_bits(71) + sum(gamma_bits(len(toks[b]) + 1) for b in ids)
    print(f"  [{name}] digits={nd} RAW={raw:.0f} | GENERATIVE module-code={gc['TOTAL']:.0f} (M={gc['M']}) "
          f"LZ77={lzc:.0f} | message-bearing token-KT={tb:.0f}")
    win = gc['TOTAL'] < tb and gc['TOTAL'] < raw
    print(f"      generative beats message-bearing? {'YES' if win else 'NO'} "
          f"(margin gen-vs-token {tb - gc['TOTAL']:+.0f} bits)")
    return gc, tb, raw

run_control("ENGLISH x 14-sym merge x same homophonic code, matched lengths", en_books)

# shuffled-symbol control: real symbols globally shuffled, resplit to real lengths
allsym = list("".join(dec[b] for b in ids))
rng.shuffle(allsym)
sh_books = {}
pos = 0
for b, L in zip(ids, lens):
    sh_books[b] = "".join(allsym[pos:pos+L]); pos += L
run_control("SHUFFLED real symbols x same code", sh_books)

# and the real corpus itself re-encoded through the sampler (sanity: modularity is in the
# symbol sequence, not an artifact of the actual digit choices)
real_re = {b: dec[b] for b in ids}
run_control("REAL symbol streams re-encoded via homophone sampler (sanity)", real_re)

print("\n-- deterministic-homophone variants (symbol-level repetition CAN surface as digit repetition) --")
run_control("ENGLISH merge, deterministic encoding", en_books, det=True)
run_control("SHUFFLED real symbols, deterministic encoding", sh_books, det=True)
run_control("REAL symbol streams, deterministic encoding (positive control)", real_re, det=True)

print("\nDONE c2")
