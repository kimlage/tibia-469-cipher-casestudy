#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"

DIRECT = [
    ("62", "N", "NARCISSIST_MICRO_ANCHOR", "HARD_WITHIN_PROVISIONAL_SOURCE"),
    ("79", "A", "NARCISSIST_MICRO_ANCHOR", "HARD_WITHIN_PROVISIONAL_SOURCE"),
    ("20", "R", "NARCISSIST_MICRO_ANCHOR", "HARD_WITHIN_PROVISIONAL_SOURCE"),
    ("68", "C", "NARCISSIST_MICRO_ANCHOR", "HARD_WITHIN_PROVISIONAL_SOURCE"),
    ("65", "I", "NARCISSIST_MICRO_ANCHOR", "HARD_WITHIN_PROVISIONAL_SOURCE"),
    ("72", "S", "NARCISSIST_MICRO_ANCHOR", "HARD_WITHIN_PROVISIONAL_SOURCE"),
    ("61", "T", "NARCISSIST_MICRO_ANCHOR", "HARD_WITHIN_PROVISIONAL_SOURCE"),
]

AUDIT_ONLY_WORDS = [
    ("3478", "BE", "KNIGHTMARE_LITERAL_ROW0", "AUDIT_ONLY_PHRASE_UNCONFIRMED"),
    ("67", "A", "KNIGHTMARE_LITERAL_ROW0", "AUDIT_ONLY_PHRASE_UNCONFIRMED"),
    ("6880326", "IAVN", "AVAR_TAR_LITERAL_ROW0", "AUDIT_ONLY_UNINTERPRETED"),
    ("677", "IN", "AVAR_TAR_LITERAL_ROW0", "AUDIT_ONLY_COMMON_WORD_CANDIDATE"),
    ("7223", "SO", "POLL_LITERAL_ROW0", "AUDIT_ONLY_COMMON_WORD_CANDIDATE"),
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists minimal_external_semantic_lexicon_v1_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            direct_code_count integer not null,
            audit_only_word_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists minimal_external_semantic_lexicon_v1_items(
            run_id integer not null,
            item_type text not null,
            key text not null,
            value text not null,
            source text not null,
            evidence_tier text not null,
            promotion_scope text not null,
            evidence_json text not null,
            primary key(run_id, item_type, key, value)
        );
        """
    )
    decision = "MINIMAL_EXTERNAL_SEMANTIC_LEXICON_CREATED_NO_BOOK_GLOSS"
    next_action = "Use direct NARCISSIST letters for constrained external decoding only; keep audit-only words out of book translation."
    payload = {"direct": DIRECT, "audit_only_words": AUDIT_ONLY_WORDS}
    cur.execute(
        "insert into minimal_external_semantic_lexicon_v1_runs(created_at,direct_code_count,audit_only_word_count,decision,next_action,payload_json) values (?,?,?,?,?,?)",
        (now(), len(DIRECT), len(AUDIT_ONLY_WORDS), decision, next_action, j(payload)),
    )
    run_id = cur.lastrowid
    for code, value, source, tier in DIRECT:
        cur.execute(
            "insert into minimal_external_semantic_lexicon_v1_items(run_id,item_type,key,value,source,evidence_tier,promotion_scope,evidence_json) values (?,?,?,?,?,?,?,?)",
            (run_id, "code_letter", code, value, source, tier, "external_micro_only", j({"code": code, "value": value, "source": source, "tier": tier})),
        )
    for seq, value, source, tier in AUDIT_ONLY_WORDS:
        cur.execute(
            "insert into minimal_external_semantic_lexicon_v1_items(run_id,item_type,key,value,source,evidence_tier,promotion_scope,evidence_json) values (?,?,?,?,?,?,?,?)",
            (run_id, "word_candidate", seq, value, source, tier, "audit_only_no_promotion", j({"sequence": seq, "value": value, "source": source, "tier": tier})),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "direct_code_count": len(DIRECT), "audit_only_word_count": len(AUDIT_ONLY_WORDS)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
