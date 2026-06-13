#!/usr/bin/env python3
"""Is zero-omission predictable from context? Compare preceding-code last digit
for omitted vs written occurrences of 0X codes (using project's reconstruction)."""
import sqlite3, json, collections, math

URI = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(URI, uri=True)
rows = con.execute("SELECT bookid, omitted_positions_json, reconstructed_code_stream FROM row0_code_symbol_probe_books").fetchall()
print("ROWCOUNT", len(rows))

om_prev = collections.Counter(); wr_prev = collections.Counter()
om_next = collections.Counter(); wr_next = collections.Counter()
percode = collections.defaultdict(lambda: [0,0])
for bid, omj, stream in rows:
    codes = stream.split()
    om = {p-1 for p in json.loads(omj)}  # positions are 1-based code indices
    for i,c in enumerate(codes):
        if not c.startswith("0"): continue
        prev = codes[i-1][-1] if i>0 else "^"
        nxt = codes[i+1][0] if i+1<len(codes) else "$"
        if i in om:
            om_prev[prev]+=1; om_next[nxt]+=1
        else:
            wr_prev[prev]+=1; wr_next[nxt]+=1

print("omitted: n=%d ; written-0X: n=%d" % (sum(om_prev.values()), sum(wr_prev.values())))
print("prev-last-digit | omitted | written")
for d in "0123456789^":
    print("  %s : %4d  %4d" % (d, om_prev[d], wr_prev[d]))
# chi2 omitted vs written over prev digit
keys=[d for d in "0123456789" if om_prev[d]+wr_prev[d]>0]
No=sum(om_prev[d] for d in keys); Nw=sum(wr_prev[d] for d in keys)
chi=0
for d in keys:
    tot=om_prev[d]+wr_prev[d]
    eo=tot*No/(No+Nw); ew=tot*Nw/(No+Nw)
    if eo>0: chi+=(om_prev[d]-eo)**2/eo
    if ew>0: chi+=(wr_prev[d]-ew)**2/ew
print("prev-digit chi2 (omitted vs written) = %.1f df=%d" % (chi, len(keys)-1))

print("\nnext-first-digit | omitted | written")
for d in "0123456789$":
    print("  %s : %4d  %4d" % (d, om_next[d], wr_next[d]))
con.close()
