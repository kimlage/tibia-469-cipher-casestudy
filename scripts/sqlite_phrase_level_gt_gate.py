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
TARGETS = ("Knightmare1", "Poll2014_C")


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def rows(cur, sql, params=()):
    return [dict(r) for r in cur.execute(sql, params).fetchall()]


def create_tables(cur):
    cur.executescript("""
    create table if not exists phrase_level_gt_gate_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        candidate_count integer not null,
        phrase_level_promotable_count integer not null,
        component_gloss_promotable_count integer not null,
        book_decode_promotable_count integer not null,
        payload_json text not null
    );
    create table if not exists phrase_level_gt_gate_items (
        run_id integer not null,
        refname text not null,
        digits text not null,
        expected_phrase text not null,
        decoded_phrase text,
        gt_pass integer not null,
        verifiedcount integer not null,
        decision text not null,
        scope text not null,
        component_gloss_allowed integer not null,
        book_decode_promotable integer not null,
        risk text not null,
        next_action text not null,
        evidence_json text not null,
        primary key (run_id, refname)
    );
    """)


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

    items = []
    for ref in TARGETS:
        gt = rows(cur, "select * from sheet__externalgroundtruthcheck_v120 where refname=? order by __export_id desc limit 1", (ref,))
        refs = rows(cur, "select __export_id,__row_index,refname,type,source,numerictext,digitssanitized,dp_strictplus,codestreamdp_concat_readable_v120 from sheet__externalrefs_v115 where refname=? order by __export_id desc", (ref,))
        val = rows(cur, "select __export_id,__row_index,reference,numerictext,verifiedsources,verifiedcount,notes from sheet__externalvalidation_v129 where reference like ? order by __export_id desc", (f"%{ref.split('_')[0]}%",))
        # Poll row does not contain refname directly in reference, fallback by exact digits after refs are known.
        digits = refs[0]["digitssanitized"] if refs else ""
        if ref == "Poll2014_C":
            val = rows(cur, "select __export_id,__row_index,reference,numerictext,verifiedsources,verifiedcount,notes from sheet__externalvalidation_v129 where numerictext like '%663 902073%' order by __export_id desc")
        elif ref == "Knightmare1":
            val = rows(cur, "select __export_id,__row_index,reference,numerictext,verifiedsources,verifiedcount,notes from sheet__externalvalidation_v129 where numerictext like '%3478 67 90871%' order by __export_id desc")
        verified = 0
        for v in val:
            try:
                verified = max(verified, int(v.get("verifiedcount") or 0))
            except ValueError:
                pass
        gtrow = gt[0] if gt else {}
        expected = gtrow.get("expected") or ""
        decoded = gtrow.get("decoded_lossless_v120") or (refs[0].get("dp_strictplus") if refs else "")
        gt_pass = 1 if str(gtrow.get("pass") or "").upper() == "TRUE" else 0
        decision = "PHRASE_LEVEL_GT_PROMOTABLE_NO_COMPONENT_GLOSS" if gt_pass and verified >= 1 else "GT_AUDIT_ONLY"
        risk = "phrase-level roundtrip can validate external full phrase, but component words may be DP artifacts or normalized display text"
        next_action = "use as external phrase holdout/validation only; do not derive word-level dictionary or book semantics"
        items.append({
            "refname": ref,
            "digits": digits,
            "expected_phrase": expected,
            "decoded_phrase": decoded,
            "gt_pass": gt_pass,
            "verifiedcount": verified,
            "decision": decision,
            "scope": "external_phrase_level_gt",
            "component_gloss_allowed": 0,
            "book_decode_promotable": 0,
            "risk": risk,
            "next_action": next_action,
            "evidence": {"groundtruth": gt, "externalrefs": refs, "validation": val},
        })

    phrase_promote = sum(1 for x in items if x["decision"] == "PHRASE_LEVEL_GT_PROMOTABLE_NO_COMPONENT_GLOSS")
    cur.execute("""
        insert into phrase_level_gt_gate_runs
        (created_at, decision, candidate_count, phrase_level_promotable_count, component_gloss_promotable_count, book_decode_promotable_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
    """, (now(), "PHRASE_LEVEL_GT_GATE_READY", len(items), phrase_promote, 0, 0, j({"targets": list(TARGETS)})))
    run_id = cur.lastrowid
    for item in items:
        cur.execute("""
            insert into phrase_level_gt_gate_items
            (run_id, refname, digits, expected_phrase, decoded_phrase, gt_pass, verifiedcount, decision, scope,
             component_gloss_allowed, book_decode_promotable, risk, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_id, item["refname"], item["digits"], item["expected_phrase"], item["decoded_phrase"], item["gt_pass"], item["verifiedcount"], item["decision"], item["scope"], item["component_gloss_allowed"], item["book_decode_promotable"], item["risk"], item["next_action"], j(item["evidence"])))
    con.commit()

    out = {"run_id": run_id, "decision": "PHRASE_LEVEL_GT_GATE_READY", "candidate_count": len(items), "phrase_level_promotable_count": phrase_promote, "component_gloss_promotable_count": 0, "book_decode_promotable_count": 0}
    print(json.dumps(out, ensure_ascii=False))

    if args.discord:
        lines = [
            f"[469][phrase-gt-gate][run={run_id}] anchors externos frase-level registrados",
            f"promovíveis como frase inteira={phrase_promote}/{len(items)} | gloss de componentes=0 | promoção para livros=0",
        ]
        for item in items:
            lines.append(f"{item['refname']}: pass={item['gt_pass']} | verified={item['verifiedcount']} | esperado='{item['expected_phrase']}' | decisão={item['decision']}")
        lines.append("uso permitido: validação/holdout de frase externa; proibido decompor em dicionário ou traduzir livros a partir disso.")
        send_discord("\n".join(lines))


if __name__ == "__main__":
    main()
