#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
SEQ='62792068657272657261'

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists tibia_org_hex_signature_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      exact_sequence text not null, ascii_decoded text not null, primary_source_count integer not null,
      blocks_narcissist_inference integer not null, book_promotable_count integer not null,
      payload_json text not null);
    create table if not exists tibia_org_hex_signature_gate_items(
      run_id integer not null, source_id text not null, source_url text not null,
      source_status text not null, exact_sequence_present integer not null,
      semantic_status text not null, recommendation text not null, payload_json text not null,
      primary key(run_id,source_id));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    decoded=bytes.fromhex(SEQ).decode('ascii')
    con=sqlite3.connect(args.db); cur=con.cursor(); create(cur)
    sources=[
        ('TIBIA_ORG_LIVE','http://www.tibia.org/','PRIMARY_LIVE_HTTP_200_S3_HTML'),
        ('WAYBACK_TIBIA_ORG_20200915233841_ID','https://web.archive.org/web/20200915233841id_/http://www.tibia.org/','PRIMARY_ARCHIVE_RAW_CAPTURE'),
        ('WAYBACK_TIBIA_ORG_20200915233841','https://web.archive.org/web/20200915233841/http://www.tibia.org/','PRIMARY_ARCHIVE_REWRITTEN_CAPTURE')
    ]
    cur.execute('insert into tibia_org_hex_signature_gate_runs(created_at,decision,exact_sequence,ascii_decoded,primary_source_count,blocks_narcissist_inference,book_promotable_count,payload_json) values (?,?,?,?,?,?,?,?)',
        (now(),'TIBIA_ORG_VARIANT_IS_HEX_SIGNATURE_NOT_469_SEMANTIC_ANCHOR',SEQ,decoded,len(sources),1,0,j({'reason':'standard hex byte decoding gives an author/signature string; primary HTML does not attest NARCISSIST/M or 469 meaning'})))
    run_id=cur.lastrowid
    for sid,url,status in sources:
        cur.execute('insert into tibia_org_hex_signature_gate_items(run_id,source_id,source_url,source_status,exact_sequence_present,semantic_status,recommendation,payload_json) values (?,?,?,?,?,?,?,?)',
            (run_id,sid,url,status,1,'ASCII_HEX_SIGNATURE_BY_HERRERA_NO_469_MEANING','block NARCISSIST/M inference; keep source as provenance/contamination note only',j({})))
    con.commit()
    out={'run_id':run_id,'decision':'TIBIA_ORG_VARIANT_IS_HEX_SIGNATURE_NOT_469_SEMANTIC_ANCHOR','exact_sequence':SEQ,'ascii_decoded':decoded,'blocks_narcissist_inference':1,'book_promotable_count':0}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][tibia-org-hex][run={run_id}] Tibia.org variant reclassificado",f"{SEQ} -> ASCII hex: {decoded!r}",'decisão: bloqueia hipótese NARCISSIST/M como anchor forte; isto parece assinatura/contaminação HTML, não tradução 469. Promoção para livros=0.']))
if __name__=='__main__': main()
