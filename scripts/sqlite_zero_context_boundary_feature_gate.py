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
        create table if not exists zero_context_boundary_feature_gate_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          source_zero_run_id integer not null,
          accepted_feature_count integer not null,
          new_functional_promotion_count integer not null,
          gloss_allowed integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists zero_context_boundary_feature_gate_items(
          run_id integer not null,
          context_key text not null,
          books_json text not null,
          dominant_existing_tags_json text not null,
          feature_status text not null,
          decision text not null,
          evidence_json text not null,
          primary key(run_id, context_key)
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

    zrun = one(cur, "select max(run_id) as run_id from zero_context_recurrence_scorer_items")
    zitems = rows(cur, "select * from zero_context_recurrence_scorer_items where run_id=? and decision like 'HIGH_VALUE%'", (zrun.get("run_id"),))
    latest_reading = one(cur, "select max(run_id) as run_id from final_honest_reading_v16_books")
    accepted = []
    for zi in zitems:
        books = json.loads(zi["books_json"] or "[]")
        if not books:
            continue
        q = ",".join("?" for _ in books)
        readings = rows(cur, f"select bookid,functional_tags_json,functional_tag_count from final_honest_reading_v16_books where run_id=? and bookid in ({q})", (latest_reading.get("run_id"), *books))
        tag_counts = {}
        for r in readings:
            try:
                tags = json.loads(r.get("functional_tags_json") or "[]")
            except Exception:
                tags = []
            for tag in tags:
                tid = tag.get("tag_id") or tag.get("label") or "UNKNOWN"
                tag_counts[tid] = tag_counts.get(tid, 0) + 1
        dominant = sorted(tag_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
        tagged_book_count = sum(1 for r in readings if int(r.get("functional_tag_count") or 0) > 0)
        if tagged_book_count == len(books) and dominant:
            status = "ACCEPT_AS_EXISTING_BOUNDARY_FEATURE_NO_NEW_PROMOTION"
            decision = "use as structural feature for future segmentation scorer; no new functional tag"
        else:
            status = "AUDIT_ONLY_MIXED_OR_UNTAGGED"
            decision = "do not use until all books are covered by compatible existing families"
        accepted.append({"context_key": zi["context_key"], "books": books, "dominant_existing_tags": dominant, "feature_status": status, "decision": decision, "source": dict(zi)})

    accepted_count = sum(1 for i in accepted if i["feature_status"].startswith("ACCEPT"))
    cur.execute(
        """
        insert into zero_context_boundary_feature_gate_runs
        (created_at, source_zero_run_id, accepted_feature_count, new_functional_promotion_count, gloss_allowed, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), zrun.get("run_id") or 0, accepted_count, 0, 0, "ZERO_CONTEXT_FEATURES_ACCEPTED_FOR_SCORING_ONLY", "feed accepted zero-context features into segmentation scorer; no book text/gloss change", j({"items": accepted})),
    )
    run_id = cur.lastrowid
    for item in accepted:
        cur.execute(
            """
            insert into zero_context_boundary_feature_gate_items
            (run_id, context_key, books_json, dominant_existing_tags_json, feature_status, decision, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["context_key"], j(item["books"]), j(item["dominant_existing_tags"]), item["feature_status"], item["decision"], j(item)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": "ZERO_CONTEXT_FEATURES_ACCEPTED_FOR_SCORING_ONLY", "accepted_feature_count": accepted_count, "new_functional_promotion_count": 0, "gloss_allowed": 0}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        send("\n".join([
            f"[469][zero-boundary-gate][run={run_id}] 00 como feature estrutural, não tradução",
            f"features aceitas para scoring={accepted_count} | novas promoções funcionais=0 | gloss=0",
            "interpretação: os 00 recorrentes reforçam famílias estruturais já aceitas, principalmente C86/VNCTIIN/R20/BENNA; não abrem significado lexical.",
            "próxima ação: usar essas features para rankear segmentações e anomalias, sem alterar os livros finais.",
        ]))


if __name__ == "__main__":
    main()
