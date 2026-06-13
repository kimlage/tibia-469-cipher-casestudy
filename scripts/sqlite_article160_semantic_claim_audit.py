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
SOURCE_URL = "https://tibiasecrets.com/article160"
CLAIM_ID = "ARTICLE160_FAST_BOOT_FIFTEEN_STATUES"
FULL_SEQ = "57652197278943151911851911801894452197278894383435081243485611451912167046726114580036"
PARTS = [
    "5765219727894315191185191180189445",
    "21972788943",
    "834",
    "3508124",
    "3485611451912167046726114580036",
]
CLAIM_TEXT = "You should be fast / set by boots / weigh fifteen statues"


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
        create table if not exists external_semantic_claim_audit_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          source_url text not null,
          claim_count integer not null,
          accepted_count integer not null,
          quarantine_count integer not null,
          rejected_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists external_semantic_claim_audit_items(
          run_id integer not null,
          claim_id text not null,
          source_url text not null,
          exact_sequence text not null,
          meaning_claim text not null,
          full_sequence_hit_count integer not null,
          component_hit_count integer not null,
          hit_books_json text not null,
          acceptance_status text not null,
          risk text not null,
          next_action text not null,
          evidence_json text not null,
          primary key(run_id, claim_id)
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

    books = rows(cur, "select distinct bookid, digits from sheet__books")
    full_hits = [b["bookid"] for b in books if FULL_SEQ in (b["digits"] or "")]
    part_hits = []
    all_hit_books = set(full_hits)
    for part in PARTS:
        hits = [b["bookid"] for b in books if part in (b["digits"] or "")]
        all_hit_books.update(hits)
        part_hits.append({"part": part, "hits": sorted(set(hits), key=lambda x: int(x) if x.isdigit() else 9999), "hit_count": len(set(hits))})

    latest = one(cur, "select max(run_id) as run_id from final_honest_reading_v16_books")
    qmarks = ",".join("?" for _ in all_hit_books) or "''"
    readings = []
    if all_hit_books:
        readings = rows(cur, f"select bookid, reading_status, functional_tag_count, honest_text, functional_tags_json from final_honest_reading_v16_books where run_id=? and bookid in ({qmarks}) order by cast(bookid as int)", (latest.get("run_id"), *sorted(all_hit_books, key=lambda x: int(x) if x.isdigit() else 9999)))

    if full_hits:
        status = "QUARANTINE_FULL_SEQUENCE_HIT_NEEDS_CONTRAST"
        risk = "external interpretation still adjusted/speculative; exact full sequence exists but must survive local contrast"
        next_action = "run local contrast against exact full-sequence books before any semantic promotion"
    else:
        status = "QUARANTINE_COMPONENT_ONLY_NO_PROMOTION"
        risk = "claim is assembled from components and added zeroes; no exact full-sequence hit in canonical books"
        next_action = "use only as semantic holdout for books 15/16/39; do not promote plaintext"

    cur.execute(
        """
        insert into external_semantic_claim_audit_runs
        (created_at, source_url, claim_count, accepted_count, quarantine_count, rejected_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), SOURCE_URL, 1, 0, 1, 0, "ARTICLE160_CLAIM_QUARANTINED_NO_GLOSS", next_action, j({"claim_id": CLAIM_ID, "part_hits": part_hits, "readings": readings})),
    )
    run_id = cur.lastrowid
    cur.execute(
        """
        insert into external_semantic_claim_audit_items
        (run_id, claim_id, source_url, exact_sequence, meaning_claim, full_sequence_hit_count, component_hit_count, hit_books_json, acceptance_status, risk, next_action, evidence_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, CLAIM_ID, SOURCE_URL, FULL_SEQ, CLAIM_TEXT, len(set(full_hits)), len(part_hits), j(sorted(all_hit_books, key=lambda x: int(x) if x.isdigit() else 9999)), status, risk, next_action, j({"full_hits": full_hits, "part_hits": part_hits, "readings": readings})),
    )
    con.commit()
    out = {"run_id": run_id, "decision": "ARTICLE160_CLAIM_QUARANTINED_NO_GLOSS", "full_sequence_hit_count": len(set(full_hits)), "hit_books": sorted(all_hit_books, key=lambda x: int(x) if x.isdigit() else 9999), "acceptance_status": status, "next_action": next_action}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        send("\n".join([
            f"[469][semantic-claim-audit][run={run_id}] artigo TibiaSecrets article160 auditado como hipótese, não verdade",
            f"claim={CLAIM_TEXT}",
            f"sequência completa: hits={len(set(full_hits))}; componentes batem em livros={','.join(sorted(all_hit_books, key=lambda x: int(x) if x.isdigit() else 9999))}",
            f"status={status}",
            "interpretação: a fonte ajuda a escolher uma direção semântica, mas mistura componentes/zeros e não autoriza gloss dos livros.",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
