#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, List

from sqlite_probe_registry import add_probe, connect, init_schema
from sqlite_snapshot_ref import lookup_export_id_by_artifact


DEFAULT_DB = "./data/bonelord_operational.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Finalize a completed probe batch into SQLite using ingested snapshots")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite snapshot DB")
    parser.add_argument("--family", required=True, help="Probe family name")
    parser.add_argument(
        "--artifact",
        action="append",
        required=True,
        help="Completed legacy artifact path already ingested into SQLite; repeat for multiple artifacts",
    )
    parser.add_argument("--outcome", required=True, help="Observed outcome bucket, e.g. DP_UNUSED or NO_OP")
    parser.add_argument(
        "--status",
        default=None,
        help="Registry status override; defaults to FlowState.Status or CLOSED",
    )
    parser.add_argument(
        "--skip-top",
        default=None,
        help="Top skip reason override; defaults to FlowState.PromotionSkipReasonTop",
    )
    parser.add_argument(
        "--expected-failure-mode",
        default=None,
        help="Expected failure mode to record in the registry",
    )
    parser.add_argument(
        "--reason-selected",
        default=None,
        help="Why this batch was selected",
    )
    parser.add_argument(
        "--notes",
        default=None,
        help="Freeform notes appended to the registry row",
    )
    return parser.parse_args()

def read_flow_state(conn: sqlite3.Connection, export_id: int) -> Dict[str, str]:
    out: Dict[str, str] = {}
    rows = conn.execute(
        """
        SELECT key, value
        FROM sheet__flowstate
        WHERE __export_id = ?
        ORDER BY __row_index
        """,
        (export_id,),
    ).fetchall()
    for row in rows:
        key = "" if row["key"] is None else str(row["key"]).strip()
        if key:
            value = row["value"]
            out[key] = "" if value is None else str(value)
    return out


def derive_probe_name(artifact_path: Path) -> str:
    stem = artifact_path.stem
    if stem.endswith("_probe"):
        stem = stem[: -len("_probe")]
    return stem


def main() -> int:
    args = parse_args()
    conn = connect(args.db)
    try:
        init_schema(conn)
        results: List[Dict[str, object]] = []
        for artifact in args.artifact:
            path = Path(artifact).resolve()
            export_id = lookup_export_id_by_artifact(conn, path)
            if export_id is None:
                raise SystemExit(f"Artifact not found in SQLite exports: {path}")
            flow = read_flow_state(conn, export_id)
            status = args.status or flow.get("Status") or "CLOSED"
            skip_top = args.skip_top or flow.get("PromotionSkipReasonTop") or None
            notes_parts = []
            if args.notes:
                notes_parts.append(args.notes)
            if flow.get("CurrentIteration"):
                notes_parts.append(f"flow_iter={flow.get('CurrentIteration')}")
            if flow.get("LastCompletedStepID"):
                notes_parts.append(f"last_step={flow.get('LastCompletedStepID')}")
            if flow.get("NextStepID"):
                notes_parts.append(f"next_step={flow.get('NextStepID')}")
            if flow.get("Status"):
                notes_parts.append(f"flow_status={flow.get('Status')}")
            if skip_top:
                notes_parts.append(f"skip_top={skip_top}")
            notes = " | ".join(notes_parts) if notes_parts else None
            probe_id = add_probe(
                conn,
                family=args.family,
                probe_name=derive_probe_name(path),
                artifact=str(path),
                status=status,
                outcome=args.outcome,
                skip_top=skip_top,
                notes=notes,
                expected_failure_mode=args.expected_failure_mode,
                reason_selected=args.reason_selected,
            )
            results.append(
                {
                    "probe_id": probe_id,
                    "artifact": str(path),
                    "export_id": export_id,
                    "status": status,
                    "outcome": args.outcome,
                    "skip_top": skip_top,
                }
            )
        print(json.dumps({"family": args.family, "finalized": results}, ensure_ascii=True, indent=2))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
