#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
DISCORD_CHANNEL = "0"
DISCORD_SCRIPT = "~/.codex/skills/discord/scripts/discord_skill.py"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def rows(cur, sql, params=()):
    return [dict(r) for r in cur.execute(sql, params).fetchall()]


def create_tables(cur):
    cur.executescript(
        """
        create table if not exists external_anchor_provenance_gate_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            checked_anchor_count integer not null,
            direct_source_attested_semantic_count integer not null,
            npc_only_quarantined_count integer not null,
            book_promotable_count integer not null,
            payload_json text not null
        );
        create table if not exists external_anchor_provenance_gate_items (
            run_id integer not null,
            anchor_id text not null,
            digits text not null,
            claimed_meaning text,
            source_chain_json text not null,
            numeric_attestation_count integer not null,
            direct_semantic_source_count integer not null,
            operational_derivation text not null,
            decision text not null,
            scope text not null,
            promote_to_books integer not null,
            reason text not null,
            next_action text not null,
            payload_json text not null,
            primary key (run_id, anchor_id)
        );
        """
    )


def send_discord(message: str):
    if not os.path.exists(DISCORD_SCRIPT):
        return
    cmd = f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(message)}"
    subprocess.run(["/bin/zsh", "-lc", cmd], check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--discord", action="store_true")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    create_tables(cur)

    external_refs = rows(cur, "select __export_id,__row_index,refname,type,source,numerictext,digitssanitized from sheet__externalrefs_v115 where digitssanitized='653768764' or refname='Elder2'")
    external_validation = rows(cur, "select __export_id,__row_index,reference,numerictext,verifiedsources,verifiedcount,notes from sheet__externalvalidation_v129 where numerictext like '%653768764%' or reference like '%Elder%'")
    source_hits = rows(cur, "select __export_id,__row_index,sourceid,url,digitsrun,exactrefmatch,hitkind,notes from sheet__externalsourcedigithits_v472 where digitsrun='653768764' or sourceid='REDDIT_2025_POLYPHONIC'")
    community = rows(cur, "select __export_id,__row_index,sourceid,url,evidenceclass,sequencesmentioned,keyexcerpt,reliability,independence,targetrefname,notes from sheet__externalcommunitysources_v472 where sourceid='REDDIT_2025_POLYPHONIC'")
    phrase_audit = rows(cur, "select run_id,anchor_id,digits,refname,expected_core,best_score_pct,status,payload_json from external_phrase_anchor_audit where digits='653768764' order by run_id desc")
    phrase_anchor = rows(cur, "select * from npc_phrase_anchors where digits='653768764'")
    word_anchors = rows(cur, "select * from npc_wordcode_anchors where phrase_id='NPC-Elder2-653768764' order by anchor_id")

    numeric_attestation_count = 0
    for r in external_validation:
        try:
            numeric_attestation_count = max(numeric_attestation_count, int(r.get("verifiedcount") or 0))
        except ValueError:
            pass
    if external_refs:
        numeric_attestation_count = max(numeric_attestation_count, 1)

    direct_semantic_source_count = 0
    claimed = phrase_anchor[0].get("expected_text") if phrase_anchor else "look at you"
    operational_derivation = "derived_from_external_phrase_anchor_audit.expected_full/core; normalized source tables attest digits but not direct meaning"
    decision = "NPC_ONLY_QUARANTINED_DERIVED_SEMANTIC_EXPECTATION_NO_BOOK_PROMOTION"
    item = {
        "anchor_id": "NPC-Elder2-653768764",
        "digits": "653768764",
        "claimed_meaning": claimed,
        "source_chain": {
            "sheet__externalrefs_v115": external_refs,
            "sheet__externalvalidation_v129": external_validation,
            "sheet__externalsourcedigithits_v472": source_hits,
            "sheet__externalcommunitysources_v472": community,
            "external_phrase_anchor_audit": phrase_audit[:3],
            "npc_phrase_anchors": phrase_anchor,
            "npc_wordcode_anchors": word_anchors,
        },
        "numeric_attestation_count": numeric_attestation_count,
        "direct_semantic_source_count": direct_semantic_source_count,
        "operational_derivation": operational_derivation,
        "decision": decision,
        "scope": "external_npc_only",
        "promote_to_books": 0,
        "reason": "sequence is externally attested, but direct source-attested semantic mapping is absent in normalized SQLite; phrase remains useful only as quarantined NPC context",
        "next_action": "require normalized source row attesting both 653768764 and 'Let me take a look at you'/'look at you' before any stronger semantic promotion",
    }

    cur.execute(
        """
        insert into external_anchor_provenance_gate_runs
        (created_at, decision, checked_anchor_count, direct_source_attested_semantic_count,
         npc_only_quarantined_count, book_promotable_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), "EXTERNAL_ANCHOR_PROVENANCE_GATE_READY", 1, direct_semantic_source_count, 1, 0, j({"anchors": [item["anchor_id"]]})),
    )
    run_id = cur.lastrowid
    cur.execute(
        """
        insert into external_anchor_provenance_gate_items
        (run_id, anchor_id, digits, claimed_meaning, source_chain_json, numeric_attestation_count,
         direct_semantic_source_count, operational_derivation, decision, scope, promote_to_books,
         reason, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, item["anchor_id"], item["digits"], item["claimed_meaning"], j(item["source_chain"]),
         item["numeric_attestation_count"], item["direct_semantic_source_count"], item["operational_derivation"],
         item["decision"], item["scope"], item["promote_to_books"], item["reason"], item["next_action"], j(item)),
    )
    con.commit()

    out = {
        "run_id": run_id,
        "decision": "EXTERNAL_ANCHOR_PROVENANCE_GATE_READY",
        "anchor_id": item["anchor_id"],
        "numeric_attestation_count": numeric_attestation_count,
        "direct_semantic_source_count": direct_semantic_source_count,
        "promote_to_books": 0,
    }
    print(json.dumps(out, ensure_ascii=False))

    if args.discord:
        send_discord("\n".join([
            f"[469][external-anchor-gate][run={run_id}] Elder2 auditado sem contaminar livros",
            "653768764: sequência confirmada em fontes externas; significado 'look at you' é expectativa operacional derivada, não linha-fonte normalizada direta.",
            f"direct_semantic_source_count={direct_semantic_source_count} | numeric_attestation_count={numeric_attestation_count} | promote_to_books=0",
            "decisão: manter como NPC-only/quarentena; não usar para traduzir livros até existir fonte que ateste sequência + significado explicitamente.",
        ]))


if __name__ == "__main__":
    main()
