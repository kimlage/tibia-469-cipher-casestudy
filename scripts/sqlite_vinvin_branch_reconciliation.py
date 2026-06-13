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


def rows(cur, sql, params=()):
    return [dict(r) for r in cur.execute(sql, params).fetchall()]


def latest(cur, table):
    r = cur.execute(f"select max(run_id) from {table}").fetchone()
    return r[0] if r and r[0] is not None else None


def create_tables(cur):
    cur.executescript(
        """
        create table if not exists vinvin_branch_reconciliation_runs (
            run_id integer primary key autoincrement,
            created_at text not null,
            decision text not null,
            suffix_class_count integer not null,
            reconciled_ready_count integer not null,
            discrepancy_count integer not null,
            lexical_gloss_allowed_count integer not null,
            payload_json text not null
        );
        create table if not exists vinvin_branch_reconciliation_items (
            run_id integer not null,
            suffix_class text not null,
            suffix_books_json text not null,
            strict_edge_books_json text not null,
            missing_strict_edge_books_json text not null,
            suffix_contig_supported_count integer not null,
            strict_edge_supported_count integer not null,
            negative_or_partial_count integer not null,
            branch_score real not null,
            decision text not null,
            confidence real not null,
            gloss_allowed integer not null,
            reason text not null,
            next_action text not null,
            evidence_json text not null,
            primary key (run_id, suffix_class)
        );
        """
    )


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

    branch_run = latest(cur, "vinvin_branch_subfunction_items")
    suffix_run = latest(cur, "vinvin_suffix_contrast_items")
    cross_run = latest(cur, "vinvin_vtlr_cross_contig_items")

    branch_rows = rows(cur, "select * from vinvin_branch_subfunction_items where run_id=? order by suffix_class", (branch_run,))
    suffix_rows = rows(cur, "select * from vinvin_suffix_contrast_items where run_id=?", (suffix_run,))
    cross_rows = rows(cur, "select * from vinvin_vtlr_cross_contig_items where run_id=?", (cross_run,))

    items = []
    for b in branch_rows:
        cls = b["suffix_class"]
        s_books = sorted({str(r["bookid"]) for r in suffix_rows if r["suffix_class"] == cls and r["contig_support_class"] != "NO_CONTIG_EDGE_SUPPORT"}, key=lambda x: int(x) if x.isdigit() else x)
        e_books = sorted({str(r["bookid"]) for r in cross_rows if r["suffix_class"] == cls and "edge" in (r.get("contig_support_json") or "").lower()}, key=lambda x: int(x) if x.isdigit() else x)
        missing = [x for x in s_books if x not in e_books]
        if b["branch_status"] == "SUBFUNCTION_READY" and len(e_books) >= 2 and int(b["partial_or_negative_count"]) == 0:
            decision = "FUNCTIONAL_READY_STRICT_EDGE_SUPPORTED_WITH_SUFFIX_DISCREPANCY" if missing else "FUNCTIONAL_READY_STRICT_EDGE_SUPPORTED"
            conf = min(0.9, float(b["branch_score"]) - (0.08 if missing else 0.0))
            next_action = "keep functional promotion no gloss; reconcile missing suffix-only books before broader generalization" if missing else "keep functional promotion no gloss"
        elif b["branch_status"] == "SUBFUNCTION_READY":
            decision = "FUNCTIONAL_READY_BUT_STRICT_EDGE_WEAK"
            conf = 0.55
            next_action = "keep as provisional functional class until more strict edge support"
        else:
            decision = "NEGATIVE_OR_PARTIAL_CONTROL"
            conf = float(b["branch_score"])
            next_action = "retain as negative/partial control"
        items.append({
            "suffix_class": cls,
            "suffix_books": s_books,
            "strict_edge_books": e_books,
            "missing_strict_edge_books": missing,
            "suffix_contig_supported_count": len(s_books),
            "strict_edge_supported_count": len(e_books),
            "negative_or_partial_count": int(b["partial_or_negative_count"]),
            "branch_score": float(b["branch_score"]),
            "decision": decision,
            "confidence": round(conf, 3),
            "gloss_allowed": 0,
            "reason": f"suffix_support={len(s_books)}, strict_edge_support={len(e_books)}, missing_strict_edge={missing}",
            "next_action": next_action,
            "evidence": {"branch_row": b, "suffix_rows": [r for r in suffix_rows if r["suffix_class"] == cls], "cross_rows": [r for r in cross_rows if r["suffix_class"] == cls]},
        })

    ready = sum(1 for x in items if x["decision"].startswith("FUNCTIONAL_READY"))
    discrepancies = sum(1 for x in items if x["missing_strict_edge_books"])
    cur.execute(
        """
        insert into vinvin_branch_reconciliation_runs
        (created_at, decision, suffix_class_count, reconciled_ready_count, discrepancy_count,
         lexical_gloss_allowed_count, payload_json)
        values (?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), "VINVIN_BRANCH_RECONCILIATION_READY_NO_GLOSS", len(items), ready, discrepancies, 0,
         j({"branch_run": branch_run, "suffix_run": suffix_run, "cross_run": cross_run})),
    )
    run_id = cur.lastrowid
    for item in items:
        cur.execute(
            """
            insert into vinvin_branch_reconciliation_items
            (run_id, suffix_class, suffix_books_json, strict_edge_books_json, missing_strict_edge_books_json,
             suffix_contig_supported_count, strict_edge_supported_count, negative_or_partial_count, branch_score,
             decision, confidence, gloss_allowed, reason, next_action, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["suffix_class"], j(item["suffix_books"]), j(item["strict_edge_books"]), j(item["missing_strict_edge_books"]),
             item["suffix_contig_supported_count"], item["strict_edge_supported_count"], item["negative_or_partial_count"], item["branch_score"],
             item["decision"], item["confidence"], item["gloss_allowed"], item["reason"], item["next_action"], j(item["evidence"])),
        )
    con.commit()

    out = {"run_id": run_id, "decision": "VINVIN_BRANCH_RECONCILIATION_READY_NO_GLOSS", "suffix_class_count": len(items), "reconciled_ready_count": ready, "discrepancy_count": discrepancies, "lexical_gloss_allowed_count": 0}
    print(json.dumps(out, ensure_ascii=False))

    if args.discord:
        top = [x for x in items if x["decision"].startswith("FUNCTIONAL_READY")]
        desc = "; ".join(f"{x['suffix_class']}: edge={x['strict_edge_supported_count']}, suffix={x['suffix_contig_supported_count']}, missing={','.join(x['missing_strict_edge_books']) or 'none'}" for x in top)
        send_discord("\n".join([
            f"[469][vinvin-reconcile][run={run_id}] branch funcional reconciliada sem gloss",
            f"classes={len(items)} | funcionais={ready} | discrepâncias={discrepancies} | gloss lexical=0",
            desc,
            "decisão: VINVIN pode entrar como função branch/subfunção; livro 61 fica marcado como suporte suffix-only até prova strict-edge. Nada vira tradução em inglês.",
        ]))


if __name__ == "__main__":
    main()
