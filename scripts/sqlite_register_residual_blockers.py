#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists residual_blocker_checkpoint_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      blocked_book_count integer not null, open_candidate_count integer not null, payload_json text not null);
    create table if not exists residual_blocker_checkpoint_items(
      run_id integer not null, bookid text not null, blocker_status text not null,
      reason text not null, next_action text not null, evidence_json text not null,
      primary key(run_id,bookid));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor(); create(cur)
    blocked=[
        ('4','C86_SURFACE_PAYLOAD_BLOCKED','C86 EBFAI/VL branch has no edge support and is AUDIT_OR_SURFACE_CONTEXT_NO_PROMOTION','do not promote without independent edge/context support'),
        ('34','FRAGMENTED_CONTEXT_ALIGNMENT_BLOCKED','residual LCS to 10/35 is fragmented and below accepted template controls','abandon current residual-template promotion path'),
        ('49','O32_NEEI_RESIDUAL_AUDIT_ONLY','Book49 O32/NEEI residual policy is audit-only with repeated controls','retain as residual negative/control only'),
        ('56','O23_NAESE_CONTROL_BLOCKED','Book56 is explicit O23/ONAF negative and rare NAESE/C68 variant control','do not promote residual similarity; keep as contradiction control')
    ]
    open_candidates=['41','55']
    cur.execute('insert into residual_blocker_checkpoint_runs(created_at,decision,blocked_book_count,open_candidate_count,payload_json) values (?,?,?,?,?)',
        (now(),'RESIDUAL_BLOCKERS_REGISTERED_KEEP_ONLY_41_55_OPEN',len(blocked),len(open_candidates),j({'open_candidates':open_candidates})))
    run_id=cur.lastrowid
    for b,status,reason,nxt in blocked:
        cur.execute('insert into residual_blocker_checkpoint_items(run_id,bookid,blocker_status,reason,next_action,evidence_json) values (?,?,?,?,?,?)',(run_id,b,status,reason,nxt,j({})))
    con.commit(); out={'run_id':run_id,'decision':'RESIDUAL_BLOCKERS_REGISTERED_KEEP_ONLY_41_55_OPEN','blocked_books':[x[0] for x in blocked],'open_candidates':open_candidates}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][residual-blockers][run={run_id}] bloqueios residuais registrados",f"bloqueados=4,34,49,56 | ainda abertos=41,55",'objetivo: evitar reabrir famílias mortas; próximos probes focam só micro-boundary 41/55.']))
if __name__=='__main__': main()
