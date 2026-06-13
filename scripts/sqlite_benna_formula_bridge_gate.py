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
    create table if not exists benna_formula_bridge_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_core_run_id integer not null, checked_count integer not null, clean_bridge_count integer not null,
      variant_or_residual_count integer not null, formula_only integer not null, lexical_gloss_allowed integer not null,
      payload_json text not null);
    create table if not exists benna_formula_bridge_gate_items(
      run_id integer not null, bookid text not null, target_class text not null, prefix_class text not null,
      suffix_class text not null, has_ltast_tail integer not null, functional_class text not null,
      decision text not null, confidence real not null, functional_label text not null, formula_only integer not null,
      lexical_gloss_allowed integer not null, reason text not null, next_action text not null, evidence_json text not null,
      primary key(run_id, bookid));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT): subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    src=rows(cur,'select * from benna_core_vs_ltast_tail_probe_runs order by run_id desc limit 1')[0]
    items=rows(cur,'select * from benna_core_vs_ltast_tail_items where run_id=? order by cast(bookid as integer)',(src['run_id'],))
    clean=[x for x in items if x['functional_class']=='clean_bridge_with_tail' and int(x['has_strong_boundary_tail'])==1]
    cur.execute('insert into benna_formula_bridge_gate_runs(created_at,decision,source_core_run_id,checked_count,clean_bridge_count,variant_or_residual_count,formula_only,lexical_gloss_allowed,payload_json) values (?,?,?,?,?,?,?,?,?)',(now(),'BENNA_FORMULA_BRIDGE_GATE_READY_FORMULA_ONLY_NO_GLOSS',src['run_id'],len(items),len(clean),len(items)-len(clean),1,0,j({'source_run':src})))
    run_id=cur.lastrowid
    for x in items:
        ok=x in clean
        dec='BENNA_FORMULA_BRIDGE_CLEAN_WITH_TAIL_NO_GLOSS' if ok else 'BENNA_VARIANT_OR_RESIDUAL_FORMULA_AUDIT_ONLY'
        conf=0.72 if ok else 0.38
        label='BENNA formula/concordance bridge with LTAST boundary tail' if ok else 'BENNA formula variant/residual context'
        reason='core/suffix concordance survives LTAST tail holdout' if ok else 'variant/residual context blocks clean formula tag or broad prose reading'
        next_action='materialize formula/concordance tag only; no prose/gloss' if ok else 'keep formula/audit-only; no lexical promotion'
        cur.execute('insert into benna_formula_bridge_gate_items(run_id,bookid,target_class,prefix_class,suffix_class,has_ltast_tail,functional_class,decision,confidence,functional_label,formula_only,lexical_gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(run_id,x['bookid'],x['target_class'],x['prefix_class'],x['suffix_class'],x['has_ltast_tail'],x['functional_class'],dec,conf,label,1,0,reason,next_action,j(x)))
    con.commit(); out={'run_id':run_id,'decision':'BENNA_FORMULA_BRIDGE_GATE_READY_FORMULA_ONLY_NO_GLOSS','checked_count':len(items),'clean_bridge_count':len(clean),'variant_or_residual_count':len(items)-len(clean),'lexical_gloss_allowed':0}; print(json.dumps(out,ensure_ascii=False))
    if args.discord: send('\n'.join([f"[469][benna-formula][run={run_id}] BENNA fórmula/concordância materializada",f"clean_bridge={len(clean)} | variantes/residuais={len(items)-len(clean)} | gloss lexical=0",'decisão: BENNA pode ser tag funcional de fórmula/concordância, nunca prosa ou tradução lexical.']))
if __name__=='__main__': main()
