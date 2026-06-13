#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any
DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
ALLOW={'11','32','36','43'}; BLOCK={'58','59'}
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def create(cur):
    cur.executescript('''
    create table if not exists btii_display_drift_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      checked_count integer not null, accepted_book_count integer not null, blocked_book_count integer not null,
      family_wide_promotion_allowed integer not null, lexical_gloss_allowed integer not null, payload_json text not null);
    create table if not exists btii_display_drift_gate_items(
      run_id integer not null, bookid text not null, drift_status text not null, split_status text,
      decision text not null, confidence real not null, functional_label text not null,
      family_wide_promotion_allowed integer not null, lexical_gloss_allowed integer not null,
      reason text not null, next_action text not null, evidence_json text not null, primary key(run_id,bookid));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT): subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    drift=rows(cur,'select * from btii_nsbvn_drift_items where run_id=(select max(run_id) from btii_nsbvn_drift_items)')
    split={str(x['bookid']):x for x in rows(cur,'select * from btii_nsbvn_local_split_policy_items where run_id=(select max(run_id) from btii_nsbvn_local_split_policy_items)')}
    targets=[x for x in drift if str(x['bookid']) in (ALLOW|BLOCK)]
    accepted=[x for x in targets if str(x['bookid']) in ALLOW]
    cur.execute('insert into btii_display_drift_gate_runs(created_at,decision,checked_count,accepted_book_count,blocked_book_count,family_wide_promotion_allowed,lexical_gloss_allowed,payload_json) values (?,?,?,?,?,?,?,?)',(now(),'BTII_DISPLAY_DRIFT_BOOK_SCOPED_GATE_READY_NO_GLOSS',len(targets),len(accepted),len(targets)-len(accepted),0,0,j({'allowed':sorted(ALLOW),'blocked':sorted(BLOCK)})))
    run_id=cur.lastrowid
    for x in targets:
        b=str(x['bookid']); s=split.get(b); ok=b in ALLOW
        dec='BTII_NSBVN_ATFNAAST_BLOCK_DISPLAY_DRIFT_NO_GLOSS' if ok else 'BTII_RESIDUAL_BLOCKED_CONTEXT_NO_PROMOTION'
        conf=0.55 if b in {'11','32'} else 0.45 if ok else 0.2
        label='BTII/NSBVN/ATFNAAST display-drift marker, book-scoped' if ok else 'BTII residual blocked context'
        reason='book-local display drift marker accepted without semantic payload' if ok else 'residual blocked context remains; family-wide promotion blocked'
        next_action='materialize display-drift tag only; preserve surface; no semantic payload' if ok else 'keep outside tag promotion; preserve residual block'
        cur.execute('insert into btii_display_drift_gate_items(run_id,bookid,drift_status,split_status,decision,confidence,functional_label,family_wide_promotion_allowed,lexical_gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?)',(run_id,b,x['drift_status'],s['split_status'] if s else None,dec,conf,label,0,0,reason,next_action,j({'drift':x,'split':s})))
    con.commit(); out={'run_id':run_id,'decision':'BTII_DISPLAY_DRIFT_BOOK_SCOPED_GATE_READY_NO_GLOSS','accepted_books':sorted(ALLOW),'blocked_books':sorted(BLOCK),'lexical_gloss_allowed':0}; print(json.dumps(out,ensure_ascii=False))
    if args.discord: send('\n'.join([f"[469][btii-drift][run={run_id}] BTII display-drift materializado",f"aceitos=11,32,36,43 | bloqueados=58,59 | gloss lexical=0 | promoção familiar=0",'decisão: tag book-local de drift/display; nenhum payload semântico.']))
if __name__=='__main__': main()
