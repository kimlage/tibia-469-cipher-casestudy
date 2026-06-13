#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
CORE={'BOOK30_CORE_TAESESTIEN_VNSBLFSINNAI','BOOK30_CORE_ALT_ETAESESTIEN_VNSBLFSINNAI'}

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def one(cur,sql,p=()):
    r=cur.execute(sql,p).fetchone(); return dict(r) if r else {}
def create(cur):
    cur.executescript('''
    create table if not exists book30_core_context_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_probe_run_id integer not null, checked_count integer not null, accepted_book_count integer not null,
      residual_control_count integer not null, lexical_gloss_allowed integer not null, payload_json text not null);
    create table if not exists book30_core_context_gate_items(
      run_id integer not null, bookid text not null, segment_id text not null, positions_json text not null,
      decision text not null, confidence real not null, functional_label text not null,
      lexical_gloss_allowed integer not null, reason text not null, next_action text not null,
      evidence_json text not null, primary key(run_id,bookid,segment_id));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    policy=one(cur,"select * from book30_split_context_policy_items where policy_status='LOCAL_CONTEXT_READY' order by run_id desc limit 1")
    probe=one(cur,'select * from book30_split_frame_probe_runs order by run_id desc limit 1')
    if policy:
        accepted=[{'bookid':str(b),'segment_id':policy['context_id'],'positions':[],'policy':policy} for b in json.loads(policy.get('books_json') or '[]')]
        payload=json.loads(policy.get('payload_json') or '{}')
        controls=payload.get('controls') or []
        source_run_id=int(policy['run_id'])
        source_kind='book30_split_context_policy_items'
    else:
        payload=json.loads(probe.get('payload_json') or '{}'); items=payload.get('items') or []
        accepted=[x for x in items if x.get('segment_id') in CORE]
        controls=[x for x in items if x.get('segment_id') not in CORE]
        source_run_id=int(probe['run_id'])
        source_kind='book30_split_frame_probe_runs'
    accepted_books=sorted({str(x['bookid']) for x in accepted}, key=lambda z:int(z) if z.isdigit() else z)
    cur.execute('insert into book30_core_context_gate_runs(created_at,decision,source_probe_run_id,checked_count,accepted_book_count,residual_control_count,lexical_gloss_allowed,payload_json) values (?,?,?,?,?,?,?,?)',
        (now(),'BOOK30_CORE_CONTEXT_GATE_READY_NO_GLOSS',source_run_id,len(accepted)+len(controls),len(accepted_books),len(controls),0,j({'source_kind':source_kind,'accepted_books':accepted_books,'core_segment_ids':sorted(CORE),'residual_controls':controls})))
    run_id=cur.lastrowid
    for x in accepted+controls:
        seg=x['segment_id']; ok=(source_kind=='book30_split_context_policy_items') or seg in CORE; b=str(x['bookid'])
        dec='BOOK30_CORE_CONTEXT_NO_GLOSS' if ok else 'BOOK30_PREFIX_SUFFIX_RESIDUAL_CONTROL_NO_PROMOTION'
        label='Book30-family repeated core context TAESESTIEN/VNSBLFSINNAI' if ok else 'Book30 prefix/suffix residual control'
        reason='core segment repeats across local Book30-family contexts and passed SQLite policy gate' if ok else 'prefix/suffix is local residual context, not safe for family promotion'
        next_action='materialize functional context tag only; no English gloss' if ok else 'preserve as residual control; do not promote'
        cur.execute('insert into book30_core_context_gate_items(run_id,bookid,segment_id,positions_json,decision,confidence,functional_label,lexical_gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?)',
            (run_id,b,seg,j(x.get('positions') or []),dec,0.79 if ok and policy else 0.7 if ok else 0.25,label,0,reason,next_action,j({'source_kind':source_kind,'probe_decision':probe.get('decision'),'item':x})))
    con.commit()
    out={'run_id':run_id,'decision':'BOOK30_CORE_CONTEXT_GATE_READY_NO_GLOSS','accepted_books':accepted_books,'residual_control_count':len(controls),'lexical_gloss_allowed':0}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][book30-core][run={run_id}] núcleo recorrente Book30 materializado",f"aceitos={','.join(accepted_books)} | controles residuais={len(controls)} | gloss lexical=0",'sentido do avanço: marcamos uma estrutura repetida defensável entre Books 12/21/30, sem traduzir como inglês até existir anchor semântico direto.']))
if __name__=='__main__': main()
