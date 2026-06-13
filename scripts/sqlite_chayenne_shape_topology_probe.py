#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
BLOCK='AEFIEIEFIIVFAEATVAT'
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def classify(tags):
    ids={t.get('tag_id') for t in tags}
    if 'VNCTIIN_CONTEXT_FRAME' in ids: return 'VNCTIIN_BRANCH'
    if 'BENNA_FORMULA_BRIDGE' in ids: return 'BENNA_LTAST_FORMULA_BRANCH'
    if any(str(x).startswith('RESIDUAL_TEMPLATE') for x in ids): return 'RESIDUAL_CONTINUATION_BRANCH'
    return 'UNCLASSIFIED_CHAYENNE_SHAPE'
def create(cur):
    cur.executescript('''
    create table if not exists chayenne_shape_topology_probe_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      book_count integer not null, branch_count integer not null, payload_json text not null);
    create table if not exists chayenne_shape_topology_probe_items(
      run_id integer not null, bookid text not null, block_pos integer not null,
      left_context text not null, right_context text not null, branch_class text not null,
      functional_tags_json text not null, next_action text not null, evidence_json text not null,
      primary key(run_id,bookid));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    books=rows(cur,"select v.bookid,t.symbol_text,v.functional_tags_json from final_honest_reading_v13_books v join row0_variant_book_tokens t on t.bookid=v.bookid where v.run_id=(select max(run_id) from final_honest_reading_v13_books) and t.run_id=(select max(run_id) from row0_variant_book_tokens) and v.functional_tags_json like '%CHAYENNE_EXTERNAL_SHAPE_FRAME%' order by cast(v.bookid as integer)")
    out=[]
    for b in books:
        pos=b['symbol_text'].find(BLOCK)
        tags=json.loads(b['functional_tags_json'])
        branch=classify(tags)
        left=b['symbol_text'][max(0,pos-24):pos] if pos>=0 else ''
        right=b['symbol_text'][pos+len(BLOCK):pos+len(BLOCK)+32] if pos>=0 else ''
        nxt='use as branch topology control; no semantic gloss'
        out.append((b['bookid'],pos,left,right,branch,b['functional_tags_json'],nxt,j({'block':BLOCK})))
    branches=sorted({x[4] for x in out})
    cur.execute('insert into chayenne_shape_topology_probe_runs(created_at,decision,book_count,branch_count,payload_json) values (?,?,?,?,?)',
        (now(),'CHAYENNE_SHAPE_TOPOLOGY_READY_NO_GLOSS',len(out),len(branches),j({'branches':branches,'block':BLOCK})))
    run_id=cur.lastrowid
    for x in out:
        cur.execute('insert into chayenne_shape_topology_probe_items(run_id,bookid,block_pos,left_context,right_context,branch_class,functional_tags_json,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?)',(run_id,)+x)
    con.commit()
    res={'run_id':run_id,'decision':'CHAYENNE_SHAPE_TOPOLOGY_READY_NO_GLOSS','book_count':len(out),'branches':branches}
    print(json.dumps(res,ensure_ascii=False))
    if args.discord:
        lines=[f"[469][chayenne-topology][run={run_id}] topologia do frame Chayenne",f"bloco={BLOCK} | livros={len(out)} | ramos={','.join(branches)}",'uso: separar branches mecânicos dentro de um holdout externo; gloss=0.']
        for x in out: lines.append(f"- book {x[0]} pos={x[1]} branch={x[4]}")
        send('\n'.join(lines))
if __name__=='__main__': main()
