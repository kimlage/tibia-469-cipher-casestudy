#!/usr/bin/env python3
"""Classify Hellgate book 39 as formula/boundary holdout, no gloss."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "bonelord_operational.sqlite"
BOOKID = "39"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        create table if not exists hellgate39_formula_holdout_probe_runs (
            run_id integer primary key,
            created_at text not null,
            decision text not null,
            exact_external_hit integer not null,
            row0_code_hit integer not null,
            fast_family_hit_count integer not null,
            formula_family_hit_count integer not null,
            gloss_allowed integer not null,
            payload_json text not null
        );

        create table if not exists hellgate39_formula_holdout_items (
            run_id integer not null,
            feature_id text not null,
            hit_count integer not null,
            feature_status text not null,
            evidence_json text not null,
            primary key (run_id, feature_id)
        );
        """
    )

    run_id = conn.execute("select coalesce(max(run_id), 0) + 1 from hellgate39_formula_holdout_probe_runs").fetchone()[0]
    anchor = conn.execute(
        """
        select exact_digit_hit, row0_code_hit, anchor_status, symbol_window
        from hellgate_long_anchor_items
        where run_id=(select max(run_id) from hellgate_long_anchor_items)
          and expected_bookid=?
        """,
        (BOOKID,),
    ).fetchone()
    if not anchor:
        raise SystemExit("missing Hellgate book 39 anchor")

    text = anchor["symbol_window"] or ""
    features = {
        "FAST_FAMILY": text.count("FAST"),
        "EIFAST_PREFIX": text.count("EIFAST"),
        "SETBTBT": text.count("SETBTBT"),
        "FORMULA_SHORT_NO_STAR": 1 if "*" not in text and len(text) <= 40 else 0,
    }
    fast_hits = features["FAST_FAMILY"] + features["EIFAST_PREFIX"]
    formula_hits = features["SETBTBT"] + features["FORMULA_SHORT_NO_STAR"]

    for feature_id, hit_count in features.items():
        if feature_id in {"FAST_FAMILY", "EIFAST_PREFIX"} and hit_count:
            status = "FAST_FORMULA_AUDIT_FEATURE"
        elif hit_count:
            status = "FORMULA_HOLDOUT_FEATURE"
        else:
            status = "ABSENT"
        conn.execute(
            """
            insert into hellgate39_formula_holdout_items
            (run_id, feature_id, hit_count, feature_status, evidence_json)
            values (?, ?, ?, ?, ?)
            """,
            (
                run_id,
                feature_id,
                hit_count,
                status,
                json.dumps({"symbol_window": text}, ensure_ascii=False),
            ),
        )

    if int(anchor["exact_digit_hit"]) and not int(anchor["row0_code_hit"]):
        decision = "HELLGATE39_EXTERNAL_HOLDOUT_FORMULA_AUDIT_NO_GLOSS"
    else:
        decision = "HELLGATE39_REQUIRES_MORE_AUDIT_NO_GLOSS"

    conn.execute(
        """
        insert into hellgate39_formula_holdout_probe_runs
        (run_id, created_at, decision, exact_external_hit, row0_code_hit,
         fast_family_hit_count, formula_family_hit_count, gloss_allowed, payload_json)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            now_iso(),
            decision,
            int(anchor["exact_digit_hit"]),
            int(anchor["row0_code_hit"]),
            fast_hits,
            formula_hits,
            0,
            json.dumps({"anchor_status": anchor["anchor_status"], "symbol_window": text}, ensure_ascii=False),
        ),
    )
    conn.commit()

    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": decision,
                "exact_external_hit": int(anchor["exact_digit_hit"]),
                "row0_code_hit": int(anchor["row0_code_hit"]),
                "fast_family_hit_count": fast_hits,
                "formula_family_hit_count": formula_hits,
                "gloss_allowed": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
