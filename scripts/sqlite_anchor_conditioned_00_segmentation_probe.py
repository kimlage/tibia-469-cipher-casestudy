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
CONTEXT = 8


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


def find_all(text: str, needle: str):
    start = 0
    while True:
        pos = text.find(needle, start)
        if pos < 0:
            break
        yield pos
        start = pos + 1


def create(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        create table if not exists anchor_conditioned_00_segmentation_probe_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          anchor_count integer not null,
          inbook_anchor_count integer not null,
          total_occurrence_count integer not null,
          high_specificity_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists anchor_conditioned_00_segmentation_probe_items(
          run_id integer not null,
          anchor_id text not null,
          digits text not null,
          anchor_strength text not null,
          occurrence_count integer not null,
          book_count integer not null,
          boundary_fit_count integer not null,
          zero_adjacent_count integer not null,
          specificity_status text not null,
          decision text not null,
          evidence_json text not null,
          primary key(run_id, anchor_id)
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

    latest_anchor = one(cur, "select max(run_id) as run_id from npc_wordcode_anchors")
    anchors = rows(cur, "select * from npc_wordcode_anchors where run_id=? order by digits, anchor_id", (latest_anchor.get("run_id"),))
    latest_paths = one(cur, "select max(run_id) as run_id from row0_path_reconstruction_items")
    paths = rows(cur, "select bookid, reconstructed_digits, decoded_text, omit_pattern_1based, selected from row0_path_reconstruction_items where run_id=? and selected=1", (latest_paths.get("run_id"),))
    latest_block = one(cur, "select max(run_id) as run_id from structural_family_reopen_block_items")
    blocked = rows(cur, "select family, affected_books_json from structural_family_reopen_block_items where run_id=?", (latest_block.get("run_id"),)) if latest_block.get("run_id") is not None else []
    blocked_books = set()
    for b in blocked:
        try:
            blocked_books.update(json.loads(b.get("affected_books_json") or "[]"))
        except Exception:
            pass

    items = []
    total_occ = 0
    high_specificity = 0
    inbook_anchor_count = 0
    for anchor in anchors:
        digits = anchor["digits"]
        occs = []
        books = set()
        boundary_fit = 0
        zero_adjacent = 0
        for p in paths:
            text = p["reconstructed_digits"] or ""
            decoded = p["decoded_text"] or ""
            for pos in find_all(text, digits):
                books.add(p["bookid"])
                before = text[max(0, pos - CONTEXT):pos]
                after = text[pos + len(digits):pos + len(digits) + CONTEXT]
                prev_char = text[pos - 1:pos]
                next_char = text[pos + len(digits):pos + len(digits) + 1]
                z_adj = int(prev_char == "0" or next_char == "0" or before.endswith("00") or after.startswith("00"))
                if z_adj:
                    zero_adjacent += 1
                # Boundary fit is structural only: short anchor at start/end, adjacent zero, or isolated by reconstructed omission boundary marker.
                bfit = int(pos == 0 or pos + len(digits) == len(text) or z_adj)
                if bfit:
                    boundary_fit += 1
                occs.append({"bookid": p["bookid"], "pos": pos, "before": before, "after": after, "decoded_context": decoded[max(0, pos//2 - 8):pos//2 + 16], "zero_adjacent": bool(z_adj), "boundary_fit": bool(bfit), "blocked_book": p["bookid"] in blocked_books})
        occ_count = len(occs)
        total_occ += occ_count
        if occ_count:
            inbook_anchor_count += 1
        if occ_count == 0:
            specificity = "EXTERNAL_ONLY_HOLDOUT"
            decision = "use for external segmentation validation only"
        elif len(books) <= 3 and boundary_fit >= max(1, occ_count // 2):
            specificity = "HIGH_SPECIFICITY_BOUNDARY_CANDIDATE"
            decision = "candidate boundary class; no word meaning promotion"
            high_specificity += 1
        elif len(books) <= 10:
            specificity = "MEDIUM_SPECIFICITY_AUDIT_ONLY"
            decision = "audit boundary pattern; no semantic promotion"
        else:
            specificity = "LOW_SPECIFICITY_NO_PROMOTION"
            decision = "too common for wordcode transfer"
        items.append({"anchor": anchor, "occurrences": occs, "book_count": len(books), "occurrence_count": occ_count, "boundary_fit_count": boundary_fit, "zero_adjacent_count": zero_adjacent, "specificity_status": specificity, "decision": decision})

    decision = "ANCHOR_BOUNDARY_CANDIDATES_FOUND_NO_GLOSS" if high_specificity else "NPC_ANCHORS_DO_NOT_TRANSFER_TO_BOOK_BOUNDARIES"
    next_action = "open narrow boundary-class audit for high-specificity candidates only" if high_specificity else "use NPC anchors only as external holdouts; continue semantic model without book promotion"
    cur.execute(
        """
        insert into anchor_conditioned_00_segmentation_probe_runs
        (created_at, anchor_count, inbook_anchor_count, total_occurrence_count, high_specificity_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), len(anchors), inbook_anchor_count, total_occ, high_specificity, decision, next_action, j({"latest_anchor": latest_anchor, "latest_paths": latest_paths, "items": items})),
    )
    run_id = cur.lastrowid
    for item in items:
        a = item["anchor"]
        cur.execute(
            """
            insert into anchor_conditioned_00_segmentation_probe_items
            (run_id, anchor_id, digits, anchor_strength, occurrence_count, book_count, boundary_fit_count, zero_adjacent_count, specificity_status, decision, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, a["anchor_id"], a["digits"], a["strength"], item["occurrence_count"], item["book_count"], item["boundary_fit_count"], item["zero_adjacent_count"], item["specificity_status"], item["decision"], j(item)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "anchor_count": len(anchors), "inbook_anchor_count": inbook_anchor_count, "total_occurrence_count": total_occ, "high_specificity_count": high_specificity, "next_action": next_action}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        lines = [
            f"[469][anchor-00-segmentation][run={run_id}] probe de boundary com anchors NPC + 00",
            f"anchors={len(anchors)} | anchors que aparecem em livros={inbook_anchor_count} | ocorrências={total_occ} | candidatos high-specificity={high_specificity}",
            f"decisão={decision}",
            "leitura: anchors NPC foram usados só para fronteira/segmentação; nenhum significado foi transferido para livros.",
            f"próxima ação: {next_action}",
        ]
        send("\n".join(lines))


if __name__ == "__main__":
    main()
