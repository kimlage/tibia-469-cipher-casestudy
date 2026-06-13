#!/usr/bin/env python3
import argparse, datetime as dt, json, os, sqlite3, subprocess
from typing import Any
DB_DEFAULT='./data/bonelord_operational.sqlite'
DISCORD_CHANNEL='0'
DISCORD_SCRIPT='~/.codex/skills/discord/scripts/discord_skill.py'
def now(): return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00','Z')
def j(x:Any): return json.dumps(x,ensure_ascii=False,sort_keys=True)
def rows(cur,sql,p=()): return [dict(r) for r in cur.execute(sql,p).fetchall()]
def create(cur):
    cur.executescript('''
    create table if not exists r20_vtlrnefie_control_gate_runs(
      run_id integer primary key autoincrement, created_at text not null, decision text not null,
      total_book_count integer not null, vinvin_explicit_count integer not null, vinvin_tag_only_count integer not null,
      r20_solo_count integer not null, independent_phase_promotable_count integer not null, gloss_allowed_count integer not null,
      payload_json text not null);
    create table if not exists r20_vtlrnefie_control_gate_items(
      run_id integer not null, bookid text not null, r20_vtlr_class text not null, suffix_class text,
      suspect_status text, decision text not null, confidence real not null, independent_phase_promotable integer not null,
      gloss_allowed integer not null, reason text not null, next_action text not null, evidence_json text not null,
      primary key(run_id, bookid));''')
def send(msg):
    if os.path.exists(DISCORD_SCRIPT):
        subprocess.run(['/bin/zsh','-lc',f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(msg)}"],check=False)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',default=DB_DEFAULT); ap.add_argument('--discord',action='store_true'); args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor(); create(cur)
    books=rows(cur,"select bookid,functional_tags_json,honest_text from final_honest_reading_v3_books where run_id=(select max(run_id) from final_honest_reading_v3_books) and honest_text like '%R20_VTLRNEFIE_BLOCK%'")
    vrows=rows(cur,"select * from vinvin_vtlr_cross_contig_items where run_id=(select max(run_id) from vinvin_vtlr_cross_contig_items)")
    srows=rows(cur,"select * from vtlrnefie_suspect_resolution_items where run_id=(select max(run_id) from vtlrnefie_suspect_resolution_items)")
    items=[]
    for b in books:
        tags=json.loads(b['functional_tags_json'] or '[]')
        v=next((x for x in vrows if str(x['bookid'])==str(b['bookid'])),None)
        s=next((x for x in srows if str(x.get('bookid'))==str(b['bookid'])),None)
        has_vin_tag=any(str(t.get('tag_id','')).startswith('VINVIN') or str(t.get('source','')).startswith('vinvin_') for t in tags)
        if v:
            cls='VINVIN_VTLR_EXPLICIT'; suffix=v.get('suffix_class'); decision='KEEP_AS_STRUCTURAL_BRANCH_BOUNDARY_NO_GLOSS' if suffix in ('INEIIVNSENI_STAR_LEAENT','TIFAVONAFIEI') else 'KEEP_AS_NEGATIVE_OR_PARTIAL_CONTROL_NO_GLOSS'; conf=0.72 if suffix=='TIFAVONAFIEI' else 0.83 if suffix=='INEIIVNSENI_STAR_LEAENT' else 0.18
            reason='explicit VINVIN/VTLR occurrence; contig support belongs to branch structure, not independent R20 phase'
            next_action='keep under VINVIN branch control; no independent R20_VTLRNEFIE promotion'
        elif has_vin_tag:
            cls='VINVIN_TAG_ONLY'; suffix=None; decision='AUDIT_MISSING_STRICT_EDGE_BEFORE_GENERALIZATION'; conf=0.45; reason='VINVIN functional tag exists but strict VINVIN_VTLR edge row absent'
            next_action='audit missing strict edge, especially book 61; no broader generalization'
        else:
            cls='R20_SOLO_NO_VINVIN'; suffix=None; decision='DO_NOT_PROMOTE_PHASE_REQUIRE_INDEPENDENT_EVIDENCE'; conf=0.25; reason='R20/VTLRNEFIE appears without VINVIN tag/edge support; solo phase claim unsupported'
            next_action='isolate as risk set 15/16; require independent contig/contrast before any promotion'
        items.append({'bookid':str(b['bookid']),'class':cls,'suffix':suffix,'suspect':s,'decision':decision,'confidence':conf,'reason':reason,'next_action':next_action,'evidence':{'book':b,'vinvin':v,'suspect':s,'tags':tags}})
    counts={k:sum(1 for x in items if x['class']==k) for k in ('VINVIN_VTLR_EXPLICIT','VINVIN_TAG_ONLY','R20_SOLO_NO_VINVIN')}
    cur.execute('insert into r20_vtlrnefie_control_gate_runs(created_at,decision,total_book_count,vinvin_explicit_count,vinvin_tag_only_count,r20_solo_count,independent_phase_promotable_count,gloss_allowed_count,payload_json) values (?,?,?,?,?,?,?,?,?)',(now(),'R20_VTLRNEFIE_KEEP_UNDER_VINVIN_CONTROL_NO_GLOSS',len(items),counts['VINVIN_VTLR_EXPLICIT'],counts['VINVIN_TAG_ONLY'],counts['R20_SOLO_NO_VINVIN'],0,0,j({'note':'do not promote R20_VTLRNEFIE_BLOCK independently'})))
    run_id=cur.lastrowid
    for x in items:
        cur.execute('insert into r20_vtlrnefie_control_gate_items(run_id,bookid,r20_vtlr_class,suffix_class,suspect_status,decision,confidence,independent_phase_promotable,gloss_allowed,reason,next_action,evidence_json) values (?,?,?,?,?,?,?,?,?,?,?,?)',(run_id,x['bookid'],x['class'],x['suffix'],x['suspect'].get('status') if x['suspect'] else None,x['decision'],x['confidence'],0,0,x['reason'],x['next_action'],j(x['evidence'])))
    con.commit(); out={'run_id':run_id,'decision':'R20_VTLRNEFIE_KEEP_UNDER_VINVIN_CONTROL_NO_GLOSS','total_book_count':len(items),'vinvin_explicit_count':counts['VINVIN_VTLR_EXPLICIT'],'vinvin_tag_only_count':counts['VINVIN_TAG_ONLY'],'r20_solo_count':counts['R20_SOLO_NO_VINVIN'],'independent_phase_promotable_count':0,'gloss_allowed_count':0}; print(json.dumps(out,ensure_ascii=False))
    if args.discord: send('\n'.join([f"[469][r20-vtlrnefie][run={run_id}] R20/VTLRNEFIE bloqueado como fase independente",f"total={len(items)} | VINVIN explícito={counts['VINVIN_VTLR_EXPLICIT']} | tag-only={counts['VINVIN_TAG_ONLY']} | solo sem VINVIN={counts['R20_SOLO_NO_VINVIN']}",'decisão: manter sob controle VINVIN/display-suspect; 0 promoção de fase independente; 0 gloss lexical.']))
if __name__=='__main__': main()
