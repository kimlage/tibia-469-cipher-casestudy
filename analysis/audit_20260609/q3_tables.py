import sqlite3, re, collections
con = sqlite3.connect("file:./data/bonelord_operational.sqlite?mode=ro", uri=True)
cur = con.cursor()
names = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("total tables:", len(names))
# bucket by leading token(s)
buckets = collections.Counter()
for n in names:
    parts = n.split("_")
    buckets["_".join(parts[:2])] += 1
for k,v in buckets.most_common(120):
    print(f"{v:4d}  {k}")
