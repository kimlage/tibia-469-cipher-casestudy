#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
RESIDUAL={'4','34','49','56'}
SPECIAL={'*','C86','C68','O23','O32','R20','R02'}

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists hard_residual_segmentation_probe_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      residual_book_count integer not null, special_hit_count integer not null, payload_json text not null);
    create table if not exists hard_residual_segmentation_probe_items(
      run_id integer not null, bookid text not null, token_count integer not null,
      special_positions_json text not null, segment_count integer not null,
      segments_json text not null, dominant_class text not null, recommendation text not null,
      evidence_json text not null, primary key(run_id,bookid));''')
def segment(tokens):
    specials=[]
    for i,t in enumerate(tokens):
        if t in SPECIAL: specials.append({'pos':i,'token':t})
    cuts=[-1]+[s['pos'] for s in specials]+[len(tokens)]
    segs=[]
    for a,b in zip(cuts,cuts[1:]):
        if b-a-1>0:
            segs.append({'start':a+1,'end':b,'tokens':tokens[a+1:b],'text':' '.join(tokens[a+1:b]),'kind':'plain'})
        if b<len(tokens):
            segs.append({'start':b,'end':b+1,'tokens':[tokens[b]],'text':tokens[b],'kind':'special'})
    return specials,segs
def classify(specials,segs):
    toks=[s['token'] for s in specials]
    if 'O32' in toks: return 'O32_RESIDUAL_SINGLETON'
    if 'O23' in toks and 'C68' in toks: return 'O23_C68_MIXED_CONTROL'
    if 'C86' in toks and 'O23' in toks and 'R20' in toks: return 'C86_O23_R20_MIXED_SURFACE'
    if not toks: return 'PLAIN_INTERNAL_RESIDUAL'
    return 'SPECIAL_MIXED_RESIDUAL'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    books=rows(cur,'select bookid,token_count,tokens_json from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens)')
    out=[]
    for b in books:
        if b['bookid'] not in RESIDUAL: continue
        toks=json.loads(b['tokens_json']); specials,segs=segment(toks); dom=classify(specials,segs)
        rec='treat as blocked mixed-control residue; require new external/contig support' if 'MIXED' in dom or 'O32' in dom else 'search for internal recurrence/grammar only; no operator promotion'
        out.append((b['bookid'],int(b['token_count']),j(specials),len(segs),j(segs),dom,rec,j({})))
    cur.execute('insert into hard_residual_segmentation_probe_runs(created_at,decision,residual_book_count,special_hit_count,payload_json) values (?,?,?,?,?)',
        (now(),'HARD_RESIDUAL_SEGMENTATION_PROBE_NO_PROMOTION',len(out),sum(len(json.loads(x[2])) for x in out),j({})))
    run_id=cur.lastrowid
    for x in out:
        cur.execute('insert into hard_residual_segmentation_probe_items(run_id,bookid,token_count,special_positions_json,segment_count,segments_json,dominant_class,recommendation,evidence_json) values (?,?,?,?,?,?,?,?,?)',(run_id,)+x)
    con.commit()
    res={'run_id':run_id,'decision':'HARD_RESIDUAL_SEGMENTATION_PROBE_NO_PROMOTION','items':[{'bookid':x[0],'dominant_class':x[5],'specials':json.loads(x[2])} for x in out]}
    print(json.dumps(res,ensure_ascii=False))
    if args.discord:
        lines=[f"[469][hard-residual-seg][run={run_id}] segmentação dos 4 resíduos",'sem promoção; classifica estrutura por operadores especiais.']
        for it in res['items']: lines.append(f"- book {it['bookid']}: {it['dominant_class']} specials={it['specials']}")
        send('\n'.join(lines))
if __name__=='__main__': main()
