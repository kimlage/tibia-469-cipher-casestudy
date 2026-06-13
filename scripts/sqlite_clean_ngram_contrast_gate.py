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
NOISE_WORDS = {"fast", "fine", "sestine", "fact", "you've", "set", "into", "eye", "fair", "far", "lo", "oft", "inventive", "biface"}


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
        create table if not exists clean_ngram_contrast_gate_runs(
          run_id integer primary key autoincrement,
          created_at text not null,
          source_scorer_run_id integer not null,
          reviewed_count integer not null,
          accepted_review_count integer not null,
          rejected_noise_count integer not null,
          decision text not null,
          next_action text not null,
          payload_json text not null
        );
        create table if not exists clean_ngram_contrast_gate_items(
          run_id integer not null,
          source_rank integer not null,
          phrase text not null,
          source_score real not null,
          book_count integer not null,
          anomaly_overlap_count integer not null,
          noise_word_count integer not null,
          gate_status text not null,
          decision text not null,
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

    srun = one(cur, "select max(run_id) as run_id from semantic_masked_clean_ngram_scorer_items")
    arun = one(cur, "select max(run_id) as run_id from semantic_anomaly_audit_items")
    candidates = rows(cur, "select * from semantic_masked_clean_ngram_scorer_items where run_id=? and review_status='REVIEW_CLEAN_RECURRENT_PHRASE_NO_GLOSS' order by rank limit 100", (srun.get("run_id"),))
    anomalies = rows(cur, "select phrase, recommendation from semantic_anomaly_audit_items where run_id=?", (arun.get("run_id"),))
    items = []
    accepted = 0
    rejected = 0
    for c in candidates:
        phrase = c["phrase"]
        words = phrase.split()
        noise = sum(1 for w in words if w in NOISE_WORDS)
        overlap = sum(1 for a in anomalies if phrase in a["phrase"] or a["phrase"] in phrase)
        if overlap > 0 or noise >= max(1, len(words) // 2):
            status = "REJECT_DISPLAY_OR_ANOMALY_DRIFT"
            decision = "do not review as semantic candidate; treat as shadow display drift"
            rejected += 1
        else:
            status = "CONTRASTIVE_REVIEW_CANDIDATE_NO_GLOSS"
            decision = "eligible for raw row0/source alignment review; no lexical promotion"
            accepted += 1
        items.append({"source_rank": c["rank"], "phrase": phrase, "source_score": c["score"], "book_count": c["book_count"], "anomaly_overlap_count": overlap, "noise_word_count": noise, "gate_status": status, "decision": decision, "source": dict(c)})

    decision = "CLEAN_NGRAM_GATE_HAS_CONTRASTIVE_CANDIDATES" if accepted else "CLEAN_NGRAM_GATE_REJECTED_ALL_AS_DISPLAY_DRIFT"
    next_action = "inspect raw row0/source alignment for accepted candidates" if accepted else "do not use masked English ngrams; seek non-English structural objective"
    cur.execute(
        """
        insert into clean_ngram_contrast_gate_runs
        (created_at, source_scorer_run_id, reviewed_count, accepted_review_count, rejected_noise_count, decision, next_action, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (now(), srun.get("run_id") or 0, len(items), accepted, rejected, decision, next_action, j({"items": items})),
    )
    run_id = cur.lastrowid
    for item in items:
        cur.execute(
            """
            insert into clean_ngram_contrast_gate_items
            (run_id, source_rank, phrase, source_score, book_count, anomaly_overlap_count, noise_word_count, gate_status, decision, evidence_json)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (run_id, item["source_rank"], item["phrase"], item["source_score"], item["book_count"], item["anomaly_overlap_count"], item["noise_word_count"], item["gate_status"], item["decision"], j(item)),
        )
    con.commit()
    out = {"run_id": run_id, "decision": decision, "reviewed_count": len(items), "accepted_review_count": accepted, "rejected_noise_count": rejected, "top_accepted": [{"phrase": i["phrase"], "books": i["book_count"], "score": i["source_score"]} for i in items if i["gate_status"].startswith("CONTRASTIVE")][:10]}
    print(json.dumps(out, ensure_ascii=False))
    if args.discord:
        acc = [i for i in items if i["gate_status"].startswith("CONTRASTIVE")][:5]
        lines = [f"{k+1}. {i['phrase']} | books={i['book_count']} | score={i['source_score']}" for k, i in enumerate(acc)] or ["nenhum candidato limpo sobreviveu ao gate"]
        send("\n".join([
            f"[469][clean-ngram-gate][run={run_id}] gate contra display/anomalia",
            f"revisados={len(items)} | aceitos para contraste={accepted} | rejeitados como ruído={rejected} | gloss=0",
            *lines,
            f"decisão={decision}",
            f"próxima ação: {next_action}",
        ]))


if __name__ == "__main__":
    main()
