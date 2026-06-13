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
    create table if not exists external_semantic_anchor_search_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      source_count integer not null, accepted_semantic_anchor_count integer not null,
      exact_sequence_only_count integer not null, speculative_count integer not null, payload_json text not null);
    create table if not exists external_semantic_anchor_search_items(
      run_id integer not null, source_id text not null, url text not null, source_type text not null,
      claim text not null, exact_sequence text, meaning_claim text, evidence_status text not null,
      accept_as_semantic_anchor integer not null, risk text not null, payload_json text not null,
      primary key(run_id, source_id));''')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor(); create(cur)
    items=[
        {
            'source_id':'WRINKLED_BONELORD_TRANSCRIPT_486486_1_0_469',
            'url':'https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts',
            'source_type':'npc_transcript',
            'claim':'NPC transcript attests scoped lore anchors: 486486 self-name, 1 for Tibia, 0 obscene number, 469 language of his kind; also states books are written in 469 and deciphering needs fast mathematical processing.',
            'exact_sequence':'486486;1;0;469',
            'meaning_claim':'scoped NPC/lore meanings only',
            'evidence_status':'ACCEPT_SCOPED_LORE_ANCHOR_NO_BOOK_PROMOTION',
            'accept':0,
            'risk':'real anchor but not a book-level plaintext mapping'
        },
        {
            'source_id':'BONELORD_TOME_OFFICIAL_FANSITE_ITEM',
            'url':'https://www.tibiawiki.com.br/wiki/Bonelord_Tome',
            'source_type':'official_fansite_item_sounds',
            'claim':'Bonelord Tome sound list includes the Knightmare-style sequence and a separate English line saying 486486 holds answers; adjacency is not an explicit translation.',
            'exact_sequence':'3478 67 90871 97664 3466 0 345',
            'meaning_claim':'none explicit; contextual hint only',
            'evidence_status':'EXACT_SEQUENCE_WITH_CONTEXT_NO_SEMANTIC_BINDING',
            'accept':0,
            'risk':'official/fansite item context may validate sequence importance, but not its meaning'
        },
        {
            'source_id':'ELDER_BEHOLDER_SOUNDS_653768764',
            'url':'https://tibia.fandom.com/sv/wiki/Elder_Beholder',
            'source_type':'creature_sound_list',
            'claim':'Creature sound list places English and numeric shouts in the same list, including 653768764 and 659978 54764, but does not bind either numeric shout to an English sentence.',
            'exact_sequence':'653768764;659978 54764',
            'meaning_claim':'none explicit',
            'evidence_status':'NPC_SOUND_ADJACENCY_NO_DIRECT_TRANSLATION',
            'accept':0,
            'risk':'parallel sound list is suggestive but not a source-attested translation'
        },
        {
            'source_id':'TIBIAQA_AVAR_TAR_TIBIAORG_VARIANT',
            'url':'https://www.tibiaqa.com/25041/is-avar-tar-lying-about-his-stories',
            'source_type':'community_lore_audit',
            'claim':'TibiaQA discussion records Avar Tar poem, Knightmare sequence, Elder Bonelord sequences, and a claimed old Tibia.org variant containing 62792068657272657261.',
            'exact_sequence':'62792068657272657261;29639 46781...;3478 67 90871 97664 3466 0 345',
            'meaning_claim':'NARCISSIST/NARCISSISM is inferred elsewhere from pattern, not attested here',
            'evidence_status':'ARCHIVAL_CLAIM_AND_CONTEXT_NO_ACCEPTED_GLOSS',
            'accept':0,
            'risk':'useful target for archival verification, not sufficient as semantic anchor'
        },
        {
            'source_id':'TIBIASECRETS_ARTICLE160_CIPHER_HYPOTHESIS',
            'url':'https://tibiasecrets.com/article160',
            'source_type':'community_cipher_hypothesis',
            'claim':'Article proposes homophonic/cipher readings and derives candidate meanings for several external phrases.',
            'exact_sequence':'347867908719766434660345;66390207372236753846780097;62792068657272657261',
            'meaning_claim':'derived candidate readings only',
            'evidence_status':'SPECULATIVE_OR_DERIVED_NO_PROMOTION',
            'accept':0,
            'risk':'circular if used as truth; keep as hypothesis/probe source only'
        }
    ]
    exact_only=sum(1 for x in items if x['evidence_status'] in {'EXACT_SEQUENCE_WITH_CONTEXT_NO_SEMANTIC_BINDING','NPC_SOUND_ADJACENCY_NO_DIRECT_TRANSLATION','ARCHIVAL_CLAIM_AND_CONTEXT_NO_ACCEPTED_GLOSS'})
    speculative=sum(1 for x in items if x['evidence_status']=='SPECULATIVE_OR_DERIVED_NO_PROMOTION')
    cur.execute('insert into external_semantic_anchor_search_runs(created_at,decision,source_count,accepted_semantic_anchor_count,exact_sequence_only_count,speculative_count,payload_json) values (?,?,?,?,?,?,?)',
        (now(),'EXTERNAL_SEARCH_FOUND_SCOPED_LORE_ONLY_ZERO_BOOK_PROMOTABLE_ANCHORS',len(items),0,exact_only,speculative,j({'acceptance_gate':'exact sequence plus explicit source-attested meaning/provenance'})))
    run_id=cur.lastrowid
    for x in items:
        cur.execute('insert into external_semantic_anchor_search_items(run_id,source_id,url,source_type,claim,exact_sequence,meaning_claim,evidence_status,accept_as_semantic_anchor,risk,payload_json) values (?,?,?,?,?,?,?,?,?,?,?)',
            (run_id,x['source_id'],x['url'],x['source_type'],x['claim'],x['exact_sequence'],x['meaning_claim'],x['evidence_status'],x['accept'],x['risk'],j({'search_round':'2026-05-08-external-anchors'})))
    con.commit()
    out={'run_id':run_id,'decision':'EXTERNAL_SEARCH_FOUND_SCOPED_LORE_ONLY_ZERO_BOOK_PROMOTABLE_ANCHORS','source_count':len(items),'accepted_semantic_anchor_count':0,'book_promotable_count':0}
    print(json.dumps(out,ensure_ascii=False))
    if args.discord:
        send('\n'.join([f"[469][external-anchor-search][run={run_id}] busca externa registrada",f"fontes={len(items)} | anchors semânticos promovíveis para livros=0 | sequências/contexto sem gloss={exact_only} | especulativos={speculative}",'resultado: há anchors lore/NPC e pistas fortes, mas nenhuma fonte dá sequência exata de livro + significado explícito. Próxima frente: arquivo primário Tibia.org/Wayback ou evidência oficial equivalente.']))
if __name__=='__main__': main()
