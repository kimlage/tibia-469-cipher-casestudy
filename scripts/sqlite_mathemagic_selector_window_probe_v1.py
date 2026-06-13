#!/usr/bin/env python3
import argparse
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')
KEYS = [1, 13, 49, 94]
B5_BOOKS = ['2','8','19','23','24','27','57','67']
CONTROL_RULES = {
    'K_ORIGINAL': lambda k: k,
    'SHIFT_PLUS_1': lambda k: k + 1,
    'SHIFT_PLUS_2': lambda k: k + 2,
    'DOUBLE': lambda k: k * 2,
    'MOD70_PLUS35': lambda k: (k % 70) + 35,
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def classify(tok, window):
    if tok == '*00':
        return 'BOUNDARY'
    if tok in ('C68', 'C86'):
        return 'VARIANT_C'
    if tok in ('O23', 'O32'):
        return 'VARIANT_O'
    if tok in ('R20', 'R02'):
        return 'VARIANT_R'
    joined = ' '.join(window)
    if any(x in joined for x in ('B E N N A', 'L T A S T', 'N A E S E')):
        return 'HANDOFF_FRAME'
    if tok in ('*', '*00'):
        return 'DISPLAY_CONTROL'
    return 'OTHER'


def create_tables(conn):
    conn.executescript('''
    create table if not exists mathemagic_selector_window_probe_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        target_family text not null,
        original_variant_hit_count integer not null,
        best_control_variant_hit_count integer not null,
        original_margin integer not null,
        accepted_prose_gloss_count integer not null,
        payload_json text not null
    );
    create table if not exists mathemagic_selector_window_probe_v1_items (
        run_id integer not null,
        rule_id text not null,
        bookid text not null,
        key_value integer not null,
        selected_index integer not null,
        center_token text not null,
        structural_class text not null,
        window_json text not null
    );
    create index if not exists idx_mathemagic_selector_window_probe_v1_items_run on mathemagic_selector_window_probe_v1_items(run_id);
    ''')


def load_books(conn):
    rows = conn.execute('''
        select bookid, token_count, tokens_json
        from row0_variant_book_tokens
        where bookid in (%s)
        order by cast(bookid as integer)
    ''' % ','.join('?' for _ in B5_BOOKS), B5_BOOKS).fetchall()
    out = []
    for bookid, token_count, tokens_json in rows:
        out.append((bookid, int(token_count), json.loads(tokens_json)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=str(DEFAULT_DB))
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    create_tables(conn)
    books = load_books(conn)

    all_items = []
    summary = {}
    for rule_id, fn in CONTROL_RULES.items():
        counts = Counter()
        for bookid, token_count, tokens in books:
            for k in KEYS:
                idx = (fn(k) - 1) % token_count
                left = max(0, idx - 6)
                right = min(token_count, idx + 7)
                window = tokens[left:right]
                center = tokens[idx]
                cls = classify(center, window)
                counts[cls] += 1
                all_items.append((rule_id, bookid, k, idx, center, cls, window))
        variant_hits = counts['VARIANT_C'] + counts['VARIANT_O'] + counts['VARIANT_R']
        summary[rule_id] = {'counts': dict(counts), 'variant_hits': variant_hits}

    original = summary['K_ORIGINAL']['variant_hits']
    best_control = max(v['variant_hits'] for k, v in summary.items() if k != 'K_ORIGINAL')
    margin = original - best_control
    if original > best_control:
        decision = 'K_SELECTOR_BEATS_CONTROLS_STRUCTURE_ONLY_NO_PROSE'
    elif original == best_control:
        decision = 'K_SELECTOR_TIES_CONTROLS_STRUCTURE_ONLY_NO_PROSE'
    else:
        decision = 'K_SELECTOR_FAILS_CONTROLS_STRUCTURE_ONLY_NO_PROSE'

    payload = {
        'keys': KEYS,
        'target_books': B5_BOOKS,
        'classification_only': True,
        'summary': summary,
        'interpretation': 'Tests whether mathemagic results select structural variant windows in B5 C68 dual subframes; no plaintext is generated or accepted.',
    }
    cur = conn.execute('''
        insert into mathemagic_selector_window_probe_v1_runs
        (created_at, decision, target_family, original_variant_hit_count, best_control_variant_hit_count, original_margin, accepted_prose_gloss_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (now(), decision, 'B5_C68_DUAL_SUBFRAMES', original, best_control, margin, 0, json.dumps(payload, ensure_ascii=True, sort_keys=True)))
    run_id = cur.lastrowid
    for rule_id, bookid, k, idx, center, cls, window in all_items:
        conn.execute('''
            insert into mathemagic_selector_window_probe_v1_items
            (run_id, rule_id, bookid, key_value, selected_index, center_token, structural_class, window_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (run_id, rule_id, bookid, k, idx, center, cls, json.dumps(window, ensure_ascii=True)))
    conn.commit()
    result = {
        'run_id': run_id,
        'decision': decision,
        'original_variant_hit_count': original,
        'best_control_variant_hit_count': best_control,
        'original_margin': margin,
        'accepted_prose_gloss_count': 0,
        'summary': summary,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2 if args.json else None, sort_keys=True))

if __name__ == '__main__':
    main()
