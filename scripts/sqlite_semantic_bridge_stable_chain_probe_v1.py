#!/usr/bin/env python3
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')
STABLE_CHAINS = {
    'C86_C68_NAESE_SLOT_PATH': ['C86', 'C68', 'NAESE'],
    'R02_NAESE_SLOT_BRIDGE_PATH': ['R02', 'NAESE', 'C68'],
    'VINVIN_TYPED_BRANCH': ['VINVIN', 'C86', 'R20'],
    'FNAAST_NARROW_WINDOWS': ['FNAAST', 'BTILBETA', 'O23'],
    'BENNA_LTAST_ROUTING': ['BENNA', 'LTAST'],
}


def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def create_tables(conn):
    conn.executescript('''
    create table if not exists semantic_bridge_stable_chain_probe_v1_runs (
      run_id integer primary key autoincrement,
      created_at text not null,
      decision text not null,
      benchmark_count integer not null,
      chain_match_count integer not null,
      plaintext_promotable_count integer not null,
      accepted_prose_gloss_count integer not null,
      payload_json text not null
    );
    create table if not exists semantic_bridge_stable_chain_probe_v1_items (
      run_id integer not null,
      benchmark_id text not null,
      target text not null,
      projection text not null,
      matched_chains_json text not null,
      gate_status text not null,
      plaintext_allowed integer not null,
      reason text not null,
      evidence_json text not null,
      primary key(run_id, benchmark_id)
    );
    ''')

def load_benchmarks(conn):
    rows=[]
    if conn.execute("select 1 from sqlite_master where type='table' and name='plaintext_prediction_benchmark_v1_items'").fetchone():
        # flexible schema by selecting all and using known displayed fields if present
        cols=[r[1] for r in conn.execute('pragma table_info(plaintext_prediction_benchmark_v1_items)').fetchall()]
        data=conn.execute('select * from plaintext_prediction_benchmark_v1_items where run_id=(select max(run_id) from plaintext_prediction_benchmark_v1_runs)').fetchall()
        for row in data:
            d=dict(zip(cols,row))
            bid=d.get('benchmark_id') or d.get('id') or d.get('target_id') or d.get('name') or f"row{len(rows)+1}"
            target=d.get('target') or d.get('sequence') or d.get('raw_text') or d.get('expected') or json.dumps(d,ensure_ascii=True)
            rows.append((str(bid),str(target),d))
    return rows

def external_projection(conn, target):
    hits=[]
    if conn.execute("select 1 from sqlite_master where type='table' and name='confirmed_external_row0_projection_items'").fetchone():
        for phrase_id, raw_digits, global_symbols, word_symbols_json, projection_status in conn.execute('select phrase_id, raw_digits, global_symbols, word_symbols_json, projection_status from confirmed_external_row0_projection_items'):
            if raw_digits and raw_digits in target.replace(' ','') or target.replace(' ','') in (raw_digits or ''):
                hits.append({'phrase_id':phrase_id,'global_symbols':global_symbols,'word_symbols_json':word_symbols_json,'projection_status':projection_status})
    return hits

def chain_matches(text):
    compact=text.replace(' ','').upper()
    matches=[]
    for chain, markers in STABLE_CHAINS.items():
        score=sum(1 for m in markers if m.replace(' ','').upper() in compact)
        if score >= 2:
            matches.append({'chain':chain,'marker_hits':score,'markers':markers})
    return matches

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=str(DEFAULT_DB)); ap.add_argument('--json',action='store_true'); args=ap.parse_args()
    conn=sqlite3.connect(args.db); create_tables(conn)
    benchmarks=load_benchmarks(conn)
    items=[]; match_count=0; promotable=0
    for bid,target,raw in benchmarks:
        projections=external_projection(conn,target)
        proj_text=' '.join([p.get('global_symbols') or '' for p in projections] + [target])
        matches=chain_matches(proj_text)
        if matches:
            match_count+=1
        # strict gate: projection matching stable chain is not enough; need explicit exact gloss provenance in DB
        exact_gloss=[]
        if conn.execute("select 1 from sqlite_master where type='table' and name='external_exact_gloss_search_v2_items'").fetchone():
            for row in conn.execute('select source_id, status, sequence, finding from external_exact_gloss_search_v2_items'):
                sid,status,seq,finding=row
                if seq and seq.replace(' ','') in target.replace(' ','') and 'NO_GLOSS' not in (status or '') and 'NO_GLOSS' not in (finding or ''):
                    exact_gloss.append({'source_id':sid,'status':status,'finding':finding})
        allow=1 if matches and exact_gloss else 0
        promotable+=allow
        gate='SEMANTIC_BRIDGE_PROMOTABLE' if allow else ('STRUCTURAL_MATCH_NO_EXACT_GLOSS' if matches else 'NO_STABLE_CHAIN_MATCH')
        reason='Exact external gloss plus stable-chain match.' if allow else ('Stable chain matched, but no exact external plaintext/gloss provenance.' if matches else 'Benchmark does not project onto promoted stable grammar chains.')
        items.append((bid,target,proj_text,matches,gate,allow,reason,{'raw':raw,'projections':projections,'exact_gloss':exact_gloss}))
    decision='SEMANTIC_BRIDGE_FOUND_PROMOTABLE' if promotable else 'NO_SEMANTIC_BRIDGE_PROMOTABLE_YET'
    payload={'stable_chains':STABLE_CHAINS,'policy':'require stable-chain match plus exact external gloss provenance; structural match alone cannot promote plaintext'}
    cur=conn.execute('insert into semantic_bridge_stable_chain_probe_v1_runs(created_at,decision,benchmark_count,chain_match_count,plaintext_promotable_count,accepted_prose_gloss_count,payload_json) values(?,?,?,?,?,?,?)',(now(),decision,len(benchmarks),match_count,promotable,0,json.dumps(payload,ensure_ascii=True,sort_keys=True)))
    run_id=cur.lastrowid
    for bid,target,proj,matches,gate,allow,reason,evidence in items:
        conn.execute('insert into semantic_bridge_stable_chain_probe_v1_items(run_id,benchmark_id,target,projection,matched_chains_json,gate_status,plaintext_allowed,reason,evidence_json) values(?,?,?,?,?,?,?,?,?)',(run_id,bid,target,proj,json.dumps(matches,ensure_ascii=True),gate,allow,reason,json.dumps(evidence,ensure_ascii=True,sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'benchmark_count':len(benchmarks),'chain_match_count':match_count,'plaintext_promotable_count':promotable,'accepted_prose_gloss_count':0},ensure_ascii=True,indent=2 if args.json else None,sort_keys=True))
if __name__=='__main__': main()
