#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
CORE='VFETTIITAV'

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def positions(s,p):
    out=[]; start=0
    while True:
        i=s.find(p,start)
        if i<0: return out
        out.append(i); start=i+1
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists book55_internal_repeat_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      core_pattern text not null, book55_occurrence_count integer not null, tagged_control_count integer not null,
      lexical_gloss_allowed integer not null, payload_json text not null);
    create table if not exists book55_internal_repeat_gate_items(
      run_id integer not null, bookid text not null, positions_json text not null,
      occurrence_count integer not null, role text not null, decision text not null,
      confidence real not null, functional_label text not null, lexical_gloss_allowed integer not null,
      reason text not null, next_action text not null, evidence_json text not null,
      primary key(run_id,bookid));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    layer={x['bookid']:int(x['functional_tag_count']) for x in rows(cur,'select bookid,functional_tag_count from final_honest_reading_v14_books where run_id=(select max(run_id) from final_honest_reading_v14_books)')}
    books=rows(cur,'select bookid,symbol_text from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens)')
    hits=[]
    for b in books:
        pos=positions(b['symbol_text'],CORE)
        if pos:
            hits.append((b['bookid'],pos,layer.get(b['bookid'],0)))
    book55=[h for h in hits if h[0]=='55'][0]
    controls=[h for h in hits if h[0]!='55' and h[2]>0]
    ready=len(book55[1])>=2 and len(controls)>=1
    decision='BOOK55_INTERNAL_REPEAT_VARIANT_READY_NO_GLOSS' if ready else 'BOOK55_INTERNAL_REPEAT_VARIANT_NOT_READY'
    cur.execute('insert into book55_internal_repeat_gate_runs(created_at,decision,core_pattern,book55_occurrence_count,tagged_control_count,lexical_gloss_allowed,payload_json) values (?,?,?,?,?,?,?)',
        (now(),decision,CORE,len(book55[1]),len(controls),0,j({'hits':[{'bookid':h[0],'positions':h[1],'functional_tag_count':h[2]} for h in hits]})))
    run_id=cur.lastrowid
    for bookid,pos,tc in hits:
        ok=bookid=='55' and ready
        role='ACCEPTED_INTERNAL_REPEAT_VARIANT' if ok else 'TAGGED_CONTROL' if tc>0 else 'UNTAGGED_CONTROL'
        dec='BOOK55_INTERNAL_REPEAT_VARIANT_NO_GLOSS' if ok else 'BOOK55_REPEAT_CONTROL_NO_PROMOTION'
        label='Book55 internal VFETTIITAV repeat/variant frame' if ok else 'VFETTIITAV repeat control'
        reason='Book55 has two internal occurrences and one tagged-control occurrence in Book16; scope is local repeat/variant only' if ok else 'control occurrence for Book55 repeat gate'
        nxt='materialize Book55 local repeat/variant tag only' if ok else 'retain as control'
        conf=0.61 if ok else 0.4
        cur.execute('insert into book55_internal_repeat_gate_items(run_id,bookid,positions_json,occurrence_count,role,decision,confidence,functional_label,lexical_gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?)',
            (run_id,bookid,j(pos),len(pos),role,dec,conf,label,0,reason,nxt,j({})))
    con.commit()
    out={'run_id':run_id,'decision':decision,'accepted_books':['55'] if ready else [],'controls':[h[0] for h in controls],'lexical_gloss_allowed':0}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][book55-repeat][run={run_id}] Book55 repeat/variant",f"core={CORE} | book55_occ={len(book55[1])} | controles={','.join(h[0] for h in controls)} | gloss=0",'Book55 ganha apenas tag de repetição/variante local; não é tradução.']))
if __name__=='__main__': main()
