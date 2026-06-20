from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TABLES = HERE / "tables"
REPORTS = HERE / "reports" / "test_results"

SEED = TABLES / "hellgate_public_bookcase_seed.csv"
OUT_MANIFEST = TABLES / "hellgate_public_bookcase_manifest.csv"
DB = ROOT / "data/bonelord_operational.sqlite"

REQUIRED_FINE_FIELDS = [
    "book_id",
    "source_location",
    "room_or_library",
    "shelf_or_container",
    "tile_or_position",
    "read_order",
    "capture_source_url_or_commit",
    "verification_date",
]


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_books() -> list[dict]:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            "select bookid, digits, digitslen, decodedbase from sheet__books order by cast(bookid as int)"
        )
    ]


def main() -> None:
    sources = yaml.safe_load((HERE / "public_topology_sources.yaml").read_text(encoding="utf-8"))
    books = load_books()
    seed_rows = list(csv.DictReader(SEED.open(encoding="utf-8")))

    manifest_rows = []
    local_ids_seen = set()
    ambiguous = []
    unmatched = []
    resolved = []
    for row in seed_rows:
        prefix = row["public_title_prefix"]
        candidates = [
            {
                "bookid": book["bookid"],
                "digitslen": int(book["digitslen"]),
                "digits_prefix_24": book["digits"][:24],
            }
            for book in books
            if book["digits"].startswith(prefix)
        ]
        candidate_ids = [item["bookid"] for item in candidates]
        status = "resolved_unique" if len(candidates) == 1 else "ambiguous" if candidates else "unmatched"
        local_bookid = candidates[0]["bookid"] if len(candidates) == 1 else ""
        if status == "resolved_unique":
            resolved.append(row["hg_public_entry"])
            local_ids_seen.add(local_bookid)
        elif status == "ambiguous":
            ambiguous.append(row["hg_public_entry"])
            local_ids_seen.update(candidate_ids)
        else:
            unmatched.append(row["hg_public_entry"])

        manifest_rows.append(
            {
                "hg_public_entry": row["hg_public_entry"],
                "location": "Hellgate Library",
                "room_or_library": "Hellgate Library",
                "bookcase_public": row["bookcase_public"],
                "public_title_prefix": prefix,
                "local_match_status": status,
                "local_bookid": local_bookid,
                "candidate_local_bookids": "|".join(candidate_ids),
                "source_url": sources["sources"]["hellgate_library_fandom"]["url"],
                "confidence": "medium_public_bookcase_not_tile",
                "notes": "public overview order; not authorial read order; no exact tile/slot/orientation",
            }
        )

    OUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MANIFEST.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(manifest_rows[0]))
        writer.writeheader()
        writer.writerows(manifest_rows)

    source_checks = {
        key: {
            "url_present": bool(value.get("url")),
            "verified_on": value.get("verified_on"),
            "community_not_official_gt": value.get("source_type") != "official_gt",
            "blocked_use_present": bool(value.get("blocked_use")),
        }
        for key, value in sources["sources"].items()
    }
    fine_topology_available = False
    result = {
        "schema": "public_topology_manifest_audit.v1",
        "test": "01_public_topology_manifest_audit",
        "classification": "partial_public_topology_ready_fine_topology_blocked",
        "translation_delta": "NONE",
        "seed_entries": len(seed_rows),
        "local_db_books": len(books),
        "resolved_unique_entries": len(resolved),
        "ambiguous_entries": len(ambiguous),
        "unmatched_entries": len(unmatched),
        "local_books_covered_by_any_candidate": len(local_ids_seen),
        "manifest_path": str(OUT_MANIFEST.relative_to(ROOT)),
        "source_checks": source_checks,
        "fine_topology_available": fine_topology_available,
        "required_fine_fields": REQUIRED_FINE_FIELDS,
        "ambiguous_public_entries": ambiguous,
        "unmatched_public_entries": unmatched,
    }

    lines = [
        "# Public Topology Manifest Audit",
        "",
        f"Verdict: `{result['classification']}`. Translation delta: `NONE`.",
        "",
        "This audit builds a partial public Hellgate bookcase manifest and maps it",
        "to the local 70-book corpus by numeric prefix. It intentionally does not",
        "claim exact tile, slot, orientation, map-version, or authorial read order.",
        "",
        "## Coverage",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Public seed entries | `{result['seed_entries']}` |",
        f"| Local DB books | `{result['local_db_books']}` |",
        f"| Resolved unique entries | `{result['resolved_unique_entries']}` |",
        f"| Ambiguous entries | `{result['ambiguous_entries']}` |",
        f"| Unmatched entries | `{result['unmatched_entries']}` |",
        f"| Local books covered by any candidate | `{result['local_books_covered_by_any_candidate']}` |",
        "",
        "## Ambiguity",
        "",
        "The public table is usable as a partial bookcase/order seed, but several",
        "short public title prefixes are ambiguous against the local corpus. The",
        "seed also has 71 public entries while the local canonical corpus has 70",
        "books. This preserves the blocker against treating public entry order as",
        "a clean authorial sequence.",
        "",
        f"Ambiguous public entries: `{ambiguous}`",
        "",
        "## Source Checks",
        "",
        "| Source | URL | Verified date | Community/non-GT | Blocked use |",
        "|---|---:|---|---:|---:|",
    ]
    for key, check in source_checks.items():
        lines.append(
            f"| `{key}` | `{check['url_present']}` | `{check['verified_on']}` | "
            f"`{check['community_not_official_gt']}` | `{check['blocked_use_present']}` |"
        )
    lines += [
        "",
        "## Fine Topology Blocker",
        "",
        "Still missing for promotion:",
        "",
    ]
    lines.extend(f"- `{field}`" for field in REQUIRED_FINE_FIELDS)
    lines += [
        "",
        "## Conclusion",
        "",
        "Macro/bookcase topology is ready for bounded mechanical tests. Fine-grained",
        "topology remains blocked, and semantic translation remains unchanged.",
    ]
    write_result("01_public_topology_manifest_audit", result, lines)


if __name__ == "__main__":
    main()
