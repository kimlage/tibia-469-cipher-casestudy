#!/usr/bin/env python3
"""Phase-consistency test: do the verbatim book runs inside Kharos align with the
books' own token boundaries, and does a single global strict parse thread them all?"""
import sqlite3, json, math

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True); cur = con.cursor()

rows = cur.execute("SELECT code, symbol, occurrence_count, omitted_count, written_count FROM row0_code_symbol_counts").fetchall()
code2sym = {c: s for c, s, *_ in rows}
occ = {c: o for c, s, o, om, w in rows}; omi = {c: om for c, s, o, om, w in rows}; wri = {c: w for c, s, o, om, w in rows}
OMITTABLE = {c for c in code2sym if omi[c] > 0}; WRITABLE = {c for c in code2sym if wri[c] > 0}

# --- book tokenizations from probe table; verify reconstruction reproduces digits ---
pb = cur.execute("SELECT bookid, reconstructed_code_stream, omitted_positions_json, decodedbase FROM row0_code_symbol_probe_books").fetchall()
print("probe books:", len(pb))
bk = cur.execute("SELECT bookid, MIN(digits) FROM sheet__books GROUP BY bookid").fetchall()
digits_by_id = {b: d for b, d in bk}

book_tok = {}   # bookid -> list of (digit_pos, code, omitted?)
nver = 0
for bookid, stream, opos_j, base in pb:
    codes = stream.split()
    opos = set(json.loads(opos_j))
    s = []; toks = []; p = 0
    for idx, c in enumerate(codes):
        if idx in opos:
            s.append(c[1]); toks.append((p, c, True)); p += 1
        else:
            s.append(c); toks.append((p, c, False)); p += 2
    s = "".join(s)
    if s == digits_by_id[bookid]:
        nver += 1
    book_tok[bookid] = (s, toks)
print("books where probe tokenization reproduces digits exactly:", nver, "/", len(pb))

KHAROS = cur.execute("SELECT sequence_digits FROM s2ward_corpus_audit_items WHERE source_set='sorted_unique_with_kharos' AND source_index=22").fetchone()[0]
n = len(KHAROS)

# --- find all maximal shared runs >=10 between Kharos and each book ---
runs = []  # (k_start, b_id, b_start, length)
for bookid, (bs, toks) in book_tok.items():
    m = len(bs)
    # all common substrings >= 10, maximal
    for i in range(n):
        for j in range(m):
            if KHAROS[i] != bs[j]: continue
            if i > 0 and j > 0 and KHAROS[i-1] == bs[j-1]: continue  # not maximal start
            L = 0
            while i+L < n and j+L < m and KHAROS[i+L] == bs[j+L]: L += 1
            if L >= 10:
                runs.append((i, bookid, j, L))
runs.sort()
print("\nmaximal shared runs >=10:", len(runs))
for r in runs: print("  kpos=%3d book=%s bpos=%3d len=%d" % r)

# --- token-boundary constraints implied by each run alignment ---
# For run (i,b,j,L): book tokens fully inside [j, j+L) map to Kharos positions i+(tp-j).
def run_constraints(i, bookid, j, L):
    _, toks = book_tok[bookid]
    cons = []  # (k_pos, code, omitted?)
    for (tp, c, om) in toks:
        w = 1 if om else 2
        if tp >= j and tp + w <= j + L:
            cons.append((i + (tp - j), c, om))
    return cons

all_cons = []
for r in runs:
    cons = run_constraints(*r)
    all_cons.append((r, cons))

# --- check mutual compatibility where runs overlap on Kharos; build merged constraint map ---
merged = {}   # k_pos -> (code, omitted) ; conflict detection
conflicts = []
for r, cons in all_cons:
    for (kp, c, om) in cons:
        if kp in merged and merged[kp] != (c, om):
            conflicts.append((kp, merged[kp], (c, om), r))
        merged[kp] = (c, om)
# also boundary-parity conflicts: token spans must not overlap
spans = sorted((kp, kp + (1 if om else 2), c, om) for kp, (c, om) in merged.items())
overlap_conf = 0
for a in range(len(spans)-1):
    if spans[a][1] > spans[a+1][0]: overlap_conf += 1
print("\nexplicit code conflicts among run constraints:", len(conflicts))
print("token-span overlap conflicts:", overlap_conf)
covered_tok_digits = sum((1 if om else 2) for kp,(c,om) in merged.items())
print("Kharos digits covered by book-aligned whole tokens:", covered_tok_digits, "/", n)

# --- constrained global parse DP: must include exactly the merged tokens at their positions,
#     free strict tokens elsewhere ---
fixed_start = {kp: (c, om) for kp, (c, om) in merged.items()}
fixed_positions = set()
for kp, (c, om) in merged.items():
    for q in range(kp, kp + (1 if om else 2)): fixed_positions.add(q)

cnt = [0]*(n+1); cnt[0] = 1
best = [None]*(n+1); back = [None]*(n+1); best[0] = 0.0
TOT = sum(occ.values())
def lpw(c): return math.log(occ[c]/TOT) + math.log(wri[c]/occ[c]) if wri[c] else None
def lpo(c): return math.log(occ[c]/TOT) + math.log(omi[c]/occ[c]) if omi[c] else None

for i in range(n):
    if cnt[i] == 0 and best[i] is None: continue
    if i in fixed_start:
        c, om = fixed_start[i]
        w = 1 if om else 2
        lp = lpo(c) if om else lpw(c)
        if lp is None: lp = -50.0  # forced by book alignment even if rate 0
        cnt[i+w] += cnt[i]
        if best[i] is not None and (best[i+w] is None or best[i]+lp > best[i+w]):
            best[i+w] = best[i]+lp; back[i+w] = (i, c, om)
        continue
    # free position: any strict token, but must not start inside a fixed token region
    c1 = "0"+KHAROS[i]
    if c1 in OMITTABLE and (i not in fixed_positions):
        lp = lpo(c1)
        cnt[i+1] += cnt[i]
        if best[i] is not None and (best[i+1] is None or best[i]+lp > best[i+1]):
            best[i+1] = best[i]+lp; back[i+1] = (i, c1, True)
    if i+2 <= n:
        c2 = KHAROS[i:i+2]
        if c2 in WRITABLE and (i not in fixed_positions) and (i+1 not in fixed_positions):
            lp = lpw(c2)
            cnt[i+2] += cnt[i]
            if best[i] is not None and (best[i+2] is None or best[i]+lp > best[i+2]):
                best[i+2] = best[i]+lp; back[i+2] = (i, c2, False)

print("\nconstrained parses (book-phase-locked runs, strict elsewhere):", cnt[n])
if cnt[n]:
    toks = []; i = n
    while i > 0:
        j, c, om = back[i]; toks.append((c, om)); i = j
    toks = toks[::-1]
    z = sum(1 for _, om in toks if om)
    decoded = "".join(code2sym[c] for c, _ in toks)
    print("constrained ML parse: baselen=%d insertedzeros=%d identity %d+%d=2*%d %s" %
          (len(toks), z, n, z, len(toks), n+z == 2*len(toks)))
    print("omitted codes:", sorted({c for c, om in toks if om}))
    print("decoded:", decoded)
    # symbol 10-gram coverage vs books now
    base_by_id = {b: book_tok[b][1] for b in book_tok}
    book_base = [ "".join(code2sym[c] for _,c,_ in book_tok[b][1]) for b in book_tok ]
    g10 = set()
    for t in book_base:
        for a in range(len(t)-9): g10.add(t[a:a+10])
    cov = [False]*len(decoded)
    for a in range(len(decoded)-9):
        if decoded[a:a+10] in g10:
            for k in range(a, a+10): cov[k] = True
    print("symbol 10-gram coverage of constrained decode: %.4f" % (sum(cov)/len(decoded)))
else:
    print("NO globally valid parse threads all book-phase-locked runs.")
    # find where it breaks: forward reachability
    reach = [c > 0 for c in cnt]
    last = max(i for i, r in enumerate(reach) if r)
    print("forward parse reachable up to position", last, "of", n)
    print("context:", KHAROS[max(0,last-10):last+10])
    # which run constraints sit near the break
    for r, cons in all_cons:
        i, b, j, L = r
        if i <= last <= i+L: print("  run at break:", r)
