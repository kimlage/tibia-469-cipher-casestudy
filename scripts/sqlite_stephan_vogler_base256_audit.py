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
SOURCE_URL = "https://otland.net/threads/decoding-469-stephan-voglers-files-im-in-need-of-a-pic-extractor-editor.303637/post-2795682"
CLAIM_SEQ = "6653184326643486635834546035076418400106306154239717921"
CLAIM_TEXT = "Everything is a number!"
PRINTABLE = set(range(32, 127)) | {10, 13, 9}


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


def int_to_bytes_dec(s: str) -> bytes:
    n = int(s)
    if n == 0:
        return b"\x00"
    out = bytearray()
    while n:
        n, r = divmod(n, 256)
        out.append(r)
    return bytes(reversed(out))


def printable_score(bs: bytes):
    if not bs:
        return 0.0
    return sum(1 for b in bs if b in PRINTABLE) / len(bs)


def decode_latin(bs: bytes):
    return bs.decode("cp1252", errors="replace")


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists stephan_vogler_base256_audit_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          source_url text not null,
          claim_sequence text not null,
          decoded_claim text not null,
          claim_pass integer not null,
          book_count integer not null,
          printable_book_count integer not null,
          candidate_book_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists stephan_vogler_base256_audit_items(
          run_id integer not null,
          item_type text not null,
          item_id text not null,
          digit_len integer not null,
          byte_len integer not null,
          printable_score real not null,
          decoded_preview text not null,
          candidate_status text not null,
          evidence_json text not null,
          primary key(run_id, item_type, item_id)
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

    claim_bytes = int_to_bytes_dec(CLAIM_SEQ)
    decoded_claim = decode_latin(claim_bytes)
    claim_pass = int(decoded_claim == CLAIM_TEXT)
    book_rows = rows(cur, "select distinct bookid, digits from sheet__books order by cast(bookid as int)")
    items = []
    printable_books = 0
    candidate_books = 0
    for b in book_rows:
        digits = b["digits"] or ""
        try:
            bs = int_to_bytes_dec(digits)
            dec = decode_latin(bs)
            score = printable_score(bs)
            if score >= 0.8:
                printable_books += 1
            # Candidate requires high printable score and visible word-like spaces/vowels, but is audit-only.
            wordish = sum(1 for ch in dec if ch.lower() in "aeiou ") / max(1, len(dec))
            if score >= 0.9 and wordish >= 0.25:
                status = "BASE256_PRINTABLE_CANDIDATE_AUDIT_ONLY"
                candidate_books += 1
            else:
                status = "BASE256_NOT_READABLE_FOR_BOOK"
            items.append({"item_type": "book", "item_id": b["bookid"], "digit_len": len(digits), "byte_len": len(bs), "printable_score": round(score, 3), "decoded_preview": dec[:160], "candidate_status": status})
        except Exception as e:
            items.append({"item_type": "book", "item_id": b["bookid"], "digit_len": len(digits), "byte_len": 0, "printable_score": 0.0, "decoded_preview": str(e)[:160], "candidate_status": "BASE256_DECODE_ERROR"})

    decision = "BASE256_METHOD_VALID_FOR_VOGLER_CLAIM_NOT_BOOK_CORPUS" if claim_pass and candidate_books == 0 else "BASE256_METHOD_HAS_BOOK_CANDIDATES_REVIEW"
    next_action = "keep as method clue only; do not apply to books as translation" if candidate_books == 0 else "inspect printable book candidates manually before any promotion"
    cur.execute(
        """
        insert into stephan_vogler_base256_audit_runs
        (created_at, source_url, claim_sequence, decoded_claim, claim_pass, book_count, printable_book_count, candidate_book_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), SOURCE_URL, CLAIM_SEQ, decoded_claim, claim_pass, len(book_rows), printable_books, candidate_books, decision, next_action, j({"claim_bytes_hex": claim_bytes.hex(), "source_claim": CLAIM_TEXT, "items": items[:70]})),
    )
    run_id = cur.lastrowid
    cur.execute(
        """
        insert into stephan_vogler_base256_audit_items
        (run_id, item_type, item_id, digit_len, byte_len, printable_score, decoded_preview, candidate_status, evidence_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, "external_claim", "STEPHAN_VOGLER_NUMBERS", len(CLAIM_SEQ), len(claim_bytes), round(printable_score(claim_bytes), 3), decoded_claim, "CLAIM_VERIFIED" if claim_pass else "CLAIM_FAILED", j({"source_url": SOURCE_URL, "claim_text": CLAIM_TEXT, "bytes_hex": claim_bytes.hex()})),
    )
    for item in items:
        cur.execute(
            """
            insert into stephan_vogler_base256_audit_items
            (run_id, item_type, item_id, digit_len, byte_len, printable_score, decoded_preview, candidate_status, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["item_type"], item["item_id"], item["digit_len"], item["byte_len"], item["printable_score"], item["decoded_preview"], item["candidate_status"], j(item)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "decoded_claim": decoded_claim, "claim_pass": claim_pass, "book_count": len(book_rows), "printable_book_count": printable_books, "candidate_book_count": candidate_books, "next_action": next_action}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        send("\n".join([
            f"[469][vogler-base256][run={run_id}] pista Stephan Vogler/base256 auditada",
            f"claim externo decodifica='{decoded_claim}' | pass={claim_pass}",
            f"livros testados={len(book_rows)} | livros printable>=0.8={printable_books} | candidatos legíveis={candidate_books}",
            f"decisão={decision}",
            "interpretação: a conversão base10->base256 é real para a obra 'Numbers', mas não explica diretamente os livros 469 canônicos.",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
