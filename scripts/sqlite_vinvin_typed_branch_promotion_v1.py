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
    create table if not exists vinvin_typed_branch_promotion_v1_runs (
      run_id integer primary key autoincrement,
      created_at text not null,
      decision text not null,
      c86_branch_books integer not null,
      r20_branch_books integer not null,
      quarantined_controls integer not null,
      accepted_prose_gloss_count integer not null,
      payload_json text not null
    );
    create table if not exists vinvin_typed_branch_promotion_v1_items (
      run_id integer not null,
      bookid text not null,
      branch_type text not null,
      status text not null,
      role_label text not null,
      evidence_json text not null,
      primary key(run_id, bookid)
    );
    ''')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=str(DEFAULT_DB)); ap.add_argument('--json',action='store_true'); args=ap.parse_args()
    conn=sqlite3.connect(args.db); create_tables(conn)
    core_run=conn.execute('select max(run_id) from vinvin_branch_core_v1_runs').fetchone()[0]
    function_row=conn.execute("select status,function_label,accuracy,ordered_recall,negative_rejection,evidence_json from vinvin_branch_function_probe_v1_items where run_id=(select max(run_id) from vinvin_branch_function_probe_v1_runs) and hypothesis_id='VINVIN_AS_TYPED_BRANCH_SYSTEM'").fetchone()
    rows=conn.execute("select item_id,status,role_label,interpretation,evidence_json from vinvin_branch_core_v1_items where run_id=? and item_type='book' order by cast(item_id as integer)",(core_run,)).fetchall()
    c86=[]; r20=[]; controls=[]; items=[]
    for bookid,status,role,interp,ev in rows:
        if status=='ORDERED_CORE' and role=='C86_VINVIN_BRANCH_PAYLOAD':
            btype='C86_PAYLOAD_BRANCH'; c86.append(bookid)
        elif status=='ORDERED_CORE' and role in ('R20_BRANCH_HEAD','R20_CONNECTOR_ENDPOINT'):
            btype='R20_CONNECTOR_BRANCH'; r20.append(bookid)
        elif status in ('QUARANTINED','AUDIT_ONLY'):
            btype='NEGATIVE_OR_AUDIT_CONTROL'; controls.append(bookid)
        else:
            btype='RELATED_CONTEXT_NOT_VINVIN_BRANCH'
        items.append((bookid,btype,status,role,{'interpretation':interp,'source_evidence':ev}))
    passed=function_row and function_row[0]=='BEST' and function_row[2]==1.0 and function_row[3]==1.0 and function_row[4]==1.0
    decision='PROMOTE_VINVIN_TYPED_BRANCH_SYSTEM_NO_PROSE' if passed else 'HOLD_VINVIN_TYPED_BRANCH_SYSTEM_NO_PROSE'
    payload={'core_run_id':core_run,'function_probe':{'status':function_row[0] if function_row else None,'function_label':function_row[1] if function_row else None,'accuracy':function_row[2] if function_row else None,'ordered_recall':function_row[3] if function_row else None,'negative_rejection':function_row[4] if function_row else None},'blocked':'do not promote broad single VINVIN branch; book 68 remains negative/control'}
    cur=conn.execute('insert into vinvin_typed_branch_promotion_v1_runs(created_at,decision,c86_branch_books,r20_branch_books,quarantined_controls,accepted_prose_gloss_count,payload_json) values(?,?,?,?,?,?,?)',(now(),decision,len(c86),len(r20),len(controls),0,json.dumps(payload,ensure_ascii=True,sort_keys=True)))
    run_id=cur.lastrowid
    for bookid,btype,status,role,evidence in items:
        conn.execute('insert into vinvin_typed_branch_promotion_v1_items(run_id,bookid,branch_type,status,role_label,evidence_json) values(?,?,?,?,?,?)',(run_id,bookid,btype,status,role,json.dumps(evidence,ensure_ascii=True,sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'c86_branch_books':len(c86),'r20_branch_books':len(r20),'quarantined_controls':len(controls),'accepted_prose_gloss_count':0,'c86_books':c86,'r20_books':r20},ensure_ascii=True,indent=2 if args.json else None,sort_keys=True))
if __name__=='__main__': main()
