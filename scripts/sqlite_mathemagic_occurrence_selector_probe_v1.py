#!/usr/bin/env python3
import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')
KEYS = [1, 13, 49, 94]
FAMILIES = {
    'C68_C86': ['C68', 'C86'],
    'R20_R02': ['R20', 'R02'],
    'O23_O32': ['O23', 'O32'],
}
CONTROL_RULES = {
    'K_ORIGINAL': lambda k: k,
    'SHIFT_PLUS_1': lambda k: k + 1,
    'SHIFT_PLUS_2': lambda k: k + 2,
    'DOUBLE': lambda k: k * 2,
    'REVERSE_DIGITS_PLUS_1': lambda k: int(str(k)[::-1]) + 1,
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def create_tables(conn):
    conn.executescript('''
    create table if not exists mathemagic_occurrence_selector_probe_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        family_count integer not null,
        original_signature_count integer not null,
        best_control_signature_count integer not null,
        original_margin integer not null,
        accepted_prose_gloss_count integer not null,
        payload_json text not null
    );
    create table if not exists mathemagic_occurrence_selector_probe_v1_items (
        run_id integer not null,
        rule_id text not null,
        family_id text not null,
        key_value integer not null,
        occurrence_index integer not null,
        bookid text not null,
        token_position integer not null,
        selected_token text not null,
        local_signature text not null,
        window_json text not null
    );
    create index if not exists idx_mathemagic_occurrence_selector_probe_v1_items_run on mathemagic_occurrence_selector_probe_v1_items(run_id);
    ''')


def load_occurrences(conn):
    run_id = conn.execute('select max(run_id) from row0_variant_book_tokens').fetchone()[0]
    rows = conn.execute('select bookid, tokens_json from row0_variant_book_tokens where run_id=? order by cast(bookid as integer)', (run_id,)).fetchall()
    occ = {fam: [] for fam in FAMILIES}
    for bookid, tokens_json in rows:
        tokens = json.loads(tokens_json)
        for pos, tok in enumerate(tokens):
            for fam, members in FAMILIES.items():
                if tok in members:
                    left = max(0, pos - 4)
                    right = min(len(tokens), pos + 5)
                    window = tokens[left:right]
                    signature = classify_signature(tok, window)
                    occ[fam].append({
                        'bookid': str(bookid),
                        'position': pos,
                        'token': tok,
                        'window': window,
                        'signature': signature,
                    })
    return occ


def classify_signature(tok, window):
    nearby = set(window)
    parts = [tok]
    if '*00' in nearby:
        parts.append('NEAR_BOUNDARY')
    if 'B' in nearby and 'E' in nearby and 'N' in nearby and 'A' in nearby:
        parts.append('BENNA_NEAR')
    if 'L' in nearby and 'T' in nearby and 'A' in nearby and 'S' in nearby:
        parts.append('LTAST_NEAR')
    if 'N' in nearby and 'A' in nearby and 'E' in nearby and 'S' in nearby:
        parts.append('NAESE_NEAR')
    if any(t in nearby for t in ('C68', 'C86')):
        parts.append('C_FAMILY_NEAR')
    if any(t in nearby for t in ('R20', 'R02')):
        parts.append('R_FAMILY_NEAR')
    if any(t in nearby for t in ('O23', 'O32')):
        parts.append('O_FAMILY_NEAR')
    return '|'.join(parts)


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
        rule_signatures = Counter()
        family_signatures = defaultdict(list)
        for fam, occs in occurrences.items():
            if not occs:
                continue
            for k in KEYS:
                idx = (fn(k) - 1) % len(occs)
                selected = occs[idx]
                sig = selected['signature']
                rule_signatures[(fam, sig)] += 1
                family_signatures[fam].append(sig)
                all_items.append((rule_id, fam, k, idx, selected))
        distinct_signatures = len(rule_signatures)
        repeated_family_consistency = sum(1 for fam, sigs in family_signatures.items() if len(set(sigs)) < len(sigs))
        singleton_o32_selected = sum(1 for _, fam, _, _, s in all_items if rule_id == rule_id and fam == 'O23_O32' and s['token'] == 'O32')
        summary[rule_id] = {
            'distinct_family_signatures': distinct_signatures,
            'repeated_family_consistency': repeated_family_consistency,
            'singleton_o32_selected': singleton_o32_selected,
            'selected_signature_counts': {f'{fam}:{sig}': count for (fam, sig), count in sorted(rule_signatures.items())},
        }

    original_score = summary['K_ORIGINAL']['distinct_family_signatures'] + summary['K_ORIGINAL']['repeated_family_consistency']
    control_scores = {k: v['distinct_family_signatures'] + v['repeated_family_consistency'] for k, v in summary.items() if k != 'K_ORIGINAL'}
    best_control = max(control_scores.values()) if control_scores else 0
    margin = original_score - best_control
    if margin > 0:
        decision = 'K_OCCURRENCE_SELECTOR_BEATS_CONTROLS_STRUCTURE_ONLY_NO_PROSE'
    elif margin == 0:
        decision = 'K_OCCURRENCE_SELECTOR_TIES_CONTROLS_STRUCTURE_ONLY_NO_PROSE'
    else:
        decision = 'K_OCCURRENCE_SELECTOR_FAILS_CONTROLS_STRUCTURE_ONLY_NO_PROSE'

    payload = {
        'keys': KEYS,
        'families': FAMILIES,
        'score_definition': 'distinct family signatures plus within-family repeated-signature consistency; structural only, no plaintext',
        'summary': summary,
        'interpretation': 'Tests mathemagic outputs as occurrence selectors over preserved variant families rather than absolute book indexes.',
    }
    cur = conn.execute('''
        insert into mathemagic_occurrence_selector_probe_v1_runs
        (created_at, decision, family_count, original_signature_count, best_control_signature_count, original_margin, accepted_prose_gloss_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (now(), decision, len(FAMILIES), original_score, best_control, margin, 0, json.dumps(payload, ensure_ascii=True, sort_keys=True)))
    run_id = cur.lastrowid
    for rule_id, fam, k, idx, selected in all_items:
        conn.execute('''
            insert into mathemagic_occurrence_selector_probe_v1_items
            (run_id, rule_id, family_id, key_value, occurrence_index, bookid, token_position, selected_token, local_signature, window_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (run_id, rule_id, fam, k, idx, selected['bookid'], selected['position'], selected['token'], selected['signature'], json.dumps(selected['window'], ensure_ascii=True)))
    conn.commit()
    result = {
        'run_id': run_id,
        'decision': decision,
        'original_signature_count': original_score,
        'best_control_signature_count': best_control,
        'original_margin': margin,
        'accepted_prose_gloss_count': 0,
        'summary': summary,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2 if args.json else None, sort_keys=True))

if __name__ == '__main__':
    main()
