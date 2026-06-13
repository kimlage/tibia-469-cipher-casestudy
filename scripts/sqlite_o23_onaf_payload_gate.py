#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any
DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def create(cur):
    cur.executescript('''
    create table if not exists o23_onaf_payload_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_contrast_run_id integer not null, positive_count integer not null, control_count integer not null,
      payload_without_o23_count integer not null, exact_payload_book_count integer not null,
      gloss_allowed_count integer not null, lexical_promotion_allowed integer not null, payload_json text not null);
    create table if not exists o23_onaf_payload_gate_items(
      run_id integer not null, item_key text not null, bookid text not null, item_type text not null,
      context_class text not null, frame_text text not null, payload_text text not null,
      decision text not null, confidence real not null, functional_label text not null, gloss_allowed integer not null,
      lexical_promotion_allowed integer not null, reason text not null, next_action text not null, evidence_json text not null,
      primary key(run_id,item_key));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    pr=rows(cur,'select * from o23_onaf_payload_contrast_probe_runs order by run_id desc limit 1')[0]
    items=rows(cur,'select * from o23_onaf_payload_contrast_items where run_id=? order by item_key',(pr['run_id'],))
    positives=[x for x in items if x['item_type']=='payload_after_o23_onaf' and x['payload_text']=='V E I N L E T F N A A S T' and x['bookid'] in ('13','38')]
    controls=[x for x in items if x not in positives]
    cur.execute('insert into o23_onaf_payload_gate_runs(created_at,decision,source_contrast_run_id,positive_count,control_count,payload_without_o23_count,exact_payload_book_count,gloss_allowed_count,lexical_promotion_allowed,payload_json) values (?,?,?,?,?,?,?,?,?,?)',(now(),'O23_ONAF_EXACT_PAYLOAD_CONTEXT_READY_NO_GLOSS',pr['run_id'],len(positives),len(controls),int(pr['payload_without_o23_count']),len({x['bookid'] for x in positives}),0,0,j({'probe':pr})))
    run_id=cur.lastrowid
    for x in items:
        pos=x in positives
        decision='O23_ONAF_VEINLETFNAAST_PAYLOAD_CONTEXT_NO_GLOSS' if pos else 'O23_ONAF_CONTROL_KEEP_SEPARATE_NO_PROMOTION'
        conf=0.77 if pos else 0.4
        label='O23/ONAF endpoint frame with exact VEINLETFNAAST payload' if pos else 'O23/ONAF control or non-exact payload'
        reason='exact O23 NAFIEI + VEINLETFNAAST branch supported by hellgate/contig contrast' if pos else 'control differs in payload/terminal/VINVIN branch; blocks generalization'
        next_action='materialize tag only for exact 13/38 branch; no O23/ONAF/VEINLET/FNAAST gloss' if pos else 'keep as control; do not tag as exact payload'
        cur.execute('insert into o23_onaf_payload_gate_items(run_id,item_key,bookid,item_type,context_class,frame_text,payload_text,decision,confidence,functional_label,gloss_allowed,lexical_promotion_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(run_id,x['item_key'],x['bookid'],x['item_type'],x['context_class'],x['frame_text'],x['payload_text'],decision,conf,label,0,0,reason,next_action,j(x)))
    con.commit(); out={'run_id':run_id,'decision':'O23_ONAF_EXACT_PAYLOAD_CONTEXT_READY_NO_GLOSS','positive_count':len(positives),'control_count':len(controls),'exact_payload_books':[x['bookid'] for x in positives],'gloss_allowed_count':0}; print(json.dumps(out,ensure_ascii=False))
    if args.discord: send('\n'.join([f"[469][o23-onaf][run={run_id}] O23/ONAF payload exato materializado",f"positivos={len(positives)} books={','.join(x['bookid'] for x in positives)} | controles={len(controls)} | gloss lexical=0",'decisão: tag só para O23 NAFIEI + VEINLETFNAAST em 13/38; controles 24/52/56/62 permanecem separados.']))
if __name__=='__main__': main()
