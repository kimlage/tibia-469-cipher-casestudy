#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
ACCEPT={'TIINNEF_PHASE_ANCHOR','NEIAAETTA_CONTINUITY'}

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def one(cur,sql,p=()):
    r=cur.execute(sql,p).fetchone(); return dict(r) if r else {}
def create(cur):
    cur.executescript('''
    create table if not exists book7_phase_continuity_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_probe_run_id integer not null, checked_count integer not null, accepted_item_count integer not null,
      accepted_book_count integer not null, swallow_control_count integer not null, lexical_gloss_allowed integer not null,
      payload_json text not null);
    create table if not exists book7_phase_continuity_gate_items(
      run_id integer not null, bookid text not null, pattern_id text not null, positions_json text not null,
      context_status text not null, decision text not null, confidence real not null, functional_label text not null,
      lexical_gloss_allowed integer not null, reason text not null, next_action text not null,
      evidence_json text not null, primary key(run_id,bookid,pattern_id));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    probe=one(cur,'select * from book7_phase_anchor_probe_runs order by run_id desc limit 1')
    items=rows(cur,'select * from book7_phase_anchor_items where run_id=? order by cast(bookid as integer), pattern_id',(probe['run_id'],))
    accepted=[x for x in items if x['pattern_id'] in ACCEPT]
    controls=[x for x in items if x['pattern_id'] not in ACCEPT]
    accepted_books=sorted({str(x['bookid']) for x in accepted}, key=lambda z:int(z) if z.isdigit() else z)
    cur.execute('insert into book7_phase_continuity_gate_runs(created_at,decision,source_probe_run_id,checked_count,accepted_item_count,accepted_book_count,swallow_control_count,lexical_gloss_allowed,payload_json) values (?,?,?,?,?,?,?,?,?)',
        (now(),'BOOK7_PHASE_CONTINUITY_GATE_READY_NO_GLOSS',int(probe['run_id']),len(items),len(accepted),len(accepted_books),len(controls),0,j({'accepted_patterns':sorted(ACCEPT),'accepted_books':accepted_books,'probe_decision':probe.get('decision')})))
    run_id=cur.lastrowid
    for x in items:
        ok=x['pattern_id'] in ACCEPT
        if x['pattern_id']=='TIINNEF_PHASE_ANCHOR':
            label='TIINNEF local phase anchor'
        elif x['pattern_id']=='NEIAAETTA_CONTINUITY':
            label='NEIAAETTA local continuity bridge'
        else:
            label='swallow/superset control, no promotion'
        dec='BOOK7_PHASE_CONTINUITY_NO_GLOSS' if ok else 'BOOK7_SWALLOW_CONTROL_NO_PROMOTION'
        reason='local positive probe survived against swallow controls' if ok else 'surface appears inside broader swallow/superset controls'
        next_action='materialize local functional tag only; no lexical gloss' if ok else 'preserve as negative control'
        cur.execute('insert into book7_phase_continuity_gate_items(run_id,bookid,pattern_id,positions_json,context_status,decision,confidence,functional_label,lexical_gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?)',
            (run_id,str(x['bookid']),x['pattern_id'],x['positions_json'],x['context_status'],dec,0.62 if ok else 0.2,label,0,reason,next_action,j({'probe_decision':probe.get('decision'),'item':x})))
    con.commit()
    out={'run_id':run_id,'decision':'BOOK7_PHASE_CONTINUITY_GATE_READY_NO_GLOSS','accepted_books':accepted_books,'accepted_item_count':len(accepted),'swallow_control_count':len(controls),'lexical_gloss_allowed':0}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][book7-phase][run={run_id}] continuidade Book6/Book7 materializada",f"livros com tag={','.join(accepted_books)} | controles swallow={len(controls)} | gloss lexical=0",'sentido do avanço: aceitamos só marcadores locais que sobreviveram a controles de engolimento; nada vira tradução em inglês ainda.']))
if __name__=='__main__': main()
