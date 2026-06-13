#!/usr/bin/env python3
"""Corrected independent disambiguation: derive code stream from digits+pattern."""
import sqlite3, json, sys
from collections import Counter, defaultdict
from functools import lru_cache

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True); cur = con.cursor()
cur.execute("SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1")
SYM = dict(cur.fetchall()); INV = set(SYM)
cur.execute("""SELECT bookid, digits, decodedbase FROM sheet__books GROUP BY bookid""")
books = {b: (d, base) for b, d, base in cur.fetchall()}
cur.execute("SELECT bookid, pathcount FROM row0_omission_probe_book_items WHERE run_id=1")
pc = dict(cur.fetchall())
cur.execute("SELECT bookid, omitted_positions_json, reconstructed_code_stream FROM row0_code_symbol_probe_books WHERE run_id=1")
probe = {r[0]: (set(json.loads(r[1])), r[2].split()) for r in cur.fetchall()}

def enum_parses(digits, base):
    n, m = len(digits), len(base)
    @lru_cache(maxsize=None)
    def cnt(i, t):
        if t == m: return 1 if i == n else 0
        s = 0
        if i+2 <= n:
            c = digits[i:i+2]
            if c in INV and SYM[c] == base[t]: s += cnt(i+2, t+1)
        if i < n:
            c = '0'+digits[i]
            if c in INV and SYM[c] == base[t]: s += cnt(i+1, t+1)
        return s
    pats = []
    def walk(i, t, pat):
        if t == m:
            if i == n: pats.append(tuple(pat))
            return
        if i+2 <= n:
            c = digits[i:i+2]
            if c in INV and SYM[c] == base[t] and cnt(i+2, t+1): walk(i+2, t+1, pat)
        if i < n:
            c = '0'+digits[i]
            if c in INV and SYM[c] == base[t] and cnt(i+1, t+1):
                pat.append(t+1); walk(i+1, t+1, pat); pat.pop()
    sys.setrecursionlimit(100000)
    walk(0, 0, [])
    return pats

def occs_from_parse(digits, pat):
    """Derive codes from digits + omission pattern (1-based code idx)."""
    pat = set(pat); res = []; i = 0; t = 1
    while i < len(digits):
        if t in pat:
            c = '0'+digits[i]; wlen = 1
        else:
            c = digits[i:i+2]; wlen = 2
        if c[0] == '0':
            prev = digits[i-1] if i > 0 else 'S'
            nxt = digits[i+wlen] if i+wlen < len(digits) else 'E'
            res.append((c, prev, nxt, int(t in pat)))
        i += wlen; t += 1
    return res

# table from 50 single-path books
tab = defaultdict(Counter)
for b, v in pc.items():
    if v != 1: continue
    digits = books[b][0]
    for c, p, nx, y in occs_from_parse(digits, sorted(probe[b][0])):
        tab[(c, p, nx)][y] += 1
rule = {k: c.most_common(1)[0][0] for k, c in tab.items()}
print(f"table signatures: {len(rule)}")

uniq = ties = 0; conf = []
for b in sorted(books):
    if pc[b] == 1: continue
    digits, base = books[b]
    pats = enum_parses(digits, base)
    scores = []
    for p in pats:
        sc = sum(1 for c, pr, nx, y in occs_from_parse(digits, p)
                 if (c, pr, nx) in rule and rule[(c, pr, nx)] == y)
        scores.append((sc, p))
    best = max(s[0] for s in scores)
    winners = [s for s in scores if s[0] == best]
    if len(winners) == 1:
        uniq += 1
        if set(winners[0][1]) != probe[b][0]:
            conf.append(b)
    else:
        ties += 1
print(f"unique={uniq} ties={ties} conflicts={conf}")
