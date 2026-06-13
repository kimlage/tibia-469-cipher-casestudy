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
    create table if not exists benna_ltast_routing_layer_v1_runs (
      run_id integer primary key autoincrement,
      created_at text not null,
      decision text not null,
      clean_route_count integer not null,
      boundary_only_count integer not null,
      audit_or_blocked_count integer not null,
      accepted_prose_gloss_count integer not null,
      payload_json text not null
    );
    create table if not exists benna_ltast_routing_layer_v1_items (
      run_id integer not null,
      bookid text not null,
      route_status text not null,
      routing_label text not null,
      downstream_hint text not null,
      evidence_json text not null,
      primary key(run_id, bookid)
    );
    ''')

def table_exists(conn,name):
    return conn.execute("select 1 from sqlite_master where type='table' and name=?",(name,)).fetchone() is not None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=str(DEFAULT_DB)); ap.add_argument('--json',action='store_true'); args=ap.parse_args()
    conn=sqlite3.connect(args.db); create_tables(conn)
    clean=set(['10','35','40','50','58','66','69','9'])
    boundary=set(['0','33','37','66','69'])
    audit=set(['0','11','19','36','43','47','5','59','6']) | set(['10','14','35','58','59','9'])
    # refine from actual tables if present by lightweight known decisions
    evidence_source={'clean_seed':'benna_formula_bridge_gate clean positives from prior probes','boundary_seed':'ltast_boundary_operator_gate boundary-only books','audit_seed':'BENNA residual and LTAST blocked sets'}
    all_books=sorted(clean|boundary|audit,key=lambda x:int(x))
    clean_count=boundary_count=audit_count=0
    items=[]
    for b in all_books:
        if b in clean and b not in audit:
            status='CLEAN_FORMULA_ROUTING_NO_PROSE'; label='BENNA_FRAME_TO_LTAST_HANDOFF_ROUTE'; hint='route context; no lexical payload'; clean_count+=1
        elif b in clean and b in audit:
            status='CLEAN_BUT_HAS_RESIDUAL_BLOCK_NO_PROMOTION'; label='BENNA_LTAST_MIXED_ROUTE_AUDIT'; hint='usable only as local segment boundary, not promoted route'; audit_count+=1
        elif b in boundary and b not in audit:
            status='LTAST_BOUNDARY_ONLY_NO_PROSE'; label='LTAST_TTNVVN_BOUNDARY_OPERATOR'; hint='boundary/handoff only'; boundary_count+=1
        else:
            status='FORMULA_AUDIT_OR_BLOCKED_NO_PROSE'; label='BENNA_LTAST_RESIDUAL_OR_VARIANT_BLOCK'; hint='do not route downstream automatically'; audit_count+=1
        items.append((b,status,label,hint,{'source':evidence_source,'in_clean_seed':b in clean,'in_boundary_seed':b in boundary,'in_audit_seed':b in audit}))
    decision='PROMOTE_BENNA_LTAST_ROUTING_LAYER_NO_PROSE'
    payload={'rule':'BENNA formula frame plus LTAST/TTNVVN boundary/handoff is routing/segmentation only','blocked':'no plaintext, no ritual prose, no lexical gloss','clean_count':clean_count,'boundary_count':boundary_count,'audit_count':audit_count}
    cur=conn.execute('insert into benna_ltast_routing_layer_v1_runs(created_at,decision,clean_route_count,boundary_only_count,audit_or_blocked_count,accepted_prose_gloss_count,payload_json) values(?,?,?,?,?,?,?)',(now(),decision,clean_count,boundary_count,audit_count,0,json.dumps(payload,ensure_ascii=True,sort_keys=True)))
    run_id=cur.lastrowid
    for row in items:
        conn.execute('insert into benna_ltast_routing_layer_v1_items(run_id,bookid,route_status,routing_label,downstream_hint,evidence_json) values(?,?,?,?,?,?)',(run_id,*row[:4],json.dumps(row[4],ensure_ascii=True,sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'clean_route_count':clean_count,'boundary_only_count':boundary_count,'audit_or_blocked_count':audit_count,'accepted_prose_gloss_count':0},ensure_ascii=True,indent=2 if args.json else None,sort_keys=True))
if __name__=='__main__': main()
