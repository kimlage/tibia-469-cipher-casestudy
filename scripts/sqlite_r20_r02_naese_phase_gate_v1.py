#!/usr/bin/env python3
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')
POSITIVE_R02 = {'51','53'}
POSITIVE_R20 = {'45','46','51','53','64','65'}
NEGATIVE_MICRO = {'58','59','60'}
NEGATIVE_COVERED = {'15','16','61'}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def create_tables(conn):
    conn.executescript('''
    create table if not exists r20_r02_naese_phase_gate_v1_runs (
      run_id integer primary key autoincrement,
      created_at text not null,
      decision text not null,
      r02_pass_count integer not null,
      r02_total integer not null,
      r20_pass_count integer not null,
      r20_total integer not null,
      negative_reject_count integer not null,
      negative_total integer not null,
      accepted_prose_gloss_count integer not null,
      payload_json text not null
    );
    create table if not exists r20_r02_naese_phase_gate_v1_items (
      run_id integer not null,
      bookid text not null,
      expected_class text not null,
      observed_frame text not null,
      naese_status text not null,
      gate_status text not null,
      evidence_json text not null,
      primary key(run_id, bookid, expected_class)
    );
    ''')


def load_tokens(conn, books):
    run_id = conn.execute('select max(run_id) from row0_variant_book_tokens').fetchone()[0]
    rows = conn.execute('select bookid, tokens_json from row0_variant_book_tokens where run_id=? and bookid in (%s)' % ','.join('?' for _ in books), (run_id, *books)).fetchall()
    return {str(b): json.loads(t) for b,t in rows}


def has_seq(tokens, seq):
    n=len(seq)
    return any(tokens[i:i+n]==seq for i in range(0, len(tokens)-n+1))


def inspect(tokens):
    r02_bridge = has_seq(tokens, ['R02','V','E','I','I','V','N','T','B']) or has_seq(tokens, ['T','R02','V','E','I','I','V','N','T','B'])
    r20_phase = has_seq(tokens, ['V','A','E','T','R20','F','E','V','A','S','T'])
    r20_vtlr = has_seq(tokens, ['V','T','L','R20','N','E','F','I','E'])
    r02_livrn = has_seq(tokens, ['L','I','V','R02','N'])
    r20_livrn = has_seq(tokens, ['L','I','V','R20','N'])
    if r02_bridge:
        return 'R02_TRVEIIVNTBB_BRIDGE'
    if r20_phase:
        return 'R20_VAETRFEVAST_BLOCK'
    if r20_vtlr:
        return 'R20_VTLRNEFIE_COVERED_BY_VINVIN'
    if r02_livrn:
        return 'R02_LIVRN_MICRO'
    if r20_livrn:
        return 'R20_LIVRN_MICRO'
    return 'NO_R20_R02_TARGET_FRAME'


def naese_statuses(conn):
    run_id = conn.execute('select max(run_id) from naese_slot_core_v1_runs').fetchone()[0]
    rows = conn.execute("select item_id, status, role_label from naese_slot_core_v1_items where run_id=? and item_type='book'", (run_id,)).fetchall()
    return {str(i): (s,r) for i,s,r in rows}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=str(DEFAULT_DB)); ap.add_argument('--json',action='store_true'); args=ap.parse_args()
    conn=sqlite3.connect(args.db); create_tables(conn)
    all_books = POSITIVE_R02 | POSITIVE_R20 | NEGATIVE_MICRO | NEGATIVE_COVERED
    tokens_by_book=load_tokens(conn, all_books)
    ns=naese_statuses(conn)
    items=[]; r02_pass=r20_pass=neg_reject=0
    for b in sorted(all_books,key=lambda x:int(x)):
        frame=inspect(tokens_by_book.get(b,[]))
        nstatus,nrole=ns.get(b, ('NO_NAESE_SLOT_RECORD',''))
        if b in POSITIVE_R02:
            expected='POSITIVE_R02_NAESE_SLOT_BRIDGE'
            gate='PASS_R02_SLOT_BRIDGE' if frame=='R02_TRVEIIVNTBB_BRIDGE' and nrole=='R02_SLOT_BRIDGE' else 'FAIL_R02_SLOT_BRIDGE'
            r02_pass += gate.startswith('PASS')
        elif b in POSITIVE_R20:
            expected='POSITIVE_R20_PHASE_CONTEXT'
            gate='PASS_R20_PHASE_CONTEXT' if frame in ('R20_VAETRFEVAST_BLOCK','R02_TRVEIIVNTBB_BRIDGE') and nstatus in ('ORDERED_CORE','SUPPORT','VARIANT') else 'FAIL_R20_PHASE_CONTEXT'
            r20_pass += gate.startswith('PASS')
        elif b in NEGATIVE_MICRO:
            expected='NEGATIVE_MICRO_CONTEXT'
            gate='PASS_REJECT_MICRO' if frame in ('R02_LIVRN_MICRO','R20_LIVRN_MICRO','NO_R20_R02_TARGET_FRAME') else 'FAIL_MICRO_PROMOTED'
            neg_reject += gate.startswith('PASS')
        else:
            expected='NEGATIVE_COVERED_BY_VINVIN'
            gate='PASS_REJECT_COVERED' if frame in ('R20_VTLRNEFIE_COVERED_BY_VINVIN','NO_R20_R02_TARGET_FRAME') else 'FAIL_COVERED_PROMOTED'
            neg_reject += gate.startswith('PASS')
        items.append((b,expected,frame,f'{nstatus}:{nrole}',gate,{'naese_status':nstatus,'naese_role':nrole}))
    neg_total=len(NEGATIVE_MICRO|NEGATIVE_COVERED)
    decision='PROMOTE_R20_R02_NAESE_PHASE_GATE_NO_PROSE' if r02_pass==len(POSITIVE_R02) and r20_pass>=4 and neg_reject==neg_total else 'HOLD_R20_R02_NAESE_PHASE_GATE_NO_PROSE'
    payload={'r02_positive_books':sorted(POSITIVE_R02,key=lambda x:int(x)),'r20_positive_books':sorted(POSITIVE_R20,key=lambda x:int(x)),'negative_micro':sorted(NEGATIVE_MICRO,key=lambda x:int(x)),'negative_covered':sorted(NEGATIVE_COVERED,key=lambda x:int(x)),'meaning':'R02/R20 phase frames connect/support NAESE slot mechanics; no plaintext.'}
    cur=conn.execute('insert into r20_r02_naese_phase_gate_v1_runs(created_at,decision,r02_pass_count,r02_total,r20_pass_count,r20_total,negative_reject_count,negative_total,accepted_prose_gloss_count,payload_json) values(?,?,?,?,?,?,?,?,?,?)',(now(),decision,r02_pass,len(POSITIVE_R02),r20_pass,len(POSITIVE_R20),neg_reject,neg_total,0,json.dumps(payload,ensure_ascii=True,sort_keys=True)))
    run_id=cur.lastrowid
    for row in items:
        conn.execute('insert into r20_r02_naese_phase_gate_v1_items(run_id,bookid,expected_class,observed_frame,naese_status,gate_status,evidence_json) values(?,?,?,?,?,?,?)',(run_id,*row[:5],json.dumps(row[5],ensure_ascii=True,sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'r02_pass_count':r02_pass,'r02_total':len(POSITIVE_R02),'r20_pass_count':r20_pass,'r20_total':len(POSITIVE_R20),'negative_reject_count':neg_reject,'negative_total':neg_total,'accepted_prose_gloss_count':0},ensure_ascii=True,indent=2 if args.json else None,sort_keys=True))
if __name__=='__main__': main()
