#!/usr/bin/env python3
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')
PACKAGE = 'C86_EVIEFIIN_TO_C68_VN_TIIN_BRANCH'


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def create_tables(conn):
    conn.executescript('''
    create table if not exists structural_branch_propagation_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        package_id text not null,
        decision text not null,
        resolved_branch_books integer not null,
        control_books integer not null,
        unresolved_affected_books integer not null,
        accepted_prose_gloss_count integer not null,
        payload_json text not null
    );
    create table if not exists structural_branch_propagation_v1_items (
        run_id integer not null,
        bookid text not null,
        propagation_status text not null,
        promoted_label text not null,
        structural_reading text not null,
        remaining_ambiguity text not null,
        evidence_json text not null,
        primary key(run_id, bookid)
    );
    ''')


def latest_registry(conn):
    row = conn.execute('select max(run_id) from structural_promotion_registry_v1_runs where package_id=?', (PACKAGE,)).fetchone()
    reg_run = row[0]
    rows = conn.execute('''
        select bookid, promoted_label, promotion_scope, confidence, evidence_json
        from structural_promotion_registry_v1_items
        where run_id=? and package_id=?
        order by cast(bookid as integer)
    ''', (reg_run, PACKAGE)).fetchall()
    return reg_run, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=str(DEFAULT_DB))
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    create_tables(conn)
    reg_run, rows = latest_registry(conn)
    items = []
    resolved = controls = unresolved = 0
    for bookid, label, scope, confidence, evidence_json in rows:
        evidence = json.loads(evidence_json)
        if scope == 'positive_structural_branch':
            status = 'STRUCTURAL_BRANCH_RESOLVED_NO_PROSE'
            structural = 'C86_EVIEFIIN_BRANCH bridges into downstream VN-C68-TIIN subframe.'
            ambiguity = 'human plaintext unresolved; branch/function known enough for downstream mechanical tests'
            resolved += 1
        elif scope == 'negative_control_not_promoted':
            status = 'NEGATIVE_CONTROL_REJECTED_NO_PROSE'
            structural = 'Book does not instantiate the EVIEFIIN->VN-C68-TIIN branch.'
            ambiguity = 'may contain other C86/C68 roles; this package must not be applied'
            controls += 1
        else:
            status = 'UNRESOLVED_AFFECTED_BOOK_NO_PROSE'
            structural = 'No reliable propagation.'
            ambiguity = 'needs separate probe'
            unresolved += 1
        items.append((bookid, status, label, structural, ambiguity, evidence))
    decision = 'C86_BRANCH_PROPAGATED_TO_OPERATIONAL_LAYER_NO_PROSE' if resolved and controls else 'C86_BRANCH_PROPAGATION_INCOMPLETE_NO_PROSE'
    payload = {
        'source_registry_run_id': reg_run,
        'package_id': PACKAGE,
        'resolved_branch_books': resolved,
        'control_books': controls,
        'unresolved_affected_books': unresolved,
        'use': 'downstream mechanical disambiguation only; no human prose',
    }
    cur = conn.execute('''
        insert into structural_branch_propagation_v1_runs
        (created_at, package_id, decision, resolved_branch_books, control_books, unresolved_affected_books, accepted_prose_gloss_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (now(), PACKAGE, decision, resolved, controls, unresolved, 0, json.dumps(payload, ensure_ascii=True, sort_keys=True)))
    run_id = cur.lastrowid
    for bookid, status, label, structural, ambiguity, evidence in items:
        conn.execute('''
            insert into structural_branch_propagation_v1_items
            (run_id, bookid, propagation_status, promoted_label, structural_reading, remaining_ambiguity, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?)
        ''', (run_id, bookid, status, label, structural, ambiguity, json.dumps(evidence, ensure_ascii=True, sort_keys=True)))
    conn.commit()
    result = {'run_id': run_id, 'decision': decision, 'resolved_branch_books': resolved, 'control_books': controls, 'unresolved_affected_books': unresolved, 'accepted_prose_gloss_count': 0}
    print(json.dumps(result, ensure_ascii=True, indent=2 if args.json else None, sort_keys=True))

if __name__ == '__main__':
    main()
