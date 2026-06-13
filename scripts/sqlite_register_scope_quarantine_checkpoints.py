#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any

DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'

def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists scoped_semantic_anchor_quarantine_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      accepted_scoped_count integer not null, book_promotable_count integer not null,
      rejected_candidate_count integer not null, payload_json text not null);
    create table if not exists scoped_semantic_anchor_quarantine_items(
      run_id integer not null, sequence text not null, meaning text not null, scope text not null,
      book_promotable integer not null, provenance_url text not null, decision text not null,
      reason text not null, payload_json text not null, primary key(run_id,sequence));
    create table if not exists structural_family_reopen_block_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      family_count integer not null, promoter_count integer not null, blocked_control_count integer not null,
      payload_json text not null);
    create table if not exists structural_family_reopen_block_items(
      run_id integer not null, family text not null, status text not null, affected_books_json text not null,
      reason text not null, next_action text not null, payload_json text not null, primary key(run_id,family));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor(); create(cur)
    anchors=[
        ('486486',"A Wrinkled Bonelord self-name",'NPC/entity-name only','https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts','explicit NPC transcript anchor; not a book decoder key'),
        ('1','Tibia/world label in Bonelord framing','lore lexical only','https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts','explicit NPC transcript anchor; not general numeric decoder'),
        ('469','language of Bonelords','language-name only','https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts','explicit lore label; not a plaintext mapping'),
        ('0','obscene/forbidden number','pragmatic lore only','https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts','explicit NPC response; not usable as book gloss')
    ]
    rejected=['653768764','65997854764','347867908719766434660345','66390207372236753846780097','62792068657272657261','3478','2364672119.../5765219727...']
    cur.execute('insert into scoped_semantic_anchor_quarantine_runs(created_at,decision,accepted_scoped_count,book_promotable_count,rejected_candidate_count,payload_json) values (?,?,?,?,?,?)',
        (now(),'SCOPED_LORE_ANCHORS_QUARANTINED_ZERO_BOOK_PROMOTION',len(anchors),0,len(rejected),j({'rejected_candidates':rejected})))
    arun=cur.lastrowid
    for seq,meaning,scope,url,reason in anchors:
        cur.execute('insert into scoped_semantic_anchor_quarantine_items(run_id,sequence,meaning,scope,book_promotable,provenance_url,decision,reason,payload_json) values (?,?,?,?,?,?,?,?,?)',
            (arun,seq,meaning,scope,0,url,'ACCEPT_SCOPED_QUARANTINE_NO_BOOK_PROMOTION',reason,j({})))
    families=[
        ('NAESE_SLOT','MANTER_AS_AUDIT_CONTROL',['13','38','41','56'],'positive gates already represented in v10; remaining rows are negative/audit controls','do not reopen for promotion without new mechanical contrast'),
        ('VINVIN_BRANCH','MANTER_ALREADY_REPRESENTED',[],'safe structural positives already represented in v10','keep as rendered structure only'),
        ('R20_R02_PHASE','MANTER_ALREADY_REPRESENTED',[],'safe positive frames already represented in v10','keep as phase/frame tags only'),
        ('R20_VTLRNEFIE','ABANDONAR_INDEPENDENT_PROMOTION',['15','16','61'],'unrepresented rows are strict-control negative/audit contexts','use only as contradiction controls')
    ]
    cur.execute('insert into structural_family_reopen_block_runs(created_at,decision,family_count,promoter_count,blocked_control_count,payload_json) values (?,?,?,?,?,?)',
        (now(),'NO_NEW_PROMOTION_NAESE_VINVIN_R20_REOPEN_BLOCKED',len(families),0,7,j({'source':'subagent structural audit after v10'})))
    brun=cur.lastrowid
    for fam,status,books,reason,next_action in families:
        cur.execute('insert into structural_family_reopen_block_items(run_id,family,status,affected_books_json,reason,next_action,payload_json) values (?,?,?,?,?,?,?)',
            (brun,fam,status,j(books),reason,next_action,j({})))
    con.commit()
    out={'anchor_quarantine_run_id':arun,'structural_block_run_id':brun,'decision':'REGISTERED_SCOPE_QUARANTINES_AND_REOPEN_BLOCKS','book_promotable_anchors':0,'new_structural_promoters':0}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][quarantine][anchors={arun}][families={brun}] checkpoints registrados",f"anchors lore aceitos={len(anchors)} | anchors promovíveis para livros=0 | candidatos externos rejeitados={len(rejected)}",'NAESE/VINVIN/R20: sem promoção nova; positivos já estão na v10, controles negativos ficam bloqueados para evitar ciclo falso.']))
if __name__=='__main__': main()
