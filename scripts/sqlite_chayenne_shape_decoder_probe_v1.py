#!/usr/bin/env python3
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')
PHRASE_ID = 'CHAYENNE_REPLY'
SHARED_BLOCK = 'AEFIEIEFIIVFAEATVAT'
POSITIVE_BOOKS = {'8','37','63','66'}
NEGATIVE_BOOKS = {'2','22','28','32','51','53','56','67'}


def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def create_tables(conn):
    conn.executescript('''
    create table if not exists chayenne_shape_decoder_probe_v1_runs (
      run_id integer primary key autoincrement,
      created_at text not null,
      decision text not null,
      positive_match_count integer not null,
      positive_total integer not null,
      negative_reject_count integer not null,
      negative_total integer not null,
      plaintext_promotable_count integer not null,
      accepted_prose_gloss_count integer not null,
      payload_json text not null
    );
    create table if not exists chayenne_shape_decoder_probe_v1_items (
      run_id integer not null,
      bookid text not null,
      expected_class text not null,
      observed_role text not null,
      has_shared_block integer not null,
      grammar_labels_json text not null,
      gate_status text not null,
      plaintext_allowed integer not null,
      evidence_json text not null,
      primary key(run_id, bookid)
    );
    ''')

def compact(s): return (s or '').replace(' ','').replace('*00','*')

def load_books(conn, books):
    rows=conn.execute('select bookid, token_text from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens) and bookid in (%s)' % ','.join('?' for _ in books), tuple(books)).fetchall()
    return {str(b):compact(t) for b,t in rows}

def collect_labels(conn, bookid):
    labels=[]
    # snapshot accepted related labels
    sr=conn.execute('select max(run_id) from structural_grammar_snapshot_v1_runs').fetchone()[0]
    for nid,status,bj,summary in conn.execute('select node_id,status,books_json,summary from structural_grammar_snapshot_v1_items where run_id=?',(sr,)):
        try: bs=set(map(str,json.loads(bj)))
        except Exception: bs=set()
        if str(bookid) in bs:
            labels.append({'source':'snapshot','node_id':nid,'status':status,'summary':summary})
    # routing labels
    row=conn.execute('select route_status,routing_label from benna_ltast_routing_layer_v1_items where run_id=(select max(run_id) from benna_ltast_routing_layer_v1_runs) and bookid=?',(str(bookid),)).fetchone()
    if row: labels.append({'source':'benna_ltast','status':row[0],'label':row[1]})
    return labels

def classify(labels):
    text=' '.join(json.dumps(x,ensure_ascii=True) for x in labels)
    if 'BENNA_LTAST' in text or 'LTAST' in text or 'HANDOFF' in text or 'CONTINUATION' in text:
        return 'BENNA_LTAST_HANDOFF_SHAPE'
    if 'C68_VN_TIIN' in text or 'VNCTIIN' in text:
        return 'C68_VN_TIIN_CONTEXT_SHAPE'
    if 'NAESE' in text:
        return 'NAESE_SLOT_OR_VARIANT_SHAPE'
    if 'FNAAST' in text:
        return 'FNAAST_SHAPE'
    return 'OTHER_OR_UNLABELED_SHAPE'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=str(DEFAULT_DB)); ap.add_argument('--json',action='store_true'); args=ap.parse_args()
    conn=sqlite3.connect(args.db); create_tables(conn)
    books=POSITIVE_BOOKS|NEGATIVE_BOOKS
    texts=load_books(conn, books)
    projection=conn.execute('select global_symbols, word_symbols_json, projection_status from confirmed_external_row0_projection_items where phrase_id=?',(PHRASE_ID,)).fetchone()
    items=[]; pos=neg=prom=0
    for b in sorted(books,key=lambda x:int(x)):
        expected='POSITIVE_SHAPE_OVERLAP' if b in POSITIVE_BOOKS else 'NEGATIVE_CONTROL'
        has=SHARED_BLOCK in texts.get(b,'')
        labels=collect_labels(conn,b)
        role=classify(labels)
        if expected.startswith('POSITIVE'):
            gate='PASS_SHAPE_OVERLAP_STRUCTURAL_ONLY' if has else 'FAIL_POSITIVE_NO_BLOCK'
            pos += gate.startswith('PASS')
        else:
            gate='PASS_NEGATIVE_REJECTED' if not has else 'FAIL_NEGATIVE_HAS_BLOCK'
            neg += gate.startswith('PASS')
        # no plaintext allowed: shape overlap + no explicit Chayenne gloss
        allow=0
        items.append((b,expected,role,int(has),labels,gate,allow,{'book_compact':texts.get(b,''),'projection':projection,'shared_block':SHARED_BLOCK}))
    # Chayenne phrase itself is out-of-book and no explicit gloss, so decision can only be shape candidate
    if pos==len(POSITIVE_BOOKS) and neg==len(NEGATIVE_BOOKS):
        decision='CHAYENNE_SHAPE_CANDIDATE_ACCEPTED_NO_PLAINTEXT'
    else:
        decision='CHAYENNE_SHAPE_CANDIDATE_HOLD_NO_PLAINTEXT'
    payload={'phrase_id':PHRASE_ID,'shared_block':SHARED_BLOCK,'positive_books':sorted(POSITIVE_BOOKS,key=lambda x:int(x)),'negative_books':sorted(NEGATIVE_BOOKS,key=lambda x:int(x)),'policy':'shape overlap is mechanical only; no plaintext without explicit gloss or benchmark decoder'}
    cur=conn.execute('insert into chayenne_shape_decoder_probe_v1_runs(created_at,decision,positive_match_count,positive_total,negative_reject_count,negative_total,plaintext_promotable_count,accepted_prose_gloss_count,payload_json) values(?,?,?,?,?,?,?,?,?)',(now(),decision,pos,len(POSITIVE_BOOKS),neg,len(NEGATIVE_BOOKS),prom,0,json.dumps(payload,ensure_ascii=True,sort_keys=True)))
    run_id=cur.lastrowid
    for b,expected,role,has,labels,gate,allow,evidence in items:
        conn.execute('insert into chayenne_shape_decoder_probe_v1_items(run_id,bookid,expected_class,observed_role,has_shared_block,grammar_labels_json,gate_status,plaintext_allowed,evidence_json) values(?,?,?,?,?,?,?,?,?)',(run_id,b,expected,role,has,json.dumps(labels,ensure_ascii=True),gate,allow,json.dumps(evidence,ensure_ascii=True,sort_keys=True)))
    conn.commit()
    print(json.dumps({'run_id':run_id,'decision':decision,'positive_match_count':pos,'positive_total':len(POSITIVE_BOOKS),'negative_reject_count':neg,'negative_total':len(NEGATIVE_BOOKS),'plaintext_promotable_count':prom,'accepted_prose_gloss_count':0},ensure_ascii=True,indent=2 if args.json else None,sort_keys=True))
if __name__=='__main__': main()
