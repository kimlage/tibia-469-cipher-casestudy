#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"

# Partial key as published in TibiaSecrets article160, Step six table.
# Blanks are omitted. This is secondary-source evidence, not accepted truth.
ARTICLE_KEY = {
    "00": "*", "01": "N", "02": "R", "03": "V", "04": "F", "06": "I", "07": "I", "08": "I", "09": "T",
    "10": "N", "11": "E", "12": "F", "13": "N", "14": "A", "15": "E", "16": "T", "17": "V", "18": "I", "19": "I",
    "20": "R", "21": "F", "22": "A", "23": "O", "24": "L", "26": "N", "27": "S", "29": "N",
    "30": "V", "31": "N", "32": "O", "33": "E", "34": "B", "35": "L", "36": "V", "37": "A", "38": "T", "39": "N",
    "40": "F", "41": "A", "42": "L", "43": "B", "45": "F", "46": "N", "49": "N",
    "51": "E", "53": "L", "54": "F", "56": "I", "57": "E",
    "60": "I", "61": "T", "62": "N", "63": "V", "64": "N", "65": "I", "66": "E", "67": "A", "68": "C", "69": "V",
    "70": "I", "71": "V", "72": "S", "73": "A", "75": "E", "76": "A", "77": "N", "78": "E", "79": "A",
    "80": "I", "81": "I", "83": "T", "86": "C", "87": "E", "88": "A", "89": "T",
    "90": "T", "92": "N", "93": "N", "94": "N", "95": "I", "96": "V", "97": "A", "98": "T",
}


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
    row0 = {}
    for row in cur.execute(
        """
        select code, symbol
        from row0_code_symbol_counts
        where run_id=(select max(run_id) from row0_code_symbol_probe_runs)
        order by code, occurrence_count desc
        """
    ):
        row0.setdefault(str(row["code"]), str(row["symbol"]))
    compared = []
    matches = 0
    mismatches = 0
    missing = 0
    for code, article_symbol in sorted(ARTICLE_KEY.items()):
        row0_symbol = row0.get(code)
        if row0_symbol is None:
            status = "MISSING_IN_ROW0"
            missing += 1
        elif row0_symbol == article_symbol:
            status = "MATCH"
            matches += 1
        else:
            status = "MISMATCH"
            mismatches += 1
        compared.append({"code": code, "article_symbol": article_symbol, "row0_symbol": row0_symbol, "status": status})
    total_present = matches + mismatches
    agreement = round(matches / total_present, 4) if total_present else 0.0
    if agreement >= 0.95 and mismatches <= 3:
        decision = "TIBIASECRETS_KEY_TABLE_STRONGLY_MATCHES_INDEPENDENT_ROW0"
        next_action = "Treat article table as secondary corroboration for row0 homophonic layer, not as book gloss."
    else:
        decision = "TIBIASECRETS_KEY_TABLE_DOES_NOT_FULLY_MATCH_ROW0"
        next_action = "Keep only direct NARCISSIST micro-anchor; do not use article key table."
    cur.executescript(
        """
        create table if not exists tibiasecrets_key_table_compare_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            article_key_count integer not null,
            matches integer not null,
            mismatches integer not null,
            missing integer not null,
            agreement real not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        """
    )
    payload = {
        "source_url": "https://www.tibiasecrets.com/article160",
        "source_status": "secondary-source theory table",
        "compared": compared,
    }
    cur.execute(
        "insert into tibiasecrets_key_table_compare_runs(created_at,article_key_count,matches,mismatches,missing,agreement,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?,?)",
        (now(), len(ARTICLE_KEY), matches, mismatches, missing, agreement, decision, next_action, j(payload)),
    )
    con.commit()
    print(json.dumps({"run_id": cur.lastrowid, "decision": decision, "matches": matches, "mismatches": mismatches, "missing": missing, "agreement": agreement, "mismatch_items": [x for x in compared if x["status"] == "MISMATCH"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
