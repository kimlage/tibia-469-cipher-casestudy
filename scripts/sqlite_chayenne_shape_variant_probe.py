#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from difflib import SequenceMatcher
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
TARGET='AEFIEIEFIIVFAEATVAT'

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def sim(a,b):
    return SequenceMatcher(a=a,b=b,autojunk=False).ratio()
def best_window(text, target):
    n=len(target); best=None
    for start in range(max(1,len(text)-n+1)):
        for wlen in {n-2,n-1,n,n+1,n+2}:
            if wlen<8 or start+wlen>len(text): continue
            w=text[start:start+wlen]
            score=sim(target,w)
            if best is None or score>best[0]:
                best=(score,start,w)
    return best or (0.0,-1,'')
def create(cur):
    cur.executescript('''
    create table if not exists chayenne_shape_variant_probe_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      target_block text not null, candidate_count integer not null, residual_candidate_count integer not null,
      payload_json text not null);
    create table if not exists chayenne_shape_variant_probe_items(
      run_id integer not null, bookid text not null, best_score real not null,
      best_pos integer not null, best_window text not null, exact_hit integer not null,
      residual_untagged integer not null, existing_functional_tag_count integer not null,
      variant_status text not null, recommendation text not null, evidence_json text not null,
      primary key(run_id,bookid));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    layer={x['bookid']:int(x['functional_tag_count']) for x in rows(cur,'select bookid,functional_tag_count from final_honest_reading_v13_books where run_id=(select max(run_id) from final_honest_reading_v13_books)')}
    books=rows(cur,'select bookid,symbol_text from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens)')
    items=[]
    for b in books:
        score,pos,win=best_window(b['symbol_text'],TARGET)
        exact=1 if TARGET in b['symbol_text'] else 0
        residual=1 if layer.get(b['bookid'],0)==0 else 0
        if exact or score>=0.78:
            status='EXACT_CHAYENNE_SHAPE' if exact else 'NEAR_CHAYENNE_SHAPE_RESIDUAL' if residual else 'NEAR_CHAYENNE_SHAPE_TAGGED_CONTROL'
            rec='already materialized external shape' if exact else 'audit as possible Chayenne-family variant; no promotion without branch controls'
            items.append((b['bookid'],round(score,4),pos,win,exact,residual,layer.get(b['bookid'],0),status,rec,j({'target':TARGET})))
    cur.execute('insert into chayenne_shape_variant_probe_runs(created_at,decision,target_block,candidate_count,residual_candidate_count,payload_json) values (?,?,?,?,?,?)',
        (now(),'CHAYENNE_SHAPE_VARIANT_PROBE_CANDIDATES_ONLY_NO_PROMOTION',TARGET,len(items),sum(1 for x in items if x[5]),j({'threshold':'exact or SequenceMatcher >= 0.78'})))
    run_id=cur.lastrowid
    for x in sorted(items,key=lambda r:(-r[1],int(r[0]))):
        cur.execute('insert into chayenne_shape_variant_probe_items(run_id,bookid,best_score,best_pos,best_window,exact_hit,residual_untagged,existing_functional_tag_count,variant_status,recommendation,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?)',(run_id,)+x)
    con.commit()
    top=[{'bookid':x[0],'score':x[1],'window':x[3],'status':x[7]} for x in sorted(items,key=lambda r:(-r[1],int(r[0])))[:10]]
    out={'run_id':run_id,'decision':'CHAYENNE_SHAPE_VARIANT_PROBE_CANDIDATES_ONLY_NO_PROMOTION','candidate_count':len(items),'residual_candidate_count':sum(1 for x in items if x[5]),'top':top}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        lines=[f"[469][chayenne-variant][run={run_id}] variantes do frame Chayenne",f"target={TARGET} | candidatos={len(items)} | resíduos={sum(1 for x in items if x[5])}",'isto não promove; só identifica variantes mecânicas próximas do holdout externo.']
        for t in top: lines.append(f"- book {t['bookid']} score={t['score']} status={t['status']} window={t['window']}")
        send('\n'.join(lines))
if __name__=='__main__': main()
