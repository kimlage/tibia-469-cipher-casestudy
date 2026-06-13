#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
LETTERS=set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ')
COMMON_WORDS={'the','and','you','that','this','number','everything','is','a','to','of','in','be','not','with','for','as','on'}
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT): subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def one(cur,sql,p=()):
    r=cur.execute(sql,p).fetchone(); return dict(r) if r else {}
def create(cur):
    cur.executescript('''
    create table if not exists charset_base_sweep_readability_gate_runs(run_id integer primary key autoincrement,created_at text not null,source_sweep_run_id integer not null,input_candidate_count integer not null,accepted_count integer not null,rejected_count integer not null,decision text not null,next_action text not null,payload_json text not null);
    create table if not exists charset_base_sweep_readability_gate_items(run_id integer not null,item_type text not null,item_id text not null,best_base integer not null,source_score real not null,readability_score real not null,gate_status text not null,reason text not null,decoded_preview text not null,evidence_json text not null,primary key(run_id,item_type,item_id));''')
def readability(txt):
    if not txt: return 0.0, 'empty'
    alpha_space=sum(1 for c in txt if c in LETTERS)/len(txt)
    punct=sum(1 for c in txt if not c.isalnum() and c!=' ')/len(txt)
    words=[w.strip('.,;:!?"\'()[]{}<>').lower() for w in txt.split()]
    common=sum(1 for w in words if w in COMMON_WORDS)
    long_alpha=sum(1 for w in words if len(w)>=3 and w.isalpha())
    score=round(alpha_space*60 - punct*50 + common*10 + long_alpha*2,3)
    reason=f'alpha_space={alpha_space:.3f}; punct={punct:.3f}; common={common}; long_alpha={long_alpha}'
    return score, reason
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    srun=one(cur,'select max(run_id) as run_id from charset_base_sweep_audit_items')
    candidates=rows(cur,"select * from charset_base_sweep_audit_items where run_id=? and candidate_status='CHARSET_BASE_SWEEP_STRONG_CANDIDATE_AUDIT_ONLY' order by best_score desc",(srun.get('run_id'),))
    items=[]; accepted=0
    for c in candidates:
        score,reason=readability(c['decoded_preview'] or '')
        if score>=55 and ' ' in (c['decoded_preview'] or '') and any(w in (c['decoded_preview'] or '').lower().split() for w in COMMON_WORDS):
            status='ACCEPT_READABLE_BASE_CANDIDATE_AUDIT_ONLY'; accepted+=1
        else:
            status='REJECT_GIBBERISH_BASE_OUTPUT'
        items.append({'item_type':c['item_type'],'item_id':c['item_id'],'best_base':c['best_base'],'source_score':c['best_score'],'readability_score':score,'gate_status':status,'reason':reason,'decoded_preview':c['decoded_preview'],'source':dict(c)})
    rejected=len(items)-accepted
    decision='CHARSET_BASE_READABILITY_HAS_CANDIDATES' if accepted else 'CHARSET_BASE_READABILITY_REJECTED_ALL'
    next_action='manual audit accepted candidates; no promotion' if accepted else 'stop generic charset/base route for books; keep only Vogler Numbers as method clue'
    cur.execute('insert into charset_base_sweep_readability_gate_runs(created_at,source_sweep_run_id,input_candidate_count,accepted_count,rejected_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?)',(now(),srun.get('run_id') or 0,len(items),accepted,rejected,decision,next_action,j({'items':items})))
    run_id=cur.lastrowid
    for i in items:
        cur.execute('insert into charset_base_sweep_readability_gate_items(run_id,item_type,item_id,best_base,source_score,readability_score,gate_status,reason,decoded_preview,evidence_json) values (?,?,?,?,?,?,?,?,?,?)',(run_id,i['item_type'],i['item_id'],i['best_base'],i['source_score'],i['readability_score'],i['gate_status'],i['reason'],i['decoded_preview'],j(i)))
    con.commit(); print(json.dumps({'run_id':run_id,'decision':decision,'input_candidate_count':len(items),'accepted_count':accepted,'rejected_count':rejected},ensure_ascii=False))
    if args.discord: send('\n'.join([f'[469][charset-readability-gate][run={run_id}] gate de legibilidade da varredura base/charset',f'entrada={len(items)} | aceitos={accepted} | rejeitados={rejected} | gloss=0',f'decisão={decision}','interpretação: os candidatos da varredura eram pontuação/ruído, não texto. Base/charset genérico não explica os livros.',f'próxima ação: {next_action}']))
if __name__=='__main__': main()
