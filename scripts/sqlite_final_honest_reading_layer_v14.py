#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def one(cur,sql,p=()):
    r=cur.execute(sql,p).fetchone(); return dict(r) if r else {}
def create(cur):
    cur.executescript('''
    create table if not exists final_honest_reading_v14_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_v13_run_id integer not null, source_near_variant_gate_run_id integer not null,
      book_count integer not null, audit_covered_book_count integer not null, functional_tagged_book_count integer not null,
      newly_tagged_book_count integer not null, semantic_gloss_allowed_count integer not null,
      operational_coverage_pct real not null, functional_tagged_book_pct real not null, semantic_gloss_pct real not null,
      payload_json text not null);
    create table if not exists final_honest_reading_v14_books(
      run_id integer not null, bookid text not null, reading_status text not null, audit_covered integer not null,
      gloss_allowed integer not null, functional_tag_count integer not null, added_v14_tag_count integer not null,
      functional_tags_json text not null, honest_text text not null, evidence_json text not null,
      primary key(run_id, bookid));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def add(tags, tag_id, label, source, confidence):
    if not any(t.get('tag_id')==tag_id and t.get('source')==source for t in tags):
        tags.append({'tag_id':tag_id,'label':label,'source':source,'confidence':confidence,'gloss_allowed':False})
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    v13=one(cur,'select max(run_id) as run_id from final_honest_reading_v13_books')['run_id']
    gate=one(cur,'select max(run_id) as run_id from chayenne_near_variant_gate_items')['run_id']
    books=rows(cur,'select * from final_honest_reading_v13_books where run_id=? order by cast(bookid as integer)',(v13,))
    gitems={x['bookid']:x for x in rows(cur,"select * from chayenne_near_variant_gate_items where run_id=? and decision='CHAYENNE_NEAR_VARIANT_NO_GLOSS'",(gate,))}
    out=[]
    for b in books:
        bookid=str(b['bookid']); tags=json.loads(b['functional_tags_json'] or '[]'); before=len(tags); additions=[]
        if bookid in gitems:
            x=gitems[bookid]
            add(tags,'CHAYENNE_NEAR_VARIANT',x['functional_label'],'chayenne_near_variant_gate_items',float(x['confidence']))
            additions.append({'gate':'CHAYENNE_NEAR_VARIANT','window':x['best_window'],'label':x['functional_label']})
        added=len(tags)-before; status='FUNCTIONALLY_TAGGED_NO_GLOSS' if tags else b['reading_status']; prefix=''
        if added: prefix='<V14_EXTERNAL_VARIANT:'+'; '.join(a['label'] for a in additions)+'> '
        ev=json.loads(b['evidence_json'] or '{}'); ev['v14_added_tags']=additions
        out.append((bookid,status,int(b['audit_covered']),0,len(tags),added,j(tags),prefix+b['honest_text'],j(ev)))
    n=len(out); audit=sum(x[2] for x in out); tagged=sum(1 for x in out if x[4]>0); newly=sum(1 for x in out if x[5]>0); op=round(100*audit/n,3); fp=round(100*tagged/n,3)
    cur.execute('insert into final_honest_reading_v14_runs(created_at,decision,source_v13_run_id,source_near_variant_gate_run_id,book_count,audit_covered_book_count,functional_tagged_book_count,newly_tagged_book_count,semantic_gloss_allowed_count,operational_coverage_pct,functional_tagged_book_pct,semantic_gloss_pct,payload_json) values (?,?,?,?,?,?,?,?,?,?,?,?,?)',
        (now(),'FINAL_HONEST_READING_V14_CHAYENNE_NEAR_VARIANT_NO_SEMANTIC_TRANSLATION',v13,gate,n,audit,tagged,newly,0,op,fp,0.0,j({'note':'v14 adds Book41 Chayenne near-shape variant; no plaintext gloss'})))
    run_id=cur.lastrowid
    for x in out:
        cur.execute('insert into final_honest_reading_v14_books(run_id,bookid,reading_status,audit_covered,gloss_allowed,functional_tag_count,added_v14_tag_count,functional_tags_json,honest_text,evidence_json) values (?,?,?,?,?,?,?,?,?,?)',(run_id,)+x)
    con.commit(); res={'run_id':run_id,'decision':'FINAL_HONEST_READING_V14_CHAYENNE_NEAR_VARIANT_NO_SEMANTIC_TRANSLATION','book_count':n,'functional_tagged_book_count':tagged,'newly_tagged_book_count':newly,'functional_tagged_book_pct':fp,'semantic_gloss_pct':0.0}; print(json.dumps(res,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][honest-reading-v14][run={run_id}] Book41 variante Chayenne incorporada",f"livros={n} | função auditável={tagged}/{n} ({fp}%) | novos na v14={newly} | gloss lexical=0%",'Book41 agora tem tag funcional externa-próxima, ainda sem tradução semântica.']))
if __name__=='__main__': main()
