#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
TARGET_BOOK='41'
VARIANT='TAEFIEIEFIIVFATFT'

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists chayenne_near_variant_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_variant_probe_run_id integer not null, accepted_book_count integer not null,
      tagged_control_count integer not null, residual_control_count integer not null,
      lexical_gloss_allowed integer not null, payload_json text not null);
    create table if not exists chayenne_near_variant_gate_items(
      run_id integer not null, bookid text not null, best_score real not null,
      best_window text not null, variant_role text not null, decision text not null,
      confidence real not null, functional_label text not null, lexical_gloss_allowed integer not null,
      reason text not null, next_action text not null, evidence_json text not null,
      primary key(run_id,bookid));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    probe=cur.execute('select max(run_id) from chayenne_shape_variant_probe_items').fetchone()[0]
    items=rows(cur,'select * from chayenne_shape_variant_probe_items where run_id=? and best_window=?',(probe,VARIANT))
    accepted=[x for x in items if x['bookid']==TARGET_BOOK and int(x['residual_untagged'])==1]
    controls=[x for x in items if x['bookid']!=TARGET_BOOK and int(x['existing_functional_tag_count'])>0]
    residual_controls=[x for x in items if x['bookid']!=TARGET_BOOK and int(x['residual_untagged'])==1]
    decision='CHAYENNE_NEAR_VARIANT_BOOK41_READY_NO_GLOSS' if accepted and len(controls)>=3 and not residual_controls else 'CHAYENNE_NEAR_VARIANT_NOT_READY'
    cur.execute('insert into chayenne_near_variant_gate_runs(created_at,decision,source_variant_probe_run_id,accepted_book_count,tagged_control_count,residual_control_count,lexical_gloss_allowed,payload_json) values (?,?,?,?,?,?,?,?)',
        (now(),decision,probe,len(accepted),len(controls),len(residual_controls),0,j({'variant':VARIANT,'controls':[x['bookid'] for x in controls]})))
    run_id=cur.lastrowid
    for x in items:
        ok=x in accepted
        role='ACCEPTED_RESIDUAL_VARIANT' if ok else 'TAGGED_CONTROL' if int(x['existing_functional_tag_count'])>0 else 'RESIDUAL_CONTROL'
        dec='CHAYENNE_NEAR_VARIANT_NO_GLOSS' if ok else 'CHAYENNE_NEAR_VARIANT_CONTROL_NO_PROMOTION'
        conf=0.66 if ok else 0.5
        label='Chayenne near-shape variant TAEFIEIEFIIVFATFT' if ok else 'Chayenne near-shape tagged control'
        reason='unique residual shares the same near-Chayenne variant as multiple tagged controls; no semantic meaning assigned' if ok else 'control occurrence used to constrain Book41 variant promotion'
        nxt='materialize Book41 local external-shape variant tag only' if ok else 'retain as control'
        cur.execute('insert into chayenne_near_variant_gate_items(run_id,bookid,best_score,best_window,variant_role,decision,confidence,functional_label,lexical_gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?)',
            (run_id,x['bookid'],float(x['best_score']),x['best_window'],role,dec,conf,label,0,reason,nxt,j(x)))
    con.commit()
    out={'run_id':run_id,'decision':decision,'accepted_books':[x['bookid'] for x in accepted],'tagged_controls':[x['bookid'] for x in controls],'lexical_gloss_allowed':0}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][chayenne-near-variant][run={run_id}] Book41 variante Chayenne",f"aceitos={','.join(out['accepted_books']) or 'nenhum'} | controles={','.join(out['tagged_controls'])} | gloss=0",'Book41 ganha apenas tag funcional de variante externa próxima; não é tradução.']))
if __name__=='__main__': main()
