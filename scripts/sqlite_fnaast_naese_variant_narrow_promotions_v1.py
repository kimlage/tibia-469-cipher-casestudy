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
    create table if not exists fnaast_naese_variant_narrow_promotions_v1_runs (
      run_id integer primary key autoincrement,
      created_at text not null,
      decision text not null,
      promoted_subfamily_count integer not null,
      audit_or_reject_count integer not null,
      accepted_prose_gloss_count integer not null,
      payload_json text not null
    );
    create table if not exists fnaast_naese_variant_narrow_promotions_v1_items (
      run_id integer not null,
      family_id text not null,
      family_type text not null,
      status text not null,
      books_json text not null,
      promoted_label text not null,
      evidence_json text not null,
      primary key(run_id, family_id)
    );
    ''')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=str(DEFAULT_DB)); ap.add_argument('--json',action='store_true'); args=ap.parse_args()
    conn=sqlite3.connect(args.db); create_tables(conn)
    items=[]
    # FNAAST subfamilies
    fr=conn.execute('select max(run_id) from fnaast_subfamily_v1_runs').fetchone()[0]
    for sid,status,bj,interp,ev in conn.execute('select subfamily_id,status,books_json,interpretation,evidence_json from fnaast_subfamily_v1_items where run_id=?',(fr,)):
        if status in ('ACCEPT_ENDPOINT_WINDOW_NO_GLOSS','ACCEPT_FORMULA_WINDOW_NO_GLOSS'):
            label='FNAAST_NARROW_STRUCTURAL_WINDOW_NO_PROSE'
            out_status='PROMOTED_NARROW_NO_PROSE'
        else:
            label='FNAAST_AUDIT_OR_GLOBAL_REJECTED'
            out_status='AUDIT_OR_REJECT_NO_PROSE'
        items.append((sid,'FNAAST',out_status,bj,label,{'source_status':status,'interpretation':interp,'source_evidence':ev}))
    # BTILBETA pair
    br=conn.execute('select max(run_id) from btilbeta_unique_subfamily_v1_runs').fetchone()[0]
    for sid,status,bj,interp,ev in conn.execute('select subfamily_id,status,books_json,interpretation,evidence_json from btilbeta_unique_subfamily_v1_items where run_id=?',(br,)):
        label='BTILBETA_FNAAST_UNIQUE_PAIR_NO_PROSE' if status=='ACCEPT_UNIQUE_MOTIF_PAIR_NO_GLOSS' else 'BTILBETA_AUDIT'
        out_status='PROMOTED_NARROW_NO_PROSE' if status=='ACCEPT_UNIQUE_MOTIF_PAIR_NO_GLOSS' else 'AUDIT_OR_REJECT_NO_PROSE'
        items.append((sid,'BTILBETA_FNAAST',out_status,bj,label,{'source_status':status,'interpretation':interp,'source_evidence':ev}))
    # NAESE variants
    nr=conn.execute('select max(run_id) from naese_slot_subfamily_v1_runs').fetchone()[0]
    for sid,status,bj,interp,ev in conn.execute('select subfamily_id,status,books_json,interpretation,evidence_json from naese_slot_subfamily_v1_items where run_id=?',(nr,)):
        if sid=='NAESE_VARIANT_28_48_WINDOW' and status=='ACCEPT_VARIANT_WINDOW_NO_GLOSS':
            label='NAESE_VARIANT_CONTAINMENT_WINDOW_NO_PROSE'
            out_status='PROMOTED_VARIANT_WINDOW_NO_PROSE'
        elif sid=='NAESE_CANONICAL_SLOT_WINDOW':
            label='NAESE_CANONICAL_GENERAL_WINDOW_HOLD_USE_NARROW_PATHS_FIRST'
            out_status='HOLD_GENERAL_WINDOW_NO_PROSE'
        else:
            label='NAESE_AUDIT_OR_MIXED_HOLD'
            out_status='AUDIT_OR_REJECT_NO_PROSE'
        items.append((sid,'NAESE_SUBFAMILY',out_status,bj,label,{'source_status':status,'interpretation':interp,'source_evidence':ev}))
    promoted=sum(1 for i in items if i[2].startswith('PROMOTED'))
    audit=len(items)-promoted
    decision='PROMOTE_NARROW_FNAAST_AND_NAESE_VARIANT_WINDOWS_NO_PROSE'
    payload={'policy':'promote only narrow subfamilies/windows; reject global FNAAST and broad NAESE lexical interpretations','fnaast_run_id':fr,'btilbeta_run_id':br,'naese_subfamily_run_id':nr}
    cur=conn.execute('insert into fnaast_naese_variant_narrow_promotions_v1_runs(created_at,decision,promoted_subfamily_count,audit_or_reject_count,accepted_prose_gloss_count,payload_json) values(?,?,?,?,?,?)',(now(),decision,promoted,audit,0,json.dumps(payload,ensure_ascii=True,sort_keys=True)))
    run_id=cur.lastrowid
    for row in items:
        conn.execute('insert into fnaast_naese_variant_narrow_promotions_v1_items(run_id,family_id,family_type,status,books_json,promoted_label,evidence_json) values(?,?,?,?,?,?,?)',(run_id,*row[:5],json.dumps(row[5],ensure_ascii=True,sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'promoted_subfamily_count':promoted,'audit_or_reject_count':audit,'accepted_prose_gloss_count':0},ensure_ascii=True,indent=2 if args.json else None,sort_keys=True))
if __name__=='__main__': main()
