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
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def best_blocks(a,b):
    m=SequenceMatcher(a=list(a),b=list(b),autojunk=False)
    blocks=[x for x in m.get_matching_blocks() if x.size]
    total=sum(x.size for x in blocks)
    longest=max((x.size for x in blocks), default=0)
    longest_block=max(blocks,key=lambda x:x.size) if blocks else None
    return total,longest,longest_block,blocks
def create(cur):
    cur.executescript('''
    create table if not exists external_row0_lcs_probe_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      phrase_count integer not null, candidate_count integer not null, payload_json text not null);
    create table if not exists external_row0_lcs_probe_items(
      run_id integer not null, phrase_id text not null, bookid text not null,
      phrase_len integer not null, book_len integer not null, lcs_total integer not null,
      lcs_ratio_phrase real not null, longest_block_len integer not null,
      phrase_pos integer, book_pos integer, shared_block text not null,
      candidate_status text not null, recommendation text not null, evidence_json text not null,
      primary key(run_id,phrase_id,bookid));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    phrases=rows(cur,'select phrase_id,global_symbols from confirmed_external_row0_projection_items where run_id=(select max(run_id) from confirmed_external_row0_projection_items)')
    books=rows(cur,'select bookid,symbol_text from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens)')
    candidates=[]
    for p in phrases:
        a=p['global_symbols']
        for b in books:
            total,longest,lb,blocks=best_blocks(a,b['symbol_text'])
            ratio=round(total/len(a),4) if a else 0.0
            status='STRONG_EXTERNAL_SHAPE_OVERLAP' if ratio>=0.85 and longest>=12 else 'LOCAL_BLOCK_OVERLAP' if longest>=18 else 'WEAK'
            if status!='WEAK':
                shared=a[lb.a:lb.a+lb.size] if lb else ''
                candidates.append((p['phrase_id'],b['bookid'],len(a),len(b['symbol_text']),total,ratio,longest,lb.a if lb else None,lb.b if lb else None,shared,status,'use as mechanical shape holdout only; no semantic gloss',j({'blocks':[{'phrase_pos':x.a,'book_pos':x.b,'size':x.size} for x in blocks if x.size>=4]})))
    candidates=sorted(candidates,key=lambda x:(x[0],-x[5],-x[6],int(x[1])))[:200]
    cur.execute('insert into external_row0_lcs_probe_runs(created_at,decision,phrase_count,candidate_count,payload_json) values (?,?,?,?,?)',
        (now(),'EXTERNAL_ROW0_LCS_PROBE_HOLDOUTS_NO_SEMANTIC_PROMOTION',len(phrases),len(candidates),j({})))
    run_id=cur.lastrowid
    for x in candidates:
        cur.execute('insert into external_row0_lcs_probe_items(run_id,phrase_id,bookid,phrase_len,book_len,lcs_total,lcs_ratio_phrase,longest_block_len,phrase_pos,book_pos,shared_block,candidate_status,recommendation,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(run_id,)+x)
    con.commit()
    top=[{'phrase':x[0],'book':x[1],'ratio':x[5],'longest':x[6],'shared':x[9]} for x in candidates[:8]]
    out={'run_id':run_id,'decision':'EXTERNAL_ROW0_LCS_PROBE_HOLDOUTS_NO_SEMANTIC_PROMOTION','candidate_count':len(candidates),'top':top}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        lines=[f"[469][external-row0-lcs][run={run_id}] LCS externo vs livros",f"candidatos={len(candidates)} | promoção semântica=0",'uso: identificar sobreposição mecânica; não traduzir.']
        for t in top: lines.append(f"- {t['phrase']} ~ book {t['book']} | ratio={t['ratio']} | longest={t['longest']} | block={t['shared'][:30]}")
        send('\n'.join(lines))
if __name__=='__main__': main()
