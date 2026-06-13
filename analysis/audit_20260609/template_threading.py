#!/usr/bin/env python3
"""Template threading: express Kharos as a concatenation of token-aligned book chunks
(runs of whole book tokens, preserving each book's own zero-omission rendering).
Min-segment DP + decode; 100 shuffle controls."""
import sqlite3, json, random, statistics as st

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True); cur = con.cursor()

rows = cur.execute("SELECT code, symbol FROM row0_code_symbol_counts").fetchall()
code2sym = dict(rows)

pb = cur.execute("SELECT bookid, reconstructed_code_stream, omitted_positions_json FROM row0_code_symbol_probe_books").fetchall()
bk = {b: d for b, d in cur.execute("SELECT bookid, MIN(digits) FROM sheet__books GROUP BY bookid")}

# books as token lists: (render, code, omitted)
book_tokens = {}
for bookid, stream, oj in pb:
    codes = stream.split(); op = {p-1 for p in json.loads(oj)}
    toks = []
    for i, c in enumerate(codes):
        om = i in op
        toks.append((c[1] if om else c, c, om))
    assert "".join(t[0] for t in toks) == bk[bookid]
    book_tokens[bookid] = toks
print("books loaded:", len(book_tokens))

# index: rendered first-token string -> list of (bookid, token_idx)
from collections import defaultdict
tok_index = defaultdict(list)
for b, toks in book_tokens.items():
    for t, (r, c, om) in enumerate(toks):
        tok_index[r].append((b, t))
print("distinct token renders:", len(tok_index))

def chunk_lengths_from(s, i):
    """All token-aligned book chunk lengths (in digits) starting at s[i:], with best provenance.
    Returns dict digitlen -> (bookid, tok_idx, ntokens) keeping max ntokens per len."""
    out = {}
    cands = []
    if i+1 <= len(s): cands += tok_index.get(s[i], [])
    if i+2 <= len(s): cands += tok_index.get(s[i:i+2], [])
    for b, t0 in cands:
        toks = book_tokens[b]
        p = i; t = t0; ntok = 0
        while t < len(toks):
            r = toks[t][0]
            if s[p:p+len(r)] != r: break
            p += len(r); t += 1; ntok += 1
            dl = p - i
            if dl not in out or ntok > out[dl][2]:
                out[dl] = (b, t0, ntok)
        # note: every prefix in token steps is recorded
    return out

def min_segments(s):
    n = len(s)
    INF = 10**9
    dp = [INF]*(n+1); choice = [None]*(n+1); dp[0] = 0
    for i in range(n):
        if dp[i] == INF: continue
        for dl, (b, t0, ntok) in chunk_lengths_from(s, i).items():
            if dp[i]+1 < dp[i+dl]:
                dp[i+dl] = dp[i]+1; choice[i+dl] = (i, b, t0, ntok, dl)
    if dp[n] == INF: return None, None
    segs = []; i = n
    while i > 0:
        j, b, t0, ntok, dl = choice[i]; segs.append((j, b, t0, ntok, dl)); i = j
    return dp[n], segs[::-1]

KHAROS = cur.execute("SELECT sequence_digits FROM s2ward_corpus_audit_items WHERE source_set='sorted_unique_with_kharos' AND source_index=22").fetchone()[0]

print("\n=== KHAROS template threading ===")
k, segs = min_segments(KHAROS)
print("min token-aligned book chunks to build all 137 digits:", k)
if segs:
    decoded = []
    print("segments (kpos, book, tok_start, ntokens, digitlen):")
    for (j, b, t0, ntok, dl) in segs:
        toks = book_tokens[b][t0:t0+ntok]
        sym = "".join(code2sym[c] for _, c, _ in toks)
        decoded.append(sym)
        print(f"  kpos={j:3d} book={b:>2} tok[{t0}:{t0+ntok}] ntok={ntok:2d} digits={dl:2d} sym={sym}")
    dec = "".join(decoded)
    print("decoded baselen:", len(dec), "insertedzeros:", 2*len(dec)-len(KHAROS),
          "identity:", len(KHAROS) + (2*len(dec)-len(KHAROS)) == 2*len(dec))
    print("decoded:", dec)
    # symbol 10-gram coverage vs books
    book_base = ["".join(c2 for _, c2, _ in [(None, code2sym[c], None) for _, c, _ in toks2]) for toks2 in
                 ( [ (r,c,om) for (r,c,om) in book_tokens[b2] ] for b2 in book_tokens)]
    book_base = ["".join(code2sym[c] for _, c, _ in book_tokens[b2]) for b2 in book_tokens]
    g10 = set()
    for t in book_base:
        for a in range(len(t)-9): g10.add(t[a:a+10])
    cov = [False]*len(dec)
    for a in range(len(dec)-9):
        if dec[a:a+10] in g10:
            for q in range(a, a+10): cov[q] = True
    print("symbol 10-gram coverage of threaded decode: %.4f" % (sum(cov)/len(dec)))

print("\n=== CONTROL: 100 shuffles ===")
random.seed(469)
res = []
for _ in range(100):
    sh = list(KHAROS); random.shuffle(sh); sh = "".join(sh)
    kc, _segs = min_segments(sh)
    res.append(kc)
nfail = sum(1 for r in res if r is None)
vals = [r for r in res if r is not None]
print("controls coverable:", len(vals), "/100 ; uncoverable:", nfail)
if vals:
    mu, sd = st.mean(vals), st.pstdev(vals)
    print(f"control min-chunks: mean={mu:.2f} sd={sd:.2f} min={min(vals)} max={max(vals)}")
    if k is not None and sd > 0:
        print(f"kharos={k} -> z = {(k-mu)/sd:.2f}; empirical p(control <= {k}) = {sum(1 for v in vals if v <= k)}/{len(vals)}")
