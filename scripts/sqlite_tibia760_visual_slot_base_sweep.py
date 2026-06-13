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

UNDEFINED_CP1252 = {0x81, 0x8D, 0x8F, 0x90, 0x9D}
COMMON = {
    "the",
    "and",
    "you",
    "that",
    "this",
    "number",
    "everything",
    "is",
    "a",
    "to",
    "of",
    "in",
    "be",
    "not",
    "with",
    "for",
    "as",
    "on",
}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def send(message: str) -> None:
    if not os.path.exists(DISCORD_SCRIPT):
        return
    subprocess.run(
        [
            "/bin/zsh",
            "-lc",
            f"source ~/.env 2>/dev/null || true; python {DISCORD_SCRIPT} send --channel {DISCORD_CHANNEL} --message {json.dumps(message)}",
        ],
        check=False,
    )


def rows(cur: sqlite3.Cursor, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in cur.execute(sql, params).fetchall()]


def tibia760_visual_slots() -> list[str]:
    # The extracted 7.60 Tibia.pic font sheet visibly contains the classic
    # client's extended text pages.  For a base-N test the important point is
    # preserving slot order, not forcing a modern printable-only charset.  Keep
    # bytes 32..255 as visual slots; undefined CP1252 slots become private-use
    # sentinels so the base index is not shifted.
    alphabet: list[str] = []
    for byte in range(32, 256):
        if byte in UNDEFINED_CP1252:
            alphabet.append(chr(0xE000 + byte))
        else:
            alphabet.append(bytes([byte]).decode("cp1252"))
    return alphabet


ALPHABET = tibia760_visual_slots()


def to_base(digits: str, base: int) -> str:
    n = int(digits)
    if n == 0:
        return ALPHABET[0]
    out: list[str] = []
    while n:
        n, r = divmod(n, base)
        out.append(ALPHABET[r])
    return "".join(reversed(out))


def is_private(ch: str) -> bool:
    return 0xE000 <= ord(ch) <= 0xF8FF


def score_text(text: str) -> tuple[float, str]:
    if not text:
        return -999.0, "empty"
    private = sum(1 for ch in text if is_private(ch)) / len(text)
    alpha = sum(1 for ch in text if ch.isalpha() or ch == " ") / len(text)
    punct = sum(1 for ch in text if not ch.isalnum() and ch != " " and not is_private(ch)) / len(text)
    space = text.count(" ") / len(text)
    words = [w.strip(".,;:!?\"'()[]{}<>").lower() for w in text.split()]
    common = sum(1 for w in words if w in COMMON)
    long_alpha = sum(1 for w in words if len(w) >= 3 and w.isalpha())
    score = round(alpha * 65 + min(space, 0.22) * 35 + common * 12 + long_alpha * 2 - punct * 65 - private * 110, 3)
    return score, f"alpha={alpha:.3f};space={space:.3f};punct={punct:.3f};private={private:.3f};common={common};long_alpha={long_alpha}"


def clean_preview(text: str, limit: int = 180) -> str:
    out = []
    for ch in text[:limit]:
        if is_private(ch):
            out.append(f"<U+{ord(ch):04X}>")
        elif ch in "\n\r\t":
            out.append(" ")
        else:
            out.append(ch)
    return "".join(out)


def create_tables(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists tibia760_visual_slot_base_sweep_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            alphabet_len integer not null,
            item_count integer not null,
            strong_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists tibia760_visual_slot_base_sweep_items(
            run_id integer not null,
            item_type text not null,
            item_id text not null,
            best_base integer not null,
            best_score real not null,
            decoded_preview text not null,
            readability_reason text not null,
            candidate_status text not null,
            evidence_json text not null,
            primary key(run_id,item_type,item_id)
        );
        """
    )


def collect_items(cur: sqlite3.Cursor) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for book in rows(cur, "select distinct bookid item_id, digits from sheet__books order by cast(bookid as int)"):
        if book["digits"]:
            items.append({"item_type": "book", "item_id": str(book["item_id"]), "digits": "".join(ch for ch in str(book["digits"]) if ch.isdigit())})
    frontier = rows(cur, "select max(run_id) run_id from npc_sequence_frontier")
    frontier_run = frontier[0]["run_id"] if frontier else None
    if frontier_run is not None:
        for seq in rows(cur, "select sequence_id item_id, digits from npc_sequence_frontier where run_id=? and digits is not null", (frontier_run,)):
            digits = "".join(ch for ch in str(seq["digits"]) if ch.isdigit())
            if digits:
                items.append({"item_type": "external", "item_id": str(seq["item_id"]), "digits": digits})
    return items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    parser.add_argument("--discord", action="store_true")
    args = parser.parse_args()

    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    create_tables(cur)

    items = collect_items(cur)
    results = []
    strong_count = 0
    for item in items:
        best = {"base": 0, "score": -999.0, "text": "", "reason": ""}
        for base in range(64, len(ALPHABET) + 1):
            try:
                text = to_base(item["digits"], base)
                score, reason = score_text(text)
            except Exception:
                continue
            if score > best["score"]:
                best = {"base": base, "score": score, "text": text, "reason": reason}
        text_lower_words = best["text"].lower().split()
        status = (
            "TIBIA760_VISUAL_SLOT_STRONG_CANDIDATE_AUDIT_ONLY"
            if best["score"] >= 55 and any(word in COMMON for word in text_lower_words) and len(best["text"]) >= 8
            else "TIBIA760_VISUAL_SLOT_NO_READABLE_TEXT"
        )
        if status.startswith("TIBIA760_VISUAL_SLOT_STRONG"):
            strong_count += 1
        results.append(
            {
                "item_type": item["item_type"],
                "item_id": item["item_id"],
                "best_base": best["base"],
                "best_score": best["score"],
                "decoded_preview": clean_preview(best["text"]),
                "readability_reason": best["reason"],
                "candidate_status": status,
            }
        )

    decision = "TIBIA760_VISUAL_SLOT_HAS_CANDIDATES" if strong_count else "TIBIA760_VISUAL_SLOT_NO_TRANSLATION_SIGNAL"
    next_action = "manual audit strong candidates only" if strong_count else "close 7.60 visual-slot base-N route; pivot to non-base mechanical/semantic constraints"
    payload = {
        "source_artifacts": [
            "./tmp/tibia_clients/tibia760_extracted/image_02_256x128.png",
            "./tmp/tibia_clients/tibia760_extracted/image_07_256x128.png",
        ],
        "alphabet_start": "".join(ch if not is_private(ch) else "?" for ch in ALPHABET[:48]),
        "items": results,
    }
    cur.execute(
        "insert into tibia760_visual_slot_base_sweep_runs(created_at,alphabet_len,item_count,strong_count,decision,next_action,payload_json) values (?,?,?,?,?,?,?)",
        (now(), len(ALPHABET), len(items), strong_count, decision, next_action, j(payload)),
    )
    run_id = cur.lastrowid
    for result in results:
        cur.execute(
            "insert into tibia760_visual_slot_base_sweep_items(run_id,item_type,item_id,best_base,best_score,decoded_preview,readability_reason,candidate_status,evidence_json) values (?,?,?,?,?,?,?,?,?)",
            (
                run_id,
                result["item_type"],
                result["item_id"],
                result["best_base"],
                result["best_score"],
                result["decoded_preview"],
                result["readability_reason"],
                result["candidate_status"],
                j(result),
            ),
        )
    con.commit()

    top = sorted(results, key=lambda row: row["best_score"], reverse=True)[:10]
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "alphabet_len": len(ALPHABET),
                "item_count": len(items),
                "strong_count": strong_count,
                "top": top,
            },
            ensure_ascii=False,
        )
    )
    if args.discord:
        lines = [
            f"[469][tibia760-visual-slot-base][run={run_id}] varredura com slots visuais reais do cliente 7.60",
            f"alfabeto=slots 32..255 preservados | tamanho={len(ALPHABET)} | itens={len(items)} | candidatos fortes={strong_count} | gloss=0",
        ]
        for row in top[:5]:
            lines.append(
                f"{row['item_type']}:{row['item_id']} base={row['best_base']} score={row['best_score']} {row['candidate_status']} preview={row['decoded_preview'][:70]}"
            )
        lines.append(f"decisão={decision}")
        lines.append(f"próxima ação: {next_action}")
        send("\n".join(lines))


if __name__ == "__main__":
    main()
