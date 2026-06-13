#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
TARGETS=['NEIIVINSTAETFTE','FAIFTNIVNSENI','IAENNEENINOEENEE','IFAIONAFIEIVEINL']
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists hard_residual_external_search_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      query_count integer not null, hit_count integer not null, payload_json text not null);
    create table if not exists hard_residual_external_search_items(
      run_id integer not null, query text not null, search_status text not null,
      result_count integer not null, recommendation text not null, payload_json text not null,
      primary key(run_id,query));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor(); create(cur)
    cur.execute('insert into hard_residual_external_search_runs(created_at,decision,query_count,hit_count,payload_json) values (?,?,?,?,?)',
        (now(),'HARD_RESIDUAL_EXTERNAL_LITERAL_SEARCH_NO_HITS',len(TARGETS),0,j({'source':'web search in current run; all exact quoted queries returned no public hits'})))
    run_id=cur.lastrowid
    for q in TARGETS:
        cur.execute('insert into hard_residual_external_search_items(run_id,query,search_status,result_count,recommendation,payload_json) values (?,?,?,?,?,?)',
            (run_id,q,'NO_PUBLIC_EXACT_HIT',0,'treat as internal corpus component; do not expect external phrase unlock from this literal string',j({})))
    con.commit()
    out={'run_id':run_id,'decision':'HARD_RESIDUAL_EXTERNAL_LITERAL_SEARCH_NO_HITS','query_count':len(TARGETS),'hit_count':0}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][hard-residual-web][run={run_id}] busca externa literal dos 4 resíduos",f"queries={len(TARGETS)} | hits públicos=0",'conclusão: os resíduos finais parecem internos ao corpus; próxima frente deve ser mecânica/contraste, não busca literal externa.']))
if __name__=='__main__': main()
