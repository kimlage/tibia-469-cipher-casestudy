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
PHRASE = "if belittle men"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def send(message: str) -> None:
    if not os.path.exists(DISCORD_SCRIPT):
        return
    cmd = f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(message)}"
    subprocess.run(["/bin/zsh", "-lc", cmd], check=False)


def rows(cur: sqlite3.Cursor, sql: str, params=()):
    return [dict(r) for r in cur.execute(sql, params).fetchall()]


def one(cur: sqlite3.Cursor, sql: str, params=()):
    r = cur.execute(sql, params).fetchone()
    return dict(r) if r else {}


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists belittle_men_formula_drift_gate_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          phrase text not null,
          hit_book_count integer not null,
          benna_family_hit_count integer not null,
          formula_tail_hit_count integer not null,
          decision text not null,
          gloss_allowed integer not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists belittle_men_formula_drift_gate_items(
          run_id integer not null,
          bookid text not null,
          has_phrase integer not null,
          has_benna_family integer not null,
          has_formula_tail integer not null,
          context text not null,
          decision text not null,
          evidence_json text not null,
          primary key(run_id, bookid)
        );
        """
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--discord", action="store_true")
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    create(cur)

    latest_shadow = one(cur, "select max(run_id) as run_id from best_shadow_book_translations")
    latest_reading = one(cur, "select max(run_id) as run_id from final_honest_reading_v16_books")
    shadows = rows(cur, "select bookid,best_shadow_text from best_shadow_book_translations where run_id=? and lower(best_shadow_text) like ?", (latest_shadow.get("run_id"), f"%{PHRASE}%"))
    books = [r["bookid"] for r in shadows]
    readings = {}
    if books:
        q = ",".join("?" for _ in books)
        readings = {r["bookid"]: r for r in rows(cur, f"select bookid,honest_text,functional_tags_json from final_honest_reading_v16_books where run_id=? and bookid in ({q})", (latest_reading.get("run_id"), *books))}

    items = []
    benna_hits = 0
    formula_hits = 0
    for s in shadows:
        b = s["bookid"]
        text = s["best_shadow_text"] or ""
        idx = text.lower().find(PHRASE)
        context = text[max(0, idx - 50):idx + len(PHRASE) + 80] if idx >= 0 else ""
        honest = readings.get(b, {}).get("honest_text", "")
        tags = readings.get(b, {}).get("functional_tags_json", "")
        has_benna = int("BENNA" in honest or "BENNA" in tags)
        has_tail = int("TTNVVN" in honest or "LTAST" in honest or "infinite fasten" in text.lower() or "infinity last" in text.lower())
        benna_hits += has_benna
        formula_hits += has_tail
        decision = "DISPLAY_DRIFT_IN_BENNA_FORMULA_ZONE_NO_GLOSS" if has_benna or has_tail else "REVIEW_OUTSIDE_FORMULA_ZONE"
        items.append({"bookid": b, "has_phrase": 1, "has_benna_family": has_benna, "has_formula_tail": has_tail, "context": context, "decision": decision, "shadow": text, "honest": honest, "tags": tags})

    hit_count = len(items)
    if hit_count and (benna_hits + formula_hits) >= hit_count:
        decision = "BELITTLE_MEN_IS_FORMULA_DISPLAY_DRIFT_NO_GLOSS"
        next_action = "mark this anomaly family as formula/display drift in cleaned frontier; do not translate literally"
    else:
        decision = "BELITTLE_MEN_HAS_OUTSIDE_FORMULA_CASES_REVIEW"
        next_action = "review outside-formula cases before masking"
    cur.execute(
        """
        insert into belittle_men_formula_drift_gate_runs
        (created_at, phrase, hit_book_count, benna_family_hit_count, formula_tail_hit_count, decision, gloss_allowed, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), PHRASE, hit_count, benna_hits, formula_hits, decision, 0, next_action, j({"items": items})),
    )
    run_id = cur.lastrowid
    for item in items:
        cur.execute(
            """
            insert into belittle_men_formula_drift_gate_items
            (run_id, bookid, has_phrase, has_benna_family, has_formula_tail, context, decision, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["bookid"], item["has_phrase"], item["has_benna_family"], item["has_formula_tail"], item["context"], item["decision"], j(item)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "hit_book_count": hit_count, "benna_family_hit_count": benna_hits, "formula_tail_hit_count": formula_hits, "gloss_allowed": 0, "next_action": next_action}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        send("\n".join([
            f"[469][belittle-men-gate][run={run_id}] família 'if belittle men' auditada",
            f"hits={hit_count} | em família BENNA={benna_hits} | com cauda fórmula/TTNVVN={formula_hits} | gloss=0",
            f"decisão={decision}",
            "interpretação: isso é drift de display em zona formulaica, não frase inglesa confiável. Vamos mascarar como fórmula/suspect em vez de fingir tradução.",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
