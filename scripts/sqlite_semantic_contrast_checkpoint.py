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
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def j(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def one(cur: sqlite3.Cursor, sql: str, params=()):
    row = cur.execute(sql, params).fetchone()
    return dict(row) if row else None


def all_rows(cur: sqlite3.Cursor, sql: str, params=()):
    return [dict(r) for r in cur.execute(sql, params).fetchall()]


def create_tables(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists semantic_contrast_checkpoint_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            item_count integer not null,
            functional_promotable_count integer not null,
            lexical_gloss_allowed_count integer not null,
            npc_only_anchor_count integer not null,
            book_anchor_promotable_count integer not null,
            payload_json text not null
        );
        create table if not exists semantic_contrast_checkpoint_items (
            run_id integer not null,
            rank integer not null,
            item_id text not null,
            lane text not null,
            evidence_type text not null,
            decision text not null,
            functional_meaning text not null,
            lexical_gloss_allowed integer not null,
            promote_to_books integer not null,
            confidence real not null,
            reason text not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, rank)
        );
        """
    )


def latest_run_id(cur: sqlite3.Cursor, table: str) -> int | None:
    row = cur.execute(f"select max(run_id) as run_id from {table}").fetchone()
    return row[0] if row and row[0] is not None else None


def build_items(cur: sqlite3.Cursor):
    items = []

    vin_run = latest_run_id(cur, "vinvin_branch_subfunction_items")
    vin = all_rows(
        cur,
        """
        select * from vinvin_branch_subfunction_items
        where run_id=?
        order by branch_score desc, suffix_class
        """,
        (vin_run,),
    ) if vin_run else []
    positives = [r for r in vin if r["branch_status"] == "SUBFUNCTION_READY"]
    negatives = [r for r in vin if r["branch_status"] != "SUBFUNCTION_READY"]
    if positives:
        min_pos = min(float(r["branch_score"]) for r in positives)
        max_neg = max([float(r["branch_score"]) for r in negatives] or [0.0])
        ready = min_pos > max_neg and all(int(r["contig_supported_count"]) > 0 for r in positives)
        items.append({
            "item_id": "VINVIN_BRANCH_HOLDOUT_CONTRAST_SQL",
            "lane": "Structural/Semantic contrast",
            "evidence_type": "internal_contrast",
            "decision": "FUNCTIONAL_PROMOTION_READY_NO_GLOSS" if ready else "KEEP_AUDIT_PENDING",
            "functional_meaning": "branch selector / payload subfunction under contig support" if ready else "unresolved branch contrast",
            "lexical_gloss_allowed": 0,
            "promote_to_books": 0,
            "confidence": round(min(0.92, max(0.0, min_pos - max_neg + 0.25)), 3),
            "reason": f"positive branches separate from negative controls: min_pos={min_pos}, max_neg={max_neg}",
            "next_action": "materialize as functional label in honest reading, not plaintext" if ready else "open narrower holdout probe",
            "evidence_json": {"source_run_id": vin_run, "positives": positives, "negatives": negatives},
        })

    c68_run = latest_run_id(cur, "c68_fatct_slot_items")
    c68 = all_rows(cur, "select * from c68_fatct_slot_items where run_id=?", (c68_run,)) if c68_run else []
    naese_run = latest_run_id(cur, "naese_ivifast_slot_items")
    naese_counts = all_rows(
        cur,
        """
        select suffix_class, prefix_class, count(*) as n,
               sum(case when next_action like 'clean_template%' then 1 else 0 end) as clean_n
        from naese_ivifast_slot_items
        where run_id=?
        group by suffix_class, prefix_class
        order by n desc, suffix_class
        """,
        (naese_run,),
    ) if naese_run else []
    canonical = sum(1 for r in c68 if r["context_class"] == "CANONICAL_NAESE_FATCT_SLOT")
    edge = sum(1 for r in c68 if r["edge_support"] != "NO_EDGE_SUPPORT")
    if c68:
        ready = canonical >= 8 and edge >= 2
        items.append({
            "item_id": "NAESE_C68_FATCT_SLOT_SUFFIX_CONTRAST_SQL",
            "lane": "Structural/Semantic contrast",
            "evidence_type": "local_slot_contrast",
            "decision": "LOCAL_SLOT_FUNCTION_READY_NO_GLOSS" if ready else "LOCAL_SLOT_AUDIT_PENDING",
            "functional_meaning": "local slot classifier inside NAESE_IVIFAST" if ready else "possible local slot classifier",
            "lexical_gloss_allowed": 0,
            "promote_to_books": 0,
            "confidence": 0.81 if ready else 0.55,
            "reason": f"C68/FATCT canonical={canonical}/{len(c68)}, edge_supported={edge}; suffix variants remain local controls",
            "next_action": "use as local function label only; do not assign global C68/FATCT meaning",
            "evidence_json": {"source_c68_run_id": c68_run, "source_naese_run_id": naese_run, "c68_items": c68, "naese_suffix_counts": naese_counts},
        })

    phase_run = latest_run_id(cur, "r20_r02_phase_frame_items")
    phase = all_rows(cur, "select * from r20_r02_phase_frame_items where run_id=? order by phase_score desc", (phase_run,)) if phase_run else []
    ready_frames = [r for r in phase if r["phase_status"] == "PHASE_FRAME_READY"]
    micro = [r for r in phase if "MICRO" in r["frame_key"]]
    if phase:
        min_ready = min([float(r["phase_score"]) for r in ready_frames] or [0.0])
        max_micro = max([float(r["phase_score"]) for r in micro] or [0.0])
        ready = bool(ready_frames) and min_ready > max_micro and all(int(r["edge_supported_count"]) > 0 for r in ready_frames)
        items.append({
            "item_id": "R20_R02_PHASE_FRAME_NEGATIVE_CONTROL_SQL",
            "lane": "Structural/Semantic contrast",
            "evidence_type": "phase_negative_control",
            "decision": "PHASE_FUNCTION_READY_NO_GLOSS" if ready else "PHASE_AUDIT_PENDING",
            "functional_meaning": "phase boundary / bridge frame" if ready else "possible phase frame",
            "lexical_gloss_allowed": 0,
            "promote_to_books": 0,
            "confidence": round(min(0.9, min_ready - max_micro + 0.2), 3) if ready else 0.5,
            "reason": f"ready phase frames separate from LIVRN_MICRO: min_ready={min_ready}, max_micro={max_micro}",
            "next_action": "keep R20/R02 as phase function labels; keep LIVRN_MICRO audit-only",
            "evidence_json": {"source_run_id": phase_run, "ready_frames": ready_frames, "micro_controls": micro, "all_phase": phase},
        })

    npc_run = latest_run_id(cur, "npc_phrase_anchors")
    npc = all_rows(cur, "select * from npc_phrase_anchors where run_id=? order by phrase_id", (npc_run,)) if npc_run else []
    word = all_rows(cur, "select * from npc_wordcode_anchors where run_id=? order by anchor_id", (npc_run,)) if npc_run else []
    for phrase in npc:
        if phrase["digits"] in ("653768764", "65997854764"):
            hard = phrase["strength"] == "HARD_EXTERNAL_PHRASE" and int(phrase["verified_count"]) >= 2 and int(phrase["inbooks_count"]) == 0
            soft = phrase["strength"] == "SOFT_LEGACY_PHRASE"
            items.append({
                "item_id": f"NPC_ONLY_ANCHOR_{phrase['digits']}",
                "lane": "External anchor quarantine",
                "evidence_type": "npc_only_external_anchor",
                "decision": "NPC_ONLY_SEMANTIC_ANCHOR_QUARANTINED" if hard else "SOFT_NPC_ANCHOR_NOT_PROMOTABLE" if soft else "NPC_ANCHOR_AUDIT",
                "functional_meaning": phrase["expected_text"] or "<untranslated>",
                "lexical_gloss_allowed": 1 if hard else 0,
                "promote_to_books": 0,
                "confidence": 0.78 if hard else 0.35,
                "reason": f"scope={phrase['scope']}; verified_count={phrase['verified_count']}; inbooks_count={phrase['inbooks_count']}; promotion_status={phrase['promotion_status']}",
                "next_action": "retain NPC-only quarantine; do not project into book corpus" if hard else "seek independent source before any semantic use",
                "evidence_json": {"source_run_id": npc_run, "phrase": phrase, "word_segments": [w for w in word if w["phrase_id"] == phrase["phrase_id"]]},
            })

    return items


def send_discord(message: str) -> None:
    if not os.path.exists(DISCORD_SCRIPT):
        return
    cmd = f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(message)}"
    subprocess.run(["/bin/zsh", "-lc", cmd], check=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--discord", action="store_true")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    create_tables(cur)
    items = build_items(cur)

    functional_count = sum(1 for x in items if x["decision"].endswith("NO_GLOSS") or "FUNCTION_READY" in x["decision"] or "FUNCTIONAL_PROMOTION" in x["decision"])
    lexical_count = sum(int(x["lexical_gloss_allowed"]) for x in items)
    npc_only = sum(1 for x in items if x["evidence_type"] == "npc_only_external_anchor" and x["decision"] == "NPC_ONLY_SEMANTIC_ANCHOR_QUARANTINED")
    book_promote = sum(int(x["promote_to_books"]) for x in items)
    decision = "SEMANTIC_CONTRAST_FUNCTIONAL_ADVANCE_NO_BOOK_LEXICAL_PROMOTION"

    cur.execute(
        """
        insert into semantic_contrast_checkpoint_runs
        (created_at, decision, item_count, functional_promotable_count, lexical_gloss_allowed_count,
         npc_only_anchor_count, book_anchor_promotable_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), decision, len(items), functional_count, lexical_count, npc_only, book_promote, j({"items": [x["item_id"] for x in items]})),
    )
    run_id = cur.lastrowid
    for rank, item in enumerate(items, 1):
        cur.execute(
            """
            insert into semantic_contrast_checkpoint_items
            (run_id, rank, item_id, lane, evidence_type, decision, functional_meaning,
             lexical_gloss_allowed, promote_to_books, confidence, reason, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rank,
                item["item_id"],
                item["lane"],
                item["evidence_type"],
                item["decision"],
                item["functional_meaning"],
                int(item["lexical_gloss_allowed"]),
                int(item["promote_to_books"]),
                float(item["confidence"]),
                item["reason"],
                item["next_action"],
                j(item["evidence_json"]),
            ),
        )
    con.commit()

    summary = {
        "run_id": run_id,
        "decision": decision,
        "item_count": len(items),
        "functional_promotable_count": functional_count,
        "lexical_gloss_allowed_count": lexical_count,
        "npc_only_anchor_count": npc_only,
        "book_anchor_promotable_count": book_promote,
    }
    print(json.dumps(summary, ensure_ascii=False))

    if args.discord:
        lines = [
            f"[469][semantic-contrast][run={run_id}] avanço funcional sem promoção lexical",
            f"decisão={decision}",
            f"itens={len(items)} | funções promovíveis={functional_count} | gloss lexical permitido={lexical_count} | anchors NPC-only={npc_only} | anchors para livros={book_promote}",
            "mudança real: consolidamos função contrastiva auditável (branch/slot/fase) e mantivemos anchors externos em quarentena para não contaminar os livros.",
            "próximo: agentes verificam proveniência Elder2 e holdouts VINVIN/NAESE/R20 para decidir se a leitura honesta recebe novos rótulos funcionais.",
        ]
        send_discord("\n".join(lines))


if __name__ == "__main__":
    main()
