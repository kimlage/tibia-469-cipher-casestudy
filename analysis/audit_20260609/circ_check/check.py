import sqlite3, json
from collections import Counter, defaultdict

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True); cur = con.cursor()

# E: provenance — does probe omitted_positions == sheet v118 omitidxs?
cur.execute("SELECT bookid, omitidxs_1based FROM sheet__booksdigitmodel_v118 GROUP BY bookid")
sheetidx = {b: tuple(int(x) for x in (s.split(',') if s else [])) for b, s in cur.fetchall()}
print("sheet v118 rows:", len(sheetidx))
cur.execute("SELECT bookid, omitted_positions_json FROM row0_code_symbol_probe_books WHERE run_id=1")
probeidx = {b: tuple(json.loads(j)) for b, j in cur.fetchall()}
print("probe rows:", len(probeidx))
same = sum(1 for b in sheetidx if sheetidx[b] == probeidx.get(b))
print("probe omitted_positions identical to sheet v118 omitidxs:", same, "/", len(sheetidx))
cur.execute("SELECT bookid, omitidxs_1based, pathcount FROM row0_omission_probe_book_items WHERE run_id=1")
omis = {b: (tuple(int(x) for x in (s.split(',') if s else [])), pc) for b, s, pc in cur.fetchall()}
same2 = sum(1 for b in sheetidx if sheetidx[b] == omis[b][0])
print("omission-probe omitidxs identical to sheet v118:", same2, "/", len(sheetidx))

# A: held-out label parse-dependence on the 20 multipath books
cur.execute("SELECT code, symbol FROM row0_code_symbol_counts WHERE run_id=1")
SYM = dict(cur.fetchall()); INV = set(SYM)
print("map codes:", len(SYM))
cur.execute("SELECT bookid, digits, decodedbase FROM sheet__books GROUP BY bookid")
books = {b: (d, base) for b, d, base in cur.fetchall()}
print("books:", len(books))

def enum_parses(digits, base):
    out=[]; n2,m=len(digits),len(base); stack=[(0,0,())]
    while stack:
        i,t,pat=stack.pop()
        if t==m:
            if i==n2: out.append(pat)
            continue
        if i+2<=n2:
            c=digits[i:i+2]
            if c in INV and SYM[c]==base[t]: stack.append((i+2,t+1,pat))
        if i+1<=n2:
            c='0'+digits[i]
            if c in INV and SYM[c]==base[t]: stack.append((i+1,t+1,pat+(t+1,)))
    return out

def occs_for_parse(digits, pat):
    pat=set(pat); res=[]; i=0; t=1
    while i<len(digits):
        if t in pat: c='0'+digits[i]; wlen=1
        else: c=digits[i:i+2]; wlen=2
        if c[0]=='0':
            prev=digits[i-1] if i>0 else 'S'
            nxt=digits[i+wlen] if i+wlen<len(digits) else 'E'
            res.append((t,c[1],prev,nxt,int(t in pat)))
        i+=wlen; t+=1
    return res

# build 50-book table
occ = json.load(open('./tmp/audit_20260609/occurrences.json'))
data=[o for o in occ if o['pc']==1]
labs=defaultdict(Counter)
for o in data: labs[(o['x'],o['prev'],o['nxt'])][o['omitted']]+=1
table={k:c.most_common(1)[0][0] for k,c in labs.items()}

tot=0; cov=0; corr_cov=0
forced_cov=0; forced_corr=0; amb_cov=0; amb_corr=0
amb_total=0
for b in sorted(set(o['book'] for o in occ if o['pc']>1), key=int):
    digits, base = books[b]
    parses = enum_parses(digits, base)
    chosen = probeidx[b]
    occ_chosen = occs_for_parse(digits, chosen)
    # an occurrence (by code index t) is "parse-dependent" if its (presence,label,context) differs across parses
    # represent each parse's occurrence set keyed by t
    per_parse = []
    for pat in parses:
        per_parse.append({r[0]: r[1:] for r in occs_for_parse(digits, pat)})
    for (t,x,prev,nxt,y) in occ_chosen:
        tot+=1
        # forced = identical (x,prev,nxt,label) tuple at this t in ALL parses
        vals = set()
        for pp in per_parse:
            vals.add(pp.get(t))
        forced = len(vals)==1
        if not forced: amb_total+=1
        k=(x,prev,nxt)
        if k in table:
            cov+=1; ok = table[k]==y; corr_cov+=ok
            if forced: forced_cov+=1; forced_corr+=ok
            else: amb_cov+=1; amb_corr+=ok
print("\nheld-out multipath books: total occ", tot, "covered", cov, "acc on covered", corr_cov, "/", cov)
print("parse-DEPENDENT occurrences (label/context differ across decodedbase-constrained parses):", amb_total, "of", tot)
print("  covered & forced:", forced_cov, "acc", forced_corr)
print("  covered & parse-dependent:", amb_cov, "acc", amb_corr)

# B: honest LOBO lookup table for (x,prev,nxt) on 50 books
glob=int(sum(o['omitted'] for o in data)*2>len(data))
books50=sorted(set(o['book'] for o in data))
correct=0; correct_seen=0; seen_n=0
for b in books50:
    tr=[o for o in data if o['book']!=b]; te=[o for o in data if o['book']==b]
    tab=defaultdict(Counter); ctab=defaultdict(Counter)
    for o in tr:
        tab[(o['x'],o['prev'],o['nxt'])][o['omitted']]+=1
        ctab[o['x']][o['omitted']]+=1
    for o in te:
        k=(o['x'],o['prev'],o['nxt'])
        if k in tab:
            pred=tab[k].most_common(1)[0][0]; seen_n+=1; correct_seen+=pred==o['omitted']
        elif o['x'] in ctab: pred=ctab[o['x']].most_common(1)[0][0]
        else: pred=glob
        correct+=pred==o['omitted']
print("\nLOBO (x,prev,nxt) lookup on 50 books: overall", correct, "/", len(data), "=", round(correct/len(data),4))
print("  on contexts SEEN in training:", correct_seen, "/", seen_n, "=", round(correct_seen/seen_n,4))
# out-of-sample capacity bound from LOBO error
import math
err=1-correct/len(data)
print("  LOBO error", round(err,4), "-> per-occ entropy bound H(err)=", round(-(err*math.log2(err)+(1-err)*math.log2(1-err)),3),
      "bits; x376 =", round(376*-(err*math.log2(err)+(1-err)*math.log2(1-err)),1), "bits; x634 =", round(634*-(err*math.log2(err)+(1-err)*math.log2(1-err)),1))
