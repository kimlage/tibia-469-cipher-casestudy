#!/usr/bin/env python3
import argparse, json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
DEFAULT_DB=Path('./data/bonelord_operational.sqlite')

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def create(conn):
 conn.executescript('''
 create table if not exists chayenne_role_bridge_gate_v1_runs(
  run_id integer primary key autoincrement, created_at text not null, decision text not null,
  context_count integer not null, handoff_count integer not null, mixed_bridge_pass integer not null,
  plaintext_promotable_count integer not null, accepted_prose_gloss_count integer not null, payload_json text not null);
 create table if not exists chayenne_role_bridge_gate_v1_items(
  run_id integer not null, bookid text not null, role_group text not null, gate_status text not null, evidence_json text not null, primary key(run_id,bookid));
 ''')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',default=str(DEFAULT_DB)); ap.add_argument('--json',action='store_true'); args=ap.parse_args()
 conn=sqlite3.connect(args.db); create(conn)
 src=conn.execute('select max(run_id) from chayenne_shape_decoder_probe_v1_runs').fetchone()[0]
 rows=conn.execute("select bookid, observed_role, grammar_labels_json, evidence_json from chayenne_shape_decoder_probe_v1_items where run_id=? and expected_class='POSITIVE_SHAPE_OVERLAP' order by cast(bookid as integer)",(src,)).fetchall()
 items=[]; context=handoff=other=0
 for b,role,labels,ev in rows:
  text=(role+' '+labels).upper()
  has_context='VNCTIIN' in text or 'C68' in text
  has_handoff='BENNA' in text or 'LTAST' in text or 'HANDOFF' in text or 'BOUNDARY' in text
  if has_context and has_handoff:
   group='CONTEXT_AND_HANDOFF'
  elif has_context:
   group='CONTEXT_ONLY'
   context+=1
  elif has_handoff:
   group='HANDOFF_ONLY'
   handoff+=1
  else:
   group='OTHER'
   other+=1
  gate='PASS_RELATED_ROLE' if group!='OTHER' else 'FAIL_UNRELATED_ROLE'
  items.append((b,group,gate,{'observed_role':role,'labels':json.loads(labels),'source_evidence':ev}))
 mixed=int(context>=1 and handoff>=1 and other==0)
 decision='CHAYENNE_SHAPE_BRIDGES_CONTEXT_AND_HANDOFF_NO_PLAINTEXT' if mixed else 'CHAYENNE_SHAPE_ROLE_BRIDGE_HOLD_NO_PLAINTEXT'
 payload={'source_run_id':src,'interpretation':'Chayenne shared shape spans promoted context/handoff grammar roles; structural bridge only, no plaintext.'}
 cur=conn.execute('insert into chayenne_role_bridge_gate_v1_runs(created_at,decision,context_count,handoff_count,mixed_bridge_pass,plaintext_promotable_count,accepted_prose_gloss_count,payload_json) values(?,?,?,?,?,?,?,?)',(now(),decision,context,handoff,mixed,0,0,json.dumps(payload,ensure_ascii=True,sort_keys=True)))
 run_id=cur.lastrowid
 for row in items:
  conn.execute('insert into chayenne_role_bridge_gate_v1_items(run_id,bookid,role_group,gate_status,evidence_json) values(?,?,?,?,?)',(run_id,*row[:3],json.dumps(row[3],ensure_ascii=True,sort_keys=True)))
 conn.commit()
 print(json.dumps({'run_id':run_id,'decision':decision,'context_count':context,'handoff_count':handoff,'mixed_bridge_pass':mixed,'plaintext_promotable_count':0,'accepted_prose_gloss_count':0},indent=2 if args.json else None,sort_keys=True))
if __name__=='__main__': main()
