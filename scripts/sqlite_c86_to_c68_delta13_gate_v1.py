#!/usr/bin/env python3
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path('./data/bonelord_operational.sqlite')
POSITIVE = {'2','10','27','35','67'}
NEGATIVE = {'31','42','57'}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def create_tables(conn):
    conn.executescript('''
    create table if not exists c86_to_c68_delta13_gate_v1_runs (
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
    create table if not exists c86_to_c68_delta13_gate_v1_items (
      run_id integer not null,
      bookid text not null,
      expected_class text not null,
      nearest_delta integer,
      has_c86_eviefiin integer not null,
      has_vn_c68_tiin integer not null,
      gate_status text not null,
      evidence_json text not null,
      primary key(run_id, bookid)
    );
    ''')


def load(conn):
    run_id = conn.execute('select max(run_id) from row0_variant_book_tokens').fetchone()[0]
    books = POSITIVE | NEGATIVE
    rows = conn.execute('select bookid, tokens_json from row0_variant_book_tokens where run_id=? and bookid in (%s)' % ','.join('?' for _ in books), (run_id, *books)).fetchall()
    return {str(b): json.loads(t) for b,t in rows}


def inspect(tokens):
    c86=[]; c68=[]
    for i,tok in enumerate(tokens):
        if tok=='C86':
            right=tokens[i+1:i+9]
            c86.append({'pos':i,'eviefiin': right[:8]==['E','V','I','E','F','I','I','N'] or right[:7]==['E','V','I','E','F','I','I'], 'right':right})
        if tok=='C68':
            left=tokens[max(0,i-2):i]
            right=tokens[i+1:i+5]
            c68.append({'pos':i,'vn_tiin': left==['V','N'] and right[:3]==['T','I','I'], 'left':left, 'right':right})
    evie=[x for x in c86 if x['eviefiin']]
    vn=[x for x in c68 if x['vn_tiin']]
    deltas=[v['pos']-e['pos'] for e in evie for v in vn]
    nearest=min(deltas, key=lambda d:abs(d-13)) if deltas else None
    return evie, vn, nearest, deltas


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=str(DEFAULT_DB)); ap.add_argument('--json',action='store_true'); args=ap.parse_args()
    conn=sqlite3.connect(args.db); create_tables(conn); books=load(conn)
    pos_pass=neg_reject=0; items=[]
    for bookid in sorted(POSITIVE|NEGATIVE,key=lambda x:int(x)):
        evie,vn,nearest,deltas=inspect(books.get(bookid,[]))
        expected='POSITIVE' if bookid in POSITIVE else 'NEGATIVE'
        has_e=int(bool(evie)); has_v=int(bool(vn)); delta13=nearest==13
        if expected=='POSITIVE':
            gate='PASS_DELTA13_BRANCH' if has_e and has_v and delta13 else 'FAIL_POSITIVE_DELTA13_MISSING'
            pos_pass += gate.startswith('PASS')
        else:
            gate='PASS_NEGATIVE_REJECTED' if not (has_e and has_v and delta13) else 'FAIL_NEGATIVE_DELTA13_ACCEPTED'
            neg_reject += gate.startswith('PASS')
        items.append((bookid,expected,nearest,has_e,has_v,gate,{'eviefiin_c86':evie,'vn_c68_tiin':vn,'deltas':deltas}))
    decision='PROMOTE_DELTA13_AS_BRANCH_INVARIANT_NO_PROSE' if pos_pass==len(POSITIVE) and neg_reject==len(NEGATIVE) else 'HOLD_DELTA13_NOT_INVARIANT_NO_PROSE'
    payload={'positive_books':sorted(POSITIVE,key=lambda x:int(x)),'negative_books':sorted(NEGATIVE,key=lambda x:int(x)),'invariant':'C86_EVIEFIIN to VN-C68-TIIN at delta +13','positive_pass_count':pos_pass,'negative_reject_count':neg_reject}
    cur=conn.execute('insert into c86_to_c68_delta13_gate_v1_runs(created_at,decision,positive_pass_count,positive_total,negative_reject_count,negative_total,accepted_prose_gloss_count,payload_json) values(?,?,?,?,?,?,?,?)',(now(),decision,pos_pass,len(POSITIVE),neg_reject,len(NEGATIVE),0,json.dumps(payload,ensure_ascii=True,sort_keys=True)))
    run_id=cur.lastrowid
    for row in items:
        conn.execute('insert into c86_to_c68_delta13_gate_v1_items(run_id,bookid,expected_class,nearest_delta,has_c86_eviefiin,has_vn_c68_tiin,gate_status,evidence_json) values(?,?,?,?,?,?,?,?)',(run_id,*row[:6],json.dumps(row[6],ensure_ascii=True,sort_keys=True)))
    conn.commit()
    result={'run_id':run_id,'decision':decision,'positive_pass_count':pos_pass,'positive_total':len(POSITIVE),'negative_reject_count':neg_reject,'negative_total':len(NEGATIVE),'accepted_prose_gloss_count':0}
    print(json.dumps(result,ensure_ascii=True,indent=2 if args.json else None,sort_keys=True))
if __name__=='__main__': main()
