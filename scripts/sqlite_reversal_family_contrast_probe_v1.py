#!/usr/bin/env python3
import argparse
import json
import math
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')
FAMILIES = {
    'C68_C86': ('C68', 'C86'),
    'R20_R02': ('R20', 'R02'),
    'O23_O32': ('O23', 'O32'),
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def create_tables(conn):
    conn.executescript('''
    create table if not exists reversal_family_contrast_probe_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        strongest_family text not null,
        strong_family_count integer not null,
        accepted_prose_gloss_count integer not null,
        payload_json text not null
    );
    create table if not exists reversal_family_contrast_probe_v1_items (
        run_id integer not null,
        family_id text not null,
        token_a text not null,
        token_b text not null,
        count_a integer not null,
        count_b integer not null,
        book_count_a integer not null,
        book_count_b integer not null,
        same_book_count integer not null,
        signature_overlap integer not null,
        signature_union integer not null,
        jaccard real not null,
        contrast_score real not null,
        decision text not null,
        evidence_json text not null,
        primary key (run_id, family_id)
    );
    create table if not exists reversal_family_contrast_probe_v1_occurrences (
        run_id integer not null,
        family_id text not null,
        token text not null,
        bookid text not null,
        token_pos integer not null,
        signature text not null,
        window_json text not null
    );
    create index if not exists idx_reversal_family_contrast_probe_v1_occurrences_run on reversal_family_contrast_probe_v1_occurrences(run_id);
    ''')


def signature(tokens, pos):
    left = tokens[max(0, pos-6):pos]
    right = tokens[pos+1:min(len(tokens), pos+7)]
    center = tokens[pos]
    joined_left = ' '.join(left)
    joined_right = ' '.join(right)
    sig = []
    if '*00' in left or '*00' in right:
        sig.append('NEAR_BOUNDARY')
    if joined_left.endswith('V N') or joined_right.startswith('T I I N'):
        sig.append('VN_TIIN_FRAME')
    if joined_left.endswith('F A T') or joined_right.startswith('T I V'):
        sig.append('FAT_TIV_FRAME')
    if any(t in left+right for t in ('B','E','N','A')) and 'B' in left+right and 'A' in left+right:
        sig.append('BENNA_NEAR')
    if any(t in left+right for t in ('L','T','A','S')) and 'L' in left+right and 'S' in left+right:
        sig.append('LTAST_NEAR')
    if any(t in left+right for t in ('N','A','E','S')) and 'N' in left+right and 'S' in left+right:
        sig.append('NAESE_NEAR')
    if any(t in left+right for t in ('C68','C86')):
        sig.append('C_NEAR')
    if any(t in left+right for t in ('R20','R02')):
        sig.append('R_NEAR')
    if any(t in left+right for t in ('O23','O32')):
        sig.append('O_NEAR')
    if not sig:
        sig.append('PLAIN_CONTEXT')
    return center + ':' + '|'.join(sig), left + [center] + right


def load_occurrences(conn):
    run_id = conn.execute('select max(run_id) from row0_variant_book_tokens').fetchone()[0]
    rows = conn.execute('select bookid, tokens_json from row0_variant_book_tokens where run_id=? order by cast(bookid as integer)', (run_id,)).fetchall()
    out = defaultdict(list)
    target_to_family = {tok: fam for fam, toks in FAMILIES.items() for tok in toks}
    for bookid, tokens_json in rows:
        tokens = json.loads(tokens_json)
        for pos, tok in enumerate(tokens):
            fam = target_to_family.get(tok)
            if not fam:
                continue
            sig, window = signature(tokens, pos)
            out[fam].append({'token': tok, 'bookid': str(bookid), 'pos': pos, 'signature': sig, 'window': window})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=str(DEFAULT_DB))
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    create_tables(conn)
    occs = load_occurrences(conn)

    family_results = []
    for fam, (a, b) in FAMILIES.items():
        rows = occs.get(fam, [])
        rows_a = [r for r in rows if r['token'] == a]
        rows_b = [r for r in rows if r['token'] == b]
        books_a = {r['bookid'] for r in rows_a}
        books_b = {r['bookid'] for r in rows_b}
        sig_a = {r['signature'].split(':',1)[1] for r in rows_a}
        sig_b = {r['signature'].split(':',1)[1] for r in rows_b}
        overlap = len(sig_a & sig_b)
        union = len(sig_a | sig_b) or 1
        jaccard = overlap / union
        balance = min(len(rows_a), len(rows_b)) / max(len(rows_a), len(rows_b), 1)
        same_book = len(books_a & books_b)
        rarity_bonus = 1.0 if min(len(rows_a), len(rows_b)) <= 2 else 0.0
        contrast_score = (1 - jaccard) * 4 + balance * 2 + (same_book > 0) * 1 + rarity_bonus
        if len(rows_b) <= 1:
            decision = 'AUDIT_ONLY_SINGLETON_CONTRAST_DO_NOT_PROMOTE'
        elif contrast_score >= 5 and jaccard <= 0.5:
            decision = 'STRONG_STRUCTURAL_CONTRAST_NO_PROSE'
        elif contrast_score >= 3:
            decision = 'PARTIAL_STRUCTURAL_CONTRAST_NO_PROSE'
        else:
            decision = 'WEAK_OR_BASE_RATE_CONTRAST_NO_PROSE'
        evidence = {
            'signature_a': sorted(sig_a),
            'signature_b': sorted(sig_b),
            'books_a': sorted(books_a, key=lambda x:int(x)),
            'books_b': sorted(books_b, key=lambda x:int(x)),
            'sample_a': rows_a[:5],
            'sample_b': rows_b[:5],
        }
        family_results.append((fam, a, b, rows_a, rows_b, books_a, books_b, same_book, overlap, union, jaccard, contrast_score, decision, evidence))

    strong = [r for r in family_results if r[12] in ('STRONG_STRUCTURAL_CONTRAST_NO_PROSE','PARTIAL_STRUCTURAL_CONTRAST_NO_PROSE')]
    strongest = max(family_results, key=lambda r:r[11])[0] if family_results else 'NONE'
    decision = 'REVERSAL_FAMILY_CONTRAST_FOUND_NO_PROSE' if strong else 'REVERSAL_FAMILY_CONTRAST_WEAK_NO_PROSE'
    payload = {
        'families': list(FAMILIES.keys()),
        'score_definition': '(1-jaccard)*4 + balance*2 + same_book_bonus + rarity_bonus; structural signatures only',
        'strongest_family': strongest,
        'results': {r[0]: {'contrast_score': r[11], 'decision': r[12], 'jaccard': r[10]} for r in family_results},
        'accepted_prose_gloss_count': 0,
    }
    cur = conn.execute('''
        insert into reversal_family_contrast_probe_v1_runs
        (created_at, decision, strongest_family, strong_family_count, accepted_prose_gloss_count, payload_json)
        values (?, ?, ?, ?, ?, ?)
    ''', (now(), decision, strongest, len(strong), 0, json.dumps(payload, ensure_ascii=True, sort_keys=True)))
    run_id = cur.lastrowid
    for fam, a, b, rows_a, rows_b, books_a, books_b, same_book, overlap, union, jaccard, contrast_score, item_decision, evidence in family_results:
        conn.execute('''
            insert into reversal_family_contrast_probe_v1_items
            (run_id, family_id, token_a, token_b, count_a, count_b, book_count_a, book_count_b, same_book_count, signature_overlap, signature_union, jaccard, contrast_score, decision, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (run_id, fam, a, b, len(rows_a), len(rows_b), len(books_a), len(books_b), same_book, overlap, union, jaccard, contrast_score, item_decision, json.dumps(evidence, ensure_ascii=True, sort_keys=True)))
        for r in rows_a + rows_b:
            conn.execute('''
                insert into reversal_family_contrast_probe_v1_occurrences
                (run_id, family_id, token, bookid, token_pos, signature, window_json)
                values (?, ?, ?, ?, ?, ?, ?)
            ''', (run_id, fam, r['token'], r['bookid'], r['pos'], r['signature'], json.dumps(r['window'], ensure_ascii=True)))
    conn.commit()
    result = {
        'run_id': run_id,
        'decision': decision,
        'strongest_family': strongest,
        'strong_family_count': len(strong),
        'accepted_prose_gloss_count': 0,
        'items': payload['results'],
    }
    print(json.dumps(result, ensure_ascii=True, indent=2 if args.json else None, sort_keys=True))

if __name__ == '__main__':
    main()
