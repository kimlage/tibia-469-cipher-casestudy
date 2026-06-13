#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
DEFAULT_APPROVED=''

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists residual_template_context_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_probe_run_id integer not null, approved_pair_count integer not null,
      accepted_residual_book_count integer not null, lexical_gloss_allowed integer not null,
      payload_json text not null);
    create table if not exists residual_template_context_gate_items(
      run_id integer not null, residual_bookid text not null, matched_bookid text not null,
      candidate_status text not null, decision text not null, confidence real not null,
      functional_label text not null, lexical_gloss_allowed integer not null,
      reason text not null, next_action text not null, evidence_json text not null,
      primary key(run_id,residual_bookid,matched_bookid));''')
def parse_pairs(raw):
    out=[]
    for part in raw.split(','):
        part=part.strip()
        if not part: continue
        a,b=part.split(':',1); out.append((a,b))
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--approved-pairs',default=DEFAULT_APPROVED,help='comma list residual:matched'); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    approved=parse_pairs(args.approved_pairs)
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    probe_run=cur.execute('select max(run_id) from residual_book_similarity_probe_items').fetchone()[0]
    pmap={}
    for x in rows(cur,'select * from residual_book_similarity_probe_items order by run_id'):
        pmap[(x['residual_bookid'],x['matched_bookid'])]=x
    items=[]
    for key in approved:
        if key in pmap: items.append(pmap[key])
    books=sorted({x['residual_bookid'] for x in items}, key=lambda z:int(z) if z.isdigit() else z)
    cur.execute('insert into residual_template_context_gate_runs(created_at,decision,source_probe_run_id,approved_pair_count,accepted_residual_book_count,lexical_gloss_allowed,payload_json) values (?,?,?,?,?,?,?)',
        (now(),'RESIDUAL_TEMPLATE_CONTEXT_GATE_READY_NO_GLOSS',probe_run,len(items),len(books),0,j({'approved_pairs':approved,'accepted_books':books})))
    run_id=cur.lastrowid
    for x in items:
        conf=0.72 if float(x['lcs_ratio_shorter'])>=0.95 else 0.64 if float(x['lcs_ratio_shorter'])>=0.9 else 0.55
        label=f"residual local template aligned to Book {x['matched_bookid']}"
        cur.execute('insert into residual_template_context_gate_items(run_id,residual_bookid,matched_bookid,candidate_status,decision,confidence,functional_label,lexical_gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?)',
            (run_id,x['residual_bookid'],x['matched_bookid'],x['candidate_status'],'RESIDUAL_LOCAL_TEMPLATE_NO_GLOSS',conf,label,0,'approved by residual similarity audit with negative controls outside this gate','materialize local residual template tag only; no lexical gloss',j(x)))
    con.commit()
    out={'run_id':run_id,'decision':'RESIDUAL_TEMPLATE_CONTEXT_GATE_READY_NO_GLOSS','accepted_books':books,'approved_pair_count':len(items),'lexical_gloss_allowed':0}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][residual-template][run={run_id}] templates residuais materializados",f"livros aceitos={','.join(books) if books else 'nenhum'} | pares={len(items)} | gloss lexical=0",'gate genérica só aceita pares explicitamente aprovados por auditoria; não promove por similaridade bruta.']))
if __name__=='__main__': main()
