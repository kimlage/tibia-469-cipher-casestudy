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
        create table if not exists semantic_holdout_cluster_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          cluster_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists semantic_holdout_cluster_items(
          run_id integer not null,
          cluster_id text not null,
          source_claim_id text not null,
          books_json text not null,
          candidate_theme text not null,
          acceptance_status text not null,
          gloss_allowed integer not null,
          required_validation text not null,
          evidence_json text not null,
          primary key(run_id, cluster_id)
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

    latest_claim = one(cur, "select max(run_id) as run_id from external_semantic_claim_audit_items")
    claim = one(cur, "select * from external_semantic_claim_audit_items where run_id=? and claim_id='ARTICLE160_FAST_BOOT_FIFTEEN_STATUES'", (latest_claim.get("run_id"),))
    hit_books = json.loads(claim.get("hit_books_json") or "[]") if claim else []
    focus_books = [b for b in hit_books if b in ("15", "16", "39")]
    latest_reading = one(cur, "select max(run_id) as run_id from final_honest_reading_v16_books")
    readings = []
    if focus_books:
        q = ",".join("?" for _ in focus_books)
        readings = rows(cur, f"select bookid, reading_status, functional_tag_count, honest_text, functional_tags_json from final_honest_reading_v16_books where run_id=? and bookid in ({q}) order by cast(bookid as int)", (latest_reading.get("run_id"), *focus_books))

    cluster = {
        "cluster_id": "ARTICLE160_FAST_BOOT_STATUE_HOLDOUT",
        "source_claim_id": "ARTICLE160_FAST_BOOT_FIFTEEN_STATUES",
        "books": focus_books,
        "candidate_theme": "fast / boots / fifteen statues",
        "acceptance_status": "SEMANTIC_HOLDOUT_ONLY_NO_GLOSS",
        "gloss_allowed": 0,
        "required_validation": "needs exact full-sequence hit or independent in-game evidence tying the theme to books 15/16/39; current component-only match is insufficient",
        "evidence": {"claim": claim, "readings": readings},
    }
    cur.execute(
        """
        insert into semantic_holdout_cluster_runs(created_at, cluster_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?)
        """,
        (now(), 1, "SEMANTIC_HOLDOUT_REGISTERED_NO_TRANSLATION_PROMOTION", "use holdout only to evaluate future semantic models; do not alter book translations", j({"cluster": cluster})),
    )
    run_id = cur.lastrowid
    cur.execute(
        """
        insert into semantic_holdout_cluster_items
        (run_id, cluster_id, source_claim_id, books_json, candidate_theme, acceptance_status, gloss_allowed, required_validation, evidence_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, cluster["cluster_id"], cluster["source_claim_id"], j(cluster["books"]), cluster["candidate_theme"], cluster["acceptance_status"], cluster["gloss_allowed"], cluster["required_validation"], j(cluster["evidence"])),
    )
    con.commit()
    out = {"run_id": run_id, "decision": "SEMANTIC_HOLDOUT_REGISTERED_NO_TRANSLATION_PROMOTION", "books": focus_books, "candidate_theme": cluster["candidate_theme"], "gloss_allowed": 0}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        send("\n".join([
            f"[469][semantic-holdout][run={run_id}] holdout semântico registrado sem promoção",
            f"tema candidato={cluster['candidate_theme']} | livros foco={','.join(focus_books) or '<none>'} | gloss_allowed=0",
            "por que não promove: a fonte externa bate só por componentes e ajustes de zero, não por sequência completa no corpus canônico.",
            "uso correto: testar futuros modelos semânticos; se um modelo gerar esse tema independentemente para 15/16/39, isso vira evidência, não verdade automática.",
        ]))


if __name__ == "__main__":
    main()
