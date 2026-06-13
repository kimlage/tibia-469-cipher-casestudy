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
    create table if not exists ltast_boundary_operator_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_f02_run_id integer not null, checked_book_count integer not null, boundary_only_count integer not null,
      residual_blocked_count integer not null, gloss_allowed_count integer not null, lexical_promotion_allowed integer not null, payload_json text not null);
    create table if not exists ltast_boundary_operator_gate_items(
      run_id integer not null, bookid text not null, split_status text not null, decision text not null,
      confidence real not null, functional_label text not null, gloss_allowed integer not null, lexical_promotion_allowed integer not null,
      reason text not null, next_action text not null, evidence_json text not null, primary key(run_id, bookid));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    src=rows(cur,'select * from f02_boundary_split_probe_runs order by run_id desc limit 1')[0]
    items=rows(cur,'select * from f02_boundary_split_items where run_id=? order by cast(bookid as integer)',(src['run_id'],))
    boundary=[x for x in items if x['split_status']=='BOUNDARY_OPERATOR_ONLY_CANDIDATE_NO_GLOSS']
    residual=[x for x in items if x['split_status']!='BOUNDARY_OPERATOR_ONLY_CANDIDATE_NO_GLOSS']
    cur.execute('insert into ltast_boundary_operator_gate_runs(created_at,decision,source_f02_run_id,checked_book_count,boundary_only_count,residual_blocked_count,gloss_allowed_count,lexical_promotion_allowed,payload_json) values (?,?,?,?,?,?,?,?,?)',(now(),'LTAST_TTNVVN_BOUNDARY_OPERATOR_GATE_READY_NO_GLOSS',src['run_id'],len(items),len(boundary),len(residual),0,0,j({'source_run':src})))
    run_id=cur.lastrowid
    for x in items:
        ok=x['split_status']=='BOUNDARY_OPERATOR_ONLY_CANDIDATE_NO_GLOSS'
        dec='LTAST_TTNVVN_BOUNDARY_OPERATOR_NO_GLOSS' if ok else 'LTAST_TTNVVN_RESIDUAL_BLOCKED_CONTEXT_NO_PROMOTION'
        conf=0.86 if ok else 0.42
        label='LTAST/TTNVVN boundary handoff operator' if ok else 'LTAST/TTNVVN boundary with residual blocked context'
        reason='F02 split isolates boundary operator without residual blockers' if ok else 'boundary exists but residual F01/F05/BTII/R-phase context blocks clean functional tag'
        next_action='materialize boundary operator tag only; no lexical gloss' if ok else 'preserve residual blocked context; no promotion'
        cur.execute('insert into ltast_boundary_operator_gate_items(run_id,bookid,split_status,decision,confidence,functional_label,gloss_allowed,lexical_promotion_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?)',(run_id,x['bookid'],x['split_status'],dec,conf,label,0,0,reason,next_action,j(x)))
    con.commit(); out={'run_id':run_id,'decision':'LTAST_TTNVVN_BOUNDARY_OPERATOR_GATE_READY_NO_GLOSS','checked_book_count':len(items),'boundary_only_count':len(boundary),'residual_blocked_count':len(residual),'gloss_allowed_count':0}; print(json.dumps(out,ensure_ascii=False))
    if args.discord: send('\n'.join([f"[469][ltast-boundary][run={run_id}] LTAST/TTNVVN boundary materializado",f"boundary-only={len(boundary)} | residual-bloqueado={len(residual)} | gloss lexical=0",'decisão: tag funcional só nos boundary-only; preservar contextos residuais bloqueados.']))
if __name__=='__main__': main()
