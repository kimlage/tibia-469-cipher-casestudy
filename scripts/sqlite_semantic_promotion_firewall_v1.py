#!/usr/bin/env python3
"""Firewall external/micro semantic hints from being counted as human translation."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    create table if not exists semantic_promotion_firewall_v1_runs (
        run_id integer primary key autoincrement,
        created_at text not null,
        decision text not null,
        inspected_item_count integer not null,
        allowed_plaintext_count integer not null,
        blocked_hint_count integer not null,
        summary_json text not null
    );
    create table if not exists semantic_promotion_firewall_v1_items (
        run_id integer not null,
        source_table text not null,
        item_key text not null,
        semantic_status text not null,
        plaintext_promotion_allowed integer not null,
        reason text not null,
        required_test text not null,
        evidence_json text not null,
        primary key (run_id, source_table, item_key)
    );
    """)
    items = []
    # External provenance confirmed: provenance without explicit meaning remains blocked.
    for r in conn.execute("select * from external_provenance_confirmed_items order by run_id desc"):
        key = r["phrase_id"] if "phrase_id" in r.keys() else str(len(items))
        status = r["meaning_status"] if "meaning_status" in r.keys() else "UNKNOWN"
        allowed = 1 if status == "EXPLICIT_MEANING" else 0
        reason = "Explicit meaning present." if allowed else "Source confirms provenance/context but not explicit plaintext meaning."
        required = "exact sequence plus explicit meaning, or predictive decoder that roundtrips this phrase"
        items.append(("external_provenance_confirmed_items", key, status, allowed, reason, required, json.dumps(dict(r), ensure_ascii=False, sort_keys=True)))
    # Minimal lexicon items are not enough for book prose unless hard external and predictive.
    for r in conn.execute("select * from minimal_external_semantic_lexicon_v1_items order by run_id desc"):
        item_type = r["item_type"] if "item_type" in r.keys() else r[1]
        seq = r["sequence"] if "sequence" in r.keys() else r[2]
        tier = r["tier"] if "tier" in r.keys() else r[5]
        key = f"{item_type}:{seq}"
        allowed = 0
        if tier in ("HARD_EXTERNAL_EXPLICIT", "SOURCE_EXPLICIT_MEANING"):
            # Even then, scoped lexical anchors are not full book prose.
            allowed = 0
            reason = "Scoped external lexical anchor; can seed tests but cannot count as book translation by itself."
        else:
            reason = "Audit/provisional/micro hint; blocked from plaintext promotion."
        required = "must predict held-out external phrase and at least one book segment without contradiction"
        items.append(("minimal_external_semantic_lexicon_v1_items", key, tier, allowed, reason, required, json.dumps(dict(r), ensure_ascii=False, sort_keys=True)))
    allowed_count = sum(i[3] for i in items)
    summary = {"principle": "no lexical/micro/fan hint counts as human translation without predictive validation", "allowed_plaintext_count": allowed_count}
    cur = conn.execute("insert into semantic_promotion_firewall_v1_runs values (null,?,?,?,?,?,?)", (utc_now(), "SEMANTIC_HINTS_FIREWALLED_FROM_BOOK_TRANSLATION", len(items), allowed_count, len(items)-allowed_count, json.dumps(summary, ensure_ascii=False, sort_keys=True)))
    run_id = cur.lastrowid
    for item in items:
        conn.execute("insert into semantic_promotion_firewall_v1_items values (?,?,?,?,?,?,?,?)", (run_id, *item))
    conn.commit()
    print(json.dumps({"run_id": run_id, "decision": "SEMANTIC_HINTS_FIREWALLED_FROM_BOOK_TRANSLATION", "inspected_item_count": len(items), "allowed_plaintext_count": allowed_count, "blocked_hint_count": len(items)-allowed_count}, ensure_ascii=False))

if __name__ == "__main__":
    main()
