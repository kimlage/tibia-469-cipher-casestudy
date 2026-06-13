#!/usr/bin/env python3
import argparse, datetime as dt, json, os, re, sqlite3, string, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
PRINTABLE=set(bytes(string.printable,'ascii'))

PHRASES=[
    ('TIBIA_ORG_SIGNATURE_WORD','62792068657272657261'),
    ('AVAR_ORIGINAL_POEM','29639 46781 9063376290 3222011 677 80322429 67538 14805394 6880326 677 63378129 337011 72683 149630 4378 453 639 578300 986372 2953639'),
    ('AVAR_TIBIA_ORG_VARIANT','29639 46781 9063376290 3222011 677 80322429 67538 14805394 6880326 677 62792068657272657261 337011 72683 149630 4378 453 639 578300 986372 2953639'),
    ('KNIGHTMARE_PHRASE','3478 67 90871 97664 3466 0 345'),
    ('POLL_2020_OPTION_C','663 902073 7223 67538 467 80097'),
    ('CHAYENNE_REPLY','114514519485611451908304576512282177 6612527570584'),
    ('ELDER_BONELORD_SOUNDS','659978 54764 653768764'),
]

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def clean(s): return re.sub(r'[^0-9]','',s)
def hex_decode(digits):
    if len(digits)%2: digits='0'+digits
    bs=bytes.fromhex(digits)
    printable=sum(1 for b in bs if b in PRINTABLE)
    text=''.join(chr(b) if b in PRINTABLE and b not in {10,11,12,13} else '.' for b in bs)
    return bs,round(printable/len(bs),4) if bs else 0.0,text
def create(cur):
    cur.executescript('''
    create table if not exists external_phrase_encoding_audit_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      phrase_count integer not null, printable_ascii_candidate_count integer not null,
      payload_json text not null);
    create table if not exists external_phrase_encoding_audit_items(
      run_id integer not null, phrase_id text not null, digit_length integer not null,
      byte_length integer not null, printable_ascii_ratio real not null, ascii_preview text not null,
      encoding_status text not null, recommendation text not null, payload_json text not null,
      primary key(run_id,phrase_id));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor(); create(cur)
    results=[]
    for pid,seq in PHRASES:
        d=clean(seq); bs,ratio,text=hex_decode(d)
        status='ASCII_SIGNATURE_CANDIDATE' if ratio>=0.9 and len(bs)>=4 else 'NOT_GENERAL_ASCII_TEXT'
        rec='treat as isolated ASCII/hex signature; block 469 semantic inference' if status=='ASCII_SIGNATURE_CANDIDATE' else 'do not use ASCII/hex as general decoder for this phrase'
        results.append((pid,d,len(bs),ratio,text[:120],status,rec))
    cur.execute('insert into external_phrase_encoding_audit_runs(created_at,decision,phrase_count,printable_ascii_candidate_count,payload_json) values (?,?,?,?,?)',
        (now(),'EXTERNAL_PHRASE_ENCODING_AUDIT_ASCII_NOT_GENERAL_469_DECODER',len(results),sum(1 for r in results if r[5]=='ASCII_SIGNATURE_CANDIDATE'),j({'method':'strip non-digits, pad leading zero if odd, decode as hex bytes, measure printable ASCII'})))
    run_id=cur.lastrowid
    for pid,d,bl,ratio,text,status,rec in results:
        cur.execute('insert into external_phrase_encoding_audit_items(run_id,phrase_id,digit_length,byte_length,printable_ascii_ratio,ascii_preview,encoding_status,recommendation,payload_json) values (?,?,?,?,?,?,?,?,?)',
            (run_id,pid,len(d),bl,ratio,text,status,rec,j({})))
    con.commit()
    out={'run_id':run_id,'decision':'EXTERNAL_PHRASE_ENCODING_AUDIT_ASCII_NOT_GENERAL_469_DECODER','ascii_candidates':[r[0] for r in results if r[5]=='ASCII_SIGNATURE_CANDIDATE']}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        lines=[f"[469][encoding-audit][run={run_id}] ASCII/hex audit externo",f"frases={len(results)} | candidatos ASCII legíveis={len(out['ascii_candidates'])}: {','.join(out['ascii_candidates']) or 'nenhum'}",'resultado: hex/ASCII não é decoder geral; só o trecho Tibia.org parece assinatura isolada.']
        for r in results:
            if r[5]=='ASCII_SIGNATURE_CANDIDATE': lines.append(f"- {r[0]} -> {r[4]!r} ratio={r[3]}")
        send('\n'.join(lines))
if __name__=='__main__': main()
