#!/usr/bin/env python3
"""Q23: triage a recent external GitHub 'solved 469' claim without promotion."""

from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"

REPO_URL = "https://github.com/arturoornelasb/tibia-bonelord-469-cipher"
RAW_BASE = "https://raw.githubusercontent.com/arturoornelasb/tibia-bonelord-469-cipher/master"
RAW_URLS = {
    "mapping_v7": f"{RAW_BASE}/data/mapping_v7.json",
    "books": f"{RAW_BASE}/data/books.json",
    "readme": f"{RAW_BASE}/README.md",
    "narrative": f"{RAW_BASE}/docs/narrative_translation.md",
}

LORE_PAGES = {
    "tibiawiki_br_469": "https://www.tibiawiki.com.br/wiki/469",
    "fandom_469": "https://tibia.fandom.com/wiki/469",
}

ANCHOR_PROBES = [
    {
        "probe_id": "AWB_NAME_486486",
        "raw_digits": "486486",
        "expected_role": "A Wrinkled Bonelord name/self-identification anchor",
        "expected_meaning": "proper name / 486486, not generic plaintext",
    },
    {
        "probe_id": "AWB_TIBIA_ONE",
        "raw_digits": "1",
        "expected_role": "A Wrinkled Bonelord says Tibia is 1",
        "expected_meaning": "Tibia/world anchor",
    },
    {
        "probe_id": "AWB_ZERO_TABOO",
        "raw_digits": "0",
        "expected_role": "A Wrinkled Bonelord treats 0 as obscene/taboo",
        "expected_meaning": "taboo/control anchor",
    },
    {
        "probe_id": "AVAR_ORIGINAL_SLOT_63378129",
        "raw_digits": "63378129",
        "expected_role": "Q20 original Avar slot",
        "expected_meaning": "row0 external slot projects as VAIN",
    },
    {
        "probe_id": "AVAR_VARIANT_SLOT_62792068657272657261",
        "raw_digits": "62792068657272657261",
        "expected_role": "Q20 Tibia.org Avar variant slot",
        "expected_meaning": "row0 external slot projects as NARCISSIST",
    },
    {
        "probe_id": "KNIGHTMARE_3478_PHRASE",
        "raw_digits": "347867908719766434660345",
        "expected_role": "Knightmare/Bonelord Tome phrase holdout",
        "expected_meaning": "phrase-level holdout only",
    },
    {
        "probe_id": "CHAYENNE_REPLY",
        "raw_digits": "1145145194856114519083045765122821776612527570584",
        "expected_role": "Chayenne external 469 shape frame",
        "expected_meaning": "external frame/register holdout",
    },
]

CLAIMED_PROPER_NOUNS = [
    "SALZBERG",
    "ORANGENSTRASSE",
    "WEICHSTEIN",
    "GOTTDIENER",
    "SCHARDT",
]

DISCLAIMER_PATTERNS = [
    "I cannot confirm that the decoded content is the actual intended plaintext",
    "overfitting concern",
    "Books vs NPCs: two different cipher systems",
    "No results. No new dialogue, no reactions, nothing",
    "smoking gun",
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def j(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def fetch(url: str, timeout: int = 30) -> dict[str, object]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
            return {
                "ok": True,
                "url": url,
                "status": getattr(resp, "status", None),
                "final_url": resp.geturl(),
                "length": len(body),
                "body": body,
            }
    except Exception as exc:
        return {
            "ok": False,
            "url": url,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "body": "",
        }


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def decode_even_pairs(raw_digits: str, mapping: dict[str, str]) -> dict[str, object]:
    digits = re.sub(r"\D", "", raw_digits)
    if len(digits) % 2:
        return {
            "pair_decodable": False,
            "reason": "odd digit count under two-digit book-cipher assumption",
            "digit_count": len(digits),
            "decoded": "",
            "missing_codes": [],
        }
    pairs = [digits[i : i + 2] for i in range(0, len(digits), 2)]
    missing = [pair for pair in pairs if pair not in mapping]
    decoded = "".join(mapping.get(pair, "?") for pair in pairs)
    return {
        "pair_decodable": len(missing) == 0,
        "reason": "decoded by candidate two-digit mapping" if not missing else "missing candidate codes",
        "digit_count": len(digits),
        "pairs": pairs,
        "decoded": decoded,
        "missing_codes": sorted(set(missing)),
    }


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_q23_recent_github_candidate_solution_triage_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            repo_url TEXT NOT NULL,
            raw_fetch_success_count INTEGER NOT NULL,
            mapping_code_count INTEGER NOT NULL,
            book_count INTEGER NOT NULL,
            disclaimer_signal_count INTEGER NOT NULL,
            in_game_anchor_pass_count INTEGER NOT NULL,
            external_phrase_bridge_pass_count INTEGER NOT NULL,
            claimed_lore_noun_hit_count INTEGER NOT NULL,
            accepted_candidate_use_count INTEGER NOT NULL,
            canonical_promotion_allowed_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_q23_recent_github_candidate_solution_triage_v1_items (
            run_id INTEGER NOT NULL,
            item_id TEXT NOT NULL,
            item_type TEXT NOT NULL,
            status TEXT NOT NULL,
            role_label TEXT NOT NULL,
            support_class TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, item_id)
        );
        """
    )


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    raw_results = {key: fetch(url) for key, url in RAW_URLS.items()}
    lore_results = {key: fetch(url) for key, url in LORE_PAGES.items()}

    mapping: dict[str, str] = {}
    books: list[str] = []
    if raw_results["mapping_v7"]["ok"]:
        mapping = json.loads(str(raw_results["mapping_v7"]["body"]))
    if raw_results["books"]["ok"]:
        books = json.loads(str(raw_results["books"]["body"]))

    readme_text = str(raw_results["readme"].get("body", ""))
    narrative_text = str(raw_results["narrative"].get("body", ""))
    combined_docs = normalize_text(readme_text + "\n" + narrative_text)
    claimed_letter_counts = [
        int(match)
        for match in re.findall(r"(\d+)\s+German letters", combined_docs, flags=re.IGNORECASE)
    ]
    readme_claimed_letter_count = claimed_letter_counts[0] if claimed_letter_counts else None
    mapping_unique_letter_count = len(set(mapping.values()))

    disclaimer_hits = [
        pattern for pattern in DISCLAIMER_PATTERNS if pattern.lower() in combined_docs.lower()
    ]
    anchor_results = []
    for probe in ANCHOR_PROBES:
        decoded = decode_even_pairs(str(probe["raw_digits"]), mapping)
        status = "ANCHOR_NOT_LINKED_TO_CANDIDATE_MAPPING"
        if not decoded["pair_decodable"]:
            status = "ANCHOR_NOT_PAIR_DECODABLE_UNDER_CANDIDATE_BOOK_CIPHER"
        anchor_results.append({**probe, **decoded, "status": status})

    in_game_anchor_pass_count = 0
    external_phrase_bridge_pass_count = 0

    lore_hit_details = []
    for source_id, result in lore_results.items():
        body = str(result.get("body", ""))
        hits = [noun for noun in CLAIMED_PROPER_NOUNS if noun.lower() in body.lower()]
        lore_hit_details.append(
            {
                "source_id": source_id,
                "url": LORE_PAGES[source_id],
                "ok": bool(result.get("ok")),
                "length": int(result.get("length", 0) or 0),
                "claimed_noun_hits": hits,
            }
        )
    claimed_lore_noun_hit_count = sum(len(row["claimed_noun_hits"]) for row in lore_hit_details)

    accepted_candidate_use_count = int(
        len(mapping) == 98
        and len(books) == 70
        and len(disclaimer_hits) >= 3
        and in_game_anchor_pass_count == 0
        and external_phrase_bridge_pass_count == 0
    )
    canonical_promotion_allowed_count = 0

    raw_fetch_success_count = sum(1 for row in raw_results.values() if row.get("ok"))
    decision = (
        "Q23_RECENT_GITHUB_GERMAN_CANDIDATE_AUDIT_ONLY_NO_PROMOTION"
        if raw_fetch_success_count >= 3
        and len(mapping) == 98
        and len(books) == 70
        and accepted_candidate_use_count == 1
        and canonical_promotion_allowed_count == 0
        else "Q23_RECENT_GITHUB_CANDIDATE_REQUIRES_MANUAL_REVIEW"
    )

    items: list[dict[str, object]] = []
    for key, result in raw_results.items():
        body = str(result.get("body", ""))
        items.append(
            {
                "item_id": f"fetch:{key}",
                "item_type": "raw_remote_fetch",
                "status": "RAW_ARTIFACT_FETCHED" if result.get("ok") else "RAW_ARTIFACT_FETCH_FAILED",
                "role_label": f"Fetched candidate artifact {key}.",
                "support_class": "SUPPORT_CANDIDATE_TRIAGE" if result.get("ok") else "BLOCK_CANDIDATE_TRIAGE",
                "evidence_json": j(
                    {
                        "url": result.get("url"),
                        "ok": result.get("ok"),
                        "status": result.get("status"),
                        "length": result.get("length"),
                        "preview": body[:500],
                    }
                ),
            }
        )
    items.append(
        {
            "item_id": "candidate:mapping-shape",
            "item_type": "mapping_shape",
            "status": (
                "CANDIDATE_MAPPING_SHAPE_RECORDED_WITH_CLAIM_MISMATCH"
                if mapping and readme_claimed_letter_count is not None and mapping_unique_letter_count != readme_claimed_letter_count
                else "CANDIDATE_MAPPING_SHAPE_RECORDED" if mapping else "CANDIDATE_MAPPING_MISSING"
            ),
            "role_label": "Candidate maps two-digit codes to German/MHG letters.",
            "support_class": "CONTROL_CLAIM_MISMATCH" if mapping and readme_claimed_letter_count is not None and mapping_unique_letter_count != readme_claimed_letter_count else "SUPPORT_AUDIT_ONLY_HYPOTHESIS",
            "evidence_json": j(
                {
                    "mapping_code_count": len(mapping),
                    "book_count": len(books),
                    "letters": sorted(set(mapping.values())),
                    "mapping_unique_letter_count": mapping_unique_letter_count,
                    "readme_claimed_letter_count": readme_claimed_letter_count,
                    "missing_codes_from_00_99": [
                        f"{value:02d}" for value in range(100) if f"{value:02d}" not in mapping
                    ],
                }
            ),
        }
    )
    items.append(
        {
            "item_id": "candidate:self-disclaimer",
            "item_type": "candidate_disclaimer",
            "status": "CANDIDATE_SELF_IDENTIFIES_OVERFIT_AND_ANCHOR_GAPS" if len(disclaimer_hits) >= 3 else "CANDIDATE_DISCLAIMER_WEAK",
            "role_label": "Candidate documentation itself says intent is unconfirmed and NPC/book systems may differ.",
            "support_class": "CONTROL_BLOCK_PROMOTION",
            "evidence_json": j({"hits": disclaimer_hits}),
        }
    )
    for result in anchor_results:
        items.append(
            {
                "item_id": f"anchor:{result['probe_id']}",
                "item_type": "in_game_anchor_probe",
                "status": str(result["status"]),
                "role_label": str(result["expected_role"]),
                "support_class": "CONTROL_NO_INGAME_BRIDGE",
                "evidence_json": j(result),
            }
        )
    for row in lore_hit_details:
        items.append(
            {
                "item_id": f"lore-page:{row['source_id']}",
                "item_type": "claimed_lore_noun_probe",
                "status": "CLAIMED_NOUNS_NOT_FOUND_ON_469_LORE_PAGE" if not row["claimed_noun_hits"] else "CLAIMED_NOUNS_FOUND_ON_469_LORE_PAGE",
                "role_label": "Current 469 lore page check for candidate proper nouns.",
                "support_class": "CONTROL_LORE_LINK_WEAK" if not row["claimed_noun_hits"] else "SUPPORT_LORE_LINK",
                "evidence_json": j(row),
            }
        )
    items.append(
        {
            "item_id": "decision:audit-only-use",
            "item_type": "promotion_control",
            "status": "AUDIT_ONLY_SOURCE_NO_CANONICAL_PROMOTION",
            "role_label": "Candidate can inspire tests but cannot become a human or canonical translation layer yet.",
            "support_class": "CONTROL_NO_PROMOTION",
            "evidence_json": j(
                {
                    "accepted_candidate_use_count": accepted_candidate_use_count,
                    "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
                    "next_probe": "Import candidate mapping as shadow-only and test against contigs, row0 invariants, exact external anchors, and source-linked lore nouns before any reuse.",
                }
            ),
        }
    )

    payload = {
        "question": "Can the recent GitHub German/MHG candidate be used as a human translation solution?",
        "answer": (
            "No. It is useful as an audit-only external hypothesis because it has a concrete mapping and corpus, "
            "but it currently lacks the in-game/external anchor bridge required here and its own documentation flags intent, overfit, and NPC-system gaps."
        ),
        "allowed_reading": "Use as a quarantined candidate for adversarial tests and source-search prompts.",
        "blocked_reading": "Do not import its narrative translation as a solved Bonelord reading or promote book glosses.",
        "next_probe": "Run a shadow-only benchmark of the mapping against local contig/overlap data and exact external anchors.",
    }

    with conn:
        cur = conn.execute(
            """
            INSERT INTO human_q23_recent_github_candidate_solution_triage_v1_runs (
                created_at, decision, repo_url, raw_fetch_success_count,
                mapping_code_count, book_count, disclaimer_signal_count,
                in_game_anchor_pass_count, external_phrase_bridge_pass_count,
                claimed_lore_noun_hit_count, accepted_candidate_use_count,
                canonical_promotion_allowed_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now(),
                decision,
                REPO_URL,
                raw_fetch_success_count,
                len(mapping),
                len(books),
                len(disclaimer_hits),
                in_game_anchor_pass_count,
                external_phrase_bridge_pass_count,
                claimed_lore_noun_hit_count,
                accepted_candidate_use_count,
                canonical_promotion_allowed_count,
                j(payload),
            ),
        )
        run_id = int(cur.lastrowid)
        conn.executemany(
            """
            INSERT INTO human_q23_recent_github_candidate_solution_triage_v1_items (
                run_id, item_id, item_type, status, role_label, support_class,
                evidence_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    str(item["item_id"]),
                    str(item["item_type"]),
                    str(item["status"]),
                    str(item["role_label"]),
                    str(item["support_class"]),
                    str(item["evidence_json"]),
                )
                for item in items
            ],
        )

    print(
        j(
            {
                "run_id": run_id,
                "decision": decision,
                "repo_url": REPO_URL,
                "raw_fetch_success_count": raw_fetch_success_count,
                "mapping_code_count": len(mapping),
                "book_count": len(books),
                "disclaimer_signal_count": len(disclaimer_hits),
                "in_game_anchor_pass_count": in_game_anchor_pass_count,
                "external_phrase_bridge_pass_count": external_phrase_bridge_pass_count,
                "claimed_lore_noun_hit_count": claimed_lore_noun_hit_count,
                "accepted_candidate_use_count": accepted_candidate_use_count,
                "canonical_promotion_allowed_count": canonical_promotion_allowed_count,
            }
        )
    )


if __name__ == "__main__":
    main()
