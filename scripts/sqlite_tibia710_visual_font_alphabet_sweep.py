#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any
DB_DEFAULT='./data/bonelord_operational.sqlite'; DISCORD_CHANNEL='0'; DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
# Visual order read from extracted Tibia 7.10 Linux font.pic. Space is first char of symbol row.
ALPHABET='@ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜabcdefghijklmnopqrstuvwxyzäöüß '+r'''!"#$%&'()*+,-./0123456789:;<=>?'''
COMMON={'the','and','you','that','this','number','everything','is','a','to','of','in','be','not','with','for','as','on','tibia'}
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT): subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def to_base(s,base,alphabet=ALPHABET):
    n=int(s)
    if n==0: return alphabet[0]
    out=[]
    while n:
        n,r=divmod(n,base); out.append(alphabet[r])
    return ''.join(reversed(out))
def score_text(txt):
    if not txt: return -999,'empty'
    alpha=sum(1 for c in txt if c.isalpha() or c==' ')/len(txt); punct=sum(1 for c in txt if not c.isalnum() and c!=' ')/len(txt); space=txt.count(' ')/len(txt)
    words=[w.strip('.,;:!?"\'()[]{}<>').lower() for w in txt.split()]
    common=sum(1 for w in words if w in COMMON); long_alpha=sum(1 for w in words if len(w)>=3 and w.isalpha())
    sc=round(alpha*70+min(space,0.22)*45+common*15+long_alpha*3-punct*70,3); return sc,f'alpha={alpha:.3f};space={space:.3f};punct={punct:.3f};common={common};long_alpha={long_alpha}'
def create(cur):
    cur.executescript('''
    create table if not exists tibia710_visual_font_alphabet_sweep_runs(run_id integer primary key autoincrement,created_at text not null,alphabet text not null,alphabet_len integer not null,item_count integer not null,strong_count integer not null,decision text not null,next_action text not null,payload_json text not null);
    create table if not exists tibia710_visual_font_alphabet_sweep_items(run_id integer not null,item_type text not null,item_id text not null,best_base integer not null,best_score real not null,decoded_preview text not null,readability_reason text not null,candidate_status text not null,evidence_json text not null,primary key(run_id,item_type,item_id));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args(); con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    items=[]
    for b in rows(cur,'select distinct bookid item_id,digits from sheet__books order by cast(bookid as int)'): items.append({'item_type':'book','item_id':b['item_id'],'digits':b['digits']})
    fr=rows(cur,'select max(run_id) run_id from npc_sequence_frontier')[0]['run_id']
    for s in rows(cur,'select sequence_id item_id,digits from npc_sequence_frontier where run_id=? and digits is not null',(fr,)): items.append({'item_type':'external','item_id':s['item_id'],'digits':''.join(ch for ch in s['digits'] if ch.isdigit())})
    results=[]; strong=0
    # Test base exactly alphabet_len and nearby in case first glyph @ is not numeric zero or space row includes/excludes blank.
    bases=sorted(set([len(ALPHABET),len(ALPHABET)-1,len(ALPHABET)-2,90,91,92,93,94,95,96]))
    for item in items:
        best={'base':0,'score':-999,'text':'','reason':''}
        for base in bases:
            if base<2 or base>len(ALPHABET): continue
            try: txt=to_base(item['digits'],base); sc,reason=score_text(txt)
            except Exception: continue
            if sc>best['score']: best={'base':base,'score':sc,'text':txt,'reason':reason}
        status='VISUAL_FONT_ALPHABET_STRONG_CANDIDATE_AUDIT_ONLY' if best['score']>=60 and any(w in best['text'].lower().split() for w in COMMON) and len(best['text'])>=8 else 'VISUAL_FONT_ALPHABET_NO_READABLE_TEXT'
        if status.startswith('VISUAL_FONT_ALPHABET_STRONG'): strong+=1
        results.append({'item_type':item['item_type'],'item_id':item['item_id'],'best_base':best['base'],'best_score':best['score'],'decoded_preview':best['text'][:200],'readability_reason':best['reason'],'candidate_status':status})
    decision='VISUAL_FONT_ALPHABET_HAS_CANDIDATES' if strong else 'VISUAL_FONT_ALPHABET_NO_TRANSLATION_SIGNAL'; next_action='manual audit candidates only' if strong else 'visual font alphabet does not directly decode books/holdouts'
    cur.execute('insert into tibia710_visual_font_alphabet_sweep_runs(created_at,alphabet,alphabet_len,item_count,strong_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?)',(now(),ALPHABET,len(ALPHABET),len(items),strong,decision,next_action,j({'bases_tested':bases,'items':results})))
    run_id=cur.lastrowid
    for r in results: cur.execute('insert into tibia710_visual_font_alphabet_sweep_items(run_id,item_type,item_id,best_base,best_score,decoded_preview,readability_reason,candidate_status,evidence_json) values (?,?,?,?,?,?,?,?,?)',(run_id,r['item_type'],r['item_id'],r['best_base'],r['best_score'],r['decoded_preview'],r['readability_reason'],r['candidate_status'],j(r)))
    con.commit(); print(json.dumps({'run_id':run_id,'decision':decision,'alphabet_len':len(ALPHABET),'strong_count':strong,'top':[{'id':r['item_id'],'type':r['item_type'],'base':r['best_base'],'score':r['best_score'],'preview':r['decoded_preview'][:80],'status':r['candidate_status']} for r in sorted(results,key=lambda x:x['best_score'],reverse=True)[:10]]},ensure_ascii=False))
    if args.discord:
        top=sorted(results,key=lambda x:x['best_score'],reverse=True)[:5]; lines=[f"{r['item_type']}:{r['item_id']} base={r['best_base']} score={r['best_score']} {r['candidate_status']} preview={r['decoded_preview'][:50]}" for r in top]
        send('\n'.join([f'[469][visual-font-base][run={run_id}] teste com alfabeto visual real do font.pic 7.10',f'alphabet_len={len(ALPHABET)} | itens={len(items)} | candidatos fortes={strong} | gloss=0',*lines,f'decisão={decision}',f'próxima ação: {next_action}']))
if __name__=='__main__': main()
