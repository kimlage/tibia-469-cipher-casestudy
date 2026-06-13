import sqlite3, json
DB="file:./data/bonelord_operational.sqlite?mode=ro"
con=sqlite3.connect(DB, uri=True); cur=con.cursor()
cur.execute("SELECT name FROM pragma_table_info('row0_code_symbol_probe_books')")
print("cols:",[r[0] for r in cur.fetchall()])
rows=cur.execute("SELECT * FROM row0_code_symbol_probe_books LIMIT 1").fetchall()
