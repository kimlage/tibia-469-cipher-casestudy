#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
from typing import Any
DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def send(msg):
    if os.path.exists(DISCORD_SCRIPT): subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def create(cur):
    cur.executescript('''
    create table if not exists non_circular_hypothesis_queue_runs(run_id integer primary key autoincrement,created_at text not null,hypothesis_count integer not null,decision text not null,next_action text not null,payload_json text not null);
    create table if not exists non_circular_hypothesis_queue_items(run_id integer not null,rank integer not null,hypothesis_id text not null,lane text not null,priority integer not null,reason_selected text not null,required_evidence text not null,success_gate text not null,abandon_gate text not null,status text not null,payload_json text not null,primary key(run_id,rank));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor(); create(cur)
    hypotheses=[
      dict(hypothesis_id='EXACT_EXTERNAL_MEANING_SOURCE_SEARCH',lane='external_research',priority=100,reason_selected='only route that can raise semantic_gloss_pct safely',required_evidence='exact 469 sequence plus explicit natural-language meaning and provenance',success_gate='source can be ingested as audit-only and predicts held-out phrase/book without DP component leakage',abandon_gate='source repeats numeric text or speculative translation without proof',status='OPEN'),
      dict(hypothesis_id='BASE_N_WITH_AUTHENTIC_TIBIA_CHARSET',lane='method_research',priority=82,reason_selected='Vogler Numbers validates base conversion, but generic base256/charset failed books',required_evidence='actual old Tibia PIC charset bytes/order plus reproducible base conversion producing readable holdout',success_gate='at least one external holdout or book decodes into readable text with low punctuation and source-independent validation',abandon_gate='only gibberish or only reproduces Vogler Numbers claim',status='OPEN'),
      dict(hypothesis_id='RAW_DIGIT_GENERATIVE_MODEL_WITH_HOLDOUTS',lane='cryptanalytic_model',priority=76,reason_selected='all English-shadow routes are circular; need raw digit objective',required_evidence='model trained on raw recurrence/zero features predicts heldout NPC segmentation without using plaintext',success_gate='improves holdout segmentation consistency over shuffled controls and does not assign gloss',abandon_gate='overfits 00/wildcards or fails shuffled controls',status='OPEN'),
      dict(hypothesis_id='BOOK_ORDER_SUPERCONTIG_RECONSTRUCTION_REVISIT',lane='structural_reconstruction',priority=64,reason_selected='public methods suggest books may be one large sequence; current contigs cover only known edges',required_evidence='new non-fragmented supercontig order that includes currently isolated books without forcing dead families',success_gate='adds contiguous support for 4/34/49 or increases long-run reconstruction with no contradictions',abandon_gate='only reopens known dead contigs or fragmented LCS',status='OPEN'),
      dict(hypothesis_id='SOURCE_CORPUS_EXPANSION_OLD_FORUM_ATTACHMENTS',lane='archive_research',priority=58,reason_selected='new OTLand 2026 lead references old PIC tools/charset and possible hidden assets',required_evidence='downloadable primary artifact or exact charset/order/source file',success_gate='artifact is reproducible locally and explains at least one holdout better than current methods',abandon_gate='requires login-only inaccessible attachment or unverifiable claims',status='OPEN')]
    cur.execute('insert into non_circular_hypothesis_queue_runs(created_at,hypothesis_count,decision,next_action,payload_json) values (?,?,?,?,?)',(now(),len(hypotheses),'NON_CIRCULAR_QUEUE_READY','execute highest priority lane next; keep gloss at 0 until success gate passes',j({'hypotheses':hypotheses})))
    run_id=cur.lastrowid
    for rank,h in enumerate(hypotheses,1):
        cur.execute('insert into non_circular_hypothesis_queue_items(run_id,rank,hypothesis_id,lane,priority,reason_selected,required_evidence,success_gate,abandon_gate,status,payload_json) values (?,?,?,?,?,?,?,?,?,?,?)',(run_id,rank,h['hypothesis_id'],h['lane'],h['priority'],h['reason_selected'],h['required_evidence'],h['success_gate'],h['abandon_gate'],h['status'],j(h)))
    con.commit(); print(json.dumps({'run_id':run_id,'decision':'NON_CIRCULAR_QUEUE_READY','hypothesis_count':len(hypotheses),'top':hypotheses[:3]},ensure_ascii=False))
    if args.discord: send('\n'.join([f'[469][next-hypothesis-queue][run={run_id}] fila não-circular criada',f'hipóteses={len(hypotheses)} | gloss permanece 0 até gate passar','top1: busca externa por sequência exata + significado explícito','top2: base-N com charset Tibia autêntico, não aproximação','top3: modelo raw-digit com holdouts e controles embaralhados','próxima ação: executar a lane mais alta sem voltar para inglês do shadow.']))
if __name__=='__main__': main()
