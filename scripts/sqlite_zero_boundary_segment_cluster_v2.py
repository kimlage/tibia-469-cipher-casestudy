#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any
DB_DEFAULT='./data/bonelord_operational.sqlite'; DISCORD_CHANNEL='0'; DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
MIN_LEN=4; MAX_LEN=80; MIN_BOOKS=2
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT): subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def one(cur,sql,p=()):
    r=cur.execute(sql,p).fetchone(); return dict(r) if r else {}
def create(cur):
    cur.executescript('''
    create table if not exists zero_boundary_segment_cluster_v2_runs(run_id integer primary key autoincrement,created_at text not null,source_path_run_id integer not null,segment_count integer not null,recurrent_segment_count integer not null,review_segment_count integer not null,decision text not null,next_action text not null,payload_json text not null);
    create table if not exists zero_boundary_segment_cluster_v2_items(run_id integer not null,rank integer not null,segment_digits text not null,digit_len integer not null,occurrence_count integer not null,book_count integer not null,books_json text not null,dominant_tag_id text,dominant_tag_share real not null,review_status text not null,decision text not null,evidence_json text not null,primary key(run_id,rank));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    prun=one(cur,'select max(run_id) as run_id from row0_path_reconstruction_items'); paths=rows(cur,'select bookid,reconstructed_digits from row0_path_reconstruction_items where run_id=? and selected=1 order by cast(bookid as int)',(prun.get('run_id'),))
    latest=one(cur,'select max(run_id) as run_id from final_honest_reading_v16_books'); readings={r['bookid']:r for r in rows(cur,'select bookid,functional_tags_json from final_honest_reading_v16_books where run_id=?',(latest.get('run_id'),))}
    stats={}; total=0
    for p in paths:
        for idx,seg in enumerate((p['reconstructed_digits'] or '').split('00')):
            if MIN_LEN<=len(seg)<=MAX_LEN:
                total+=1; st=stats.setdefault(seg,{'occ':0,'books':set(),'examples':[]}); st['occ']+=1; st['books'].add(p['bookid'])
                if len(st['examples'])<5: st['examples'].append({'bookid':p['bookid'],'part_index':idx})
    cand=[]
    for seg,st in stats.items():
        bc=len(st['books'])
        if bc<MIN_BOOKS: continue
        tag_books={}
        for b in st['books']:
            tags=json.loads(readings.get(b,{}).get('functional_tags_json') or '[]')
            for tag in tags:
                tid=tag.get('tag_id') or tag.get('label') or 'UNKNOWN'; tag_books.setdefault(tid,set()).add(b)
        dom,count=(None,0)
        if tag_books:
            dom,books=max(tag_books.items(),key=lambda kv:len(kv[1])); count=len(books)
        share=round(count/max(1,bc),3)
        if share>=0.6: status='EXPLAINED_BY_EXISTING_FUNCTIONAL_FAMILY'; decision='use as support feature only; no new lane'
        else: status='ZERO_SEGMENT_REVIEW_CANDIDATE_NO_GLOSS'; decision='candidate structural segment for contrast; no semantic promotion'
        score=round(bc*10+st['occ']+len(seg)/10-share*5,3)
        cand.append({'segment':seg,'digit_len':len(seg),'occurrence_count':st['occ'],'book_count':bc,'books':sorted(st['books'],key=lambda x:int(x) if x.isdigit() else 9999),'dominant_tag_id':dom,'dominant_tag_share':share,'review_status':status,'decision':decision,'score':score,'examples':st['examples'],'tag_book_counts':{k:len(v) for k,v in tag_books.items()}})
    cand.sort(key=lambda x:(x['review_status']!='ZERO_SEGMENT_REVIEW_CANDIDATE_NO_GLOSS',-x['score']))
    selected=cand[:100]; review=sum(1 for c in selected if c['review_status']=='ZERO_SEGMENT_REVIEW_CANDIDATE_NO_GLOSS')
    decision='ZERO_BOUNDARY_SEGMENTS_HAVE_REVIEW_CANDIDATES' if review else 'ZERO_BOUNDARY_SEGMENTS_ALL_EXPLAINED'; next_action='gate review candidates against dead residuals and external holdouts' if review else 'use 00 segments as existing-structure support only'
    cur.execute('insert into zero_boundary_segment_cluster_v2_runs(created_at,source_path_run_id,segment_count,recurrent_segment_count,review_segment_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?)',(now(),prun.get('run_id') or 0,total,len(cand),review,decision,next_action,j({'selected':selected})))
    run_id=cur.lastrowid
    for rank,c in enumerate(selected,1): cur.execute('insert into zero_boundary_segment_cluster_v2_items(run_id,rank,segment_digits,digit_len,occurrence_count,book_count,books_json,dominant_tag_id,dominant_tag_share,review_status,decision,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?)',(run_id,rank,c['segment'],c['digit_len'],c['occurrence_count'],c['book_count'],j(c['books']),c['dominant_tag_id'],c['dominant_tag_share'],c['review_status'],c['decision'],j(c)))
    con.commit(); print(json.dumps({'run_id':run_id,'decision':decision,'segment_count':total,'recurrent_segment_count':len(cand),'review_segment_count':review,'top':[{'segment':c['segment'],'books':c['book_count'],'dominant':c['dominant_tag_id'],'share':c['dominant_tag_share'],'status':c['review_status']} for c in selected[:5]]},ensure_ascii=False))
    if args.discord: send('\n'.join([f'[469][zero-segment-cluster-v2][run={run_id}] segmentos 00 com métrica corrigida',f'segmentos={total} | recorrentes={len(cand)} | revisão={review} | gloss=0',f'decisão={decision}',f'próxima ação: {next_action}']))
if __name__=='__main__': main()
