#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import math
import sqlite3
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def longest_common_substring(a: str, b: str) -> tuple[int, str]:
    prev = [0] * (len(b) + 1)
    best_len = 0
    best_end = 0
    for i, ca in enumerate(a, 1):
        cur = [0] * (len(b) + 1)
        for k, cb in enumerate(b, 1):
            if ca == cb:
                cur[k] = prev[k - 1] + 1
                if cur[k] > best_len:
                    best_len = cur[k]
                    best_end = i
        prev = cur
    return best_len, a[best_end - best_len : best_end]


def parse_digits(digits: str, code_symbol: dict[str, tuple[str, int]]) -> dict[str, Any]:
    n = len(digits)
    best: list[tuple[float, list[tuple[str, str, int]]] | None] = [None] * (n + 1)
    best[0] = (0.0, [])
    for i in range(n):
        if best[i] is None:
            continue
        score, path = best[i]
        if i + 2 <= n:
            code = digits[i : i + 2]
            if code in code_symbol:
                symbol, count = code_symbol[code]
                cand = (score + math.log(count + 1.0), path + [(code, symbol, 0)])
                if best[i + 2] is None or cand[0] > best[i + 2][0]:
                    best[i + 2] = cand
        code = "0" + digits[i : i + 1]
        if code in code_symbol:
            symbol, count = code_symbol[code]
            cand = (score + math.log(count + 1.0) - 0.35, path + [(code, symbol, 1)])
            if best[i + 1] is None or cand[0] > best[i + 1][0]:
                best[i + 1] = cand
    if best[n] is None:
        return {"valid": 0, "score": -999.0, "tokens": [], "symbol_text": "", "omitted_count": 0}
    score, path = best[n]
    return {
        "valid": 1,
        "score": round(score, 3),
        "tokens": [{"code": code, "symbol": symbol, "omitted": omitted} for code, symbol, omitted in path],
        "symbol_text": "".join(symbol for _, symbol, _ in path),
        "omitted_count": sum(omitted for _, _, omitted in path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists s2ward_extra_row0_projection_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            source_audit_run_id integer not null,
            source_index integer not null,
            valid_parse integer not null,
            digit_len integer not null,
            token_count integer not null,
            omitted_count integer not null,
            best_match_bookid text,
            best_match_lcs_len integer not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        """
    )
    audit_run = cur.execute("select max(run_id) from s2ward_corpus_audit_runs").fetchone()[0]
    source = cur.execute(
        """
        select source_index, sequence_digits
        from s2ward_corpus_audit_items
        where run_id=? and source_set='sorted_unique_with_kharos' and exact_sheet_bookid is null
        order by sequence_len desc, source_index
        limit 1
        """,
        (audit_run,),
    ).fetchone()
    if not source:
        raise SystemExit("no new s2ward extra sequence found")
    code_rows = cur.execute(
        """
        select code, symbol, occurrence_count
        from row0_code_symbol_counts
        where run_id=(select max(run_id) from row0_code_symbol_probe_runs)
        order by code, occurrence_count desc
        """
    ).fetchall()
    code_symbol: dict[str, tuple[str, int]] = {}
    for row in code_rows:
        code_symbol.setdefault(str(row["code"]), (str(row["symbol"]), int(row["occurrence_count"])))
    parsed = parse_digits(str(source["sequence_digits"]), code_symbol)
    best = {"bookid": None, "lcs_len": 0, "lcs_text": ""}
    if parsed["valid"]:
        for row in cur.execute("select bookid, symbol_text from row0_variant_book_tokens where run_id=(select max(run_id) from row0_variant_frontier_runs)"):
            lcs_len, lcs_text = longest_common_substring(parsed["symbol_text"], str(row["symbol_text"]))
            if lcs_len > best["lcs_len"]:
                best = {"bookid": str(row["bookid"]), "lcs_len": lcs_len, "lcs_text": lcs_text}
    omitted_ratio = (parsed["omitted_count"] / len(parsed["tokens"])) if parsed["tokens"] else 0.0
    decision = "S2WARD_EXTRA_ROW0_VALID_AUDIT_ONLY" if parsed["valid"] else "S2WARD_EXTRA_ROW0_PARSE_FAILED"
    if parsed["valid"] and omitted_ratio > 0.35:
        decision = "S2WARD_EXTRA_ROW0_DEGENERATE_OMITTED_ZERO_PARSE"
    elif parsed["valid"] and best["lcs_len"] < 20:
        decision = "S2WARD_EXTRA_ROW0_VALID_BUT_NO_STRONG_BOOK_OVERLAP"
    next_action = "Keep as external structural holdout; do not promote gloss. Investigate only if it predicts a residual family or aligns with an external meaning source."
    payload = {
        "source_index": int(source["source_index"]),
        "digits": str(source["sequence_digits"]),
        "symbol_text": parsed["symbol_text"],
        "tokens": parsed["tokens"],
        "best_match": best,
        "omitted_ratio": omitted_ratio,
    }
    cur.execute(
        "insert into s2ward_extra_row0_projection_runs(created_at,source_audit_run_id,source_index,valid_parse,digit_len,token_count,omitted_count,best_match_bookid,best_match_lcs_len,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            now(),
            audit_run,
            int(source["source_index"]),
            parsed["valid"],
            len(str(source["sequence_digits"])),
            len(parsed["tokens"]),
            parsed["omitted_count"],
            best["bookid"],
            best["lcs_len"],
            decision,
            next_action,
            j(payload),
        ),
    )
    run_id = cur.lastrowid
    con.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "source_index": int(source["source_index"]),
                "valid_parse": parsed["valid"],
                "digit_len": len(str(source["sequence_digits"])),
                "token_count": len(parsed["tokens"]),
                "omitted_count": parsed["omitted_count"],
                "omitted_ratio": round(omitted_ratio, 3),
                "symbol_text": parsed["symbol_text"],
                "best_match": best,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
