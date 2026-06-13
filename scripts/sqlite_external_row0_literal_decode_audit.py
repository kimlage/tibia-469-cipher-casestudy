#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import re
import sqlite3
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"

PHRASES = [
    ("AVAR_TAR_POEM_ORIGINAL", "29639 46781 9063376290 3222011 677 80322429 67538 14805394 6880326 677 63378129 337011 72683 149630 4378 453 639 578300 986372 2953639"),
    ("AVAR_TAR_POEM_TIBIA_ORG_VARIANT", "29639 46781 9063376290 3222011 677 80322429 67538 14805394 6880326 677 62792068657272657261 337011 72683 149630 4378 453 639 578300 986372 2953639"),
    ("KNIGHTMARE_PHRASE", "3478 67 90871 97664 3466 0 345"),
    ("TIBIA_2014_POLL_C", "663 902073 7223 67538 467 80097"),
]

COMMON = {"BE", "A", "WIT", "THAN", "FOOL", "NARCISSIST", "NARCISSISM", "RUN", "FAST", "FIFTEEN"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def decode_word(raw: str, mapping: dict[str, str]) -> dict[str, Any]:
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) % 2:
        digits = "0" + digits
        leading_zero_added = 1
    else:
        leading_zero_added = 0
    pairs = [digits[i : i + 2] for i in range(0, len(digits), 2)]
    decoded = "".join(mapping.get(pair, "?") for pair in pairs)
    return {"raw": raw, "normalized_digits": digits, "leading_zero_added": leading_zero_added, "pairs": pairs, "decoded": decoded}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
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
    cur.executescript(
        """
        create table if not exists external_row0_literal_decode_audit_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            phrase_count integer not null,
            accepted_phrase_gloss_count integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        create table if not exists external_row0_literal_decode_audit_items(
            run_id integer not null,
            phrase_id text not null,
            raw_phrase text not null,
            decoded_literal text not null,
            recognized_word_count integer not null,
            unknown_count integer not null,
            acceptance text not null,
            evidence_json text not null,
            primary key(run_id, phrase_id)
        );
        """
    )
    results = []
    accepted = 0
    for phrase_id, phrase in PHRASES:
        words = re.findall(r"\d+", phrase)
        decoded_words = [decode_word(word, mapping) for word in words]
        literal = " ".join(item["decoded"] for item in decoded_words)
        recognized = sum(1 for item in decoded_words if item["decoded"] in COMMON)
        unknowns = literal.count("?")
        if phrase_id == "AVAR_TAR_POEM_TIBIA_ORG_VARIANT" and "NARCISSIST" in literal:
            acceptance = "ACCEPT_MICRO_WORD_ONLY_NO_PHRASE_GLOSS"
        else:
            acceptance = "REJECT_PHRASE_GLOSS_LITERAL_TOO_WEAK"
        if acceptance.startswith("ACCEPT"):
            accepted += 1
        results.append(
            {
                "phrase_id": phrase_id,
                "raw_phrase": phrase,
                "decoded_literal": literal,
                "recognized_word_count": recognized,
                "unknown_count": unknowns,
                "acceptance": acceptance,
                "decoded_words": decoded_words,
            }
        )
    decision = "EXTERNAL_ROW0_LITERAL_DECODE_MICRO_ONLY_NO_PHRASE_GLOSS"
    next_action = "Use NARCISSIST as provisional micro-anchor only; phrase-level translations still require stronger evidence."
    cur.execute(
        "insert into external_row0_literal_decode_audit_runs(created_at,phrase_count,accepted_phrase_gloss_count,decision,next_action,payload_json) values (?,?,?,?,?,?)",
        (now(), len(results), 0, decision, next_action, j({"results": results})),
    )
    run_id = cur.lastrowid
    for row in results:
        cur.execute(
            "insert into external_row0_literal_decode_audit_items(run_id,phrase_id,raw_phrase,decoded_literal,recognized_word_count,unknown_count,acceptance,evidence_json) values (?,?,?,?,?,?,?,?)",
            (run_id, row["phrase_id"], row["raw_phrase"], row["decoded_literal"], row["recognized_word_count"], row["unknown_count"], row["acceptance"], j(row)),
        )
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "results": [{"phrase_id": r["phrase_id"], "decoded_literal": r["decoded_literal"], "acceptance": r["acceptance"]} for r in results]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
