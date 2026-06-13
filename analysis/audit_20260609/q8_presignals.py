import sqlite3, json, math, collections
con = sqlite3.connect("file:./data/bonelord_operational.sqlite?mode=ro", uri=True)
con.row_factory = sqlite3.Row
cur = con.cursor()
rows = cur.execute("SELECT bookid, reconstructed_code_stream FROM row0_code_symbol_probe_books WHERE valid=1").fetchall()
print("books:", len(rows))
even = collections.Counter(); odd = collections.Counter()
for r in rows:
    codes = r["reconstructed_code_stream"].split()
    for i, c in enumerate(codes):
        (even if i % 2 == 0 else odd)[c] += 1
ne, no = sum(even.values()), sum(odd.values())
# chi2 between even and odd code distributions
allc = set(even) | set(odd)
chi2 = 0.0
for c in allc:
    a, b = even[c], odd[c]
    tot = a + b
    ea, eb = tot * ne / (ne + no), tot * no / (ne + no)
    if ea > 0: chi2 += (a - ea) ** 2 / ea
    if eb > 0: chi2 += (b - eb) ** 2 / eb
print(f"even codes n={ne} odd n={no} distinct={len(allc)} chi2(even vs odd)={chi2:.1f} df~{len(allc)-1}")
# digit length mod 3
lens = [len(r["reconstructed_code_stream"].split()) * 2 for r in rows]
raw = cur.execute("SELECT bookid, MAX(digits) d FROM sheet__books WHERE bookid IS NOT NULL GROUP BY bookid").fetchall()
mod3 = collections.Counter(len(r["d"]) % 3 for r in raw)
print("raw digitlen mod3 distribution:", dict(mod3))
