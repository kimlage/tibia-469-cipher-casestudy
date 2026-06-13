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
        create table if not exists masked_english_circularity_guard_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          source_gate_run_id integer not null,
          input_candidate_count integer not null,
          accepted_count integer not null,
          rejected_circular_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists masked_english_circularity_guard_items(
          run_id integer not null,
          source_rank integer not null,
          phrase text not null,
          prior_status text not null,
          guard_status text not null,
          reason text not null,
          required_to_reopen text not null,
          evidence_json text not null,
          primary key(run_id, source_rank)
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

    grun = one(cur, "select max(run_id) as run_id from clean_ngram_contrast_gate_items")
    candidates = rows(cur, "select * from clean_ngram_contrast_gate_items where run_id=? and gate_status='CONTRASTIVE_REVIEW_CANDIDATE_NO_GLOSS' order by source_score desc, source_rank", (grun.get("run_id"),))
    phrase_gt = rows(cur, "select digits, expected_phrase, refname from phrase_level_gt_gate_items where run_id=(select max(run_id) from phrase_level_gt_gate_items) and gt_pass=1")
    external_words = set()
    for gt in phrase_gt:
        for w in (gt.get("expected_phrase") or "").lower().replace("<*>", " ").replace("!", "").split():
            external_words.add(w.strip(".,;:'\""))
    items = []
    accepted = 0
    for c in candidates:
        words = [w.strip(".,;:'\"").lower() for w in c["phrase"].split()]
        # Even overlap with phrase-level GT words is insufficient because component gloss is disallowed.
        overlap = sorted(set(words) & external_words)
        status = "REJECT_CIRCULAR_MASKED_ENGLISH"
        reason = "phrase is derived from best_shadow/masked English; no independent exact sequence+meaning or structural alignment proves it"
        required = "source-attested exact sequence meaning, or raw row0/digit component alignment that predicts a held-out external phrase without using English shadow text"
        items.append({"source_rank": c["source_rank"], "phrase": c["phrase"], "prior_status": c["gate_status"], "guard_status": status, "reason": reason, "required_to_reopen": required, "gt_word_overlap": overlap, "source": dict(c)})
    rejected = len(items) - accepted
    decision = "ALL_MASKED_ENGLISH_CANDIDATES_REJECTED_AS_CIRCULAR"
    next_action = "switch candidate generation to raw digit/row0 structural prediction, not English shadow ngrams"
    cur.execute(
        """
        insert into masked_english_circularity_guard_runs
        (created_at, source_gate_run_id, input_candidate_count, accepted_count, rejected_circular_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), grun.get("run_id") or 0, len(items), accepted, rejected, decision, next_action, j({"items": items, "phrase_gt_word_set": sorted(external_words)})),
    )
    run_id = cur.lastrowid
    for item in items:
        cur.execute(
            """
            insert into masked_english_circularity_guard_items
            (run_id, source_rank, phrase, prior_status, guard_status, reason, required_to_reopen, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["source_rank"], item["phrase"], item["prior_status"], item["guard_status"], item["reason"], item["required_to_reopen"], j(item)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "input_candidate_count": len(items), "accepted_count": accepted, "rejected_circular_count": rejected, "next_action": next_action}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        send("\n".join([
            f"[469][circularity-guard][run={run_id}] guard contra inglês circular do shadow",
            f"candidatos de inglês mascarado={len(items)} | aceitos=0 | rejeitados={rejected}",
            "decisão: nenhum n-gram inglês do shadow vira candidato sem prova externa exata ou alinhamento raw independente.",
            "impacto: evita voltar para frases plausíveis mas sem evidência; próximo passo precisa operar em dígitos/row0, não em inglês gerado.",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
