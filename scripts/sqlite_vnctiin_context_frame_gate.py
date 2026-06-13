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
    create table if not exists vnctiin_context_frame_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_variant_run_id integer not null, occurrence_count integer not null, book_count integer not null,
      contig_edge_count integer not null, functional_tag_book_count integer not null,
      global_c68_gloss_allowed integer not null, lexical_gloss_allowed integer not null, payload_json text not null);
    create table if not exists vnctiin_context_frame_gate_items(
      run_id integer not null, bookid text not null, frame_key text not null, occurrence_role text not null,
      edge_refs_json text not null, decision text not null, confidence real not null, functional_label text not null,
      global_c68_gloss_allowed integer not null, lexical_gloss_allowed integer not null, reason text not null,
      next_action text not null, evidence_json text not null, primary key(run_id, bookid, frame_key));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    vf=rows(cur,"select * from variant_frame_items where run_id=(select max(run_id) from variant_frame_items) and frame_key='C68_VNCTIIN_FAMILY'")
    if not vf: raise SystemExit('missing C68_VNCTIIN_FAMILY')
    vf=vf[0]; books=json.loads(vf['books_json'] or '[]')
    edges=rows(cur,"select * from contig_max_overlap_edges where run_id=(select max(run_id) from contig_max_overlap_edges) and (overlap_text like '%VNCTIINNV%' or overlap_text like '%VNCTIIN%')")
    edge_by_book={str(b):[] for b in books}
    for e in edges:
        for k in ('left_bookid','right_bookid'):
            b=str(e[k])
            if b in edge_by_book:
                edge_by_book[b].append(f"{e['basecontigid']}:{e['edge_index']}:{e['left_bookid']}->{e['right_bookid']}")
    source_run=int(vf['run_id']); edge_count=sum(1 for x in edge_by_book.values() if x)
    cur.execute('insert into vnctiin_context_frame_gate_runs(created_at,decision,source_variant_run_id,occurrence_count,book_count,contig_edge_count,functional_tag_book_count,global_c68_gloss_allowed,lexical_gloss_allowed,payload_json) values (?,?,?,?,?,?,?,?,?,?)',(now(),'VNCTIIN_CONTEXT_FRAME_READY_NO_GLOBAL_C68_GLOSS',source_run,int(vf['occurrence_count']),int(vf['book_count']),edge_count,len(books),0,0,j({'variant_frame':vf,'edges':edges})))
    run_id=cur.lastrowid
    for b in books:
        refs=edge_by_book.get(str(b),[])
        conf=0.78 if refs else 0.68
        reason='VNCTIIN/C68 family marker with contig overlap support' if refs else 'VNCTIIN/C68 family marker by recurring local frame; no global C68 gloss'
        cur.execute('insert into vnctiin_context_frame_gate_items(run_id,bookid,frame_key,occurrence_role,edge_refs_json,decision,confidence,functional_label,global_c68_gloss_allowed,lexical_gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?,?)',(run_id,str(b),'C68_VNCTIIN_FAMILY','family_marker',j(refs),'VNCTIIN_CONTEXT_FRAME_NO_GLOSS',conf,'VNCTIIN local context frame / C68 family marker',0,0,reason,'materialize as local context frame only; do not mutate C68 globally; no plaintext gloss',j({'variant_frame':vf,'edge_refs':refs})))
    con.commit(); out={'run_id':run_id,'decision':'VNCTIIN_CONTEXT_FRAME_READY_NO_GLOBAL_C68_GLOSS','occurrence_count':int(vf['occurrence_count']),'book_count':int(vf['book_count']),'contig_edge_book_count':edge_count,'functional_tag_book_count':len(books),'lexical_gloss_allowed':0}; print(json.dumps(out,ensure_ascii=False))
    if args.discord: send('\n'.join([f"[469][vnctiin-gate][run={run_id}] VNCTIIN/C68 frame materializado",f"occ={vf['occurrence_count']} | livros={vf['book_count']} | livros com edge={edge_count} | gloss C68 global=0 | gloss lexical=0",'decisão: usar como frame local/family marker; não traduzir C68 nem VNCTIIN como palavras.']))
if __name__=='__main__': main()
