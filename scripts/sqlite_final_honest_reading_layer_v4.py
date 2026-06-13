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
    create table if not exists final_honest_reading_v4_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_v3_run_id integer not null, source_c86_gate_run_id integer not null, source_vnctiin_gate_run_id integer not null,
      book_count integer not null, audit_covered_book_count integer not null, functional_tagged_book_count integer not null,
      newly_tagged_book_count integer not null, semantic_gloss_allowed_count integer not null,
      operational_coverage_pct real not null, functional_tagged_book_pct real not null, semantic_gloss_pct real not null,
      payload_json text not null);
    create table if not exists final_honest_reading_v4_books(
      run_id integer not null, bookid text not null, reading_status text not null, audit_covered integer not null,
      gloss_allowed integer not null, functional_tag_count integer not null, added_v4_tag_count integer not null,
      functional_tags_json text not null, honest_text text not null, evidence_json text not null,
      primary key(run_id, bookid));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def add(tags, tag_id, label, source, confidence):
    if not any(t.get('tag_id')==tag_id and t.get('label')==label and t.get('source')==source for t in tags):
        tags.append({'tag_id':tag_id,'label':label,'source':source,'confidence':confidence,'gloss_allowed':False})
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    v3_run=one(cur,'select max(run_id) as run_id from final_honest_reading_v3_books')['run_id']
    c86_run=one(cur,'select max(run_id) as run_id from c86_payload_operator_gate_items')['run_id']
    vn_run=one(cur,'select max(run_id) as run_id from vnctiin_context_frame_gate_items')['run_id']
    books=rows(cur,'select * from final_honest_reading_v3_books where run_id=? order by cast(bookid as integer)',(v3_run,))
    c86=rows(cur,"select * from c86_payload_operator_gate_items where run_id=? and decision='PAYLOAD_BRANCH_FUNCTION_READY_NO_GLOSS'",(c86_run,))
    vn=rows(cur,"select * from vnctiin_context_frame_gate_items where run_id=? and decision='VNCTIIN_CONTEXT_FRAME_NO_GLOSS'",(vn_run,))
    c86_by_book={}
    for x in c86:
        for b in json.loads(x['books_json'] or '[]'):
            c86_by_book.setdefault(str(b),[]).append(x)
    vn_by_book={str(x['bookid']):x for x in vn}
    outbooks=[]
    for b in books:
        bookid=str(b['bookid']); tags=json.loads(b['functional_tags_json'] or '[]'); before=len(tags); additions=[]
        for x in c86_by_book.get(bookid,[]):
            label=x['functional_label']; add(tags,'C86_PAYLOAD_OPERATOR',label,'c86_payload_operator_gate_items',float(x['bridge_score'])); additions.append({'gate':'C86','branch_id':x['branch_id'],'label':label})
        if bookid in vn_by_book:
            x=vn_by_book[bookid]; add(tags,'VNCTIIN_CONTEXT_FRAME',x['functional_label'],'vnctiin_context_frame_gate_items',float(x['confidence'])); additions.append({'gate':'VNCTIIN','label':x['functional_label']})
        added=len(tags)-before
        status='FUNCTIONALLY_TAGGED_NO_GLOSS' if tags else b['reading_status']
        prefix=''
        if added:
            prefix='<V4_FUNCTIONAL:'+'; '.join(a['label'] for a in additions)+'> '
        ev=json.loads(b['evidence_json'] or '{}'); ev['v4_added_tags']=additions
        outbooks.append((bookid,status,int(b['audit_covered']),0,len(tags),added,j(tags),prefix+b['honest_text'],j(ev)))
    book_count=len(outbooks); audit=sum(x[2] for x in outbooks); tagged=sum(1 for x in outbooks if x[4]>0); newly=sum(1 for x in outbooks if x[5]>0)
    op=round(100*audit/book_count,3) if book_count else 0.0; fp=round(100*tagged/book_count,3) if book_count else 0.0
    cur.execute('insert into final_honest_reading_v4_runs(created_at,decision,source_v3_run_id,source_c86_gate_run_id,source_vnctiin_gate_run_id,book_count,audit_covered_book_count,functional_tagged_book_count,newly_tagged_book_count,semantic_gloss_allowed_count,operational_coverage_pct,functional_tagged_book_pct,semantic_gloss_pct,payload_json) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(now(),'FINAL_HONEST_READING_V4_C86_VNCTIIN_FUNCTIONAL_TAGS_NO_SEMANTIC_TRANSLATION',v3_run,c86_run,vn_run,book_count,audit,tagged,newly,0,op,fp,0.0,j({'note':'v4 adds C86 and VNCTIIN functional tags only'})))
    run_id=cur.lastrowid
    for x in outbooks:
        cur.execute('insert into final_honest_reading_v4_books(run_id,bookid,reading_status,audit_covered,gloss_allowed,functional_tag_count,added_v4_tag_count,functional_tags_json,honest_text,evidence_json) values (?,?,?,?,?,?,?,?,?,?)',(run_id,)+x)
    con.commit(); res={'run_id':run_id,'decision':'FINAL_HONEST_READING_V4_C86_VNCTIIN_FUNCTIONAL_TAGS_NO_SEMANTIC_TRANSLATION','book_count':book_count,'functional_tagged_book_count':tagged,'newly_tagged_book_count':newly,'functional_tagged_book_pct':fp,'semantic_gloss_pct':0.0}; print(json.dumps(res,ensure_ascii=False))
    if args.discord: send('\n'.join([f"[469][honest-reading-v4][run={run_id}] C86 + VNCTIIN incorporados",f"livros={book_count} | função auditável={tagged}/{book_count} ({fp}%) | novos na v4={newly} | gloss lexical=0%",'camada v4 só adiciona função: operador C86 e frame VNCTIIN. Não traduz livros para inglês sem anchor.']))
if __name__=='__main__': main()
