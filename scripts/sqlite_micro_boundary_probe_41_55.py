#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
PATTERNS={
    'BOOK41_TAIL_NSTAEFIEIEFIIVFATFTFNLIBEI':['N','S','T','A','E','F','I','E','I','E','F','I','I','V','F','A','T','F','T','F','N','L','I','B','E','I'],
    'BOOK55_VFETTIITAVNEIEFIFTNI':['V','F','E','T','T','I','I','T','A','V','N','E','I','E','F','I','F','T','N','I'],
}
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def find_all(tokens, pat):
    out=[]; n=len(pat)
    for i in range(0,len(tokens)-n+1):
        if tokens[i:i+n]==pat: out.append(i)
    return out
def create(cur):
    cur.executescript('''
    create table if not exists micro_boundary_probe_41_55_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      pattern_count integer not null, hit_count integer not null, candidate_count integer not null,
      payload_json text not null);
    create table if not exists micro_boundary_probe_41_55_items(
      run_id integer not null, pattern_id text not null, bookid text not null,
      positions_json text not null, hit_status text not null, functional_tag_count integer not null,
      evidence_json text not null, primary key(run_id,pattern_id,bookid));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    tags={x['bookid']:int(x['functional_tag_count']) for x in rows(cur,'select bookid,functional_tag_count from final_honest_reading_v12_books where run_id=(select max(run_id) from final_honest_reading_v12_books)')}
    books=rows(cur,'select bookid,tokens_json from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens)')
    found=[]
    for pid,pat in PATTERNS.items():
        for b in books:
            pos=find_all(json.loads(b['tokens_json']),pat)
            if pos:
                status='TARGET_RESIDUAL' if b['bookid'] in {'41','55'} else 'TAGGED_CONTROL' if tags.get(b['bookid'],0)>0 else 'UNTAGGED_CONTROL'
                found.append((pid,b['bookid'],pos,status,tags.get(b['bookid'],0)))
    candidates=sum(1 for x in found if x[3]=='TARGET_RESIDUAL')
    decision='MICRO_BOUNDARY_PROBE_CANDIDATES_ONLY_NO_PROMOTION'
    cur.execute('insert into micro_boundary_probe_41_55_runs(created_at,decision,pattern_count,hit_count,candidate_count,payload_json) values (?,?,?,?,?,?)',
        (now(),decision,len(PATTERNS),len(found),candidates,j({'patterns':{k:''.join(v) for k,v in PATTERNS.items()}})))
    run_id=cur.lastrowid
    for pid,b,pos,status,tc in found:
        cur.execute('insert into micro_boundary_probe_41_55_items(run_id,pattern_id,bookid,positions_json,hit_status,functional_tag_count,evidence_json) values (?,?,?,?,?,?,?)',(run_id,pid,b,j(pos),status,tc,j({})))
    con.commit()
    out={'run_id':run_id,'decision':decision,'hit_count':len(found),'candidate_count':candidates,'hits':[{'pattern':x[0],'book':x[1],'status':x[3],'positions':x[2]} for x in found]}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        lines=[f"[469][micro-boundary-41-55][run={run_id}] probe sem promoção",f"patterns={len(PATTERNS)} | hits={len(found)} | targets={candidates}",'objetivo: testar se 41/55 têm micro-boundary local ou só substring genérica.']
        for h in out['hits'][:10]: lines.append(f"- {h['pattern']} em book {h['book']} ({h['status']}) pos={h['positions']}")
        send('\n'.join(lines))
if __name__=='__main__': main()
