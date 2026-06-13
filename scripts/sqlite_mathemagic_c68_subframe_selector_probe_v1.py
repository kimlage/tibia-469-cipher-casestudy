#!/usr/bin/env python3
import argparse
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')
KEYS = [1, 13, 49, 94]
CONTROL_RULES = {
    'K_ORIGINAL': lambda k: k,
    'SHIFT_PLUS_1': lambda k: k + 1,
    'SHIFT_PLUS_2': lambda k: k + 2,
    'DOUBLE': lambda k: k * 2,
    'REVERSE_DIGITS_PLUS_1': lambda k: int(str(k)[::-1]) + 1,
    'SQUARE_DIGIT_SUM': lambda k: sum(int(c) for c in str(k)) ** 2,
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def create_tables(conn):
    conn.executescript('''
    create table if not exists mathemagic_c68_subframe_selector_probe_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        selected_count integer not null,
        original_score integer not null,
        best_control_score integer not null,
        original_margin integer not null,
        accepted_prose_gloss_count integer not null,
        payload_json text not null
    );
    create table if not exists mathemagic_c68_subframe_selector_probe_v1_items (
        run_id integer not null,
        rule_id text not null,
        key_value integer not null,
        selected_index integer not null,
        bookid text not null,
        occurrence_index integer not null,
        token_pos integer not null,
        subframe text not null,
        target_book integer not null,
        left_context text not null,
        right_context text not null
    );
    create index if not exists idx_mathemagic_c68_subframe_selector_probe_v1_items_run on mathemagic_c68_subframe_selector_probe_v1_items(run_id);
    ''')


def load_occurrences(conn):
    run_id = conn.execute('select max(run_id) from c68_subframe_split_gate_v1_occurrences').fetchone()[0]
    rows = conn.execute('''
        select bookid, occurrence_index, token_pos, subframe, target_book, left_context, right_context
        from c68_subframe_split_gate_v1_occurrences
        where run_id=?
        order by cast(bookid as integer), occurrence_index
    ''', (run_id,)).fetchall()
    return [dict(bookid=str(r[0]), occurrence_index=int(r[1]), token_pos=int(r[2]), subframe=r[3], target_book=int(r[4]), left_context=r[5], right_context=r[6]) for r in rows]


def score_selected(selected):
    counts = Counter(s['subframe'] for s in selected)
    target_hits = sum(s['target_book'] for s in selected)
    context_hits = counts['C68_VN_TIIN_CONTEXT_SUBFRAME']
    slot_hits = counts['C68_FAT_TIV_SLOT_SUBFRAME']
    unclassified_penalty = counts['C68_UNCLASSIFIED_CONTEXT'] + counts['C68_TIIN_CONTEXT_WEAK']
    preserves_split = 1 if context_hits > 0 and slot_hits > 0 else 0
    score = target_hits + preserves_split - unclassified_penalty
    return score, {
        'subframe_counts': dict(counts),
        'target_hits': target_hits,
        'preserves_context_slot_split': preserves_split,
        'unclassified_penalty': unclassified_penalty,
        'score': score,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=str(DEFAULT_DB))
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    create_tables(conn)
    occurrences = load_occurrences(conn)

    all_items = []
    summary = {}
    for rule_id, fn in CONTROL_RULES.items():
        selected = []
        for k in KEYS:
            idx = (fn(k) - 1) % len(occurrences)
            row = occurrences[idx]
            selected.append(row)
            all_items.append((rule_id, k, idx, row))
        score, details = score_selected(selected)
        summary[rule_id] = details

    original = summary['K_ORIGINAL']['score']
    best_control = max(v['score'] for k, v in summary.items() if k != 'K_ORIGINAL')
    margin = original - best_control
    if margin > 0:
        decision = 'K_C68_SUBFRAME_SELECTOR_BEATS_CONTROLS_STRUCTURE_ONLY_NO_PROSE'
    elif margin == 0:
        decision = 'K_C68_SUBFRAME_SELECTOR_TIES_CONTROLS_STRUCTURE_ONLY_NO_PROSE'
    else:
        decision = 'K_C68_SUBFRAME_SELECTOR_FAILS_CONTROLS_STRUCTURE_ONLY_NO_PROSE'

    payload = {
        'keys': KEYS,
        'score_definition': 'target_book hits plus context/slot split preservation minus weak/unclassified selections',
        'summary': summary,
        'interpretation': 'Tests whether mathemagic results select useful C68 subframe rows better than controls. Structural only; no plaintext.',
    }
    cur = conn.execute('''
        insert into mathemagic_c68_subframe_selector_probe_v1_runs
        (created_at, decision, selected_count, original_score, best_control_score, original_margin, accepted_prose_gloss_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (now(), decision, len(KEYS), original, best_control, margin, 0, json.dumps(payload, ensure_ascii=True, sort_keys=True)))
    run_id = cur.lastrowid
    for rule_id, k, idx, row in all_items:
        conn.execute('''
            insert into mathemagic_c68_subframe_selector_probe_v1_items
            (run_id, rule_id, key_value, selected_index, bookid, occurrence_index, token_pos, subframe, target_book, left_context, right_context)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (run_id, rule_id, k, idx, row['bookid'], row['occurrence_index'], row['token_pos'], row['subframe'], row['target_book'], row['left_context'], row['right_context']))
    conn.commit()
    result = {
        'run_id': run_id,
        'decision': decision,
        'original_score': original,
        'best_control_score': best_control,
        'original_margin': margin,
        'accepted_prose_gloss_count': 0,
        'summary': summary,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2 if args.json else None, sort_keys=True))

if __name__ == '__main__':
    main()
