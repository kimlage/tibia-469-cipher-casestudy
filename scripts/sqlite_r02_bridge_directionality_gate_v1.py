#!/usr/bin/env python3
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')


def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def create_tables(conn):
    conn.executescript('''
    create table if not exists r02_bridge_directionality_gate_v1_runs (
      run_id integer primary key autoincrement,
      created_at text not null,
      decision text not null,
      forward_pass integer not null,
      reverse_reject integer not null,
      accepted_prose_gloss_count integer not null,
      payload_json text not null
    );
    create table if not exists r02_bridge_directionality_gate_v1_items (
      run_id integer not null,
      edge_id text not null,
      expected text not null,
      observed_status text not null,
      gate_status text not null,
      evidence_json text not null,
      primary key(run_id, edge_id)
    );
    ''')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=str(DEFAULT_DB)); ap.add_argument('--json',action='store_true'); args=ap.parse_args()
    conn=sqlite3.connect(args.db); create_tables(conn)
    nr=conn.execute('select max(run_id) from naese_slot_core_v1_runs').fetchone()[0]
    edges={r[0]:(r[1],r[2],r[3],r[4]) for r in conn.execute("select item_id,status,role_label,interpretation,evidence_json from naese_slot_core_v1_items where run_id=? and item_type='edge' and item_id in ('51->53','53->51')",(nr,)).fetchall()}
    forward=edges.get('51->53',('MISSING','','',''))
    reverse=edges.get('53->51',('MISSING','','',''))
    forward_pass=int(forward[0]=='ORDERED_EDGE_FAILED_GATE' and forward[1]=='R02_BRIDGE_PAIR_CONTIG')
    reverse_reject=int(reverse[0]=='QUARANTINED_NAESE_PARALLEL_EDGE')
    decision='PROMOTE_R02_BRIDGE_DIRECTION_51_TO_53_NO_PROSE' if forward_pass and reverse_reject else 'HOLD_R02_BRIDGE_DIRECTIONALITY_NO_PROSE'
    payload={'source_naese_run_id':nr,'forward_edge':'51->53','reverse_edge':'53->51','note':'Uses current naese_slot_core statuses; preserves no plaintext.'}
    cur=conn.execute('insert into r02_bridge_directionality_gate_v1_runs(created_at,decision,forward_pass,reverse_reject,accepted_prose_gloss_count,payload_json) values(?,?,?,?,?,?)',(now(),decision,forward_pass,reverse_reject,0,json.dumps(payload,ensure_ascii=True,sort_keys=True)))
    run_id=cur.lastrowid
    for edge,expected,obs in [('51->53','FORWARD_ACCEPT',forward),('53->51','REVERSE_REJECT',reverse)]:
        gate='PASS' if (edge=='51->53' and forward_pass) or (edge=='53->51' and reverse_reject) else 'FAIL'
        conn.execute('insert into r02_bridge_directionality_gate_v1_items(run_id,edge_id,expected,observed_status,gate_status,evidence_json) values(?,?,?,?,?,?)',(run_id,edge,expected,obs[0],gate,json.dumps({'role_label':obs[1],'interpretation':obs[2],'evidence':obs[3]},ensure_ascii=True,sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'forward_pass':forward_pass,'reverse_reject':reverse_reject,'accepted_prose_gloss_count':0},ensure_ascii=True,indent=2 if args.json else None,sort_keys=True))
if __name__=='__main__': main()
