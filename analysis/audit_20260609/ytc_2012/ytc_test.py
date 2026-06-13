#!/usr/bin/env python3
"""'Your True Colour' (2012) digit string — mechanical parse test with honest nulls.

String (primary source, verified): tibia.com news id=1975, "Your True Colour"
personality quiz, question 10:  78567 34334 989 135 65142
Wayback snapshot 2012-02-24: web.archive.org/web/20120224031702/
  http://www.tibia.com:80/news/?subtopic=latestnews&id=1975

Lessons from the REFUTED Kharos run baked in:
  (a) parseability + length identity are NON-discriminative (any digit string
      parses because every single digit is a legal omitted-zero token) — we show
      this with shuffle and uniform-random controls;
  (b) verbatim-copy coverage only proves copying, not cipher mechanics;
  (c) novelty must be checked against the corpus at ALL substring lengths,
      with chance-expectation stated per length.
Read-only DB. Row counts printed on every query.
"""
import sqlite3, math, random, json
from collections import Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
random.seed(469)

YTC = "78567" "34334" "989" "135" "65142"
GROUPS = ["78567", "34334", "989", "135", "65142"]
assert YTC == "".join(GROUPS)
L = len(YTC)
print(f"[ytc] string={' '.join(GROUPS)}  concat={YTC}  len={L}")

con = sqlite3.connect(DB, uri=True)
cur = con.cursor()

# ---------- books ----------
rows = cur.execute("""
    SELECT bookid, MIN(digits), MIN(decodedbase), MIN(insertedzeros), MIN(baselen)
    FROM sheet__books GROUP BY bookid
""").fetchall()
print(f"[books] deduped rows: {len(rows)}")
assert len(rows) == 70
books = {bid: dict(digits=d.strip(), base=b.strip(), iz=int(iz), bl=int(bl))
         for bid, d, b, iz, bl in rows}
tot_digits = sum(len(b["digits"]) for b in books.values())
print(f"[books] total corpus digits={tot_digits}")

# ---------- 99-code inventory ----------
code_rows = cur.execute("""
    SELECT code, symbol, occurrence_count, omitted_count, written_count
    FROM row0_code_symbol_counts WHERE run_id=1
""").fetchall()
print(f"[codes] inventory rows: {len(code_rows)}")
code_sym = {c: s for c, s, *_ in code_rows}
occ      = {c: o  for c, s, o, om, w in code_rows}
omitted  = {c: om for c, s, o, om, w in code_rows}
written  = {c: w  for c, s, o, om, w in code_rows}
inv = set(code_sym)
print(f"[codes] absent codes: {sorted(set(f'{i:02d}' for i in range(100)) - inv)}")

TOTOCC = sum(occ.values()); ALPHA = 0.5
def lp_written(c):
    o = occ.get(c, 0); w = written.get(c, 0)
    return math.log((o+ALPHA)/(TOTOCC+100*ALPHA)) + math.log((w+ALPHA)/(o+2*ALPHA))
def lp_omit(c):
    o = occ.get(c, 0); om = omitted.get(c, 0)
    return math.log((o+ALPHA)/(TOTOCC+100*ALPHA)) + math.log((om+ALPHA)/(o+2*ALPHA))

# ---------- DP machinery (identical to Kharos audit) ----------
def count_paths(s):
    n = len(s); dp = [0]*(n+1); dp[n] = 1
    for i in range(n-1, -1, -1):
        v = dp[i+1]
        if i+1 < n and s[i:i+2] in inv: v += dp[i+2]
        dp[i] = v
    return dp[0]

def viterbi(s, boundaries=None):
    """ML parse; if boundaries given (set of indices), tokens may not straddle them."""
    n = len(s); best = [None]*(n+1); best[n] = (0.0, None, None)
    for i in range(n-1, -1, -1):
        cands = []
        if best[i+1] is not None:
            cands.append((best[i+1][0] + lp_omit("0"+s[i]), ("0"+s[i], True), i+1))
        if (i+1 < n and s[i:i+2] in inv and best[i+2] is not None
                and not (boundaries and (i+1) in boundaries)):
            cands.append((best[i+2][0] + lp_written(s[i:i+2]), (s[i:i+2], False), i+2))
        best[i] = max(cands) if cands else None
    if best[0] is None: return None, []
    toks = []; i = 0
    while i < n:
        _, tok, nxt = best[i]; toks.append(tok); i = nxt
    return best[0][0], toks

def omission_flags(toks):
    f = Counter()
    for c, om in toks:
        if c not in inv: f["invalid_code"] += 1
        if om and omitted.get(c, 0) == 0: f["omit_never_omitted"] += 1
        if (not om) and c in inv and written.get(c, 0) == 0: f["write_never_written"] += 1
    return dict(f)

# ---------- novelty at ALL substring lengths ----------
digits_list = [b["digits"] for b in books.values()]
joined = "\x00".join(digits_list)

def longest_match_at(s, i):
    lo, hi = 0, len(s)-i
    while lo < hi:
        mid = (lo+hi+1)//2
        if s[i:i+mid] in joined: lo = mid
        else: hi = mid-1
    return lo

def hits_of(sub):
    out = []
    for bid, b in books.items():
        st = b["digits"].find(sub)
        while st != -1:
            out.append((bid, st)); st = b["digits"].find(sub, st+1)
    return out

print(f"\n[novelty] per-position longest substring of YTC found anywhere in 70 books:")
lm = [longest_match_at(YTC, i) for i in range(L)]
print("  pos: " + " ".join(f"{i:2d}" for i in range(L)))
print("  dig: " + "  ".join(YTC))
print("  lm : " + " ".join(f"{v:2d}" for v in lm))
lss = max(lm)
i_lss = lm.index(lss)
print(f"[novelty] longest shared substring: len={lss} '{YTC[i_lss:i_lss+lss]}' "
      f"hits={hits_of(YTC[i_lss:i_lss+lss])[:6]}")

# chance expectation per length n: corpus has ~tot_digits positions
print(f"\n[novelty] chance a given n-gram appears in a {tot_digits}-digit corpus "
      f"(1-(1-10^-n)^N), and YTC n-gram presence:")
for n in range(3, lss+3):
    if n > L: break
    grams = [YTC[i:i+n] for i in range(L-n+1)]
    present = sum(1 for g in grams if g in joined)
    p_chance = 1 - (1 - 10**-n) ** tot_digits
    print(f"  n={n:2d}: {present}/{len(grams)} YTC n-grams in corpus | "
          f"P(single n-gram by chance)={p_chance:.4f} -> expected ~{p_chance*len(grams):.1f}")

# ---------- greedy verbatim cover at several minlens, with controls ----------
def greedy_cover(s, minlen):
    segs = []; i = 0
    while i < len(s):
        n = longest_match_at(s, i)
        if n >= minlen:
            segs.append(("MATCH", i, n)); i += n
        else:
            if segs and segs[-1][0] == "GAP":
                segs[-1] = ("GAP", segs[-1][1], segs[-1][2]+1)
            else:
                segs.append(("GAP", i, 1))
            i += 1
    return segs

NC = 100
def ctrl_strings(kind):
    out = []
    chars = list(YTC)
    for _ in range(NC):
        if kind == "shuffle":
            random.shuffle(chars); out.append("".join(chars))
        else:
            out.append("".join(random.choice("0123456789") for _ in range(L)))
    return out

ctrl_shuf = ctrl_strings("shuffle")
ctrl_unif = ctrl_strings("uniform")

print(f"\n[cover] greedy verbatim-copy cover of YTC vs controls (n={NC} each):")
for minlen in (5, 6, 7, 8):
    segs = greedy_cover(YTC, minlen)
    cov = sum(ln for t, _, ln in segs if t == "MATCH") / L
    mus = []
    for ctrl in (ctrl_shuf, ctrl_unif):
        covs = [sum(ln for t, _, ln in greedy_cover(c, minlen) if t == "MATCH")/L for c in ctrl]
        mu = sum(covs)/NC; sd = (sum((v-mu)**2 for v in covs)/(NC-1))**0.5
        nge = sum(1 for v in covs if v >= cov)
        mus.append((mu, sd, nge))
    print(f"  minlen={minlen}: ytc_cov={cov:.3f} | shuffle mu={mus[0][0]:.3f} sd={mus[0][1]:.3f} "
          f"P>= {mus[0][2]}/{NC} | uniform mu={mus[1][0]:.3f} sd={mus[1][1]:.3f} P>= {mus[1][2]}/{NC}")
    if minlen == 8:
        for t, st, ln in segs:
            if t == "MATCH":
                print(f"    MATCH pos {st} len {ln} '{YTC[st:st+ln]}' hits {hits_of(YTC[st:st+ln])[:5]}")

# longest-shared-substring control
def lss_of(s):
    return max(longest_match_at(s, i) for i in range(len(s)))
for name, ctrl in (("shuffle", ctrl_shuf), ("uniform", ctrl_unif)):
    vals = [lss_of(c) for c in ctrl]
    mu = sum(vals)/NC; sd = (sum((v-mu)**2 for v in vals)/(NC-1))**0.5
    nge = sum(1 for v in vals if v >= lss)
    print(f"[cover] longest shared substr: ytc={lss} | {name} mu={mu:.2f} sd={sd:.2f} P>= {nge}/{NC}")

# ---------- parse tests (non-discriminative parseability shown explicitly) ----------
print(f"\n[parse] exact tokenization-path counts (note: ALWAYS >=1 for any digit string):")
paths = count_paths(YTC)
print(f"  ytc: paths={paths} (log10={math.log10(paths):.2f})")
for name, ctrl in (("shuffle", ctrl_shuf), ("uniform", ctrl_unif)):
    v = [math.log10(count_paths(c)) for c in ctrl]
    mu = sum(v)/NC; sd = (sum((x-mu)**2 for x in v)/(NC-1))**0.5
    nge = sum(1 for x in v if x >= math.log10(paths))
    print(f"  {name}: log10 paths mu={mu:.2f} sd={sd:.2f} | ytc z={(math.log10(paths)-mu)/sd:+.2f} P>= {nge}/{NC}")

def parse_report(s, label, boundaries=None):
    lpv, toks = viterbi(s, boundaries)
    dec = "".join(code_sym[c] for c, _ in toks)
    n_om = sum(1 for _, om in toks if om)
    fl = omission_flags(toks)
    ident = (len(s) + n_om == 2*len(toks))
    print(f"  [{label}] tokens={len(toks)} omitted={n_om} identity(len+omit==2*tok)={ident} "
          f"lp/token={lpv/len(toks):.3f} flags={fl}")
    print(f"  [{label}] tokens: {' '.join(c+('*' if om else '') for c, om in toks)}  (*=omitted zero)")
    print(f"  [{label}] decoded symbols: {dec}")
    return lpv/len(toks), dec

print(f"\n[parse] ML (Viterbi) parse of YTC under 99-code inventory + corpus omission rates:")
lp_free, dec_free = parse_report(YTC, "free")
bnd = set(); acc = 0
for g in GROUPS[:-1]:
    acc += len(g); bnd.add(acc)
print(f"[parse] group-boundary-respecting parse (tokens may not straddle the published spaces "
      f"{GROUPS}):")
lp_grp, dec_grp = parse_report(YTC, "grouped", boundaries=bnd)
print(f"[parse] per-group parseability as whole tokens:")
for g in GROUPS:
    p = count_paths(g)
    lpv, toks = viterbi(g)
    print(f"  group {g}: paths={p} ml_tokens={' '.join(c+('*' if om else '') for c, om in toks)} "
          f"decode={''.join(code_sym[c] for c, _ in toks)}")

# control: ML lp/token distribution
print(f"\n[parse] ML logprob/token vs controls:")
for name, ctrl in (("shuffle", ctrl_shuf), ("uniform", ctrl_unif)):
    v = []
    for c in ctrl:
        lpv, toks = viterbi(c)
        v.append(lpv/len(toks))
    mu = sum(v)/NC; sd = (sum((x-mu)**2 for x in v)/(NC-1))**0.5
    nge = sum(1 for x in v if x >= lp_free)
    print(f"  {name}: mu={mu:.3f} sd={sd:.3f} | ytc={lp_free:.3f} z={(lp_free-mu)/sd:+.2f} P>= {nge}/{NC}")

# omission-consistency flags on controls
print(f"[parse] omission-consistency flag rates on controls (free ML parse):")
for name, ctrl in (("shuffle", ctrl_shuf), ("uniform", ctrl_unif)):
    nf = sum(1 for c in ctrl if omission_flags(viterbi(c)[1]))
    print(f"  {name}: {nf}/{NC} controls have any flag (ytc flags: {omission_flags(viterbi(YTC)[1])})")

# ---------- where do the YTC tokens sit vs corpus frequency? ----------
print(f"\n[tokens] YTC free-parse token inventory check vs corpus row0 counts:")
for c, om in viterbi(YTC)[1]:
    print(f"  code {c} ({'omitted' if om else 'written'}) sym={code_sym.get(c,'?')} "
          f"corpus occ={occ.get(c,0)} written={written.get(c,0)} omitted={omitted.get(c,0)}")

con.close()
print("\nDONE")
