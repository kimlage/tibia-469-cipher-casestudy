#!/usr/bin/env python3
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')
CHAIN_BOOKS = ['67','2']


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def create_tables(conn):
    conn.executescript('''
    create table if not exists c86_c68_naese_chain_probe_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        chain_id text not null,
        chain_pass integer not null,
        accepted_prose_gloss_count integer not null,
        payload_json text not null
    );
    create table if not exists c86_c68_naese_chain_probe_v1_items (
        run_id integer not null,
        item_type text not null,
        item_id text not null,
        gate_status text not null,
        evidence_json text not null
    );
    ''')


def fetch_one(conn, sql, params=()):
    row = conn.execute(sql, params).fetchone()
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=str(DEFAULT_DB))
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    create_tables(conn)

    branch_run = fetch_one(conn, 'select max(run_id) from structural_branch_propagation_v1_runs where package_id=?', ('C86_EVIEFIIN_TO_C68_VN_TIIN_BRANCH',))[0]
    branch_rows = conn.execute('''select bookid, propagation_status, promoted_label, structural_reading from structural_branch_propagation_v1_items where run_id=? and bookid in (?,?) order by cast(bookid as integer)''', (branch_run, *CHAIN_BOOKS)).fetchall()
    naese_rows = conn.execute('''select item_type, item_id, status, role_label, interpretation, evidence_json from naese_slot_core_v1_items where run_id=(select max(run_id) from naese_slot_core_v1_runs) and ((item_type='book' and item_id in (?,?)) or (item_type='edge' and item_id='67->2')) order by item_type, item_id''', tuple(CHAIN_BOOKS)).fetchall()

    book2_branch = any(r[0] == '2' and r[1] == 'STRUCTURAL_BRANCH_RESOLVED_NO_PROSE' for r in branch_rows)
    book67_branch = any(r[0] == '67' and r[1] == 'STRUCTURAL_BRANCH_RESOLVED_NO_PROSE' for r in branch_rows)
    edge_accept = any(r[0] == 'edge' and r[1] == '67->2' and r[2] == 'ORDERED_EDGE_ACCEPTED_NO_GLOSS' for r in naese_rows)
    book2_slot = any(r[0] == 'book' and r[1] == '2' and r[2] == 'ORDERED_CORE' for r in naese_rows)
    chain_pass = int(book2_branch and book67_branch and edge_accept and book2_slot)
    decision = 'PROMOTE_CHAIN_67_TO_2_C86_C68_NAESE_NO_PROSE' if chain_pass else 'HOLD_CHAIN_67_TO_2_INCOMPLETE_NO_PROSE'
    payload = {
        'chain': '67->2',
        'branch_run_id': branch_run,
        'book67_branch': book67_branch,
        'book2_branch': book2_branch,
        'book2_naese_slot': book2_slot,
        'edge_67_2_accepted': edge_accept,
        'meaning': 'C86 branch propagation supports the accepted NAESE/context edge 67->2; no plaintext.',
    }
    cur = conn.execute('''insert into c86_c68_naese_chain_probe_v1_runs(created_at,decision,chain_id,chain_pass,accepted_prose_gloss_count,payload_json) values(?,?,?,?,?,?)''', (now(), decision, '67->2_C86_C68_NAESE', chain_pass, 0, json.dumps(payload, ensure_ascii=True, sort_keys=True)))
    run_id = cur.lastrowid
    for r in branch_rows:
        conn.execute('insert into c86_c68_naese_chain_probe_v1_items(run_id,item_type,item_id,gate_status,evidence_json) values(?,?,?,?,?)', (run_id, 'branch_book', r[0], r[1], json.dumps({'promoted_label': r[2], 'structural_reading': r[3]}, ensure_ascii=True, sort_keys=True)))
    for item_type, item_id, status, role_label, interpretation, ev in naese_rows:
        conn.execute('insert into c86_c68_naese_chain_probe_v1_items(run_id,item_type,item_id,gate_status,evidence_json) values(?,?,?,?,?)', (run_id, 'naese_'+item_type, item_id, status, json.dumps({'role_label': role_label, 'interpretation': interpretation, 'evidence': ev}, ensure_ascii=True, sort_keys=True)))
    conn.commit()
    result = {'run_id': run_id, 'decision': decision, 'chain_pass': chain_pass, 'accepted_prose_gloss_count': 0, 'payload': payload}
    print(json.dumps(result, ensure_ascii=True, indent=2 if args.json else None, sort_keys=True))

if __name__ == '__main__':
    main()
