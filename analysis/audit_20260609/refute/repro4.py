#!/usr/bin/env python3
"""Inventory-only DP (no decodedbase constraint): path counts + expected symbol divergence."""
import sqlite3, math, statistics
from collections import defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True); cur = con.cursor()
cur.execute("SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1")
SYM = dict(cur.fetchall()); INV = set(SYM)
cur.execute("SELECT bookid, digits, decodedbase FROM sheet__books GROUP BY bookid")
books = cur.fetchall()
print(f"books: {len(books)}")

logs, fdiffs = [], []
for bookid, digits, base in books:
    n, m = len(digits), len(base)
    maxins = 2*m - n
    F = [defaultdict(int) for _ in range(m+1)]; F[0][0] = 1
    for t in range(m):
        for i, v in F[t].items():
            if i+2 <= n and digits[i:i+2] in INV: F[t+1][i+2] += v
            if i+1 <= n and ('0'+digits[i]) in INV and 2*(t+1)-(i+1) <= maxins: F[t+1][i+1] += v
    B = [defaultdict(int) for _ in range(m+1)]; B[m][n] = 1
    for t in range(m-1, -1, -1):
        for i in F[t]:
            tot = 0
            if i+2 <= n and digits[i:i+2] in INV: tot += B[t+1][i+2]
            if i+1 <= n and ('0'+digits[i]) in INV and 2*(t+1)-(i+1) <= maxins: tot += B[t+1][i+1]
            if tot: B[t][i] = tot
    total = F[m][n]
    assert total >= 1, bookid
    exp_diff = 0.0
    for t in range(m):
        wrong = 0
        for i, v in F[t].items():
            if i+2 <= n:
                c = digits[i:i+2]
                if c in INV:
                    w = v*B[t+1][i+2]
                    if w and SYM[c] != base[t]: wrong += w
            if i+1 <= n:
                c = '0'+digits[i]
                if c in INV and 2*(t+1)-(i+1) <= maxins:
                    w = v*B[t+1][i+1]
                    if w and SYM[c] != base[t]: wrong += w
        exp_diff += wrong/total
    logs.append(math.log10(total)); fdiffs.append(exp_diff/m)

print(f"median log10(parses) = {statistics.median(logs):.2f}  max = {max(logs):.2f}  min = {min(logs):.2f}")
print(f"expected symbol divergence: median = {statistics.median(fdiffs)*100:.1f}%  min={min(fdiffs)*100:.1f}% max={max(fdiffs)*100:.1f}%")
