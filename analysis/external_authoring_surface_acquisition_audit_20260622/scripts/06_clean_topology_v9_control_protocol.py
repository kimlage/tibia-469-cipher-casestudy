#!/usr/bin/env python3
"""Pre-registered v9 control protocol for clean topology inputs.

This script is the executable test plan for a future rights-clean topology CSV.
It performs schema/book matching, joins topology to the v9 residual streams, and
then, only if coverage is sufficient, evaluates topology features under
prefix/leave-container holdouts plus topology-label permutation controls.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/external_authoring_surface_acquisition_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
DEFAULT_INPUT = OUT_DIR / "04_clean_topology_contract_template.csv"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
MINIMAL_LEDGER = ROOT / "analysis/minimal_external_tape_program_audit_20260622/reports/test_results/02_unified_external_tape_ledger.json"
FINAL_REPORT = FRONT / "reports/final_external_authoring_surface_acquisition_audit.md"

REQUIRED_FIELDS = [
    "source_id",
    "source_rights",
    "source_version_or_date",
    "book_text_or_exact_prefix",
    "x",
    "y",
    "z",
    "container_or_bookcase_id",
    "slot_or_read_order",
    "capture_method",
]
FORBIDDEN_RIGHTS_MARKERS = ["", "unknown", "leak", "leaked", "proprietary_leak"]
MIN_TOTAL_MATCHED_BOOKS = 20
MIN_DERIVED_MATCHED_BOOKS = 10
MIN_SPLITS = 3
RANDOM_SEED = 46920260622 + 600
RANDOM_TRIALS = 150
ALPHA = 0.5
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]

FEATURES = ["container", "slot_bucket", "coord_bucket", "container_x_slot_bucket", "container_x_op_pos"]
TARGETS = {
    "coarse_control": {"row_filter": "all", "target_field": "coarse_control"},
    "op_type": {"row_filter": "all", "target_field": "op_type"},
    "copy_hint_rank_bucket": {"row_filter": "copy", "target_field": "copy_hint_rank_bucket"},
}


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def validate_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if not rows:
        return [{"line": 1, "field": "*", "error": "no_rows"}]
    header = rows[0].keys()
    for field in REQUIRED_FIELDS:
        if field not in header:
            errors.append({"line": 1, "field": field, "error": "missing_required_column"})
    if errors:
        return errors
    for index, row in enumerate(rows, start=2):
        for field in REQUIRED_FIELDS:
            if not str(row.get(field, "")).strip():
                errors.append({"line": index, "field": field, "error": "blank_required_field"})
        rights = str(row.get("source_rights", "")).strip().lower()
        if rights in FORBIDDEN_RIGHTS_MARKERS or "leak" in rights:
            errors.append({"line": index, "field": "source_rights", "error": "unacceptable_rights_marker"})
        for coord in ["x", "y", "z"]:
            try:
                int(str(row.get(coord, "")).strip())
            except ValueError:
                errors.append({"line": index, "field": coord, "error": "coordinate_not_integer"})
        try:
            int(str(row.get("slot_or_read_order", "")).strip())
        except ValueError:
            errors.append({"line": index, "field": "slot_or_read_order", "error": "slot_not_integer"})
    return errors


def match_books(rows: list[dict[str, str]], books: dict[str, str]) -> list[dict[str, Any]]:
    matches = []
    for index, row in enumerate(rows, start=2):
        prefix = "".join(ch for ch in row.get("book_text_or_exact_prefix", "") if ch.isdigit())
        matched = [
            int(book)
            for book, digits in books.items()
            if prefix and (digits == prefix or digits.startswith(prefix))
        ]
        matches.append(
            {
                "line": index,
                "prefix": prefix,
                "matched_books": sorted(matched),
                "match_status": "unique" if len(matched) == 1 else "ambiguous" if matched else "unmatched",
                "row": row,
            }
        )
    return matches


def topology_by_book(matches: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    topology: dict[int, dict[str, Any]] = {}
    for match in matches:
        if match["match_status"] != "unique":
            continue
        row = match["row"]
        book = match["matched_books"][0]
        slot = int(row["slot_or_read_order"])
        topology[book] = {
            "book": book,
            "x": int(row["x"]),
            "y": int(row["y"]),
            "z": int(row["z"]),
            "container": row["container_or_bookcase_id"],
            "slot": slot,
            "slot_bucket": f"slot_q{min(3, slot // 4)}",
            "source_id": row["source_id"],
        }
    return topology


def feature_value(row: dict[str, Any], feature: str) -> str:
    if feature == "container":
        return str(row["container"])
    if feature == "slot_bucket":
        return str(row["slot_bucket"])
    if feature == "coord_bucket":
        return str(row["coord_bucket"])
    if feature == "container_x_slot_bucket":
        return f"{row['container']}|{row['slot_bucket']}"
    if feature == "container_x_op_pos":
        return f"{row['container']}|{row['op_pos_bucket']}"
    raise KeyError(feature)


def build_joined_rows(topology: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    minimal = load_json(MINIMAL_LEDGER)
    joined = []
    for raw in minimal["ledger_rows"]:
        book = int(raw["book"])
        topo = topology.get(book)
        if topo is None:
            continue
        joined.append(
            {
                "book": book,
                "op_index": int(raw["op_index"]),
                "op_pos_bucket": raw["op_pos_bucket"],
                "coarse_control": raw["coarse_type_length_bucket"],
                "op_type": raw["op_type"],
                "copy_hint_rank_bucket": raw.get("copy_hint_rank_bucket"),
                "container": topo["container"],
                "slot_bucket": topo["slot_bucket"],
                "coord_bucket": f"{topo['x']//10}:{topo['y']//10}:{topo['z']}",
            }
        )
    return joined


def target_rows(rows: list[dict[str, Any]], target_name: str) -> list[dict[str, Any]]:
    spec = TARGETS[target_name]
    if spec["row_filter"] == "copy":
        return [row for row in rows if row["op_type"] == "copy" and row.get(spec["target_field"]) is not None]
    return rows


def target_alphabet(rows: list[dict[str, Any]], target_name: str) -> list[str]:
    field = TARGETS[target_name]["target_field"]
    return sorted({str(row[field]) for row in target_rows(rows, target_name)})


def counts_for(rows: list[dict[str, Any]], target_name: str, feature: str | None) -> tuple[Counter[str], dict[str, Counter[str]]]:
    field = TARGETS[target_name]["target_field"]
    global_counts: Counter[str] = Counter()
    feature_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in target_rows(rows, target_name):
        symbol = str(row[field])
        global_counts[symbol] += 1
        if feature is not None:
            feature_counts[feature_value(row, feature)][symbol] += 1
    return global_counts, feature_counts


def code_bits(train: list[dict[str, Any]], test: list[dict[str, Any]], target_name: str, feature: str | None, alphabet: list[str]) -> float:
    global_counts, feature_counts = counts_for(train, target_name, feature)
    field = TARGETS[target_name]["target_field"]
    vocab = max(1, len(alphabet))
    bits = 0.0
    for row in target_rows(test, target_name):
        counter = global_counts if feature is None else feature_counts.get(feature_value(row, feature), global_counts)
        total = sum(counter.values())
        probability = (counter.get(str(row[field]), 0) + ALPHA) / (total + ALPHA * vocab)
        bits += -math.log2(probability)
    return bits


def loo_train_bits(rows: list[dict[str, Any]], target_name: str, feature: str, alphabet: list[str]) -> float:
    books = sorted({row["book"] for row in rows})
    if len(books) < 2:
        return float("inf")
    total = 0.0
    for heldout in books:
        train = [row for row in rows if row["book"] != heldout]
        test = [row for row in rows if row["book"] == heldout]
        total += code_bits(train, test, target_name, feature, alphabet)
    return total + math.log2(len(FEATURES))


def select_feature(train: list[dict[str, Any]], target_name: str, alphabet: list[str]) -> str:
    candidates = [(loo_train_bits(train, target_name, feature, alphabet), feature) for feature in FEATURES]
    return min(candidates)[1]


def split_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    splits = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        if train and test and len({row["book"] for row in train}) >= 2 and len({row["book"] for row in test}) >= 2:
            splits.append({"label": f"prefix_{cutoff}", "split_type": "prefix", "train": train, "test": test})
    containers = sorted({row["container"] for row in rows})
    for container in containers:
        train = [row for row in rows if row["container"] != container]
        test = [row for row in rows if row["container"] == container]
        if train and test and len({row["book"] for row in train}) >= 2 and len({row["book"] for row in test}) >= 2:
            splits.append({"label": f"leave_container_{container}", "split_type": "leave_container", "train": train, "test": test})
    return splits


def evaluate_target(rows: list[dict[str, Any]], target_name: str, forced_features_by_split: dict[str, str] | None = None) -> dict[str, Any]:
    alphabet = target_alphabet(rows, target_name)
    split_results = []
    for split in split_rows(rows):
        feature = forced_features_by_split.get(split["label"]) if forced_features_by_split else None
        if feature is None:
            feature = select_feature(split["train"], target_name, alphabet)
        global_bits = code_bits(split["train"], split["test"], target_name, None, alphabet)
        topology_bits = code_bits(split["train"], split["test"], target_name, feature, alphabet) + math.log2(len(FEATURES))
        test_targets = target_rows(split["test"], target_name)
        split_results.append(
            {
                "feature": feature,
                "global_bits": global_bits,
                "label": split["label"],
                "saving_bits": global_bits - topology_bits,
                "split_type": split["split_type"],
                "target_rows": len(test_targets),
                "topology_bits": topology_bits,
                "train_books": len({row["book"] for row in split["train"]}),
            }
        )
    return {
        "alphabet_size": len(alphabet),
        "split_results": split_results,
        "summary": {
            "positive_splits": sum(row["saving_bits"] > 0 for row in split_results),
            "split_count": len(split_results),
            "total_global_bits": sum(row["global_bits"] for row in split_results),
            "total_topology_bits": sum(row["topology_bits"] for row in split_results),
            "total_target_rows": sum(row["target_rows"] for row in split_results),
        },
    }


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(p / 100 * len(ordered)) - 1))
    return ordered[index]


def permute_topology(topology: dict[int, dict[str, Any]], rng: random.Random) -> dict[int, dict[str, Any]]:
    books = sorted(topology)
    values = [dict(topology[book]) for book in books]
    rng.shuffle(values)
    return {book: value for book, value in zip(books, values)}


def permutation_controls(topology: dict[int, dict[str, Any]], target_name: str, real_saving: float, forced_features_by_split: dict[str, str]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + sum(ord(ch) for ch in target_name))
    savings = []
    for _ in range(RANDOM_TRIALS):
        rows = build_joined_rows(permute_topology(topology, rng))
        evaluated = evaluate_target(rows, target_name, forced_features_by_split)
        savings.append(evaluated["summary"]["total_global_bits"] - evaluated["summary"]["total_topology_bits"])
    return {
        "beats_permutation_p95": real_saving > percentile(savings, 95),
        "permutation_mean": sum(savings) / len(savings),
        "permutation_p05": percentile(savings, 5),
        "permutation_p50": percentile(savings, 50),
        "permutation_p95": percentile(savings, 95),
        "trials": RANDOM_TRIALS,
    }


def run_protocol(input_path: Path) -> dict[str, Any]:
    books = load_json(BOOKS_DIGITS)
    rows = load_csv(input_path)
    validation_errors = validate_rows(rows)
    matches = [] if validation_errors else match_books(rows, books)
    topology = topology_by_book(matches)
    matched_books = sorted(topology)
    derived_books = [book for book in matched_books if book >= 10]
    coverage_ok = len(matched_books) >= MIN_TOTAL_MATCHED_BOOKS and len(derived_books) >= MIN_DERIVED_MATCHED_BOOKS
    joined = build_joined_rows(topology) if coverage_ok else []
    split_count = len(split_rows(joined)) if joined else 0
    runnable = coverage_ok and split_count >= MIN_SPLITS

    target_results = {}
    promoted = []
    if runnable:
        for target_name in TARGETS:
            evaluated = evaluate_target(joined, target_name)
            forced = {row["label"]: row["feature"] for row in evaluated["split_results"]}
            controls = permutation_controls(
                topology,
                target_name,
                evaluated["summary"]["total_global_bits"] - evaluated["summary"]["total_topology_bits"],
                forced,
            )
            evaluated["permutation_controls"] = controls
            target_results[target_name] = evaluated
            if (
                evaluated["summary"]["total_global_bits"] > evaluated["summary"]["total_topology_bits"]
                and controls["beats_permutation_p95"]
            ):
                promoted.append(target_name)

    classification = (
        "PROMOTED_CLEAN_TOPOLOGY_V9_CONTROL_SOURCE"
        if promoted
        else "clean_topology_v9_controls_preregistered_not_run_coverage_insufficient"
        if not runnable
        else "clean_topology_v9_control_source_not_promoted"
    )
    return {
        "schema": "clean_topology_v9_control_protocol.v1",
        "scope": "analysis_only_clean_topology_v9_control_protocol",
        "classification": classification,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "input_csv": str(input_path.relative_to(ROOT)),
        "protocol": {
            "features": FEATURES,
            "targets": list(TARGETS),
            "alpha": ALPHA,
            "random_trials": RANDOM_TRIALS,
            "prefix_cutoffs": PREFIX_CUTOFFS,
            "minimum_coverage": {
                "total_matched_books": MIN_TOTAL_MATCHED_BOOKS,
                "derived_matched_books": MIN_DERIVED_MATCHED_BOOKS,
                "split_count": MIN_SPLITS,
            },
            "promotion_rule": "positive total heldout saving and beats topology-label permutation p95",
        },
        "validation_errors": validation_errors,
        "match_summary": {
            "input_rows": len(rows),
            "unique_matches": sum(1 for match in matches if match["match_status"] == "unique"),
            "ambiguous_matches": sum(1 for match in matches if match["match_status"] == "ambiguous"),
            "unmatched": sum(1 for match in matches if match["match_status"] == "unmatched"),
            "matched_books": matched_books,
            "derived_matched_books": derived_books,
        },
        "coverage_ok": coverage_ok,
        "joined_v9_rows": len(joined),
        "split_count": split_count,
        "target_results": target_results,
        "decision": {
            "external_surface_integrated": bool(promoted),
            "promoted_targets": promoted,
            "v9_reduction_bits": 0.0,
            "reason": "coverage_insufficient" if not coverage_ok else "split_count_insufficient" if not runnable else "no_promoted_target",
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# Clean Topology v9 Control Protocol",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This is the pre-registered executable control protocol for a future rights-clean topology CSV.",
        "",
        f"Current input `{result['input_csv']}` has `{result['match_summary']['unique_matches']}` unique match(es), "
        f"`{len(result['match_summary']['derived_matched_books'])}` derived-book match(es), "
        f"`{result['joined_v9_rows']}` joined v9 rows, and `{result['split_count']}` usable splits.",
        "",
        "## Protocol",
        "",
        f"- Features: `{result['protocol']['features']}`",
        f"- Targets: `{result['protocol']['targets']}`",
        f"- Permutation controls: `{result['protocol']['random_trials']}` trials",
        f"- Promotion rule: {result['protocol']['promotion_rule']}",
        "",
        "## Decision",
        "",
        "No external topology source is integrated in the current run. Net v9 reduction: `0.0` bits.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    (OUT_DIR / "06_clean_topology_v9_control_protocol.md").write_text("\n".join(lines) + "\n")


def append_final(result: dict[str, Any]) -> None:
    report = FINAL_REPORT.read_text() if FINAL_REPORT.exists() else ""
    marker = "## Clean Topology v9 Control Protocol"
    if marker in report:
        return
    addition = [
        "",
        marker,
        "",
        "A pre-registered executable control protocol now exists for future rights-clean topology CSV inputs.",
        "It will run prefix/leave-container holdouts, feature selection on training data, and topology-label permutation controls against v9 streams.",
        f"The current template input has `{result['match_summary']['unique_matches']}` unique match and does not meet coverage thresholds, so no source is integrated and no v9 reduction is claimed.",
        "",
        "- [06_clean_topology_v9_control_protocol.py](../scripts/06_clean_topology_v9_control_protocol.py)",
        "- [06_clean_topology_v9_control_protocol.json](test_results/06_clean_topology_v9_control_protocol.json)",
        "- [06_clean_topology_v9_control_protocol.md](test_results/06_clean_topology_v9_control_protocol.md)",
    ]
    FINAL_REPORT.write_text(report.rstrip() + "\n" + "\n".join(addition) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Clean topology CSV path")
    args = parser.parse_args()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT / input_path

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = run_protocol(input_path)
    (OUT_DIR / "06_clean_topology_v9_control_protocol.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    append_final(result)


if __name__ == "__main__":
    main()
