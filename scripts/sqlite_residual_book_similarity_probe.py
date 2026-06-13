#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from difflib import SequenceMatcher
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def common_prefix(a,b):
    n=0
    for x,y in zip(a,b):
        if x!=y: break
        n+=1
    return n
def common_suffix(a,b):
    n=0
    for x,y in zip(reversed(a),reversed(b)):
        if x!=y: break
        n+=1
    return n
def lcs(a,b):
    m=SequenceMatcher(a=a,b=b,autojunk=False)
    blocks=m.get_matching_blocks()
    total=sum(x.size for x in blocks)
    return total,[{'a':x.a,'b':x.b,'size':x.size} for x in blocks if x.size]
def create(cur):
    cur.executescript('''
    create table if not exists residual_book_similarity_probe_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      residual_book_count integer not null, tagged_book_count integer not null, candidate_count integer not null,
      payload_json text not null);
    create table if not exists residual_book_similarity_probe_items(
      run_id integer not null, residual_bookid text not null, matched_bookid text not null,
      residual_token_count integer not null, matched_token_count integer not null,
      lcs_len integer not null, lcs_ratio_shorter real not null, lcs_ratio_longer real not null,
      prefix_len integer not null, suffix_len integer not null, candidate_status text not null,
      next_action text not null, evidence_json text not null,
      primary key(run_id,residual_bookid,matched_bookid));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    layer=rows(cur,'select bookid,functional_tag_count from final_honest_reading_v12_books where run_id=(select max(run_id) from final_honest_reading_v12_books)')
    if not layer:
        layer=rows(cur,'select bookid,functional_tag_count from final_honest_reading_v11_books where run_id=(select max(run_id) from final_honest_reading_v11_books)')
    residual={x['bookid'] for x in layer if int(x['functional_tag_count'])==0}
    tagged={x['bookid'] for x in layer if int(x['functional_tag_count'])>0}
    toks={x['bookid']:json.loads(x['tokens_json']) for x in rows(cur,'select bookid,tokens_json from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens)')}
    candidates=[]
    for rb in sorted(residual,key=lambda z:int(z)):
        a=toks[rb]
        best=[]
        for tb in tagged:
            b=toks[tb]
            ll,blocks=lcs(a,b); shorter=min(len(a),len(b)); longer=max(len(a),len(b))
            prs=round(ll/shorter,4) if shorter else 0.0; prl=round(ll/longer,4) if longer else 0.0
            pref=common_prefix(a,b); suff=common_suffix(a,b)
            status='WEAK'
            if prs>=0.85 and ll>=12: status='LOCAL_TEMPLATE_CANDIDATE'
            elif pref>=12 or suff>=12: status='BOUNDARY_CANDIDATE'
            elif prs>=0.70 and ll>=18: status='CONTEXT_ALIGNMENT_CANDIDATE'
            if status!='WEAK':
                best.append((rb,tb,len(a),len(b),ll,prs,prl,pref,suff,status,blocks))
        best=sorted(best,key=lambda x:(x[9]!='LOCAL_TEMPLATE_CANDIDATE',-x[5],-x[4],int(x[1])))[:5]
        candidates.extend(best)
    cur.execute('insert into residual_book_similarity_probe_runs(created_at,decision,residual_book_count,tagged_book_count,candidate_count,payload_json) values (?,?,?,?,?,?)',
        (now(),'RESIDUAL_BOOK_SIMILARITY_PROBE_CANDIDATES_ONLY_NO_PROMOTION',len(residual),len(tagged),len(candidates),j({'residual_books':sorted(residual,key=lambda z:int(z))})))
    run_id=cur.lastrowid
    for x in candidates:
        rb,tb,ra,ta,ll,prs,prl,pref,suff,status,blocks=x
        nxt='open local pair policy gate with negative controls' if status=='LOCAL_TEMPLATE_CANDIDATE' else 'inspect boundary/continuation before promotion'
        cur.execute('insert into residual_book_similarity_probe_items(run_id,residual_bookid,matched_bookid,residual_token_count,matched_token_count,lcs_len,lcs_ratio_shorter,lcs_ratio_longer,prefix_len,suffix_len,candidate_status,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (run_id,rb,tb,ra,ta,ll,prs,prl,pref,suff,status,nxt,j({'lcs_blocks':blocks})))
    con.commit()
    top=[{'residual':x[0],'match':x[1],'lcs_ratio_shorter':x[5],'lcs_len':x[4],'status':x[9]} for x in candidates[:10]]
    out={'run_id':run_id,'decision':'RESIDUAL_BOOK_SIMILARITY_PROBE_CANDIDATES_ONLY_NO_PROMOTION','residual_book_count':len(residual),'candidate_count':len(candidates),'top':top}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        lines=[f"[469][residual-probe][run={run_id}] busca mecânica nos 10 livros restantes",f"residuais={len(residual)} | livros já etiquetados={len(tagged)} | candidatos={len(candidates)}",'isto não promove tradução; só abre novas hipóteses mecânicas com LCS/prefixo/sufixo.']
        for t in top[:5]: lines.append(f"- book {t['residual']} ~ {t['match']} | {t['status']} | LCS={t['lcs_len']} | ratio_curto={t['lcs_ratio_shorter']}")
        send('\n'.join(lines))
if __name__=='__main__': main()
