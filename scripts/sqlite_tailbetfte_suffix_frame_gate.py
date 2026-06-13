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
    create table if not exists tailbetfte_suffix_frame_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      candidate_book_count integer not null, edge_gated_book_count integer not null, audit_only_book_count integer not null,
      global_macro_mutation_allowed integer not null, lexical_gloss_allowed integer not null, payload_json text not null);
    create table if not exists tailbetfte_suffix_frame_gate_items(
      run_id integer not null, bookid text not null, has_tailbetfte integer not null, has_f05_vnctiin_context integer not null,
      has_vnctiin_tag integer not null, edge_refs_json text not null, decision text not null, confidence real not null,
      functional_label text not null, global_macro_mutation_allowed integer not null, lexical_gloss_allowed integer not null,
      reason text not null, next_action text not null, evidence_json text not null, primary key(run_id,bookid));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    books=rows(cur,"select bookid, symbol_text, token_text from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens) and symbol_text like '%TAILBETFTE%'")
    v4=rows(cur,'select bookid,functional_tags_json,honest_text from final_honest_reading_v4_books where run_id=(select max(run_id) from final_honest_reading_v4_books)')
    v4map={str(x['bookid']):x for x in v4}
    edges=rows(cur,"select * from contig_max_overlap_edges where run_id=(select max(run_id) from contig_max_overlap_edges) and overlap_text like '%TAILBETFTE%VNCTIIN%'")
    edge_by_book={}
    for e in edges:
        for k in ('left_bookid','right_bookid'):
            edge_by_book.setdefault(str(e[k]),[]).append(f"{e['basecontigid']}:{e['edge_index']}:{e['left_bookid']}->{e['right_bookid']}")
    items=[]
    for b in books:
        bookid=str(b['bookid']); txt=b['symbol_text']; vb=v4map.get(bookid,{})
        tags=json.loads(vb.get('functional_tags_json') or '[]')
        has_ctx=('TAILBETFTE*ICEVIEFIINI*VNCTIIN' in txt) or ('TAILBETFTE*ICEVIEFIINI*VNCTIINNV' in txt)
        has_vn=any(t.get('tag_id')=='VNCTIIN_CONTEXT_FRAME' for t in tags)
        refs=edge_by_book.get(bookid,[])
        promote=has_ctx and (has_vn or refs)
        decision='TAILBETFTE_SUFFIX_FRAME_NO_GLOSS_EDGE_GATED' if promote else 'TAILBETFTE_AUDIT_ONLY_NO_GLOBAL_MACRO_MUTATION'
        conf=0.7 if promote and refs else 0.62 if promote else 0.25
        reason='TAILBETFTE suffix frame is adjacent to ICE/VNCTIIN and gated by VNCTIIN/edge support' if promote else 'TAILBETFTE occurs but lacks narrow VNCTIIN/edge-gated suffix context; macro ranks warn against gloss'
        next_action='materialize narrow suffix-frame tag only; no AILBET/TAILBE/LIBEITE global mutation' if promote else 'keep audit-only; do not mutate played/albeit gloss globally'
        items.append({'bookid':bookid,'has_ctx':has_ctx,'has_vn':has_vn,'refs':refs,'decision':decision,'conf':conf,'reason':reason,'next_action':next_action,'row':b,'tags':tags})
    edge_gated=sum(1 for x in items if x['decision'].startswith('TAILBETFTE_SUFFIX_FRAME'))
    cur.execute('insert into tailbetfte_suffix_frame_gate_runs(created_at,decision,candidate_book_count,edge_gated_book_count,audit_only_book_count,global_macro_mutation_allowed,lexical_gloss_allowed,payload_json) values (?,?,?,?,?,?,?,?)',(now(),'TAILBETFTE_SUFFIX_FRAME_GATE_READY_NO_GLOSS',len(items),edge_gated,len(items)-edge_gated,0,0,j({'edge_refs':edges})))
    run_id=cur.lastrowid
    for x in items:
        cur.execute('insert into tailbetfte_suffix_frame_gate_items(run_id,bookid,has_tailbetfte,has_f05_vnctiin_context,has_vnctiin_tag,edge_refs_json,decision,confidence,functional_label,global_macro_mutation_allowed,lexical_gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(run_id,x['bookid'],1,int(x['has_ctx']),int(x['has_vn']),j(x['refs']),x['decision'],x['conf'],'TAILBETFTE suffix frame leading into ICE/VNCTIIN',0,0,x['reason'],x['next_action'],j({'row':x['row'],'v4_tags':x['tags']})))
    con.commit(); out={'run_id':run_id,'decision':'TAILBETFTE_SUFFIX_FRAME_GATE_READY_NO_GLOSS','candidate_book_count':len(items),'edge_gated_book_count':edge_gated,'audit_only_book_count':len(items)-edge_gated,'lexical_gloss_allowed':0}; print(json.dumps(out,ensure_ascii=False))
    if args.discord: send('\n'.join([f"[469][tailbetfte][run={run_id}] TAILBETFTE frame estreito materializado",f"candidatos={len(items)} | edge/VNCTIIN-gated={edge_gated} | audit-only={len(items)-edge_gated} | gloss lexical=0",'decisão: tag só no frame TAILBETFTE -> ICE/VNCTIIN; não mutar AILBET/TAILBE/LIBEITE globalmente.']))
if __name__=='__main__': main()
