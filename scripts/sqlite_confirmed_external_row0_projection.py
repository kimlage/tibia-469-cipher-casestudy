#!/usr/bin/env python3
import argparse, datetime as dt, json, os, re, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
PHRASES=[
    ('KNIGHTMARE_PHRASE','3478 67 90871 97664 3466 0 345'),
    ('POLL_2020_OPTION_C','663 902073 7223 67538 467 80097'),
    ('CHAYENNE_REPLY','114514519485611451908304576512282177 6612527570584'),
    ('ELDER_BONELORD_SOUNDS','659978 54764 653768764'),
    ('AVAR_ORIGINAL_POEM','29639 46781 9063376290 3222011 677 80322429 67538 14805394 6880326 677 63378129 337011 72683 149630 4378 453 639 578300 986372 2953639'),
]
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def clean(s): return re.sub(r'[^0-9]','',s)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def pair_codes(digits):
    if len(digits)%2: digits='0'+digits
    return [digits[i:i+2] for i in range(0,len(digits),2)]
def project_wordwise(raw, cmap):
    parts=re.findall(r'\d+',raw)
    code_words=[]; symbol_words=[]; unknown=[]
    for p in parts:
        codes=pair_codes(p); syms=[]
        for c in codes:
            s=cmap.get(c,'?'); syms.append(s)
            if s=='?': unknown.append(c)
        code_words.append(codes); symbol_words.append(''.join(syms))
    return code_words,symbol_words,unknown
def project_global(raw,cmap):
    codes=pair_codes(clean(raw)); syms=[]; unknown=[]
    for c in codes:
        s=cmap.get(c,'?'); syms.append(s)
        if s=='?': unknown.append(c)
    return codes,''.join(syms),unknown
def best_occ(symbol_text, books):
    hits=[]
    if not symbol_text: return hits
    for b in books:
        pos=b['symbol_text'].find(symbol_text)
        if pos>=0: hits.append({'bookid':b['bookid'],'pos':pos,'kind':'full'})
    if hits: return hits
    # fallback: longest word hit >= 5 chars
    return hits
def create(cur):
    cur.executescript('''
    create table if not exists confirmed_external_row0_projection_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      phrase_count integer not null, exact_book_hit_count integer not null, payload_json text not null);
    create table if not exists confirmed_external_row0_projection_items(
      run_id integer not null, phrase_id text not null, raw_digits text not null,
      global_symbols text not null, word_symbols_json text not null,
      unknown_codes_json text not null, exact_book_hits_json text not null,
      projection_status text not null, recommendation text not null, payload_json text not null,
      primary key(run_id,phrase_id));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    cmap={r['code']:r['symbol'] for r in rows(cur,'select code,symbol from row0_code_symbol_counts where run_id=(select max(run_id) from row0_code_symbol_counts)')}
    books=rows(cur,'select bookid,symbol_text from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_book_tokens)')
    out=[]
    for pid,raw in PHRASES:
        gcodes,gsyms,gunk=project_global(raw,cmap)
        wcodes,wsyms,wunk=project_wordwise(raw,cmap)
        hits=best_occ(gsyms,books)
        status='EXTERNAL_ROW0_SEQUENCE_IN_BOOK_CORPUS' if hits else 'EXTERNAL_ROW0_OUT_OF_BOOK_CORPUS'
        rec='use as mechanical holdout only; no semantic gloss' if hits else 'keep external-only; do not use to promote book semantics'
        out.append((pid,clean(raw),gsyms,j(wsyms),j(sorted(set(gunk+wunk))),j(hits),status,rec,j({'global_codes':gcodes,'word_codes':wcodes})))
    cur.execute('insert into confirmed_external_row0_projection_runs(created_at,decision,phrase_count,exact_book_hit_count,payload_json) values (?,?,?,?,?)',
        (now(),'CONFIRMED_EXTERNAL_ROW0_PROJECTION_HOLDOUTS_NO_SEMANTIC_PROMOTION',len(out),sum(1 for x in out if json.loads(x[5])),j({})))
    run_id=cur.lastrowid
    for x in out:
        cur.execute('insert into confirmed_external_row0_projection_items(run_id,phrase_id,raw_digits,global_symbols,word_symbols_json,unknown_codes_json,exact_book_hits_json,projection_status,recommendation,payload_json) values (?,?,?,?,?,?,?,?,?,?)',(run_id,)+x)
    con.commit()
    res={'run_id':run_id,'decision':'CONFIRMED_EXTERNAL_ROW0_PROJECTION_HOLDOUTS_NO_SEMANTIC_PROMOTION','phrase_count':len(out),'exact_book_hit_count':sum(1 for x in out if json.loads(x[5]))}
    print(json.dumps(res,ensure_ascii=False))
    if args.discord:
        lines=[f"[469][external-row0-projection][run={run_id}] projeção row0 de frases externas",f"frases={len(out)} | hits exatos em livros={res['exact_book_hit_count']} | gloss=0",'uso: holdout mecânico externo; se não aparece nos livros, não pode promover semântica dos livros.']
        for x in out: lines.append(f"- {x[0]}: {x[6]}")
        send('\n'.join(lines))
if __name__=='__main__': main()
