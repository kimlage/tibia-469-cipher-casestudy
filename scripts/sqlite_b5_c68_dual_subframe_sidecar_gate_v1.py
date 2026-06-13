#!/usr/bin/env python3
import argparse, json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
DEFAULT_DB=Path('./data/bonelord_operational.sqlite')
EXPECTED={
 ('8',39):'C68_VN_TIIN_CONTEXT_SUBFRAME',('19',12):'C68_VN_TIIN_CONTEXT_SUBFRAME',('23',43):'C68_VN_TIIN_CONTEXT_SUBFRAME',('24',28):'C68_VN_TIIN_CONTEXT_SUBFRAME',('57',4):'C68_VN_TIIN_CONTEXT_SUBFRAME',('57',107):'C68_VN_TIIN_CONTEXT_SUBFRAME',
 ('2',52):'C68_FAT_TIV_SLOT_SUBFRAME',
 ('57',51):'C68_TIIN_CONTEXT_WEAK',('23',89):'C68_UNCLASSIFIED_CONTEXT'
}

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def create(conn):
 conn.executescript('''
 create table if not exists b5_c68_dual_subframe_sidecar_gate_v1_runs(
  run_id integer primary key autoincrement, created_at text not null, decision text not null,
  expected_pass_count integer not null, expected_total integer not null, weak_hold_count integer not null,
  plaintext_promotable_count integer not null, accepted_prose_gloss_count integer not null, payload_json text not null);
 create table if not exists b5_c68_dual_subframe_sidecar_gate_v1_items(
  run_id integer not null, bookid text not null, token_pos integer not null, expected_subframe text not null,
  observed_subframe text not null, gate_status text not null, plaintext_allowed integer not null, evidence_json text not null,
  primary key(run_id,bookid,token_pos));
 ''')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',default=str(DEFAULT_DB)); ap.add_argument('--json',action='store_true'); args=ap.parse_args()
 conn=sqlite3.connect(args.db); create(conn)
 cr=conn.execute('select max(run_id) from c68_subframe_split_gate_v1_runs').fetchone()[0]
 obs={(str(b),int(pos)): (sub,left,right,ev) for b,pos,sub,left,right,ev in conn.execute('select bookid,token_pos,subframe,left_context,right_context,evidence_json from c68_subframe_split_gate_v1_occurrences where run_id=?',(cr,))}
 pass_count=weak_hold=0; rows=[]
 for key,expected in EXPECTED.items():
  b,pos=key; got=obs.get((b,pos))
  observed=got[0] if got else 'MISSING'
  if expected in ('C68_TIIN_CONTEXT_WEAK','C68_UNCLASSIFIED_CONTEXT'):
   gate='PASS_WEAK_OR_UNCLASSIFIED_HELD' if observed==expected else 'FAIL_WEAK_MISCLASSIFIED'
   weak_hold += gate.startswith('PASS')
  else:
   gate='PASS_EXPECTED_SUBFRAME' if observed==expected else 'FAIL_SUBFRAME_MISMATCH'
   pass_count += gate.startswith('PASS')
  rows.append((b,pos,expected,observed,gate,0,{'left_context':got[1] if got else None,'right_context':got[2] if got else None,'source_evidence':got[3] if got else None}))
 strong_total=sum(1 for v in EXPECTED.values() if v not in ('C68_TIIN_CONTEXT_WEAK','C68_UNCLASSIFIED_CONTEXT'))
 weak_total=len(EXPECTED)-strong_total
 decision='B5_C68_DUAL_SUBFRAME_SIDECAR_PASS_STRUCTURAL_NO_PROSE' if pass_count==strong_total and weak_hold==weak_total else 'B5_C68_DUAL_SUBFRAME_SIDECAR_HOLD_NO_PROSE'
 payload={'benchmark_id':'B5_C68_DUAL_SUBFRAMES','label':'sidecar structural gate only; not plaintext pass','strong_total':strong_total,'weak_total':weak_total,'source_c68_run_id':cr}
 cur=conn.execute('insert into b5_c68_dual_subframe_sidecar_gate_v1_runs(created_at,decision,expected_pass_count,expected_total,weak_hold_count,plaintext_promotable_count,accepted_prose_gloss_count,payload_json) values(?,?,?,?,?,?,?,?)',(now(),decision,pass_count,strong_total,weak_hold,0,0,json.dumps(payload,ensure_ascii=True,sort_keys=True)))
 run_id=cur.lastrowid
 for row in rows:
  conn.execute('insert into b5_c68_dual_subframe_sidecar_gate_v1_items(run_id,bookid,token_pos,expected_subframe,observed_subframe,gate_status,plaintext_allowed,evidence_json) values(?,?,?,?,?,?,?,?)',(run_id,*row[:6],json.dumps(row[6],ensure_ascii=True,sort_keys=True)))
 conn.commit()
 print(json.dumps({'run_id':run_id,'decision':decision,'expected_pass_count':pass_count,'expected_total':strong_total,'weak_hold_count':weak_hold,'weak_total':weak_total,'plaintext_promotable_count':0,'accepted_prose_gloss_count':0},indent=2 if args.json else None,sort_keys=True))
if __name__=='__main__': main()
