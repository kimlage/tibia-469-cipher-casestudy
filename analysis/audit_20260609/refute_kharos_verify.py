import sqlite3, json, random
DB="file:./data/bonelord_operational.sqlite?mode=ro"
con=sqlite3.connect(DB, uri=True)
cur=con.cursor()
K="51595646114145190584521765219727830464879636612527578967212778894388727857261185764217614588952196180031651288899751121615127215196805970"
assert len(K)==137
books={}
for bid,d in cur.execute("SELECT bookid, digits FROM sheet__books GROUP BY bookid"):
    books[bid]=d
print("books:",len(books),"total digits:",sum(len(v) for v in books.values()))

def longest_match_at(s,i,books):
    # longest substring of s starting at i found in any book; return (len, bookid, pos)
    best=(0,None,None)
    lo,hi=1,len(s)-i
    # simple scan
    for bid,d in books.items():
        # find longest prefix of s[i:] in d
        L=best[0]+1
        while i+L<=len(s):
            idx=d.find(s[i:i+L])
            if idx<0: break
            if L>best[0]: best=(L,bid,idx)
            L+=1
    return best

def greedy_chunks(s,books,minlen=8):
    i=0; chunks=[]; covered=0
    while i<len(s):
        L,bid,pos=longest_match_at(s,i,books)
        if L>=minlen:
            chunks.append((i,L,bid,pos)); covered+=L; i+=L
        else:
            i+=1
    return chunks,covered

chunks,cov=greedy_chunks(K,books)
print("KHAROS greedy chunks (start,len,book,bookpos):")
for c in chunks: print(" ",c)
print("covered:",cov,"/137 =",round(100*cov/137,1),"%")
# gaps
covset=set()
for st,L,b,p in chunks:
    covset.update(range(st,st+L))
gaps=[]
i=0
while i<137:
    if i not in covset:
        j=i
        while j<137 and j not in covset: j+=1
        gaps.append((i,K[i:j])); i=j
    else: i+=1
print("gaps:",gaps)
# novel check: do gap digits appear anywhere in books?
for st,g in gaps:
    occ=sum(d.count(g) for d in books.values())
    print(f" gap@{st} '{g}' len={len(g)} full-string corpus occurrences={occ}")

# LSS
best=0;arg=None
for bid,d in books.items():
    # longest common substring K vs d via DP-lite
    for i in range(137):
        L=best+1
        while i+L<=137 and d.find(K[i:i+L])>=0:
            if L>best: best=L; arg=(bid,i)
            L+=1
print("LSS:",best,arg)

# control: shuffles
random.seed(469)
ctrl_cov=[]; ctrl_lss=[]
for t in range(30):
    s=''.join(random.sample(K,len(K)))
    _,c=greedy_chunks(s,books)
    ctrl_cov.append(c)
    b=0
    for bid,d in books.items():
        for i in range(137):
            L=b+1
            while i+L<=137 and d.find(s[i:i+L])>=0:
                if L>b: b=L
                L+=1
    ctrl_lss.append(b)
import statistics as st_
print("ctrl coverage mean:",st_.mean(ctrl_cov),"max:",max(ctrl_cov))
print("ctrl LSS mean:",st_.mean(ctrl_lss),"max:",max(ctrl_lss))
