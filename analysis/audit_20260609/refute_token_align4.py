import sqlite3, json
DB="file:./data/bonelord_operational.sqlite?mode=ro"
con=sqlite3.connect(DB, uri=True); cur=con.cursor()
K="51595646114145190584521765219727830464879636612527578967212778894388727857261185764217614588952196180031651288899751121615127215196805970"
def tokmap(bid):
    digits=cur.execute("SELECT digits FROM sheet__books WHERE bookid=? GROUP BY bookid",(bid,)).fetchone()[0]
    stream, omj = cur.execute("SELECT reconstructed_code_stream, omitted_positions_json FROM row0_code_symbol_probe_books WHERE bookid=? AND run_id=1",(bid,)).fetchone()
    codes=stream.split()
    om=set(json.loads(omj))
    pos=0; spans=[]
    for ti,c in enumerate(codes):
        ln=1 if ti in om else 2
        spans.append((pos,ln,c,ti in om)); pos+=ln
    rebuilt=''.join((c[1] if o else c) for (_,_,c,o) in spans)
    print(f"book {bid}: tokens={len(codes)} byte_exact={rebuilt==digits} len={pos}/{len(digits)}")
    return set(s for s,_,_,_ in spans), set(s+l for s,l,_,_ in spans)
s13,e13=tokmap('13'); s2,e2=tokmap('2')
chunks=[(0,16,'13',120),(16,24,'13',95),(40,12,'2',108),(52,18,'2',43),(70,15,'2',84),(90,14,'2',65),(109,14,'2',161)]
aligned=0
for (kst,L,bid,bp) in chunks:
    st,en=(s13,e13) if bid=='13' else (s2,e2)
    a = bp in st and bp+L in en
    aligned+=a
    print(f"chunk k@{kst} len{L} book{bid}@{bp}: start={bp in st} end={bp+L in en}")
print("token-aligned chunks:", aligned, "/7")
