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
    create table if not exists external_archive_probe_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      target_count integer not null, success_count integer not null, blocked_count integer not null,
      payload_json text not null);
    create table if not exists external_archive_probe_items(
      run_id integer not null, target_id text not null, target_url text not null, probe_status text not null,
      result_summary text not null, next_action text not null, payload_json text not null,
      primary key(run_id,target_id));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor(); create(cur)
    targets=[
        ('WAYBACK_TIBIA_ORG_ROOT','https://web.archive.org/cdx/search/cdx?url=tibia.org/','HTTP 503 from CDX API'),
        ('WAYBACK_WWW_TIBIA_ORG_ROOT','https://web.archive.org/cdx/search/cdx?url=www.tibia.org/','HTTP 503 from CDX API'),
        ('WAYBACK_TIBIA_ORG_WILDCARD','https://web.archive.org/cdx/search/cdx?url=tibia.org/*','read timeout from CDX API')
    ]
    cur.execute('insert into external_archive_probe_runs(created_at,decision,target_count,success_count,blocked_count,payload_json) values (?,?,?,?,?,?)',
        (now(),'WAYBACK_CDX_BLOCKED_NO_ARCHIVAL_VERIFICATION_YET',len(targets),0,len(targets),j({'target_sequence':'62792068657272657261','purpose':'verify claimed old Tibia.org HTML variant'})))
    run_id=cur.lastrowid
    for tid,url,summary in targets:
        cur.execute('insert into external_archive_probe_items(run_id,target_id,target_url,probe_status,result_summary,next_action,payload_json) values (?,?,?,?,?,?,?)',
            (run_id,tid,url,'BLOCKED_BY_ARCHIVE_ACCESS',summary,'retry later or use alternate archive/source copy; do not promote Tibia.org variant until primary snapshot is inspected',j({})))
    con.commit()
    out={'run_id':run_id,'decision':'WAYBACK_CDX_BLOCKED_NO_ARCHIVAL_VERIFICATION_YET','success_count':0,'blocked_count':len(targets)}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][archive-probe][run={run_id}] Wayback CDX bloqueado",f"alvo=old tibia.org / 62792068657272657261 | sucesso=0 | bloqueios={len(targets)}",'isso não prova que o anchor é falso; só significa que ainda não temos snapshot primário. Sem promoção sem evidência primária.']))
if __name__=='__main__': main()
