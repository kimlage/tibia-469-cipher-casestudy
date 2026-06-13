#!/usr/bin/env python3
"""Part 5: DP parse count, shuffle controls, LOO benchmark, omitted-code list."""
import sqlite3, json, math, random
from collections import Counter

DB = "file:./data/bonelord_operational.sqlite?mode=ro"
con = sqlite3.connect(DB, uri=True); cur = con.cursor()
q = lambda s, *a: cur.execute(s, a).fetchall()
books = {bid: dict(digits=d, decodedbase=db_) for bid, d, db_ in
         q("SELECT bookid, MIN(digits), MIN(decodedbase) FROM sheet__books GROUP BY bookid")}
K = q("SELECT sequence_digits FROM s2ward_corpus_audit_items WHERE source_set='sorted_unique_with_kharos' AND source_index=22")[0][0]
occ = Counter(); om = Counter(); wr = Counter(); c2s = {}
for c, s, o, omc, wrc in q("SELECT code, symbol, occurrence_count, omitted_count, written_count FROM row0_code_symbol_counts WHERE run_id=1"):
    occ[c]+=o; om[c]+=omc; wr[c]+=wrc; c2s[c]=s

# ---------- exact DP count of reinsertion parses ----------
def count_parses(s, omit_set, written_set):
    n = len(s)
    dp = [0]*(n+1); dp[0] = 1
    for i in range(n):
        if not dp[i]: continue
        if ('0'+s[i]) in omit_set:
            dp[i+1] += dp[i]
        if i+2 <= n and s[i:i+2] in written_set:
            dp[i+2] += dp[i]
    return dp[n]
all_codes = set(c2s)
omitA = {c for c in all_codes if c[0]=='0'}                 # any 0d in inventory
omitB = {c for c in all_codes if om[c] > 0}                 # ever-omitted only
writA = all_codes
writB = {c for c in all_codes if wr[c] > 0}                 # ever-written only
for name, (o_, w_) in dict(
        anyA=(omitA, writA), strict=(omitB, writB), omitA_writB=(omitA, writB), omitB_writA=(omitB, writA)).items():
    cnt = count_parses(K, o_, w_)
    print(f"DP count [{name}]: 10^{math.log10(cnt):.2f}" if cnt else f"DP count [{name}]: 0", "(claim 10^28.49)")

# ---------- ML scoring ----------
N = sum(occ.values())
def lpw(c):
    return (math.log(occ[c]/N) + math.log((wr[c]+0.5)/(occ[c]+1.0))) if c in c2s else None
def lpo(c):
    return (math.log(occ[c]/N) + math.log((om[c]+0.5)/(occ[c]+1.0))) if c in c2s else None
def viterbi(s):
    n = len(s); NEG = float('-inf')
    dp = [NEG]*(n+1); bk = [None]*(n+1); dp[0] = 0.0
    for i in range(n):
        if dp[i]==NEG: continue
        c='0'+s[i]; lp=lpo(c)
        if lp is not None and dp[i]+lp>dp[i+1]: dp[i+1]=dp[i]+lp; bk[i+1]=(i,c,True)
        if i+2<=n:
            c=s[i:i+2]; lp=lpw(c)
            if lp is not None and dp[i]+lp>dp[i+2]: dp[i+2]=dp[i]+lp; bk[i+2]=(i,c,False)
    if dp[n]==NEG: return None, None
    toks=[]; i=n
    while i>0:
        pi,c,omf=bk[i]; toks.append((c,omf)); i=pi
    toks.reverse()
    return dp[n], toks

lp, toks = viterbi(K)
print(f"\nKharos ML: {len(toks)} toks, lp/tok={lp/len(toks):.4f}")
print("Kharos ML omitted codes:", sorted(c for c,o in toks if o))

allcat = [(bid, b['digits']) for bid, b in books.items()]
def metrics(s):
    grams = [s[i:i+10] for i in range(len(s)-9)]
    hitpos = set()
    gh = 0
    for i,g in enumerate(grams):
        if any(g in d for _,d in allcat): gh+=1; hitpos.update(range(i,i+10))
    # LSS via per-start extension
    best = 0
    for i in range(len(s)):
        if best < len(s)-i:
            L = best+1
            while i+L <= len(s) and any(s[i:i+L] in d for _,d in allcat):
                best = L; L += 1
    # greedy chunk cover >=8
    cov = 0; i = 0
    while i < len(s):
        gotL = 0
        for L in range(len(s)-i, 7, -1):
            if any(s[i:i+L] in d for _,d in allcat): gotL=L; break
        if gotL: cov += gotL; i += gotL
        else: i += 1
    return gh/len(grams), len(hitpos)/len(s), best, cov/len(s)

print("\nKharos metrics (gramcov, poscov, LSS, chunkcov):", metrics(K))

random.seed(469)
ctrl = dict(lpt=[], poscov=[], lss=[], chunk=[], dpcnt=[], parsed=0)
for t in range(100):
    s = list(K); random.shuffle(s); s = "".join(s)
    lp2, toks2 = viterbi(s)
    if lp2 is not None:
        ctrl['parsed'] += 1
        ctrl['lpt'].append(lp2/len(toks2))
    gc, pc, lss_, cc = metrics(s)
    ctrl['poscov'].append(pc); ctrl['lss'].append(lss_); ctrl['chunk'].append(cc)
    cnt = count_parses(s, omitA, writA)
    if cnt: ctrl['dpcnt'].append(math.log10(cnt))
import statistics as st
def ms(v): return (st.mean(v), st.pstdev(v))
print(f"\nCTRL (n=100, parsed={ctrl['parsed']}):")
print(f"  lp/tok mean,std = {ms(ctrl['lpt'])} (claim -4.685 +/- 0.093)")
print(f"  poscov mean,std = {ms(ctrl['poscov'])} (claim 0.0)")
print(f"  LSS mean,std = {ms(ctrl['lss'])} (claim 5.15 +/- 0.72)")
print(f"  chunkcov mean,std = {ms(ctrl['chunk'])} (claim 0.0006 +/- 0.0058)")
print(f"  log10 dpcount mean,std = {ms(ctrl['dpcnt'])} (claim 28.44 +/- 0.08)")

# ---------- LOO benchmark on real books ----------
poscovs = []; lsss = []
for bid, b in books.items():
    others = [(x, bb['digits']) for x, bb in books.items() if x != bid]
    s = b['digits']
    grams = [s[i:i+10] for i in range(len(s)-9)]
    hitpos = set()
    for i,g in enumerate(grams):
        if any(g in d for _,d in others): hitpos.update(range(i,i+10))
    poscovs.append(len(hitpos)/len(s))
    best = 0
    for i in range(len(s)):
        L = best+1
        while i+L <= len(s) and any(s[i:i+L] in d for _,d in others):
            best = L; L += 1
    lsss.append(best)
print(f"\nLOO books: poscov mean={st.mean(poscovs):.4f} min={min(poscovs):.4f} (claim mean .966 min .461)")
print(f"LOO books: LSS mean={st.mean(lsss):.2f} min={min(lsss)} (claim mean 116.3 min 18)")
con.close()
print("PART5 DONE")
