#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any
DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
TARGET=('2','5','9','22','46','48','51','53')
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def create(cur):
    cur.executescript('''
    create table if not exists naese_slot_stability_gate_runs (
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      target_book_count integer not null, stable_slot_count integer not null, variant_control_count integer not null,
      gloss_allowed_count integer not null, payload_json text not null);
    create table if not exists naese_slot_stability_gate_items (
      run_id integer not null, bookid text not null, c68_context_class text, c68_edge_support text,
      naese_prefix_class text, naese_suffix_class text, decision text not null, confidence real not null,
      gloss_allowed integer not null, reason text not null, next_action text not null, evidence_json text not null,
      primary key(run_id, bookid));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    c=rows(cur,'select * from c68_fatct_slot_items where run_id=(select max(run_id) from c68_fatct_slot_items)')
    n=rows(cur,'select * from naese_ivifast_slot_items where run_id=(select max(run_id) from naese_ivifast_slot_items)')
    items=[]
    for b in TARGET:
        cr=next((x for x in c if str(x['bookid'])==b),None); nr=next((x for x in n if str(x['bookid'])==b),None)
        if cr and cr['context_class']=='CANONICAL_NAESE_FATCT_SLOT' and nr and nr['prefix_class']=='NAESE_TCT_DOMINANT_C68' and nr['suffix_class'] in ('AETTAEFTEI_STAR','AETTAEFTNE','AET_TRUNC_OR_OTHER'):
            decision='SLOT_STABLE_PREFIX_SUFFIX_LOCAL_DEPENDENT_NO_GLOSS'; conf=0.82; reason='canonical C68/FATCT frame plus dominant NAESE prefix; suffix varies by local boundary/edge'
            next_action='materialize as stable local slot; keep suffix as variable; no lexical gloss'
        elif cr and cr['context_class']=='CANONICAL_NAESE_FATCT_SLOT' and not nr:
            decision='C68_CANONICAL_WITH_NON_EXACT_IVIFAST_VARIANT_KEEP_NEGATIVE_CONTROL'; conf=0.58; reason='canonical C68/FATCT frame exists but exact IVIFAST payload is absent; variant control blocks overgeneralization'
            next_action='retain as negative/variant control for payload equivalence; no lexical gloss'
        else:
            decision='AUDIT_ONLY'; conf=0.35; reason='target did not satisfy stable slot gate'; next_action='keep audit-only'
        items.append({'bookid':b,'c68':cr,'naese':nr,'decision':decision,'confidence':conf,'reason':reason,'next_action':next_action})
    stable=sum(1 for x in items if x['decision']=='SLOT_STABLE_PREFIX_SUFFIX_LOCAL_DEPENDENT_NO_GLOSS'); variant=sum(1 for x in items if 'VARIANT' in x['decision'])
    cur.execute('insert into naese_slot_stability_gate_runs(created_at,decision,target_book_count,stable_slot_count,variant_control_count,gloss_allowed_count,payload_json) values (?,?,?,?,?,?,?)',(now(),'NAESE_SLOT_STABILITY_READY_NO_GLOSS',len(items),stable,variant,0,j({'targets':TARGET})))
    run_id=cur.lastrowid
    for x in items:
        cur.execute('insert into naese_slot_stability_gate_items(run_id,bookid,c68_context_class,c68_edge_support,naese_prefix_class,naese_suffix_class,decision,confidence,gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?)',(run_id,x['bookid'],x['c68']['context_class'] if x['c68'] else None,x['c68']['edge_support'] if x['c68'] else None,x['naese']['prefix_class'] if x['naese'] else None,x['naese']['suffix_class'] if x['naese'] else None,x['decision'],x['confidence'],0,x['reason'],x['next_action'],j({'c68':x['c68'],'naese':x['naese']})))
    con.commit(); out={'run_id':run_id,'decision':'NAESE_SLOT_STABILITY_READY_NO_GLOSS','target_book_count':len(items),'stable_slot_count':stable,'variant_control_count':variant,'gloss_allowed_count':0}; print(json.dumps(out,ensure_ascii=False))
    if args.discord: send('\n'.join([f"[469][naese-slot][run={run_id}] estabilidade NAESE/C68 materializada",f"estáveis={stable}/{len(items)} | variantes/controle={variant} | gloss lexical=0",'decisão: slot funcional estável condicionado por frame; livro 46 bloqueia generalização do payload IVIFAST; nada vira tradução em inglês.']))
if __name__=='__main__': main()
