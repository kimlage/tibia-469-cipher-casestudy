from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

PARENT_AUDIT = TEST_RESULTS / "01_prequential_and_row0_origin_audit.json"
BOOKCASE_MANIFEST = (
    ROOT
    / "analysis"
    / "physical_topology_20260620"
    / "tables"
    / "hellgate_public_bookcase_manifest.csv"
)
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def bookcase_metadata() -> dict[str, dict[str, Any]]:
    metadata: dict[str, dict[str, Any]] = {}
    with BOOKCASE_MANIFEST.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("local_match_status") != "resolved_unique" or not row.get("local_bookid"):
                continue
            label = f"hellgate_public_bookcase_{row['bookcase_public']}"
            item = metadata.setdefault(
                label,
                {
                    "bookcase_public": row["bookcase_public"],
                    "location": row["location"],
                    "room_or_library": row["room_or_library"],
                    "confidence": row["confidence"],
                    "notes": row["notes"],
                    "source_url": row["source_url"],
                    "manifest_rows": [],
                    "local_bookids": [],
                    "public_title_prefixes": [],
                },
            )
            item["manifest_rows"].append(int(row["hg_public_entry"]))
            item["local_bookids"].append(int(row["local_bookid"]))
            item["public_title_prefixes"].append(row["public_title_prefix"])
    return metadata


def component_rows(row: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for component in ("copy_length", "literal_payload", "item_type"):
        uniform = float(row["test_uniform_baseline_bits"][component])
        online = float(row["test_online_cost_bits"][component])
        frozen = float(row["test_frozen_cost_bits"][component])
        rows.append(
            {
                "component": component,
                "uniform_bits": uniform,
                "online_bits": online,
                "frozen_bits": frozen,
                "online_gain_vs_uniform_bits": uniform - online,
                "frozen_gain_vs_uniform_bits": uniform - frozen,
            }
        )
    return rows


def event_total(row: dict[str, Any]) -> int:
    events = row["event_counts"]
    return int(events["test_copy"]) + int(events["test_literal_payload"]) + int(events["test_item_type"])


def failure_reason(row: dict[str, Any], components: list[dict[str, Any]]) -> str:
    negative = [
        item["component"]
        for item in components
        if item["online_gain_vs_uniform_bits"] < 0 or item["frozen_gain_vs_uniform_bits"] < 0
    ]
    has_payload = int(row["event_counts"]["test_literal_payload"]) > 0
    total_events = event_total(row)
    if total_events <= 12 and not has_payload and "copy_length" in negative:
        return "small_copy_only_family_copy_length_under_uniform"
    if total_events <= 20 and "item_type" in negative:
        return "small_family_item_type_under_uniform"
    if negative:
        return "component_under_uniform"
    return "positive_or_near_positive"


def percentile_rank(value: int, values: list[int]) -> float:
    if not values:
        return 0.0
    below_or_equal = sum(1 for candidate in values if candidate <= value)
    return below_or_equal / len(values)


def make_result(parent: dict[str, Any]) -> dict[str, Any]:
    family_rows = parent["predictive_validation"]["public_bookcase_family_holdouts"]["rows"]
    metadata = bookcase_metadata()
    occ = load_json(OCC_STREAMS)
    full_duplicate_books = {int(book) for book in occ.get("full_dup_books", [])}
    totals = [event_total(row) for row in family_rows]

    rows = []
    for row in family_rows:
        components = component_rows(row)
        online_gain = float(row["aggregate"]["test_online_gain_vs_uniform_bits"])
        frozen_gain = float(row["aggregate"]["test_frozen_gain_vs_uniform_bits"])
        label = row["label"]
        test_books = [int(book) for book in row["test_books"]]
        rows.append(
            {
                "label": label,
                "bookcase_public": metadata.get(label, {}).get("bookcase_public"),
                "test_books": test_books,
                "public_title_prefixes": metadata.get(label, {}).get("public_title_prefixes", []),
                "event_counts": row["event_counts"],
                "test_event_total": event_total(row),
                "event_total_percentile_rank_low_to_high": percentile_rank(event_total(row), totals),
                "full_duplicate_test_books": sorted(set(test_books) & full_duplicate_books),
                "online_gain_vs_uniform_bits": online_gain,
                "frozen_gain_vs_uniform_bits": frozen_gain,
                "train_test_gap_bits_per_event": row["aggregate"]["online_train_test_gap_bits_per_event"],
                "component_gains": components,
                "dominant_negative_components": [
                    item["component"]
                    for item in components
                    if item["online_gain_vs_uniform_bits"] < 0
                    or item["frozen_gain_vs_uniform_bits"] < 0
                ],
                "failure": online_gain <= 0 or frozen_gain <= 0,
                "failure_reason": failure_reason(row, components),
                "manifest_confidence": metadata.get(label, {}).get("confidence"),
                "manifest_note": metadata.get(label, {}).get("notes"),
            }
        )

    failures = [row for row in rows if row["failure"]]
    copy_only_failures = [
        row for row in failures if int(row["event_counts"]["test_literal_payload"]) == 0
    ]
    item_type_failures = [
        row for row in failures if "item_type" in row["dominant_negative_components"]
    ]
    copy_length_failures = [
        row for row in failures if "copy_length" in row["dominant_negative_components"]
    ]

    return {
        "schema": "family_holdout_failure_audit.v1",
        "classification": "family_holdout_failures_are_component_and_sample_specific",
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "sources": {
            "parent_audit": rel(PARENT_AUDIT),
            "bookcase_manifest": rel(BOOKCASE_MANIFEST),
            "occ_streams": rel(OCC_STREAMS),
        },
        "summary": {
            "family_split_count": len(rows),
            "failure_count": len(failures),
            "failure_labels": [row["label"] for row in failures],
            "copy_only_failure_count": len(copy_only_failures),
            "item_type_failure_count": len(item_type_failures),
            "copy_length_failure_count": len(copy_length_failures),
            "minimum_family_event_total": min(totals),
            "median_family_event_total": sorted(totals)[len(totals) // 2],
            "maximum_family_event_total": max(totals),
        },
        "interpretation": {
            "result": (
                "The family holdout failures are not broad row0-origin evidence. "
                "They are small, component-specific losses in public bookcase groups."
            ),
            "strongest_failure": "hellgate_public_bookcase_33",
            "mechanical_reading": (
                "Bookcase 33 has five copy events, five item-type events, and no "
                "literal-payload events; copy-length coding loses more than item-type "
                "coding saves. Bookcase 8 shows the same copy-only pattern with only "
                "two copy events. Bookcase 6 is online-positive but frozen-negative "
                "because item-type coding loses to uniform by more than copy/payload "
                "save under frozen counts."
            ),
            "progress_delta": (
                "This narrows the previous partial-predictive classification: the "
                "family failures are explainable as component/sample-size stress cases, "
                "but they still block promotion to a final generation method."
            ),
        },
        "rows": rows,
    }


def render_markdown(result: dict[str, Any]) -> str:
    failures = [row for row in result["rows"] if row["failure"]]
    lines = [
        "# Family Holdout Failure Audit",
        "",
        "Classification: `family_holdout_failures_are_component_and_sample_specific`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This audit explains the public-bookcase family failures from the",
        "prequential/row0 origin audit. It does not search for a lower bit count,",
        "derive `row0`, or test plaintext. It decomposes each family split into",
        "copy-length, literal-payload, and item-type gains against uniform.",
        "",
        "## Summary",
        "",
        f"- Family splits: `{result['summary']['family_split_count']}`",
        f"- Failures: `{result['summary']['failure_count']}`",
        f"- Failure labels: `{result['summary']['failure_labels']}`",
        f"- Copy-only failures: `{result['summary']['copy_only_failure_count']}`",
        f"- Item-type failures: `{result['summary']['item_type_failure_count']}`",
        f"- Copy-length failures: `{result['summary']['copy_length_failure_count']}`",
        f"- Family event totals min/median/max: `{result['summary']['minimum_family_event_total']}` / `{result['summary']['median_family_event_total']}` / `{result['summary']['maximum_family_event_total']}`",
        "",
        "## Failure Rows",
        "",
        "| Family | Books | Events | Online gain | Frozen gain | Negative components | Reason |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in failures:
        lines.append(
            f"| `{row['label']}` | `{row['test_books']}` | `{row['test_event_total']}` | "
            f"`{row['online_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['frozen_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['dominant_negative_components']}` | `{row['failure_reason']}` |"
        )

    lines.extend(
        [
            "",
            "## Component Decomposition",
            "",
            "| Family | Component | Uniform | Online | Online gain | Frozen | Frozen gain |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in failures:
        for component in row["component_gains"]:
            lines.append(
                f"| `{row['label']}` | `{component['component']}` | "
                f"`{component['uniform_bits']:.3f}` | `{component['online_bits']:.3f}` | "
                f"`{component['online_gain_vs_uniform_bits']:.3f}` | "
                f"`{component['frozen_bits']:.3f}` | "
                f"`{component['frozen_gain_vs_uniform_bits']:.3f}` |"
            )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The family failures are component/sample-size stress cases, not a new row0-origin signal.",
            "- The strongest failure is `hellgate_public_bookcase_33`: copy-length loses `6.297` bits online against uniform, while item-type saves only `3.332` bits.",
            "- `hellgate_public_bookcase_8` is also copy-only and has only two copy events; the net loss is small.",
            "- `hellgate_public_bookcase_6` is online-positive but frozen-negative because item-type loses to uniform under frozen counts.",
            "- These failures keep the model at partial predictive structure; they do not support promoting a final authorial generation method.",
            "- `translation_delta`: `NONE`; `row0` remains exogenous.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parent = load_json(PARENT_AUDIT)
    result = make_result(parent)
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "02_family_holdout_failure_audit.json"
    md_path = TEST_RESULTS / "02_family_holdout_failure_audit.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(result), encoding="utf-8")


if __name__ == "__main__":
    main()
