import sqlite3
con = sqlite3.connect("file:./data/bonelord_operational.sqlite?mode=ro", uri=True)
cur = con.cursor()
rows = cur.execute("SELECT hypothesis_id, status, hypothesis, next_action FROM cipher_mode_hypotheses").fetchall()
print("cipher_mode_hypotheses rows:", len(rows))
for r in rows:
    print("==", r[0], "|", r[1])
    print("   HYP:", r[2][:300])
    print("   NEXT:", r[3][:200])
