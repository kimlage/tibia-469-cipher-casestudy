#!/usr/bin/env python3
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def create_tables(conn):
    conn.executescript('''
    create table if not exists naese_after_c68_branch_gate_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        positive_pass_count integer not null,
        positive_total integer not null,
        negative_reject_count integer not null,
        negative_total integer not null,
        accepted_prose_gloss_count integer not null,
        payload_json text not null
    );
    create table if not exists naese_after_c68_branch_gate_v1_items (
        run_id integer not null,
        bookid text not null,
        naese_status text not null,
        mechanical_context text not null,
        gate_status text not null,
        promoted_label text not null,
        evidence_json text not null,
        primary key(run_id, bookid)
    );
    ''')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=str(DEFAULT_DB))
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    create_tables(conn)

    latest_naese = conn.execute('select max(run_id) from naese_slot_core_v1_runs').fetchone()[0]
    latest_branch = conn.execute('select max(run_id) from structural_branch_propagation_v1_runs where package_id=?', ('C86_EVIEFIIN_TO_C68_VN_TIIN_BRANCH',)).fetchone()[0]
    naese_rows = conn.execute('''
        select item_id, status, role_label, interpretation, evidence_json
        from naese_slot_core_v1_items
        where run_id=? and item_type='book'
        order by cast(item_id as integer)
    ''', (latest_naese,)).fetchall()
    branch = {r[0]: r[1] for r in conn.execute('select bookid, propagation_status from structural_branch_propagation_v1_items where run_id=?', (latest_branch,)).fetchall()}
    chain_pass = {r[0]: r[1] for r in conn.execute("select item_id, gate_status from c86_c68_naese_chain_probe_v1_items where run_id=(select max(run_id) from c86_c68_naese_chain_probe_v1_runs) and item_type='naese_book'").fetchall()}

    items=[]
    positives=negatives=pos_pass=neg_reject=0
    for bookid, status, role, interpretation, ev in naese_rows:
        has_branch = branch.get(bookid) == 'STRUCTURAL_BRANCH_RESOLVED_NO_PROSE'
        has_chain = chain_pass.get(bookid) == 'ORDERED_CORE'
        if status == 'ORDERED_CORE' and (has_branch or has_chain):
            expected = 'positive'
            positives += 1
            gate = 'PASS_CANONICAL_SLOT_AFTER_BRANCH' if role in ('CANONICAL_SLOT','R02_SLOT_BRIDGE') else 'FAIL_UNEXPECTED_ROLE'
            pos_pass += gate.startswith('PASS')
            label = 'NAESE_CANONICAL_SLOT_AFTER_C86_C68_BRANCH'
            mech = 'BRANCH_OR_CHAIN_CONTEXT'
        elif status in ('QUARANTINED','VARIANT','SUPPORT'):
            expected = 'negative'
            negatives += 1
            gate = 'PASS_REJECT_SURFACE_OR_VARIANT' if not (status == 'ORDERED_CORE' and has_branch) else 'FAIL_FALSE_PROMOTION'
            neg_reject += gate.startswith('PASS')
            label = 'NAESE_NOT_PROMOTED_BY_BRANCH_GATE'
            mech = 'NO_ACCEPTED_BRANCH_SLOT_CONTEXT'
        elif status == 'ORDERED_CORE':
            expected = 'positive_no_branch'
            positives += 1
            gate = 'HOLD_ORDERED_CORE_WITHOUT_BRANCH_CONTEXT'
            label = 'NAESE_CANONICAL_SLOT_EXISTING_NOT_BRANCH_DERIVED'
            mech = 'ORDERED_CORE_NO_C86_BRANCH_CONTEXT'
        else:
            expected = 'other'
            gate = 'HOLD_UNCLASSIFIED'
            label = 'NAESE_UNCLASSIFIED'
            mech = 'UNKNOWN'
        items.append((bookid,status,mech,gate,label,{'role_label':role,'interpretation':interpretation,'source_evidence':ev,'branch_status':branch.get(bookid), 'chain_status':chain_pass.get(bookid), 'expected':expected}))
    hard_positive_total = sum(1 for x in items if x[3] in ('PASS_CANONICAL_SLOT_AFTER_BRANCH','HOLD_ORDERED_CORE_WITHOUT_BRANCH_CONTEXT'))
    decision = 'PROMOTE_NAESE_BRANCH_CONDITIONED_SLOT_GATE_NO_PROSE' if pos_pass >= 1 and neg_reject == negatives else 'HOLD_NAESE_BRANCH_GATE_INCOMPLETE_NO_PROSE'
    payload = {'naese_run_id': latest_naese, 'branch_run_id': latest_branch, 'positive_pass_count': pos_pass, 'negative_reject_count': neg_reject, 'negative_total': negatives, 'meaning': 'NAESE can be promoted as canonical slot only when supported by accepted branch/chain context; surface and variants remain rejected.'}
    cur=conn.execute('''insert into naese_after_c68_branch_gate_v1_runs(created_at,decision,positive_pass_count,positive_total,negative_reject_count,negative_total,accepted_prose_gloss_count,payload_json) values(?,?,?,?,?,?,?,?)''',(now(),decision,pos_pass,positives,neg_reject,negatives,0,json.dumps(payload,ensure_ascii=True,sort_keys=True)))
    run_id=cur.lastrowid
    for item in items:
        conn.execute('insert into naese_after_c68_branch_gate_v1_items(run_id,bookid,naese_status,mechanical_context,gate_status,promoted_label,evidence_json) values(?,?,?,?,?,?,?)',(run_id,*item[:5],json.dumps(item[5],ensure_ascii=True,sort_keys=True)))
    conn.commit()
    result={'run_id':run_id,'decision':decision,'positive_pass_count':pos_pass,'positive_total':positives,'negative_reject_count':neg_reject,'negative_total':negatives,'accepted_prose_gloss_count':0}
    print(json.dumps(result,ensure_ascii=True,indent=2 if args.json else None,sort_keys=True))

if __name__=='__main__':
    main()
