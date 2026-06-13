#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any
DB_DEFAULT='./data/bonelord_operational.sqlite'; DISCORD_CHANNEL='0'; DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT): subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists charset_lane_artifact_update_runs(run_id integer primary key autoincrement,created_at text not null,artifact_run_id integer not null,base_sweep_run_id integer not null,artifact_status text not null,base_sweep_status text not null,decision text not null,next_action text not null,payload_json text not null);''')
def one(cur,sql):
    r=cur.execute(sql).fetchone(); return dict(r) if r else {}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args(); con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    art=one(cur,'select * from tibia_pic_artifact_runs order by run_id desc limit 1'); sweep=one(cur,'select * from cp1252_authentic_base_sweep_runs order by run_id desc limit 1')
    decision='CHARSET_ARTIFACT_ACQUIRED_BASE_N_DIRECT_REJECTED'
    next_action='do not pursue direct CP1252/base-N decoding for books; only reopen if OCR/glyph-specific alphabet order differs from CP1252 or another client version yields readable holdout'
    payload={'artifact':art,'sweep':sweep,'artifact_paths':['tmp/tibia_clients/tibia710/tibia/font.pic','tmp/tibia_clients/tibia710/tibia/tibia.pic','tmp/tibia_clients/extracted/font.png','tmp/tibia_clients/extracted/tibia.png']}
    cur.execute('insert into charset_lane_artifact_update_runs(created_at,artifact_run_id,base_sweep_run_id,artifact_status,base_sweep_status,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?)',(now(),art.get('run_id') or 0,sweep.get('run_id') or 0,art.get('decision',''),sweep.get('decision',''),decision,next_action,j(payload)))
    run_id=cur.lastrowid; con.commit(); print(json.dumps({'run_id':run_id,'decision':decision,'next_action':next_action},ensure_ascii=False))
    if args.discord: send('\n'.join([f'[469][charset-lane-update][run={run_id}] artifact local adquirido e testado','Tibia 7.10 Linux baixado; font.pic/tibia.pic extraídos; CP1252/base-N direto rejeitado para livros/holdouts.',f'decisão={decision}',f'próxima ação: {next_action}']))
if __name__=='__main__': main()
