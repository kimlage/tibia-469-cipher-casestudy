#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
SEQUENCE = "62792068657272657261"
EXPECTED = "NARCISSIST"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    pairs = [SEQUENCE[i : i + 2] for i in range(0, len(SEQUENCE), 2)]
    mapping = {}
    for row in cur.execute(
        """
        select code, symbol
        from row0_code_symbol_counts
        where run_id=(select max(run_id) from row0_code_symbol_probe_runs)
        order by code, occurrence_count desc
        """
    ):
        mapping.setdefault(str(row["code"]), str(row["symbol"]))
    decoded = "".join(mapping.get(pair, "?") for pair in pairs)
    exact_match = 1 if decoded == EXPECTED else 0
    cur.executescript(
        """
        create table if not exists narcissist_micro_anchor_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            sequence text not null,
            decoded_by_row0 text not null,
            expected_text text not null,
            exact_match integer not null,
            evidence_tier text not null,
            acceptance text not null,
            semantic_promotion_scope text not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        """
    )
    evidence_tier = "PROVISIONAL_EXTERNAL_SECONDARY_SOURCE"
    acceptance = "ACCEPT_MICRO_GLOSS_PROVISIONAL_NO_BOOK_PROMOTION" if exact_match else "REJECT_MICRO_GLOSS"
    scope = "external_micro_anchor_only"
    decision = "NARCISSIST_MICRO_ANCHOR_ACCEPTED_PROVISIONAL" if exact_match else "NARCISSIST_MICRO_ANCHOR_REJECTED"
    next_action = "Use as a tiny validation anchor for row0 homophonic mapping; do not translate books from it alone."
    payload = {
        "source_urls": [
            "https://tibiasecrets.com/article160",
            "https://www.tibiaqa.com/25041/is-avar-tar-lying-about-his-stories",
        ],
        "source_claim": "Old tibia.org HTML allegedly had the Avar Tar poem variant with 62792068657272657261 replacing 63378129.",
        "pairs": pairs,
        "pair_mapping": [{"code": pair, "symbol": mapping.get(pair, "?")} for pair in pairs],
        "decoded_by_row0": decoded,
        "limitations": [
            "Primary tibia.org HTML not recovered in this run.",
            "This validates a micro word in an external poem variant, not Hellgate book prose.",
            "Do not generalize to book-level semantic translation.",
        ],
    }
    cur.execute(
        "insert into narcissist_micro_anchor_runs(created_at,sequence,decoded_by_row0,expected_text,exact_match,evidence_tier,acceptance,semantic_promotion_scope,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?,?,?,?)",
        (now(), SEQUENCE, decoded, EXPECTED, exact_match, evidence_tier, acceptance, scope, decision, next_action, j(payload)),
    )
    con.commit()
    print(json.dumps({"run_id": cur.lastrowid, "decision": decision, "decoded_by_row0": decoded, "exact_match": exact_match, "acceptance": acceptance}, ensure_ascii=False))


if __name__ == "__main__":
    main()
