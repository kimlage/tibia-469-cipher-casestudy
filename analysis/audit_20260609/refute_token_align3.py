import sqlite3, json
DB="file:./data/bonelord_operational.sqlite?mode=ro"
con=sqlite3.connect(DB, uri=True); cur=con.cursor()
row=cur.execute("SELECT digits FROM sheet__books WHERE bookid='13' GROUP BY bookid").fetchone()
digits=row[0]
r=cur.execute("SELECT reconstructed_code_stream, omitted_positions_json, consumed_digits, insertedzeros, baselen, digitslen FROM row0_code_symbol_probe_books WHERE bookid='13' AND run_id=1").fetchone()
stream, omj, consumed, ins, baselen, dl = r
om=json.loads(omj)
print("digitslen",dl,"len(digits)",len(digits),"baselen",baselen,"stream/2",len(stream)//2,"insertedzeros",ins,"consumed",consumed)
print("omitted_positions sample:",om[:10], "count:",len(om))
print("digits[:40]:",digits[:40])
print("stream[:80]:",stream[:80])
