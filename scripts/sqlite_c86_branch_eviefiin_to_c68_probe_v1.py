#!/usr/bin/env python3
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')
POSITIVE = {'2','10','27','35','67'}
NEGATIVE = {'4','18','31','36','42','57'}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def create_tables(conn):
    conn.executescript('''
    create table if not exists c86_branch_eviefiin_to_c68_probe_v1_runs (
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
    create table if not exists c86_branch_eviefiin_to_c68_probe_v1_items (
        run_id integer not null,
        bookid text not null,
        expected_class text not null,
        observed_class text not null,
        c86_branch_signature text not null,
        downstream_c68_signature text not null,
        delta_to_c68 integer,
        gate_status text not null,
        evidence_json text not null,
        primary key(run_id, bookid)
    );
    ''')


def load_books(conn):
    run_id = conn.execute('select max(run_id) from row0_variant_book_tokens').fetchone()[0]
    books = POSITIVE | NEGATIVE
    rows = conn.execute('select bookid, tokens_json from row0_variant_book_tokens where run_id=? and bookid in (%s)' % ','.join('?' for _ in books), (run_id, *books)).fetchall()
    return {str(bookid): json.loads(tokens_json) for bookid, tokens_json in rows}


def classify_book(tokens):
    c86_hits = []
    c68_hits = []
    for i, tok in enumerate(tokens):
        if tok == 'C86':
            left = tokens[max(0, i-3):i]
            right = tokens[i+1:min(len(tokens), i+9)]
            sig = ' '.join(left + [tok] + right)
            is_eviefiin = right[:7] == ['E','V','I','E','F','I','I'] or right[:8] == ['E','V','I','E','F','I','I','N']
            is_ebfai = right[:4] == ['E','B','F','A']
            c86_hits.append({'pos': i, 'sig': sig, 'is_eviefiin': is_eviefiin, 'is_ebfai': is_ebfai})
        if tok == 'C68':
            left = tokens[max(0, i-3):i]
            right = tokens[i+1:min(len(tokens), i+7)]
            sig = ' '.join(left + [tok] + right)
            is_vn_tiin = len(left) >= 2 and left[-2:] == ['V','N'] and right[:3] == ['T','I','I']
            is_fat_tiv = len(left) >= 3 and left[-3:] == ['F','A','T'] and right[:3] == ['T','I','V']
            c68_hits.append({'pos': i, 'sig': sig, 'is_vn_tiin': is_vn_tiin, 'is_fat_tiv': is_fat_tiv})
    evie = [h for h in c86_hits if h['is_eviefiin']]
    vn = [h for h in c68_hits if h['is_vn_tiin']]
    ebf = [h for h in c86_hits if h['is_ebfai']]
    fat = [h for h in c68_hits if h['is_fat_tiv']]
    delta = None
    if evie and vn:
        delta = min(abs(v['pos'] - e['pos']) for e in evie for v in vn)
    if evie and vn:
        observed = 'C86_EVIEFIIN_WITH_DOWNSTREAM_VN_C68_TIIN'
    elif evie:
        observed = 'C86_EVIEFIIN_WITHOUT_DOWNSTREAM_VN_C68'
    elif ebf:
        observed = 'C86_EBFAI_CONTROL_BRANCH'
    elif c86_hits:
        observed = 'C86_OTHER_BRANCH'
    elif vn:
        observed = 'C68_VN_TIIN_WITHOUT_C86'
    elif fat:
        observed = 'C68_FAT_TIV_WITHOUT_C86'
    else:
        observed = 'NO_C86_C68_TARGET_FRAME'
    return observed, c86_hits, c68_hits, delta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=str(DEFAULT_DB))
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    create_tables(conn)
    books = load_books(conn)
    items = []
    pos_pass = 0
    neg_reject = 0
    for bookid in sorted(POSITIVE | NEGATIVE, key=lambda x:int(x)):
        tokens = books.get(bookid, [])
        observed, c86_hits, c68_hits, delta = classify_book(tokens)
        expected = 'POSITIVE' if bookid in POSITIVE else 'NEGATIVE'
        if expected == 'POSITIVE':
            gate = 'PASS_POSITIVE' if observed == 'C86_EVIEFIIN_WITH_DOWNSTREAM_VN_C68_TIIN' else 'FAIL_POSITIVE_MISSING_BRIDGE'
            pos_pass += gate == 'PASS_POSITIVE'
        else:
            gate = 'PASS_NEGATIVE_REJECTED' if observed != 'C86_EVIEFIIN_WITH_DOWNSTREAM_VN_C68_TIIN' else 'FAIL_NEGATIVE_ACCEPTED'
            neg_reject += gate == 'PASS_NEGATIVE_REJECTED'
        c86_sig = ' || '.join(h['sig'] for h in c86_hits) or '<none>'
        c68_sig = ' || '.join(h['sig'] for h in c68_hits) or '<none>'
        items.append((bookid, expected, observed, c86_sig, c68_sig, delta, gate, {'c86_hits': c86_hits, 'c68_hits': c68_hits}))
    if pos_pass == len(POSITIVE) and neg_reject == len(NEGATIVE):
        decision = 'PROMOTE_C86_EVIEFIIN_TO_C68_VN_TIIN_BRANCH_NO_PROSE'
    elif pos_pass >= 3 and neg_reject == len(NEGATIVE):
        decision = 'PARTIAL_PROMOTE_C86_EVIEFIIN_BRANCH_WITH_LIMITS_NO_PROSE'
    else:
        decision = 'HOLD_C86_EVIEFIIN_BRANCH_NOT_PREDICTIVE_ENOUGH_NO_PROSE'
    payload = {
        'positive_books': sorted(POSITIVE, key=lambda x:int(x)),
        'negative_books': sorted(NEGATIVE, key=lambda x:int(x)),
        'rule': 'C86 followed by EVIEFIIN and downstream VN-C68-TIIN frame marks structural branch bridge; no plaintext.',
        'positive_pass_count': pos_pass,
        'negative_reject_count': neg_reject,
    }
    cur = conn.execute('''
      insert into c86_branch_eviefiin_to_c68_probe_v1_runs
      (created_at, decision, positive_pass_count, positive_total, negative_reject_count, negative_total, accepted_prose_gloss_count, payload_json)
      values (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (now(), decision, pos_pass, len(POSITIVE), neg_reject, len(NEGATIVE), 0, json.dumps(payload, ensure_ascii=True, sort_keys=True)))
    run_id = cur.lastrowid
    for bookid, expected, observed, c86_sig, c68_sig, delta, gate, evidence in items:
        conn.execute('''
          insert into c86_branch_eviefiin_to_c68_probe_v1_items
          (run_id, bookid, expected_class, observed_class, c86_branch_signature, downstream_c68_signature, delta_to_c68, gate_status, evidence_json)
          values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (run_id, bookid, expected, observed, c86_sig, c68_sig, delta, gate, json.dumps(evidence, ensure_ascii=True, sort_keys=True)))
    conn.commit()
    result = {'run_id': run_id, 'decision': decision, 'positive_pass_count': pos_pass, 'positive_total': len(POSITIVE), 'negative_reject_count': neg_reject, 'negative_total': len(NEGATIVE), 'accepted_prose_gloss_count': 0}
    print(json.dumps(result, ensure_ascii=True, indent=2 if args.json else None, sort_keys=True))

if __name__ == '__main__':
    main()
