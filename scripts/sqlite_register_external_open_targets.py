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
    create table if not exists external_semantic_open_target_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      target_count integer not null, high_priority_count integer not null, payload_json text not null);
    create table if not exists external_semantic_open_targets(
      run_id integer not null, target_id text not null, target_class text not null,
      exact_sequence text not null, current_status text not null, priority integer not null,
      required_evidence text not null, next_action text not null, payload_json text not null,
      primary key(run_id,target_id));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor(); create(cur)
    targets=[
        ('TIBIA_ORG_AVAR_VARIANT','archive_primary','62792068657272657261','OPEN_ARCHIVE_ACCESS_BLOCKED',1,'primary archived Tibia.org HTML or trusted mirror with exact sequence; explicit meaning if any','retry Wayback/alternate archives; do not accept TibiaSecrets pattern inference as meaning'),
        ('POLL_2020_OPTION_C','official_poll_context','663 902073 7223 67538 467 80097','OPEN_NEEDS_PRIMARY_CONTEXT',1,'official Tibia poll/news page with exact option C; explicit meaning required for semantic promotion','find primary poll page or archived copy; likely context-only'),
        ('CHAYENNE_2009_REPLY','content_team_interview','114514519485611451908304576512282177;6612527570584','OPEN_NEEDS_PRIMARY_INTERVIEW',2,'interview transcript with exact reply and provenance; explicit meaning required','find interview source; treat as external phrase, not book decoder'),
        ('KNIGHTMARE_PHRASE','npc_phrase','3478 67 90871 97664 3466 0 345','OPEN_CONTEXT_ONLY',1,'NPC/source transcript with exact sequence and any explicit meaning; current evidence only context','keep as phrase holdout; do not promote derived BE/fool reading'),
        ('ELDER_BONELORD_SOUNDS','npc_sound_pair','659978 54764;653768764','OPEN_SOUND_ADJACENCY_ONLY',2,'source explicitly binding numeric shout to English shout, not just same sound list','search primary creature data or official fan wiki history'),
        ('FACEBOOK_MIRRORED_NUMBERS','official_social_image','737/469 and paired-number table','OPEN_IMAGE_PRIMARY_NEEDED',3,'official Facebook image or archive plus exact numeric extraction','use as mechanical clue only unless explicit meaning exists')
    ]
    cur.execute('insert into external_semantic_open_target_runs(created_at,decision,target_count,high_priority_count,payload_json) values (?,?,?,?,?)',
        (now(),'EXTERNAL_SEMANTIC_OPEN_TARGETS_REGISTERED',len(targets),sum(1 for x in targets if x[4]==1),j({'purpose':'semantic unlock backlog; not promotion'})))
    run_id=cur.lastrowid
    for t in targets:
        cur.execute('insert into external_semantic_open_targets(run_id,target_id,target_class,exact_sequence,current_status,priority,required_evidence,next_action,payload_json) values (?,?,?,?,?,?,?,?,?)',
            (run_id,)+t+(j({}),))
    con.commit()
    out={'run_id':run_id,'decision':'EXTERNAL_SEMANTIC_OPEN_TARGETS_REGISTERED','target_count':len(targets),'high_priority_count':sum(1 for x in targets if x[4]==1)}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][external-targets][run={run_id}] backlog semântico externo registrado",f"alvos={len(targets)} | alta prioridade=3 | promoção imediata=0",'alvos principais: Tibia.org variant, poll 2020 opção C, Knightmare phrase. Critério: sequência exata + significado explícito, ou não promove.']))
if __name__=='__main__': main()
