#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any
DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def create(cur):
    cur.executescript('''
    create table if not exists c86_payload_operator_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_bridge_run_id integer not null, branch_count integer not null, ready_branch_count integer not null,
      audit_branch_count integer not null, ready_book_count integer not null, edge_ref_count integer not null,
      gloss_allowed_count integer not null, lexical_promotion_allowed integer not null, payload_json text not null);
    create table if not exists c86_payload_operator_gate_items(
      run_id integer not null, branch_id text not null, payload_class text not null, books_json text not null,
      downstream_frame text not null, edge_supported_occurrence_count integer not null, edge_ref_count integer not null,
      bridge_score real not null, decision text not null, functional_label text not null, gloss_allowed integer not null,
      lexical_promotion_allowed integer not null, reason text not null, next_action text not null, evidence_json text not null,
      primary key(run_id, branch_id));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    bridge_run=rows(cur,'select max(run_id) as run_id from c86_bridge_policy_items')[0]['run_id']
    items=rows(cur,'select * from c86_bridge_policy_items where run_id=? order by branch_status desc, bridge_score desc',(bridge_run,))
    ready=[x for x in items if x['branch_status']=='BRIDGE_SUBFUNCTION_READY']
    audit=[x for x in items if x['branch_status']!='BRIDGE_SUBFUNCTION_READY']
    ready_books=sorted({b for x in ready for b in json.loads(x['books_json'] or '[]')}, key=lambda z:int(z) if str(z).isdigit() else z)
    edge_ref_count=sum(int(x['edge_ref_count']) for x in ready)
    cur.execute('insert into c86_payload_operator_gate_runs(created_at,decision,source_bridge_run_id,branch_count,ready_branch_count,audit_branch_count,ready_book_count,edge_ref_count,gloss_allowed_count,lexical_promotion_allowed,payload_json) values (?,?,?,?,?,?,?,?,?,?,?)',(now(),'C86_PAYLOAD_OPERATOR_GATE_READY_NO_GLOSS',bridge_run,len(items),len(ready),len(audit),len(ready_books),edge_ref_count,0,0,j({'ready_books':ready_books})))
    run_id=cur.lastrowid
    for x in items:
        is_ready=x['branch_status']=='BRIDGE_SUBFUNCTION_READY'
        decision='PAYLOAD_BRANCH_FUNCTION_READY_NO_GLOSS' if is_ready else 'AUDIT_OR_SURFACE_CONTEXT_NO_PROMOTION'
        label=f"C86 payload-open operator to {x['downstream_frame']}" if is_ready else 'C86 unsupported/surface payload context'
        reason='edge-supported branch and downstream frame separation survive refined C86 bridge policy' if is_ready else 'no edge support or unknown/local payload; keep as negative/surface context'
        next_action='materialize functional tag where present; no plaintext gloss' if is_ready else 'do not promote without edge support'
        cur.execute('insert into c86_payload_operator_gate_items(run_id,branch_id,payload_class,books_json,downstream_frame,edge_supported_occurrence_count,edge_ref_count,bridge_score,decision,functional_label,gloss_allowed,lexical_promotion_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(run_id,x['branch_id'],x['payload_class'],x['books_json'],x['downstream_frame'],x['edge_supported_occurrence_count'],x['edge_ref_count'],x['bridge_score'],decision,label,0,0,reason,next_action,j(dict(x))))
    con.commit(); out={'run_id':run_id,'decision':'C86_PAYLOAD_OPERATOR_GATE_READY_NO_GLOSS','branch_count':len(items),'ready_branch_count':len(ready),'audit_branch_count':len(audit),'ready_book_count':len(ready_books),'edge_ref_count':edge_ref_count,'gloss_allowed_count':0}; print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        desc='; '.join(f"{x['payload_class']}->{x['downstream_frame']} books={x['books_json']}" for x in ready)
        send('\n'.join([f"[469][c86-gate][run={run_id}] C86 materializado como operador funcional no-gloss",f"branches={len(items)} | ready={len(ready)} | audit/surface={len(audit)} | ready_books={len(ready_books)} | edge_refs={edge_ref_count}",desc,'decisão: C86 abre/encaminha payload em branches específicas; não é palavra lexical e não traduz livros sozinho.']))
if __name__=='__main__': main()
