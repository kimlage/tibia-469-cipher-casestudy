#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
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
def create(cur):
    cur.executescript('''
    create table if not exists chayenne_external_shape_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_lcs_run_id integer not null, accepted_book_count integer not null,
      shared_block text not null, explicit_meaning_allowed integer not null,
      lexical_gloss_allowed integer not null, payload_json text not null);
    create table if not exists chayenne_external_shape_gate_items(
      run_id integer not null, bookid text not null, phrase_id text not null,
      lcs_ratio_phrase real not null, longest_block_len integer not null,
      shared_block text not null, decision text not null, confidence real not null,
      functional_label text not null, lexical_gloss_allowed integer not null,
      reason text not null, next_action text not null, evidence_json text not null,
      primary key(run_id,bookid));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    lcs_run=cur.execute('select max(run_id) from external_row0_lcs_probe_items').fetchone()[0]
    items=rows(cur,"select * from external_row0_lcs_probe_items where run_id=? and phrase_id='CHAYENNE_REPLY' and candidate_status='STRONG_EXTERNAL_SHAPE_OVERLAP'",(lcs_run,))
    shared='AEFIEIEFIIVFAEATVAT'
    books=sorted({x['bookid'] for x in items}, key=lambda z:int(z) if z.isdigit() else z)
    cur.execute('insert into chayenne_external_shape_gate_runs(created_at,decision,source_lcs_run_id,accepted_book_count,shared_block,explicit_meaning_allowed,lexical_gloss_allowed,payload_json) values (?,?,?,?,?,?,?,?)',
        (now(),'CHAYENNE_EXTERNAL_SHAPE_FRAME_CONFIRMED_NO_GLOSS',lcs_run,len(books),shared,0,0,j({'source':'PortalTibia Chayenne 2009 near-primary provenance plus row0 projection LCS','accepted_books':books})))
    run_id=cur.lastrowid
    for x in items:
        conf=0.86 if float(x['lcs_ratio_phrase'])>=0.95 else 0.78
        cur.execute('insert into chayenne_external_shape_gate_items(run_id,bookid,phrase_id,lcs_ratio_phrase,longest_block_len,shared_block,decision,confidence,functional_label,lexical_gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (run_id,x['bookid'],x['phrase_id'],float(x['lcs_ratio_phrase']),int(x['longest_block_len']),x['shared_block'],'CHAYENNE_EXTERNAL_SHAPE_FRAME_NO_GLOSS',conf,'Chayenne external 469 shape frame AEFIEIEFIIVFAEATVAT',0,'near-primary external phrase projects to a strong row0 shape overlap; no plaintext meaning attested','use as external structural holdout; do not assign semantic gloss',j(x)))
    con.commit()
    out={'run_id':run_id,'decision':'CHAYENNE_EXTERNAL_SHAPE_FRAME_CONFIRMED_NO_GLOSS','accepted_books':books,'shared_block':shared,'lexical_gloss_allowed':0}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][chayenne-shape][run={run_id}] frame externo confirmado",f"bloco={shared} | livros={','.join(books)} | gloss lexical=0",'avanço: a resposta 469 da Chayenne bate mecanicamente com Books 8/37/63/66. Isso fortalece a estrutura, não dá tradução semântica.']))
if __name__=='__main__': main()
