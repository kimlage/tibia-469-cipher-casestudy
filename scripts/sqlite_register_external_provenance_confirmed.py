#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists external_provenance_confirmed_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      confirmed_sequence_count integer not null, explicit_meaning_count integer not null,
      book_promotable_count integer not null, payload_json text not null);
    create table if not exists external_provenance_confirmed_items(
      run_id integer not null, target_id text not null, exact_sequence text not null, source_url text not null,
      provenance_status text not null, semantic_status text not null, book_promotable integer not null,
      recommendation text not null, payload_json text not null, primary key(run_id,target_id));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor(); create(cur)
    items=[
        ('CHAYENNE_2009_REPLY','114514519485611451908304576512282177;6612527570584','https://forum.portaltibia.com.br/topic/11420-entrevista-com-chayenne/','SOURCE_PROVENANCE_CONFIRMED','NO_EXPLICIT_MEANING',0,'use as external phrase/corpus provenance only; no book decoder promotion'),
        ('KNIGHTMARE_PHRASE','3478 67 90871 97664 3466 0 345','https://tibia.fandom.com/wiki/Knightmare_%28NPC%29','SOURCE_PROVENANCE_CONFIRMED','NO_EXPLICIT_MEANING',0,'use as phrase holdout/provenance; no plaintext promotion'),
        ('KNIGHTMARE_BONELORD_TOME_CORROBORATION','3478 67 90871 97664 3466 0 345','https://tibia.fandom.com/wiki/Bonelord_Tome','CORROBORATIVE_PROVENANCE_CONFIRMED','NO_EXPLICIT_MEANING',0,'confirms phrase importance; still not meaning'),
        ('BONELORD_NOSTALGIA_3478','3478','https://www.tibiawiki.com.br/wiki/Bonelord_%28Nostalgia%29','PARTIAL_CONTEXT_PROVENANCE','CONTEXT_ONLY_NOT_PLAINTEXT',0,'keep as partial context anchor; do not equate to BE or Bonelord as decoder truth')
    ]
    cur.execute('insert into external_provenance_confirmed_runs(created_at,decision,confirmed_sequence_count,explicit_meaning_count,book_promotable_count,payload_json) values (?,?,?,?,?,?)',
        (now(),'EXTERNAL_PROVENANCE_CONFIRMED_ZERO_SEMANTIC_PROMOTION',len(items),0,0,j({'source':'Euler research lane'})))
    run_id=cur.lastrowid
    for it in items:
        cur.execute('insert into external_provenance_confirmed_items(run_id,target_id,exact_sequence,source_url,provenance_status,semantic_status,book_promotable,recommendation,payload_json) values (?,?,?,?,?,?,?,?,?)',
            (run_id,)+it+(j({}),))
    con.commit()
    out={'run_id':run_id,'decision':'EXTERNAL_PROVENANCE_CONFIRMED_ZERO_SEMANTIC_PROMOTION','confirmed_sequence_count':len(items),'explicit_meaning_count':0,'book_promotable_count':0}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][external-provenance][run={run_id}] proveniência confirmada",f"sequências confirmadas={len(items)} | significados explícitos=0 | promoção para livros=0",'Chayenne/Knightmare/3478-context agora estão registrados como corpus externo confiável, mas sem tradução semântica.']))
if __name__=='__main__': main()
