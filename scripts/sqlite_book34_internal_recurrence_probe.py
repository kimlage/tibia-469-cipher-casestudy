#!/usr/bin/env python3
import argparse, collections, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
BOOK='34'

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def ngrams(s,n):
    return [(s[i:i+n],i) for i in range(max(0,len(s)-n+1))]
def create(cur):
    cur.executescript('''
    create table if not exists book34_internal_recurrence_probe_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      candidate_count integer not null, payload_json text not null);
    create table if not exists book34_internal_recurrence_probe_items(
      run_id integer not null, n integer not null, ngram text not null, book34_pos integer not null,
      corpus_book_count integer not null, tagged_control_count integer not null,
      tagged_control_books_json text not null, residual_books_json text not null,
      candidate_status text not null, recommendation text not null, evidence_json text not null,
      primary key(run_id,n,ngram,book34_pos));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    books=rows(cur,'select bookid,symbol_text from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens)')
    layer={x['bookid']:int(x['functional_tag_count']) for x in rows(cur,'select bookid,functional_tag_count from final_honest_reading_v15_books where run_id=(select max(run_id) from final_honest_reading_v15_books)')}
    by={b['bookid']:b['symbol_text'] for b in books}; s=by[BOOK]
    candidates=[]
    for n in (14,12,10,8,6):
        idx=collections.defaultdict(list)
        for bid,text in by.items():
            for g,pos in ngrams(text,n): idx[g].append((bid,pos))
        for g,pos in ngrams(s,n):
            hits=idx[g]; hit_books=sorted({h[0] for h in hits},key=lambda z:int(z))
            tagged=[b for b in hit_books if layer.get(b,0)>0]
            residual=[b for b in hit_books if layer.get(b,0)==0]
            if tagged and len(hit_books)<=8:
                status='BOOK34_WITH_TAGGED_CONTROLS'
                candidates.append((n,g,pos,len(hit_books),len(tagged),j(tagged),j(residual),status,'possible local context bridge; require control audit before promotion',j({'hit_books':hit_books})))
        if candidates: break
    cur.execute('insert into book34_internal_recurrence_probe_runs(created_at,decision,candidate_count,payload_json) values (?,?,?,?)',
        (now(),'BOOK34_INTERNAL_RECURRENCE_PROBE_CANDIDATES_ONLY_NO_PROMOTION',len(candidates),j({'bookid':BOOK})))
    run_id=cur.lastrowid
    for x in candidates[:50]:
        cur.execute('insert into book34_internal_recurrence_probe_items(run_id,n,ngram,book34_pos,corpus_book_count,tagged_control_count,tagged_control_books_json,residual_books_json,candidate_status,recommendation,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?)',(run_id,)+x)
    con.commit()
    top=[{'n':x[0],'ngram':x[1],'pos':x[2],'controls':json.loads(x[5]),'residual':json.loads(x[6])} for x in candidates[:10]]
    out={'run_id':run_id,'decision':'BOOK34_INTERNAL_RECURRENCE_PROBE_CANDIDATES_ONLY_NO_PROMOTION','candidate_count':len(candidates),'top':top}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        lines=[f"[469][book34-recurrence][run={run_id}] recorrências internas Book34",f"candidatos={len(candidates)} | promoção=0",'busca por n-grams menores com controles já etiquetados.']
        for t in top[:6]: lines.append(f"- n={t['n']} pos={t['pos']} token={t['ngram']} controls={t['controls']} residual={t['residual']}")
        send('\n'.join(lines))
if __name__=='__main__': main()
