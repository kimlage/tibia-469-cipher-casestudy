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
TARGET_BOOKS = ("4", "34", "49")


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
        create table if not exists final_residual_contig_support_probe_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          target_books_json text not null,
          contig_support_count integer not null,
          edge_support_count integer not null,
          unique_ngram_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists final_residual_contig_support_probe_items(
          run_id integer not null,
          bookid text not null,
          in_contig_path integer not null,
          edge_support_count integer not null,
          unique_ngram text,
          dominant_class text,
          decision text not null,
          next_action text not null,
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

    latest_contig = one(cur, "select max(run_id) as run_id from contig_max_overlap_items")
    latest_edge = one(cur, "select max(run_id) as run_id from contig_max_overlap_edges")
    latest_seg = one(cur, "select max(run_id) as run_id from hard_residual_segmentation_probe_items")
    latest_ngram = one(cur, "select max(run_id) as run_id from hard_residual_ngram_probe_items")

    contig_rows = rows(
        cur,
        "select basecontigid, booksinorder from contig_max_overlap_items where run_id=?",
        (latest_contig.get("run_id"),),
    )
    edge_rows = rows(
        cur,
        "select basecontigid, edge_index, left_bookid, right_bookid, overlap_symbols, overlap_text from contig_max_overlap_edges where run_id=?",
        (latest_edge.get("run_id"),),
    )
    seg_by_book = {
        r["bookid"]: r
        for r in rows(
            cur,
            "select bookid, dominant_class, recommendation, special_positions_json from hard_residual_segmentation_probe_items where run_id=?",
            (latest_seg.get("run_id"),),
        )
    }
    ng_by_book = {
        r["bookid"]: r
        for r in rows(
            cur,
            "select bookid, ngram, candidate_status, recommendation from hard_residual_ngram_probe_items where run_id=? and candidate_status='UNIQUE_RESIDUAL_COMPONENT'",
            (latest_ngram.get("run_id"),),
        )
    }

    items = []
    contig_support_count = 0
    edge_support_count = 0
    unique_ngram_count = 0
    for bookid in TARGET_BOOKS:
        paths = [r for r in contig_rows if bookid in (r.get("booksinorder") or "").split("->")]
        edges = [r for r in edge_rows if r.get("left_bookid") == bookid or r.get("right_bookid") == bookid]
        seg = seg_by_book.get(bookid, {})
        ng = ng_by_book.get(bookid, {})
        if paths:
            contig_support_count += 1
        if edges:
            edge_support_count += len(edges)
        if ng:
            unique_ngram_count += 1
        decision = "NO_CONTIG_OR_EDGE_SUPPORT_REQUIRES_NEW_EVIDENCE"
        next_action = "do not reopen current route; require external anchor, non-fragmented overlap, or new row0 contrast excluding known controls"
        if paths or edges:
            decision = "HAS_CONTIG_SUPPORT_REVIEW_MANUALLY"
            next_action = "review contig edge before any promotion"
        item = {
            "bookid": bookid,
            "in_contig_path": 1 if paths else 0,
            "edge_support_count": len(edges),
            "unique_ngram": ng.get("ngram"),
            "dominant_class": seg.get("dominant_class"),
            "decision": decision,
            "next_action": next_action,
            "evidence": {"contig_paths": paths, "edges": edges, "segmentation": seg, "ngram": ng},
        }
        items.append(item)

    decision = "FINAL_RESIDUALS_HAVE_NO_CONTIG_SUPPORT_KEEP_BLOCKED"
    next_action = "switch from contig promotion to new mechanical routes: non-fragmented cross-book overlap, external exact anchor, or residual class model"
    cur.execute(
        """
        insert into final_residual_contig_support_probe_runs
        (created_at, target_books_json, contig_support_count, edge_support_count, unique_ngram_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), j(TARGET_BOOKS), contig_support_count, edge_support_count, unique_ngram_count, decision, next_action, j({"latest_runs": {"contig": latest_contig, "edge": latest_edge, "seg": latest_seg, "ngram": latest_ngram}, "items": items})),
    )
    run_id = cur.lastrowid
    for item in items:
        cur.execute(
            """
            insert into final_residual_contig_support_probe_items
            (run_id, bookid, in_contig_path, edge_support_count, unique_ngram, dominant_class, decision, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["bookid"], item["in_contig_path"], item["edge_support_count"], item["unique_ngram"], item["dominant_class"], item["decision"], item["next_action"], j(item["evidence"])),
        )
    con.commit()

    out = {
        "run_id": run_id,
        "decision": decision,
        "target_books": list(TARGET_BOOKS),
        "contig_support_count": contig_support_count,
        "edge_support_count": edge_support_count,
        "unique_ngram_count": unique_ngram_count,
        "next_action": next_action,
    }
    print(json.dumps(out, ensure_ascii=False))

    if args.discord:
        lines = [
            f"[469][residual-contig-support][run={run_id}] checkpoint dos livros finais sem função",
            "alvos=4,34,49 | suporte por contig=0 | suporte por borda=0 | n-grams únicos=3",
            "interpretação: os três resíduos não estão conectados aos contigs máximos validados. Continuar tentando promoção por contig/overlap atual seria circular.",
            "decisão operacional: manter bloqueados e só reabrir com rota mecanicamente diferente: âncora externa exata, overlap não-fragmentado novo, ou modelo de classe residual que explique os controles.",
            "impacto na tradução: melhora a confiabilidade, mas ainda não cria gloss semântico. A tradução lexical segura continua em 0%; a próxima frente precisa descobrir significado, não só função.",
        ]
        send("\n".join(lines))


if __name__ == "__main__":
    main()
