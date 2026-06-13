import sqlite3, collections
con = sqlite3.connect("file:./data/bonelord_operational.sqlite?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()
rows = cur.execute("SELECT bookid, decodedbase FROM row0_code_symbol_probe_books WHERE valid=1").fetchall()
print("books:", len(rows))
books = {r["bookid"]: r["decodedbase"] for r in rows}
K = 10
gram_books = collections.defaultdict(set)
for b, s in books.items():
    for i in range(len(s) - K + 1):
        gram_books[s[i:i+K]].add(b)
shared = {g for g, bs in gram_books.items() if len(bs) >= 2}
cov_total = 0; sym_total = 0
for b, s in books.items():
    covered = [False] * len(s)
    for i in range(len(s) - K + 1):
        if s[i:i+K] in shared:
            for j in range(i, i+K): covered[j] = True
    cov_total += sum(covered); sym_total += len(s)
print(f"K={K}: symbols covered by cross-book repeated {K}-grams: {cov_total}/{sym_total} = {cov_total/sym_total:.3f}")
# also within-book tandem coverage excluded; control: shuffle each book, recompute
import random
random.seed(469)
sh = {b: "".join(random.sample(s, len(s))) for b, s in books.items()}
gram_books2 = collections.defaultdict(set)
for b, s in sh.items():
    for i in range(len(s) - K + 1):
        gram_books2[s[i:i+K]].add(b)
shared2 = {g for g, bs in gram_books2.items() if len(bs) >= 2}
cov2 = 0
for b, s in sh.items():
    covered = [False] * len(s)
    for i in range(len(s) - K + 1):
        if s[i:i+K] in shared2:
            for j in range(i, i+K): covered[j] = True
    cov2 += sum(covered)
print(f"shuffle control coverage: {cov2}/{sym_total} = {cov2/sym_total:.3f}")
