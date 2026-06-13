#!/usr/bin/env python3
"""Control: free-ML decode 100 shuffles of the Kharos string, measure symbol
5-gram coverage vs books; compare with Kharos final decode coverage 0.463 (31/67)."""
import sqlite3, math, random
random.seed(469)
DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True); cur = con.cursor()
books = [r[1].strip() for r in cur.execute("SELECT bookid, MIN(decodedbase) FROM sheet__books GROUP BY bookid")]
crow = cur.execute("SELECT code, symbol, occurrence_count, omitted_count, written_count FROM row0_code_symbol_counts WHERE run_id=1").fetchall()
code_sym = {c:s for c,s,*_ in crow}
occ={c:o for c,s,o,om,w in crow}; omc={c:om for c,s,o,om,w in crow}; wrc={c:w for c,s,o,om,w in crow}
TOT=sum(occ.values()); AL=0.5; inv=set(code_sym)
def lp_w(c): return math.log((occ.get(c,0)+AL)/(TOT+100*AL))+math.log((wrc.get(c,0)+AL)/(occ.get(c,0)+2*AL))
def lp_o(c): return math.log((occ.get(c,0)+AL)/(TOT+100*AL))+math.log((omc.get(c,0)+AL)/(occ.get(c,0)+2*AL))
def vit(s):
    L=len(s); best=[None]*(L+1); best[L]=(0.0,None,None)
    for i in range(L-1,-1,-1):
        cands=[]
        c1="0"+s[i]
        if best[i+1] is not None: cands.append((best[i+1][0]+lp_o(c1),(c1,True),i+1))
        if i+1<L and s[i:i+2] in inv and best[i+2] is not None:
            cands.append((best[i+2][0]+lp_w(s[i:i+2]),(s[i:i+2],False),i+2))
        best[i]=max(cands) if cands else None
    toks=[];i=0
    while i<L:
        _,tok,nxt=best[i]; toks.append(tok); i=nxt
    return "".join(code_sym[c] for c,_ in toks)
n=5
grams=set()
for bs in books:
    for i in range(len(bs)-n+1): grams.add(bs[i:i+n])
KH = cur.execute("SELECT sequence_digits FROM s2ward_corpus_audit_items WHERE source_set='sorted_unique_with_kharos' AND source_index=22").fetchone()[0].strip()
def cov(dec):
    tot=len(dec)-n+1
    return sum(1 for i in range(tot) if dec[i:i+n] in grams)/tot
kh_free = cov(vit(KH))
print(f"kharos FREE-ML decode sym5 cov: {kh_free:.4f}")
chars=list(KH); vals=[]
for t in range(100):
    random.shuffle(chars); vals.append(cov(vit("".join(chars))))
mu=sum(vals)/100; sd=(sum((v-mu)**2 for v in vals)/99)**0.5
kh_final = 31/67
print(f"ctrl sym5 cov: mu={mu:.4f} sd={sd:.4f}")
print(f"z(final 0.4627)={ (kh_final-mu)/sd :+.2f}  P(ctrl>=final)={sum(1 for v in vals if v>=kh_final)}/100")
print(f"z(free  {kh_free:.4f})={ (kh_free-mu)/sd :+.2f}  P(ctrl>=free)={sum(1 for v in vals if v>=kh_free)}/100")
con.close()
