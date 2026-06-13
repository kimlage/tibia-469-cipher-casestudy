import sqlite3, json
DB="file:./data/bonelord_operational.sqlite?mode=ro"
con=sqlite3.connect(DB, uri=True); cur=con.cursor()
digits=cur.execute("SELECT digits FROM sheet__books WHERE bookid='2' GROUP BY bookid").fetchone()[0]
rows=cur.execute("SELECT run_id, reconstructed_code_stream, omitted_positions_json, insertedzeros, baselen, digitslen, valid FROM row0_code_symbol_probe_books WHERE bookid='2'").fetchall()
print("rows for book2:", len(rows))
for r in rows:
    run_id, stream, omj, ins, baselen, dl, valid = r
    codes=stream.split(); om=set(json.loads(omj))
    rebuilt=''.join((c[1] if ti in om else c) for ti,c in enumerate(codes))
    print(f"run {run_id}: tokens={len(codes)} baselen={baselen} ins={ins} dl={dl} valid={valid} exact={rebuilt==digits}")
    if rebuilt!=digits:
        for i,(a,b) in enumerate(zip(rebuilt,digits)):
            if a!=b:
                print("  first mismatch at",i, rebuilt[max(0,i-6):i+6],"vs",digits[max(0,i-6):i+6]); break
        print("  len rebuilt",len(rebuilt),"len digits",len(digits))
        print("  om:",sorted(om))
