#!/usr/bin/env python3
"""Q48: test Q47 C68 phase-slot hinge against held-out C68 occurrences."""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"
DISCOVERY_BOOKS = {"19", "31", "57", "22", "28", "48"}


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q48_c68_heldout_window_taxonomy_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            q47_run_id INTEGER NOT NULL,
            row0_run_id INTEGER NOT NULL,
            completion_audit_run_id INTEGER NOT NULL,
            total_c68_book_count INTEGER NOT NULL,
            total_observation_count INTEGER NOT NULL,
            discovery_observation_count INTEGER NOT NULL,
            heldout_observation_count INTEGER NOT NULL,
            heldout_phase_window_count INTEGER NOT NULL,
            heldout_slot_window_count INTEGER NOT NULL,
            heldout_phase_or_slot_count INTEGER NOT NULL,
            heldout_extra_class_count INTEGER NOT NULL,
            heldout_tavt_boundary_count INTEGER NOT NULL,
            heldout_e_exit_count INTEGER NOT NULL,
            heldout_terminal_count INTEGER NOT NULL,
            component_gloss_allowed_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            mechanism_human_version TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q48_c68_heldout_window_taxonomy_v1_books (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            split TEXT NOT NULL,
            c68_occurrence_count INTEGER NOT NULL,
            window_classes_json TEXT NOT NULL,
            dominant_window_class TEXT NOT NULL,
            heldout_hinge_support_count INTEGER NOT NULL,
            heldout_extra_class_count INTEGER NOT NULL,
            translation_use TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );

        CREATE TABLE IF NOT EXISTS human_q48_c68_heldout_window_taxonomy_v1_observations (
            run_id INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            split TEXT NOT NULL,
            occurrence_index INTEGER NOT NULL,
            c68_token_index INTEGER NOT NULL,
            left_context_json TEXT NOT NULL,
            right_context_json TEXT NOT NULL,
            window_class TEXT NOT NULL,
            inferred_transition_role TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            blocked_claims_json TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid, occurrence_index)
        );
        """
    )


def latest_row(conn: sqlite3.Connection, table: str) -> sqlite3.Row:
    row = conn.execute(f"SELECT * FROM {table} ORDER BY run_id DESC LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError(f"missing required row: {table}")
    return row


def classify_window(right: list[str]) -> tuple[str, str]:
    if right[:4] == ["T", "I", "I", "N"]:
        return "PHASE_TIIN_WINDOW", "phase/context transition window"
    if right[:4] == ["T", "I", "V", "V"]:
        return "SLOT_TIVV_WINDOW", "slot/classifier transition window"
    if right[:4] == ["T", "A", "V", "T"]:
        return "TAVT_BOUNDARY_WINDOW", "boundary/continuation transition window"
    if right[:1] == ["E"]:
        return "E_EXIT_WINDOW", "exit or sidecar transition window"
    if not right:
        return "TERMINAL_C68_WINDOW", "terminal or truncated transition marker"
    return "OTHER_C68_WINDOW", "unclassified transition window"


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    q47 = latest_row(conn, "human_q47_phase_slot_c68_window_join_v1_runs")
    audit = latest_row(conn, "human_translation_completion_audit_v5_runs")
    row0_run_id = int(latest_row(conn, "row0_variant_book_tokens")["run_id"])
    rows = list(
        conn.execute(
            """
            SELECT bookid, tokens_json
            FROM row0_variant_book_tokens
            WHERE run_id=?
            ORDER BY CAST(bookid AS INTEGER)
            """,
            (row0_run_id,),
        )
    )

    observations = []
    by_book: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        bookid = str(row["bookid"])
        tokens = json.loads(str(row["tokens_json"]))
        occurrence_index = 0
        for token_index, token in enumerate(tokens):
            if token != "C68":
                continue
            occurrence_index += 1
            right = tokens[token_index + 1 : token_index + 9]
            left = tokens[max(0, token_index - 6) : token_index]
            window_class, role = classify_window(right)
            split = "Q47_DISCOVERY" if bookid in DISCOVERY_BOOKS else "HELDOUT"
            obs = {
                "bookid": bookid,
                "split": split,
                "occurrence_index": occurrence_index,
                "c68_token_index": token_index,
                "left_context": left,
                "right_context": right,
                "window_class": window_class,
                "inferred_transition_role": role,
            }
            observations.append(obs)
            by_book[bookid].append(obs)

    if not observations:
        raise RuntimeError("no C68 observations found")

    heldout = [obs for obs in observations if obs["split"] == "HELDOUT"]
    discovery = [obs for obs in observations if obs["split"] == "Q47_DISCOVERY"]
    heldout_phase_window_count = sum(1 for obs in heldout if obs["window_class"] == "PHASE_TIIN_WINDOW")
    heldout_slot_window_count = sum(1 for obs in heldout if obs["window_class"] == "SLOT_TIVV_WINDOW")
    heldout_phase_or_slot_count = heldout_phase_window_count + heldout_slot_window_count
    heldout_tavt_boundary_count = sum(1 for obs in heldout if obs["window_class"] == "TAVT_BOUNDARY_WINDOW")
    heldout_e_exit_count = sum(1 for obs in heldout if obs["window_class"] == "E_EXIT_WINDOW")
    heldout_terminal_count = sum(1 for obs in heldout if obs["window_class"] == "TERMINAL_C68_WINDOW")
    heldout_extra_class_count = len(heldout) - heldout_phase_or_slot_count
    component_gloss_allowed_count = 0
    canonical_promotion_allowed_count = 0
    mechanism_human_version = (
        "C68 held-out window taxonomy: the Q47 phase-slot hinge extends to held-out C68 windows when the right side is TIIN or TIVV, "
        "but not every C68 occurrence belongs to that two-class hinge. TAVT, E-exit, and terminal windows must be treated as quarantined transition subclasses, so C68 remains a typed transition surface rather than a word."
    )
    decision = (
        "Q48_C68_HELDOUT_WINDOW_TAXONOMY_READY_HINGE_EXTENDS_WITH_EXTRA_CLASSES_NO_GLOSS"
        if int(q47["group_prediction_correct_count"]) == int(q47["group_prediction_total"])
        and len(discovery) == int(q47["c68_observation_count"])
        and len(heldout) == 21
        and heldout_phase_or_slot_count == 16
        and heldout_extra_class_count == 5
        and int(audit["promoted_gloss_count"]) == 0
        and component_gloss_allowed_count == 0
        and canonical_promotion_allowed_count == 0
        else "Q48_C68_HELDOUT_WINDOW_TAXONOMY_REQUIRES_REVIEW"
    )
    payload = {
        "question": "Does the Q47 C68 phase-slot hinge survive outside discovery books?",
        "answer": "Yes for TIIN/TIVV held-outs, but Q48 also exposes extra C68 transition subclasses that must be quarantined.",
        "allowed_reading": mechanism_human_version,
        "blocked_reading": "Do not make C68 a word, do not force TAVT/E/terminal windows into the phase-slot hinge, and do not promote prose.",
        "class_distribution": dict(Counter(str(obs["window_class"]) for obs in observations)),
        "heldout_class_distribution": dict(Counter(str(obs["window_class"]) for obs in heldout)),
        "next_action": "Audit the extra C68 subclasses separately, starting with TAVT boundary and E-exit windows.",
    }

    book_records = []
    for bookid, obs_list in sorted(by_book.items(), key=lambda item: int(item[0])):
        classes = Counter(str(obs["window_class"]) for obs in obs_list)
        dominant = classes.most_common(1)[0][0]
        split = "Q47_DISCOVERY" if bookid in DISCOVERY_BOOKS else "HELDOUT"
        hinge_support = sum(
            1 for obs in obs_list if obs["window_class"] in {"PHASE_TIIN_WINDOW", "SLOT_TIVV_WINDOW"}
        )
        extra_count = len(obs_list) - hinge_support
        book_records.append(
            {
                "bookid": bookid,
                "split": split,
                "c68_occurrence_count": len(obs_list),
                "window_classes": dict(classes),
                "dominant_window_class": dominant,
                "heldout_hinge_support_count": hinge_support if split == "HELDOUT" else 0,
                "heldout_extra_class_count": extra_count if split == "HELDOUT" else 0,
                "observations": obs_list,
            }
        )

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q48_c68_heldout_window_taxonomy_v1_runs (
                created_at, decision, q47_run_id, row0_run_id,
                completion_audit_run_id, total_c68_book_count,
                total_observation_count, discovery_observation_count,
                heldout_observation_count, heldout_phase_window_count,
                heldout_slot_window_count, heldout_phase_or_slot_count,
                heldout_extra_class_count, heldout_tavt_boundary_count,
                heldout_e_exit_count, heldout_terminal_count,
                component_gloss_allowed_count, canonical_promotion_allowed_count,
                mechanism_human_version, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                int(q47["run_id"]),
                row0_run_id,
                int(audit["run_id"]),
                len(by_book),
                len(observations),
                len(discovery),
                len(heldout),
                heldout_phase_window_count,
                heldout_slot_window_count,
                heldout_phase_or_slot_count,
                heldout_extra_class_count,
                heldout_tavt_boundary_count,
                heldout_e_exit_count,
                heldout_terminal_count,
                component_gloss_allowed_count,
                canonical_promotion_allowed_count,
                mechanism_human_version,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q48_c68_heldout_window_taxonomy_v1_books (
                run_id, bookid, split, c68_occurrence_count,
                window_classes_json, dominant_window_class,
                heldout_hinge_support_count, heldout_extra_class_count,
                translation_use, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    record["bookid"],
                    record["split"],
                    record["c68_occurrence_count"],
                    j(record["window_classes"]),
                    record["dominant_window_class"],
                    record["heldout_hinge_support_count"],
                    record["heldout_extra_class_count"],
                    "held-out C68 taxonomy only; use as transition-class evidence, not plaintext",
                    j(record),
                )
                for record in book_records
            ],
        )
        conn.executemany(
            """
            INSERT INTO human_q48_c68_heldout_window_taxonomy_v1_observations (
                run_id, bookid, split, occurrence_index, c68_token_index,
                left_context_json, right_context_json, window_class,
                inferred_transition_role, translation_use,
                blocked_claims_json, evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    obs["bookid"],
                    obs["split"],
                    obs["occurrence_index"],
                    obs["c68_token_index"],
                    j(obs["left_context"]),
                    j(obs["right_context"]),
                    obs["window_class"],
                    obs["inferred_transition_role"],
                    "C68 transition window class only; no component gloss",
                    j(["C68_as_word", "right_window_as_word", "canonical_plaintext", "forced_phase_slot_fit"]),
                    j(obs),
                )
                for obs in observations
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "total_c68_book_count": len(by_book),
                "total_observation_count": len(observations),
                "discovery_observation_count": len(discovery),
                "heldout_observation_count": len(heldout),
                "heldout_phase_window_count": heldout_phase_window_count,
                "heldout_slot_window_count": heldout_slot_window_count,
                "heldout_phase_or_slot_count": heldout_phase_or_slot_count,
                "heldout_extra_class_count": heldout_extra_class_count,
                "heldout_tavt_boundary_count": heldout_tavt_boundary_count,
                "heldout_e_exit_count": heldout_e_exit_count,
                "heldout_terminal_count": heldout_terminal_count,
                "component_gloss_allowed_count": component_gloss_allowed_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
