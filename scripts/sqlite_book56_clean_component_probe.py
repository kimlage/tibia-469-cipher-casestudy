#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from difflib import SequenceMatcher
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
BLOCK={'O23','C68'}
PAIRS=[('56','38'),('56','25')]

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def strip_block(tokens): return [t for t in tokens if t not in BLOCK]
def blocks(a,b):
    m=SequenceMatcher(a=a,b=b,autojunk=False)
    out=[x for x in m.get_matching_blocks() if x.size]
    return out,sum(x.size for x in out),max((x.size for x in out),default=0)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists book56_clean_component_probe_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      pair_count integer not null, clean_candidate_count integer not null, payload_json text not null);
    create table if not exists book56_clean_component_probe_items(
      run_id integer not null, residual_bookid text not null, matched_bookid text not null,
      stripped_residual_len integer not null, stripped_match_len integer not null,
      lcs_total integer not null, lcs_ratio_shorter real not null, longest_block_len integer not null,
      best_shared_block text not null, candidate_status text not null, recommendation text not null,
      evidence_json text not null, primary key(run_id,residual_bookid,matched_bookid));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    toks={x['bookid']:json.loads(x['tokens_json']) for x in rows(cur,'select bookid,tokens_json from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens)')}
    items=[]
    for a,b in PAIRS:
        aa=strip_block(toks[a]); bb=strip_block(toks[b]); bl,total,longest=blocks(aa,bb)
        shorter=min(len(aa),len(bb)); ratio=round(total/shorter,4) if shorter else 0.0
        best=max(bl,key=lambda x:x.size) if bl else None
        shared=''.join(aa[best.a:best.a+best.size]) if best else ''
        status='CLEAN_COMPONENT_CANDIDATE' if ratio>=0.80 and longest>=12 else 'CONTAMINATED_OR_FRAGMENTED'
        rec='can be audited as no-gloss component only; still blocked from promotion by O23/NAESE unless independent controls appear' if status=='CLEAN_COMPONENT_CANDIDATE' else 'do not promote; clean-stripped overlap insufficient'
        items.append((a,b,len(aa),len(bb),total,ratio,longest,shared,status,rec,j({'blocks':[{'a':x.a,'b':x.b,'size':x.size} for x in bl if x.size>=4],'stripped_block_tokens':sorted(BLOCK)})))
    cur.execute('insert into book56_clean_component_probe_runs(created_at,decision,pair_count,clean_candidate_count,payload_json) values (?,?,?,?,?)',
        (now(),'BOOK56_CLEAN_COMPONENT_PROBE_NO_PROMOTION',len(items),sum(1 for x in items if x[8]=='CLEAN_COMPONENT_CANDIDATE'),j({'blocked_tokens':sorted(BLOCK)})))
    run_id=cur.lastrowid
    for x in items:
        cur.execute('insert into book56_clean_component_probe_items(run_id,residual_bookid,matched_bookid,stripped_residual_len,stripped_match_len,lcs_total,lcs_ratio_shorter,longest_block_len,best_shared_block,candidate_status,recommendation,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?)',(run_id,)+x)
    con.commit()
    out={'run_id':run_id,'decision':'BOOK56_CLEAN_COMPONENT_PROBE_NO_PROMOTION','items':[{'pair':f'{x[0]}->{x[1]}','ratio':x[5],'longest':x[6],'status':x[8],'shared':x[7]} for x in items]}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        lines=[f"[469][book56-clean][run={run_id}] probe limpo sem O23/C68",'remove O23/C68 antes de comparar 56 com 38/25; promoção=0.']
        for it in out['items']: lines.append(f"- {it['pair']} ratio={it['ratio']} longest={it['longest']} status={it['status']} shared={it['shared'][:40]}")
        send('\n'.join(lines))
if __name__=='__main__': main()
