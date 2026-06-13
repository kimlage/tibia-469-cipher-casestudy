#!/usr/bin/env python3
import argparse, collections, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
RESIDUAL={'4','34','49','56'}

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def ngrams(s,n):
    return [(s[i:i+n],i) for i in range(0,max(0,len(s)-n+1))]
def create(cur):
    cur.executescript('''
    create table if not exists hard_residual_ngram_probe_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      residual_book_count integer not null, candidate_count integer not null, payload_json text not null);
    create table if not exists hard_residual_ngram_probe_items(
      run_id integer not null, bookid text not null, n integer not null, ngram text not null,
      pos integer not null, corpus_book_count integer not null, residual_book_count integer not null,
      tagged_control_books_json text not null, candidate_status text not null,
      recommendation text not null, evidence_json text not null,
      primary key(run_id,bookid,n,ngram,pos));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    books=rows(cur,'select bookid,symbol_text from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens)')
    by_book={b['bookid']:b['symbol_text'] for b in books}
    layer={x['bookid']:int(x['functional_tag_count']) for x in rows(cur,'select bookid,functional_tag_count from final_honest_reading_v15_books where run_id=(select max(run_id) from final_honest_reading_v15_books)')}
    index={}
    for n in (8,10,12,14,16):
        hits=collections.defaultdict(list)
        for bid,s in by_book.items():
            for g,pos in ngrams(s,n):
                hits[g].append((bid,pos))
        index[n]=hits
    candidates=[]
    for bid in sorted(RESIDUAL,key=int):
        s=by_book[bid]
        seen=set()
        for n in (16,14,12,10,8):
            for g,pos in ngrams(s,n):
                if g in seen: continue
                seen.add(g)
                hits=index[n][g]
                books_hit=sorted({h[0] for h in hits}, key=lambda z:int(z))
                residual_hits=[b for b in books_hit if b in RESIDUAL]
                tagged=[b for b in books_hit if layer.get(b,0)>0]
                if len(books_hit)<=3 or (len(tagged)>=1 and len(residual_hits)>=1):
                    status='UNIQUE_RESIDUAL_COMPONENT' if len(books_hit)==1 else 'RESIDUAL_WITH_TAGGED_CONTROL' if tagged else 'LOW_FREQ_RESIDUAL_CLUSTER'
                    candidates.append((bid,n,g,pos,len(books_hit),len(residual_hits),j(tagged),status,'inspect only if not overlapping known blocked family; no gloss',j({'books_hit':books_hit})))
                    break
            if any(c[0]==bid and c[1]==n for c in candidates): break
    cur.execute('insert into hard_residual_ngram_probe_runs(created_at,decision,residual_book_count,candidate_count,payload_json) values (?,?,?,?,?)',
        (now(),'HARD_RESIDUAL_NGRAM_PROBE_CANDIDATES_ONLY_NO_PROMOTION',len(RESIDUAL),len(candidates),j({'residual_books':sorted(RESIDUAL,key=int)})))
    run_id=cur.lastrowid
    for x in candidates:
        cur.execute('insert into hard_residual_ngram_probe_items(run_id,bookid,n,ngram,pos,corpus_book_count,residual_book_count,tagged_control_books_json,candidate_status,recommendation,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?)',(run_id,)+x)
    con.commit()
    out={'run_id':run_id,'decision':'HARD_RESIDUAL_NGRAM_PROBE_CANDIDATES_ONLY_NO_PROMOTION','candidate_count':len(candidates),'candidates':[{'bookid':x[0],'n':x[1],'ngram':x[2],'status':x[7],'tagged_controls':json.loads(x[6])} for x in candidates]}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        lines=[f"[469][hard-residual-ngram][run={run_id}] n-grams raros nos 4 resíduos",f"resíduos={','.join(sorted(RESIDUAL,key=int))} | candidatos={len(candidates)}",'isto não promove; só procura componentes novos fora das famílias bloqueadas.']
        for c in out['candidates']: lines.append(f"- book {c['bookid']} n={c['n']} {c['status']} controls={c['tagged_controls']} token={c['ngram']}")
        send('\n'.join(lines))
if __name__=='__main__': main()
