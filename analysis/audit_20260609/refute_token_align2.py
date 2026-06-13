import sqlite3, json
DB="file:./data/bonelord_operational.sqlite?mode=ro"
con=sqlite3.connect(DB, uri=True); cur=con.cursor()
# rebuild digit-position -> token map for books 2 and 13 (run_id=1)
def tokmap(bid):
    r=cur.execute("SELECT digits FROM sheet__books WHERE bookid=? GROUP BY bookid",(bid,)).fetchone()
    digits=r[0]
    row=cur.execute("SELECT reconstructed_code_stream, omitted_positions_json, valid FROM row0_code_symbol_probe_books WHERE bookid=? AND run_id=1",(bid,)).fetchone()
    stream, omj, valid = row
    om=set(json.loads(omj))
    codes=[stream[i:i+2] for i in range(0,len(stream),2)]
    # walk: each token consumes 2 digits unless its leading zero position was omitted
    # omitted_positions are positions in the reconstructed (full) stream of inserted zeros, presumably
    pos=0; spans=[]  # (digit_start, digit_len, token_index, code)
    full_i=0
    for ti,c in enumerate(codes):
        # token occupies full-stream positions full_i, full_i+1
        omitted = (full_i in om)
        ln = 1 if omitted else 2
        spans.append((pos, ln, ti, c, omitted))
        pos+=ln; full_i+=2
    ok = (pos==len(digits))
    # verify written digits match
    rebuilt=''.join((c[1] if o else c) for (_,_,_,c,o) in spans)
    print(f"book {bid}: tokens={len(codes)} digitlen={len(digits)} consumed={pos} match_digits={rebuilt==digits} valid={valid}")
    starts=set(s for (s,_,_,_,_) in spans)
    ends=set(s+l for (s,l,_,_,_) in spans)
    return starts, ends, digits

s13,e13,d13=tokmap('13')
s2,e2,d2=tokmap('2')
chunks=[(0,16,'13',120),(16,24,'13',95),(40,12,'2',108),(52,18,'2',43),(70,15,'2',84),(90,14,'2',65),(109,14,'2',161)]
for (kst,L,bid,bp) in chunks:
    st_set,en_set = (s13,e13) if bid=='13' else (s2,e2)
    d = d13 if bid=='13' else d2
    assert d[bp:bp+L]== "51595646114145190584521765219727830464879636612527578967212778894388727857261185764217614588952196180031651288899751121615127215196805970"[kst:kst+L], (kst,bid)
    print(f"chunk k@{kst} len{L} book{bid}@{bp}: start_aligned={bp in st_set} end_aligned={bp+L in en_set}")
