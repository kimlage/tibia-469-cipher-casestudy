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
    create table if not exists zero_pair_local_context_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_policy_run_id integer not null, accepted_context_count integer not null,
      accepted_book_count integer not null, audit_only_context_count integer not null,
      lexical_gloss_allowed integer not null, payload_json text not null);
    create table if not exists zero_pair_local_context_gate_items(
      run_id integer not null, context_id text not null, bookid text not null, source_pair_id text not null,
      policy_status text not null, decision text not null, confidence real not null,
      functional_label text not null, lexical_gloss_allowed integer not null,
      reason text not null, next_action text not null, evidence_json text not null,
      primary key(run_id,context_id,bookid));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    policy_run=cur.execute('select max(run_id) from zero_pair_context_policy_items').fetchone()[0]
    policies=rows(cur,'select * from zero_pair_context_policy_items where run_id=? order by context_id',(policy_run,))
    accepted=[p for p in policies if p['policy_status']=='LOCAL_CONTEXT_READY']
    audit=[p for p in policies if p['policy_status']!='LOCAL_CONTEXT_READY']
    books=sorted({str(b) for p in accepted for b in json.loads(p['books_json'] or '[]')}, key=lambda z:int(z) if z.isdigit() else z)
    cur.execute('insert into zero_pair_local_context_gate_runs(created_at,decision,source_policy_run_id,accepted_context_count,accepted_book_count,audit_only_context_count,lexical_gloss_allowed,payload_json) values (?,?,?,?,?,?,?,?)',
        (now(),'ZERO_PAIR_LOCAL_CONTEXT_GATE_READY_NO_GLOSS',policy_run,len(accepted),len(books),len(audit),0,j({'accepted_books':books,'accepted_contexts':[p['context_id'] for p in accepted],'audit_contexts':[p['context_id'] for p in audit]})))
    run_id=cur.lastrowid
    for p in policies:
        ok=p['policy_status']=='LOCAL_CONTEXT_READY'
        for b in json.loads(p['books_json'] or '[]'):
            label='local pair truncation alignment' if p['context_id']=='LOCAL_PAIR_20_54_TRUNCATION_ALIGNMENT' else 'local pair FAST/BEIE microtemplate' if p['context_id']=='LOCAL_PAIR_25_39_FAST_BEIE_MICROTEMPLATE' else 'audit-only pair context'
            dec='ZERO_PAIR_LOCAL_CONTEXT_NO_GLOSS' if ok else 'ZERO_PAIR_AUDIT_ONLY_NO_PROMOTION'
            reason='pair policy is LOCAL_CONTEXT_READY and promotes only the local relation, not component gloss' if ok else 'pair policy is audit-only or context-only; do not promote'
            nxt='materialize local pair tag only; no lexical gloss' if ok else 'preserve as audit/control'
            cur.execute('insert into zero_pair_local_context_gate_items(run_id,context_id,bookid,source_pair_id,policy_status,decision,confidence,functional_label,lexical_gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?)',
                (run_id,p['context_id'],str(b),p['source_pair_id'],p['policy_status'],dec,float(p['policy_confidence']),label,0,reason,nxt,j({'policy':p})))
    con.commit()
    out={'run_id':run_id,'decision':'ZERO_PAIR_LOCAL_CONTEXT_GATE_READY_NO_GLOSS','accepted_books':books,'accepted_context_count':len(accepted),'audit_only_context_count':len(audit),'lexical_gloss_allowed':0}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][zero-pair][run={run_id}] pares locais materializados",f"aceitos={','.join(books)} | contextos aceitos={len(accepted)} | audit-only={len(audit)} | gloss lexical=0",'avanço: 20/54 e 25/39 ganharam tags funcionais locais por alinhamento, sem promover componentes como palavras.']))
if __name__=='__main__': main()
