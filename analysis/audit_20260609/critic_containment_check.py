import sqlite3
uri="file:./data/bonelord_operational.sqlite?mode=ro&immutable=1"
con=sqlite3.connect(uri, uri=True)
rows=con.execute("SELECT bookid, MAX(digits) FROM sheet__books GROUP BY bookid").fetchall()
print("rows:",len(rows))
books={b:d for b,d in rows}
contained=set(); pairs=[]
for a,da in books.items():
    for b,db in books.items():
        if a==b: continue
        if da in db:
            pairs.append((a,b)); contained.add(a)
print("containment pairs (a substring of b):",len(pairs))
print("distinct contained books:",len(contained))
# proper substring only (exclude equal-length identical, shouldn't exist)
eq=[(a,b) for a,b in pairs if len(books[a])==len(books[b])]
print("equal-length pairs:",len(eq))
