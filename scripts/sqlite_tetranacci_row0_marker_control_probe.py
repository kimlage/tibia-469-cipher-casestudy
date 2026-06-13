#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sqlite3
from typing import Any

DB_DEFAULT = "./data/bonelord_operational.sqlite"
MARKERS = {"*00", "C86", "O23", "O32", "R20", "R02"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def tetranacci(seed=(1, 1, 1, 1), limit=70) -> list[int]:
    seq = list(seed)
    while len(seq) < limit:
        seq.append(sum(seq[-4:]))
    return seq


def marker_hits(tokens: list[str], positions: set[int]) -> int:
    # positions are 1-based modulo token length.
    if not tokens:
        return 0
    hits = 0
    n = len(tokens)
    for pos in positions:
        idx = (pos - 1) % n
        if tokens[idx] in MARKERS:
            hits += 1
    return hits


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=DB_DEFAULT)
    args = parser.parse_args()
    con = sqlite3.connect(args.db)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.executescript(
        """
        create table if not exists tetranacci_row0_marker_control_probe_runs(
            run_id integer primary key autoincrement,
            created_at text not null,
            observed_hits integer not null,
            observed_total integer not null,
            observed_rate real not null,
            best_control_name text not null,
            best_control_rate real not null,
            decision text not null,
            next_action text not null,
            payload_json text not null
        );
        """
    )
    seq = tetranacci(limit=16)
    orbit = {x for x in seq if x > 0}
    controls = {
        "shift_plus_1": {x + 1 for x in orbit},
        "shift_plus_2": {x + 2 for x in orbit},
        "doubling": {x * 2 for x in orbit},
        "mod70_plus35": {x + 35 for x in orbit},
    }
    rows = cur.execute(
        """
        select bookid, tokens_json
        from row0_variant_book_tokens
        where run_id=(select max(run_id) from row0_variant_frontier_runs)
        """
    ).fetchall()
    observed_hits = 0
    observed_total = 0
    control_hits = {name: 0 for name in controls}
    control_total = {name: 0 for name in controls}
    details = []
    for row in rows:
        tokens = json.loads(row["tokens_json"])
        local_positions = {((x - 1) % len(tokens)) + 1 for x in orbit} if tokens else set()
        hits = marker_hits(tokens, local_positions)
        observed_hits += hits
        observed_total += len(local_positions)
        cdetail = {}
        for name, positions in controls.items():
            local = {((x - 1) % len(tokens)) + 1 for x in positions} if tokens else set()
            chits = marker_hits(tokens, local)
            control_hits[name] += chits
            control_total[name] += len(local)
            cdetail[name] = {"hits": chits, "total": len(local), "rate": round(chits / len(local), 3) if local else 0.0}
        details.append({"bookid": row["bookid"], "token_count": len(tokens), "observed_hits": hits, "observed_total": len(local_positions), "controls": cdetail})
    observed_rate = round(observed_hits / observed_total, 4) if observed_total else 0.0
    control_rates = {
        name: round(control_hits[name] / control_total[name], 4) if control_total[name] else 0.0
        for name in controls
    }
    best_control_name, best_control_rate = max(control_rates.items(), key=lambda kv: kv[1])
    if observed_rate > best_control_rate * 1.25 and observed_hits >= best_control_rate * observed_total + 5:
        decision = "TETRANACCI_ROW0_MARKER_SIGNAL_BEATS_CONTROLS_AUDIT_ONLY"
        next_action = "Use as structural constraint only; still no semantic gloss."
    else:
        decision = "TETRANACCI_ROW0_MARKER_SIGNAL_FAILS_CONTROLS"
        next_action = "Abandon current mathemagic route until a stricter independent target exists."
    payload = {
        "tetranacci_sequence": seq,
        "orbit": sorted(orbit),
        "markers": sorted(MARKERS),
        "control_rates": control_rates,
        "details": details,
    }
    cur.execute(
        "insert into tetranacci_row0_marker_control_probe_runs(created_at,observed_hits,observed_total,observed_rate,best_control_name,best_control_rate,decision,next_action,payload_json) values (?,?,?,?,?,?,?,?,?)",
        (now(), observed_hits, observed_total, observed_rate, best_control_name, best_control_rate, decision, next_action, j(payload)),
    )
    run_id = cur.lastrowid
    con.commit()
    print(json.dumps({"run_id": run_id, "decision": decision, "observed_hits": observed_hits, "observed_total": observed_total, "observed_rate": observed_rate, "best_control_name": best_control_name, "best_control_rate": best_control_rate, "control_rates": control_rates}, ensure_ascii=False))


if __name__ == "__main__":
    main()
