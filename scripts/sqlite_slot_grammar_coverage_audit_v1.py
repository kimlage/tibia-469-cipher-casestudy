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
    create table if not exists slot_grammar_coverage_audit_v1_runs (
      run_id integer primary key autoincrement,
      created_at text not null,
      decision text not null,
      total_books integer not null,
      narrow_slot_path_books integer not null,
      naese_related_not_narrow_books integer not null,
      uncovered_books integer not null,
      accepted_prose_gloss_count integer not null,
      payload_json text not null
    );
    create table if not exists slot_grammar_coverage_audit_v1_items (
      run_id integer not null,
      bookid text not null,
      coverage_status text not null,
      active_paths_json text not null,
      naese_status text not null,
      next_action text not null,
      evidence_json text not null,
      primary key(run_id, bookid)
    );
    ''')

def latest_run(conn, table):
    row=conn.execute(f'select max(run_id) from {table}').fetchone()
    return row[0] if row else None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=str(DEFAULT_DB)); ap.add_argument('--json',action='store_true'); args=ap.parse_args()
    conn=sqlite3.connect(args.db); create_tables(conn)
    books=[str(r[0]) for r in conn.execute('select bookid from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens) order by cast(bookid as integer)').fetchall()]
    slot_run=latest_run(conn,'slot_grammar_registry_v1_runs')
    path_books={}
    if slot_run:
        for pid, books_json in conn.execute('select slot_path_id, books_json from slot_grammar_registry_v1_items where run_id=?',(slot_run,)).fetchall():
            for b in json.loads(books_json):
                path_books.setdefault(str(b),[]).append(pid)
    naese_run=latest_run(conn,'naese_slot_core_v1_runs')
    naese={}
    if naese_run:
        for item_id,status,role,interp,ev in conn.execute("select item_id,status,role_label,interpretation,evidence_json from naese_slot_core_v1_items where run_id=? and item_type='book'",(naese_run,)).fetchall():
            naese[str(item_id)]={'status':status,'role':role,'interpretation':interp,'evidence':ev}
    branch_run=latest_run(conn,'structural_branch_propagation_v1_runs')
    branch={}
    if branch_run:
        for b,st,label in conn.execute('select bookid,propagation_status,promoted_label from structural_branch_propagation_v1_items where run_id=?',(branch_run,)).fetchall():
            branch[str(b)]={'status':st,'label':label}
    r02_run=latest_run(conn,'r02_naese_slot_bridge_v1_runs')
    r02={}
    if r02_run:
        for b,label,gate in conn.execute('select bookid,bridge_label,gate_status from r02_naese_slot_bridge_v1_items where run_id=?',(r02_run,)).fetchall():
            r02[str(b)]={'label':label,'gate':gate}
    items=[]; narrow=related=uncovered=0
    for b in books:
        paths=path_books.get(b,[])
        n=naese.get(b)
        evidence={'paths':paths,'naese':n,'branch':branch.get(b),'r02':r02.get(b)}
        if paths:
            status='NARROW_SLOT_GRAMMAR_PATH'
            next_action='use as constrained grammar support; no plaintext'
            narrow+=1
        elif n:
            status='NAESE_RELATED_NOT_NARROW_PATH'
            next_action='keep as variant/quarantine/support unless a narrow predecessor gate passes'
            related+=1
        else:
            status='NO_SLOT_GRAMMAR_COVERAGE'
            next_action='select only if other family-specific evidence exists; do not infer NAESE slot'
            uncovered+=1
        naese_status=f"{n['status']}:{n['role']}" if n else '<none>'
        items.append((b,status,paths,naese_status,next_action,evidence))
    decision='SLOT_GRAMMAR_COVERAGE_AUDITED_NO_PROSE'
    payload={'slot_run_id':slot_run,'naese_run_id':naese_run,'branch_run_id':branch_run,'r02_run_id':r02_run,'coverage_note':'coverage counts narrow grammar paths, not translations'}
    cur=conn.execute('insert into slot_grammar_coverage_audit_v1_runs(created_at,decision,total_books,narrow_slot_path_books,naese_related_not_narrow_books,uncovered_books,accepted_prose_gloss_count,payload_json) values(?,?,?,?,?,?,?,?)',(now(),decision,len(books),narrow,related,uncovered,0,json.dumps(payload,ensure_ascii=True,sort_keys=True)))
    run_id=cur.lastrowid
    for b,status,paths,naese_status,next_action,evidence in items:
        conn.execute('insert into slot_grammar_coverage_audit_v1_items(run_id,bookid,coverage_status,active_paths_json,naese_status,next_action,evidence_json) values(?,?,?,?,?,?,?)',(run_id,b,status,json.dumps(paths),naese_status,next_action,json.dumps(evidence,ensure_ascii=True,sort_keys=True)))
    conn.commit()
    result={'run_id':run_id,'decision':decision,'total_books':len(books),'narrow_slot_path_books':narrow,'naese_related_not_narrow_books':related,'uncovered_books':uncovered,'accepted_prose_gloss_count':0}
    print(json.dumps(result,ensure_ascii=True,indent=2 if args.json else None,sort_keys=True))
if __name__=='__main__': main()
