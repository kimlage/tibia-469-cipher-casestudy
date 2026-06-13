#!/usr/bin/env python3
import argparse, datetime as dt, json, os, re, sqlite3, subprocess
from typing import Any
DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
TARGETS=('Knightmare1','Poll2014_C')
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def norm(s): return re.sub(r'[^a-z]+',' ',(s or '').lower()).strip()
def pair_digits(d):
    d=re.sub(r'\D','',d or '')
    if len(d)%2: d='0'+d
    return [d[i:i+2] for i in range(0,len(d),2)]
def create(cur):
    cur.executescript('''
    create table if not exists external_candidate_gt_crosscheck_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      candidate_run_id integer not null, target_count integer not null, gt_pass_count integer not null,
      candidate_semantic_pass_count integer not null, book_semantic_promotion_allowed integer not null,
      payload_json text not null);
    create table if not exists external_candidate_gt_crosscheck_items(
      run_id integer not null, refname text not null, digits text not null, expected_phrase text not null,
      candidate_decoded text not null, expected_norm text not null, candidate_norm text not null,
      exact_norm_match integer not null, token_overlap_pct real not null, decision text not null,
      reason text not null, next_action text not null, evidence_json text not null,
      primary key(run_id, refname));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def overlap(a,b):
    at=set(norm(a).split()); bt=set(norm(b).split())
    if not at: return 0.0
    return round(100*len(at & bt)/len(at),3)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    cand=rows(cur,'select * from external_candidate_solution_runs order by run_id desc limit 1')
    if not cand: raise SystemExit('no external candidate solution')
    cand_run=cand[0]['run_id']
    mapping={r['code']:r['letter'] for r in rows(cur,'select code, letter from external_candidate_solution_mapping where run_id=?',(cand_run,))}
    items=[]
    for ref in TARGETS:
        gt=rows(cur,'select * from sheet__externalgroundtruthcheck_v120 where refname=? order by __export_id desc limit 1',(ref,))[0]
        er=rows(cur,'select refname,digitssanitized,numerictext from sheet__externalrefs_v115 where refname=? order by __export_id desc limit 1',(ref,))[0]
        pairs=pair_digits(er['digitssanitized'])
        decoded=''.join(mapping.get(p,'?') for p in pairs)
        expected=gt['expected']
        exact=1 if norm(decoded)==norm(expected) else 0
        ov=overlap(expected, decoded)
        decision='CANDIDATE_PASSES_PHRASE_GT' if exact else 'CANDIDATE_FAILS_PHRASE_GT_NO_SEMANTIC_PROMOTION'
        reason='external full-corpus candidate must pass phrase-level GT before any semantic promotion; mechanical pair coverage is insufficient'
        items.append({'refname':ref,'digits':er['digitssanitized'],'expected':expected,'decoded':decoded,'exact':exact,'overlap':ov,'decision':decision,'reason':reason,'pairs':pairs})
    pass_count=sum(x['exact'] for x in items)
    decision='EXTERNAL_CANDIDATE_FAILS_PHRASE_GT_BLOCK_SEMANTIC_PROMOTION' if pass_count < len(items) else 'EXTERNAL_CANDIDATE_PASSES_ALL_PHRASE_GT_AUDIT_NEXT'
    cur.execute('insert into external_candidate_gt_crosscheck_runs(created_at,decision,candidate_run_id,target_count,gt_pass_count,candidate_semantic_pass_count,book_semantic_promotion_allowed,payload_json) values (?,?,?,?,?,?,?,?)',(now(),decision,cand_run,len(items),len(items),pass_count,0,j({'candidate':cand[0]})))
    run_id=cur.lastrowid
    for x in items:
        cur.execute('insert into external_candidate_gt_crosscheck_items(run_id,refname,digits,expected_phrase,candidate_decoded,expected_norm,candidate_norm,exact_norm_match,token_overlap_pct,decision,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?,?)',(run_id,x['refname'],x['digits'],x['expected'],x['decoded'],norm(x['expected']),norm(x['decoded']),x['exact'],x['overlap'],x['decision'],x['reason'],'keep external candidate shadow/audit-only unless it passes phrase GT and independent book validation',j({'pairs':x['pairs']})))
    con.commit(); out={'run_id':run_id,'decision':decision,'candidate_run_id':cand_run,'target_count':len(items),'candidate_semantic_pass_count':pass_count,'book_semantic_promotion_allowed':0}; print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        lines=[f"[469][external-candidate-gt][run={run_id}] candidato externo cruzado contra GT frase-level",f"candidate_run={cand_run} | passou={pass_count}/{len(items)} | promoção semântica para livros=0"]
        for x in items: lines.append(f"{x['refname']}: expected='{x['expected']}' | candidate='{x['decoded'][:80]}' | overlap={x['overlap']}% | {x['decision']}")
        lines.append('decisão: cobertura mecânica não basta; candidato externo fica shadow/audit-only se falhar nos GTs.')
        send('\n'.join(lines))
if __name__=='__main__': main()
