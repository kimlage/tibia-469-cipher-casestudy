#!/usr/bin/env python3
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')

KEYS = [
    ('K1', 'MATHEMAGIC_RESULT_1', '1', 'SHADOW_STRUCTURAL_KEY', 'NO_PLAINTEXT_MEANING'),
    ('K2', 'MATHEMAGIC_RESULT_13', '13', 'SHADOW_STRUCTURAL_KEY', 'NO_PLAINTEXT_MEANING'),
    ('K3', 'MATHEMAGIC_RESULT_49', '49', 'SHADOW_STRUCTURAL_KEY', 'NO_PLAINTEXT_MEANING'),
    ('K4', 'MATHEMAGIC_RESULT_94', '94', 'SHADOW_STRUCTURAL_KEY', 'NO_PLAINTEXT_MEANING'),
]

BENCHMARKS = [
    ('B1_KNIGHTMARE_PHRASE', 'external_phrase', '3478 67 90871 97664 3466 0 345'),
    ('B2_CHAYENNE_REPLY', 'external_phrase', '114514519485611451908304576512282177;6612527570584'),
    ('B3_POLL_SEQUENCE', 'external_phrase', '663 902073 7223 67538 467 80097'),
    ('B4_BENNA_LTAST_BOOKS', 'book_family', '0,9,10,33,35,66'),
    ('B5_C68_DUAL_SUBFRAMES', 'book_family', '2,8,19,23,24,27,57,67'),
    ('B6_DISPLAY_CONTROLS', 'negative_control', '6,32,36'),
    ('B7_O32_CONTROL', 'negative_control', '49'),
]

REVERSAL_FAMILIES = {
    'C': ('68', '86'),
    'R': ('20', '02'),
    'O': ('23', '32'),
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def create_tables(conn):
    conn.executescript('''
    create table if not exists mathemagic_option_key_benchmark_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        hypothesis_id text not null,
        decision text not null,
        option_count integer not null,
        hard_pass_count integer not null,
        soft_pass_count integer not null,
        fail_count integer not null,
        accepted_prose_gloss_count integer not null,
        payload_json text not null
    );

    create table if not exists mathemagic_option_key_inventory_v1_items (
        run_id integer not null,
        key_id text not null,
        key_label text not null,
        key_value text not null,
        allowed_status text not null,
        definition_status text not null,
        evidence_json text not null,
        primary key (run_id, key_id)
    );

    create table if not exists mathemagic_option_key_gate_v1_items (
        run_id integer not null,
        gate_id text not null,
        gate_status text not null,
        reason text not null,
        evidence_json text not null,
        primary key (run_id, gate_id)
    );

    create table if not exists mathemagic_option_key_benchmark_v1_items (
        run_id integer not null,
        benchmark_id text not null,
        benchmark_type text not null,
        target text not null,
        gate_status text not null,
        predicted_key_pattern text not null,
        fail_reason text not null,
        evidence_json text not null,
        primary key (run_id, benchmark_id)
    );
    ''')


def table_exists(conn, name):
    return conn.execute("select 1 from sqlite_master where type='table' and name=?", (name,)).fetchone() is not None


def scalar(conn, sql, params=()):
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else None


def fetch_poll_evidence(conn):
    evidence = {'found_rows': []}
    if table_exists(conn, 'confirmed_external_row0_projection_items'):
        rows = conn.execute("""
            select phrase_id, global_symbols, word_symbols_json, unknown_codes_json, projection_status, recommendation
            from confirmed_external_row0_projection_items
            where phrase_id like '%POLL%'
            order by rowid
        """).fetchall()
        for r in rows:
            evidence['found_rows'].append(dict(zip(['phrase_id','global_symbols','word_symbols_json','unknown_codes_json','projection_status','recommendation'], r)))
    if table_exists(conn, 'sheet__externalrefs_v115'):
        rows = conn.execute("""
            select refname, type, numerictext, codestreambasegroups_v120, inbooks_count
            from sheet__externalrefs_v115
            where lower(refname) like '%poll%' or lower(type) like '%poll%'
            order by rowid
        """).fetchall()
        evidence['externalrefs_rows'] = [dict(zip(['refname','type','numerictext','codestreambasegroups_v120','inbooks_count'], r)) for r in rows]
    return evidence


def fetch_variant_counts(conn):
    counts = {}
    if not table_exists(conn, 'row0_variant_book_tokens'):
        return counts
    cols = [r[1] for r in conn.execute('pragma table_info(row0_variant_book_tokens)').fetchall()]
    code_col = 'code' if 'code' in cols else ('raw_code' if 'raw_code' in cols else None)
    book_col = 'book_id' if 'book_id' in cols else ('BookID' if 'BookID' in cols else None)
    if not book_col and 'bookid' in cols:
        book_col = 'bookid'
    token_col = 'token_text' if 'token_text' in cols else ('tokens_json' if 'tokens_json' in cols else None)
    if not code_col:
        if not token_col:
            return counts
        for fam, pair in REVERSAL_FAMILIES.items():
            for code in pair:
                label = f'{fam}{code}'
                if book_col:
                    row = conn.execute(f"select count(*), count(distinct {book_col}) from row0_variant_book_tokens where {token_col} like ?", (f'%{label}%',)).fetchone()
                    counts[code] = {'hit_count': row[0], 'book_count': row[1], 'family': fam, 'token_label': label}
                else:
                    row = conn.execute(f"select count(*) from row0_variant_book_tokens where {token_col} like ?", (f'%{label}%',)).fetchone()
                    counts[code] = {'hit_count': row[0], 'book_count': None, 'family': fam, 'token_label': label}
        return counts
    for fam, pair in REVERSAL_FAMILIES.items():
        for code in pair:
            if book_col:
                row = conn.execute(f"select count(*), count(distinct {book_col}) from row0_variant_book_tokens where {code_col}=?", (code,)).fetchone()
                counts[code] = {'hit_count': row[0], 'book_count': row[1], 'family': fam}
            else:
                row = conn.execute(f"select count(*) from row0_variant_book_tokens where {code_col}=?", (code,)).fetchone()
                counts[code] = {'hit_count': row[0], 'book_count': None, 'family': fam}
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=str(DEFAULT_DB))
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    create_tables(conn)

    poll_evidence = fetch_poll_evidence(conn)
    variant_counts = fetch_variant_counts(conn)
    external_poll_rows = poll_evidence.get('externalrefs_rows', [])
    poll_projection_rows = poll_evidence.get('found_rows', [])

    gates = []
    gates.append(('G0_QUARANTINE', 'PASS', 'shadow benchmark only; accepted_prose_gloss_count remains 0', {'writes_to_functional_layer': False}))
    gates.append(('G1_FOUR_KEYS_FROM_LORE', 'PASS', 'four mathemagic outputs represented as structural keys only', {'key_values': [k[2] for k in KEYS]}))
    if poll_projection_rows and len(external_poll_rows) >= 1:
        gates.append(('G2_POLL_EXISTS_AS_EXTERNAL_HOLDOUT', 'SOFT_PASS', 'poll option C exists but remains external-only and has no accepted plaintext gloss', poll_evidence))
    else:
        gates.append(('G2_POLL_EXISTS_AS_EXTERNAL_HOLDOUT', 'FAIL', 'SQLite lacks enough poll context to run a four-option contrast', poll_evidence))
    if variant_counts:
        gates.append(('G3_VARIANT_SELECTOR_TESTABLE', 'SOFT_PASS', 'C/O/R reversal families are present and can be tested as branch selectors', {'variant_counts': variant_counts}))
    else:
        gates.append(('G3_VARIANT_SELECTOR_TESTABLE', 'FAIL', 'row0 variant token table or code columns unavailable', {'variant_counts': variant_counts}))
    gates.append(('G4_NEGATIVE_CONTROLS_PROTECTED', 'PASS', 'display controls and O32 remain no-payload guardrails by construction', {'protected_benchmarks': ['B6_DISPLAY_CONTROLS', 'B7_O32_CONTROL']}))

    benchmark_items = []
    for bid, btype, target in BENCHMARKS:
        if bid == 'B3_POLL_SEQUENCE':
            status = 'PARTIAL_KEY_STRUCTURE_ONLY_NO_PROSE' if poll_projection_rows else 'FAIL_NO_POLL_PROJECTION'
            pattern = '<K?:POLL_OPTION_C_BRANCH> IV TRA SO IET FA I*A'
            reason = 'poll sequence can be used as holdout for branch/index tests, but no plaintext allowed'
            ev = poll_evidence
        elif bid == 'B5_C68_DUAL_SUBFRAMES':
            status = 'READY_FOR_VARIANT_SELECTOR_PROBE' if variant_counts else 'FAIL_NO_VARIANT_COUNTS'
            pattern = '<C68/C86_SELECTOR> with protected row0 collapse'
            reason = 'strongest mechanical target for mathemagic-as-selector rather than plaintext key'
            ev = {'variant_counts': variant_counts}
        elif bid == 'B6_DISPLAY_CONTROLS':
            status = 'PASS_NEGATIVE_CONTROL_PROTECTED'
            pattern = '<DISPLAY_ONLY:NO_PAYLOAD>'
            reason = 'must not receive any option-key payload'
            ev = {}
        elif bid == 'B7_O32_CONTROL':
            status = 'PASS_NEGATIVE_CONTROL_PROTECTED'
            pattern = '<O32_SINGLETON:DO_NOT_COLLAPSE_TO_O23>'
            reason = 'must remain singleton/audit-only'
            ev = {}
        elif bid == 'B4_BENNA_LTAST_BOOKS':
            status = 'OPEN_STRUCTURE_ONLY'
            pattern = '<BENNA/LTAST_HANDOFF> plus optional key-role pattern'
            reason = 'may test dispatch/branch framing, not prose'
            ev = {}
        else:
            status = 'HOLDOUT_NO_PLAINTEXT_PROGRESS'
            pattern = '<UNTESTED_HOLDOUT>'
            reason = 'kept as holdout until selector rule predicts structure without borrowing context'
            ev = {}
        benchmark_items.append((bid, btype, target, status, pattern, reason, ev))

    hard_pass_count = sum(1 for _, st, _, _ in gates if st == 'PASS')
    soft_pass_count = sum(1 for _, st, _, _ in gates if st == 'SOFT_PASS')
    fail_count = sum(1 for _, st, _, _ in gates if st == 'FAIL')
    decision = 'PARTIAL_KEY_STRUCTURE_ONLY_NO_PROSE' if fail_count == 0 else 'MATHEMAGIC_KEYS_SHADOW_CREATED_WITH_GAPS'
    payload = {
        'source_fact': 'Paradox Tower/A Prisoner mathemagics gives four possible 1+1 outputs: 1,13,49,94; Bonelord lore links 469 to mathemagic.',
        'interpretation': 'treat as possible structural branch selector, not plaintext key',
        'best_next_probe': 'test preserved C/O/R reversal families and poll option C as branch/index features against B1-B7',
        'prohibited': ['assigning English meanings to K1-K4', 'promoting poll option C as book plaintext', 'collapsing O32 into O23'],
    }

    cur = conn.execute('''
        insert into mathemagic_option_key_benchmark_v1_runs
        (created_at, hypothesis_id, decision, option_count, hard_pass_count, soft_pass_count, fail_count, accepted_prose_gloss_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (now(), 'MATHEMAGIC_FOUR_RESULTS_AS_STRUCTURAL_KEYS', decision, len(KEYS), hard_pass_count, soft_pass_count, fail_count, 0, json.dumps(payload, ensure_ascii=True, sort_keys=True)))
    run_id = cur.lastrowid

    for key_id, label, value, allowed, definition in KEYS:
        conn.execute('''
            insert into mathemagic_option_key_inventory_v1_items
            (run_id, key_id, key_label, key_value, allowed_status, definition_status, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?)
        ''', (run_id, key_id, label, value, allowed, definition, json.dumps({'source': 'A Prisoner mathemagics 1+1 outputs; exact plaintext role unproven'}, ensure_ascii=True)))

    for gate_id, status, reason, ev in gates:
        conn.execute('''
            insert into mathemagic_option_key_gate_v1_items
            (run_id, gate_id, gate_status, reason, evidence_json)
            values (?, ?, ?, ?, ?)
        ''', (run_id, gate_id, status, reason, json.dumps(ev, ensure_ascii=True, sort_keys=True)))

    for bid, btype, target, status, pattern, reason, ev in benchmark_items:
        conn.execute('''
            insert into mathemagic_option_key_benchmark_v1_items
            (run_id, benchmark_id, benchmark_type, target, gate_status, predicted_key_pattern, fail_reason, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (run_id, bid, btype, target, status, pattern, reason, json.dumps(ev, ensure_ascii=True, sort_keys=True)))

    conn.commit()
    result = {
        'run_id': run_id,
        'decision': decision,
        'option_count': len(KEYS),
        'hard_pass_count': hard_pass_count,
        'soft_pass_count': soft_pass_count,
        'fail_count': fail_count,
        'accepted_prose_gloss_count': 0,
        'benchmark_statuses': {b[0]: b[3] for b in benchmark_items},
    }
    print(json.dumps(result, ensure_ascii=True, indent=2 if args.json else None, sort_keys=True))

if __name__ == '__main__':
    main()
