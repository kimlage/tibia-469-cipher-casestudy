import sqlite3, json
DB="file:./data/bonelord_operational.sqlite?mode=ro"
con=sqlite3.connect(DB, uri=True); cur=con.cursor()

def walk(bid):
    digits=cur.execute("SELECT digits FROM sheet__books WHERE bookid=? GROUP BY bookid",(bid,)).fetchone()[0]
    stream=cur.execute("SELECT reconstructed_code_stream FROM row0_code_symbol_probe_books WHERE bookid=? AND run_id=1",(bid,)).fetchone()[0]
    codes=stream.split()
    # backtracking parse: prefer 2-digit, allow 1-digit for 0x codes
    n=len(digits)
    import sys; sys.setrecursionlimit(10000)
    from functools import lru_cache
    sols=[]
    def rec(ti,pos,acc):
        if ti==len(codes):
            if pos==n: sols.append(list(acc))
            return len(sols)>0
        c=codes[ti]
        if digits.startswith(c,pos):
            acc.append((pos,2,c,False))
            if rec(ti+1,pos+2,acc): return True
            acc.pop()
        if c[0]=='0' and pos<n and digits[pos]==c[1]:
            acc.append((pos,1,c,True))
            if rec(ti+1,pos+1,acc): return True
            acc.pop()
        return False
    ok=rec(0,0,[])
    assert ok, bid
    spans=sols[0]
    starts=set(s for s,_,_,_ in spans); ends=set(s+l for s,l,_,_ in spans)
    om=[i for i,(_,l,_,o) in enumerate(spans) if o]
    print(f"book {bid}: parse OK, tokens={len(spans)}, omitted token idx={om}")
    return starts, ends

s13,e13=walk('13'); s2,e2=walk('2')
chunks=[(0,16,'13',120),(16,24,'13',95),(40,12,'2',108),(52,18,'2',43),(70,15,'2',84),(90,14,'2',65),(109,14,'2',161)]
aligned=0
for (kst,L,bid,bp) in chunks:
    st,en=(s13,e13) if bid=='13' else (s2,e2)
    a=(bp in st) and (bp+L in en); aligned+=a
    print(f"chunk k@{kst} len{L} book{bid}@{bp}: start={bp in st} end={bp+L in en} BOTH={a}")
print("fully token-aligned:",aligned,"/7")
