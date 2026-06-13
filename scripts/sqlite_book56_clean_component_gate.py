#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
BLOCK='NTEEAEISETEIVIFASTFNEIEINTAAETTAE'
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def positions(s,p):
    out=[]; start=0
    while True:
        i=s.find(p,start)
        if i<0: return out
        out.append(i); start=i+1
def create(cur):
    cur.executescript('''
    create table if not exists book56_clean_component_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_probe_run_id integer not null, accepted_book_count integer not null,
      control_book_count integer not null, lexical_gloss_allowed integer not null, payload_json text not null);
    create table if not exists book56_clean_component_gate_items(
      run_id integer not null, bookid text not null, positions_json text not null,
      role text not null, decision text not null, confidence real not null,
      functional_label text not null, lexical_gloss_allowed integer not null,
      reason text not null, next_action text not null, evidence_json text not null,
      primary key(run_id,bookid));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    probe=cur.execute('select max(run_id) from book56_clean_component_probe_items').fetchone()[0]
    books=rows(cur,'select bookid,symbol_text from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens)')
    hits=[]
    for b in books:
        pos=positions(b['symbol_text'],BLOCK)
        if pos: hits.append((b['bookid'],pos))
    ready=sorted([h[0] for h in hits],key=int)==['38','56']
    decision='BOOK56_CLEAN_COMPONENT_WITH_BOOK38_READY_NO_GLOSS' if ready else 'BOOK56_CLEAN_COMPONENT_NOT_READY'
    cur.execute('insert into book56_clean_component_gate_runs(created_at,decision,source_probe_run_id,accepted_book_count,control_book_count,lexical_gloss_allowed,payload_json) values (?,?,?,?,?,?,?)',
        (now(),decision,probe,1 if ready else 0,1 if ready else 0,0,j({'block':BLOCK,'hits':hits,'constraints':'excludes O23 payload, NAESE semantic gloss, and global C68'})))
    run_id=cur.lastrowid
    for bookid,pos in hits:
        ok=bookid=='56' and ready
        role='ACCEPTED_BOOK56_CLEAN_COMPONENT' if ok else 'BOOK38_CONTROL'
        dec='BOOK56_CLEAN_COMPONENT_NO_GLOSS' if ok else 'BOOK56_CLEAN_COMPONENT_CONTROL_NO_PROMOTION'
        label='Book56 clean component shared exactly with Book38' if ok else 'Book38 clean component control'
        reason='after removing O23/C68, Book56 shares a unique long component with Book38; no O23/NAESE/C68 semantics promoted' if ok else 'control occurrence for Book56 clean component'
        nxt='materialize narrow local component tag only' if ok else 'retain as control'
        cur.execute('insert into book56_clean_component_gate_items(run_id,bookid,positions_json,role,decision,confidence,functional_label,lexical_gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?)',
            (run_id,bookid,j(pos),role,dec,0.67 if ok else 0.5,label,0,reason,nxt,j({})))
    con.commit()
    out={'run_id':run_id,'decision':decision,'accepted_books':['56'] if ready else [],'controls':['38'] if ready else [],'lexical_gloss_allowed':0}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][book56-clean-gate][run={run_id}] componente limpo 56->38",f"bloco={BLOCK} | aceitos={','.join(out['accepted_books']) or 'nenhum'} | controles={','.join(out['controls']) or 'nenhum'} | gloss=0",'restrição: não promove O23, NAESE nem C68; só componente local compartilhado.']))
if __name__=='__main__': main()
