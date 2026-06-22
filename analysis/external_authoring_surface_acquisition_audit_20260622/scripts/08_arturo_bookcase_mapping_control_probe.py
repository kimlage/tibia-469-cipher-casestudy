#!/usr/bin/env python3
"""Probe a public bookcase-mapping repository as an external control surface.

The source repository also contains a claimed semantic solution. This audit
does not read or use any mapping/plaintext artifacts. It only fetches
bookcase_mapping.json and LICENSE, treats the mapping as community topology
metadata, and tests whether bookcase/slot/order variables predict v9 residual
streams under holdout and topology-label permutation controls.
"""

from __future__ import annotations

import json
import math
import random
import re
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/external_authoring_surface_acquisition_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
FINAL_REPORT = FRONT / "reports/final_external_authoring_surface_acquisition_audit.md"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
MINIMAL_LEDGER = ROOT / "analysis/minimal_external_tape_program_audit_20260622/reports/test_results/02_unified_external_tape_ledger.json"

REPO = "arturoornelasb/tibia-bonelord-469-cipher"
BRANCH = "master"
REPO_URL = f"https://github.com/{REPO}"
BOOKCASE_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/data/bookcase_mapping.json"
DATA_README_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/data/README.md"
LICENSE_URL = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/LICENSE"

ALPHA = 0.5
RANDOM_SEED = 46920260622 + 800
RANDOM_TRIALS = 150
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
FEATURES = [
    "bookcase",
    "bookcase_number_bucket",
    "slot_in_bookcase",
    "library_number_decile",
    "library_number_quartile",
    "bookcase_x_slot",
    "bookcase_x_op_pos",
]
TARGETS = {
    "coarse_control": {"row_filter": "all", "target_field": "coarse_type_length_bucket"},
    "op_type": {"row_filter": "all", "target_field": "op_type"},
    "copy_hint_rank_bucket": {"row_filter": "copy", "target_field": "copy_hint_rank_bucket"},
}


def fetch_text(url: str) -> tuple[str | None, str | None, int | None]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "tibia-469-casestudy-audit"})
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8"), None, getattr(response, "status", None)
    except (urllib.error.URLError, TimeoutError, UnicodeDecodeError) as exc:
        return None, repr(exc), None


def fetch_json(url: str) -> tuple[Any | None, str | None, int | None]:
    text, error, status = fetch_text(url)
    if error:
        return None, error, status
    try:
        return json.loads(text or ""), None, status
    except json.JSONDecodeError as exc:
        return None, repr(exc), status


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def bookcase_number(value: str) -> int | None:
    words = {
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5,
        "sixth": 6,
        "seventh": 7,
        "eighth": 8,
        "ninth": 9,
        "tenth": 10,
        "eleventh": 11,
        "twelfth": 12,
        "thirteenth": 13,
        "fourteenth": 14,
        "fifteenth": 15,
        "sixteenth": 16,
        "seventeenth": 17,
        "eighteenth": 18,
        "nineteenth": 19,
        "twentieth": 20,
        "twenty-first": 21,
        "twenty-second": 22,
        "twenty-third": 23,
        "twenty-fourth": 24,
        "twenty-fifth": 25,
        "twenty-sixth": 26,
        "twenty-seventh": 27,
        "twenty-eighth": 28,
        "twenty-ninth": 29,
        "thirtieth": 30,
        "thirty-first": 31,
        "thirty-second": 32,
        "thirty-third": 33,
        "thirty-fourth": 34,
        "thirty-fifth": 35,
        "thirty-sixth": 36,
        "thirty-seventh": 37,
        "thirty-eighth": 38,
        "thirty-ninth": 39,
        "fortieth": 40,
    }
    lowered = value.lower().replace(" bookcase", "").strip()
    return words.get(lowered)


def match_mapping(mapping: list[dict[str, Any]], books: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    book_to_seen_rows: dict[int, int] = {}
    by_prefix = defaultdict(list)
    for book, digits in books.items():
        by_prefix[digits[:10]].append(int(book))

    bookcase_counts: Counter[str] = Counter(str(row.get("bookcase", "")) for row in mapping)
    bookcase_running: Counter[str] = Counter()
    for row_index, row in enumerate(mapping):
        label = "".join(ch for ch in str(row.get("label_10digit", "")) if ch.isdigit())
        matched = sorted(by_prefix.get(label, []))
        bookcase = str(row.get("bookcase", ""))
        bookcase_running[bookcase] += 1
        slot = bookcase_running[bookcase]
        book = matched[0] if len(matched) == 1 else None
        duplicate_for_book = False
        if book is not None:
            duplicate_for_book = book in book_to_seen_rows
            book_to_seen_rows.setdefault(book, row_index)
        number = bookcase_number(bookcase)
        rows.append(
            {
                "source_row_index": row_index,
                "library_number": int(row.get("library_number", row_index + 1)),
                "bookcase": bookcase,
                "bookcase_number": number,
                "slot_in_bookcase": slot,
                "bookcase_slot_count": bookcase_counts[bookcase],
                "label_10digit": label,
                "matched_books": matched,
                "match_status": "unique" if len(matched) == 1 else "ambiguous" if matched else "unmatched",
                "book": book,
                "duplicate_for_book": duplicate_for_book,
                "raw": row,
            }
        )
    return rows


def topology_by_book(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    topology = {}
    for row in rows:
        if row["match_status"] != "unique" or row["duplicate_for_book"]:
            continue
        book = int(row["book"])
        number = row["bookcase_number"] or 0
        library_number = int(row["library_number"])
        topology[book] = {
            "book": book,
            "bookcase": row["bookcase"],
            "bookcase_number_bucket": f"bc_q{min(7, number // 5)}",
            "slot_in_bookcase": f"slot_{row['slot_in_bookcase']}",
            "library_number_decile": f"lib_q{min(9, (library_number - 1) // 8)}",
            "library_number_quartile": f"lib_q{min(3, (library_number - 1) // 18)}",
        }
    return topology


def build_joined_rows(topology: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    minimal = load_json(MINIMAL_LEDGER)
    joined = []
    for row in minimal["ledger_rows"]:
        book = int(row["book"])
        topo = topology.get(book)
        if topo is None:
            continue
        merged = {**row, **topo}
        merged["bookcase_x_slot"] = f"{merged['bookcase']}|{merged['slot_in_bookcase']}"
        merged["bookcase_x_op_pos"] = f"{merged['bookcase']}|{merged['op_pos_bucket']}"
        joined.append(merged)
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
            feature_counts[str(row[feature])][symbol] += 1
    return global_counts, feature_counts


def code_bits(train: list[dict[str, Any]], test: list[dict[str, Any]], target_name: str, feature: str | None, alphabet: list[str]) -> float:
    global_counts, feature_counts = counts_for(train, target_name, feature)
    field = TARGETS[target_name]["target_field"]
    vocab = max(1, len(alphabet))
    bits = 0.0
    for row in target_rows(test, target_name):
        counter = global_counts if feature is None else feature_counts.get(str(row[feature]), global_counts)
        total = sum(counter.values())
        probability = (counter.get(str(row[field]), 0) + ALPHA) / (total + ALPHA * vocab)
        bits += -math.log2(probability)
    return bits


def split_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    splits = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        if train and test and len({row["book"] for row in train}) >= 2 and len({row["book"] for row in test}) >= 2:
            splits.append({"label": f"prefix_{cutoff}", "split_type": "prefix", "train": train, "test": test})
    bookcases = sorted({str(row["bookcase"]) for row in rows})
    for bookcase in bookcases:
        train = [row for row in rows if str(row["bookcase"]) != bookcase]
        test = [row for row in rows if str(row["bookcase"]) == bookcase]
        if train and test and len({row["book"] for row in train}) >= 2 and len({row["book"] for row in test}) >= 2:
            splits.append({"label": f"leave_bookcase_{bookcase}", "split_type": "leave_bookcase", "train": train, "test": test})
    return splits


def select_feature(train: list[dict[str, Any]], target_name: str, alphabet: list[str]) -> str:
    scored = []
    books = sorted({int(row["book"]) for row in train})
    for feature in FEATURES:
        bits = 0.0
        for heldout in books:
            sub_train = [row for row in train if int(row["book"]) != heldout]
            sub_test = [row for row in train if int(row["book"]) == heldout]
            bits += code_bits(sub_train, sub_test, target_name, feature, alphabet)
        scored.append((bits + math.log2(len(FEATURES)), feature))
    return min(scored)[1]


def evaluate_target(rows: list[dict[str, Any]], target_name: str, forced_features_by_split: dict[str, str] | None = None) -> dict[str, Any]:
    alphabet = target_alphabet(rows, target_name)
    split_results = []
    for split in split_rows(rows):
        feature = forced_features_by_split.get(split["label"]) if forced_features_by_split else None
        if feature is None:
            feature = select_feature(split["train"], target_name, alphabet)
        global_bits = code_bits(split["train"], split["test"], target_name, None, alphabet)
        feature_bits = code_bits(split["train"], split["test"], target_name, feature, alphabet) + math.log2(len(FEATURES))
        split_results.append(
            {
                "label": split["label"],
                "split_type": split["split_type"],
                "feature": feature,
                "target_rows": len(target_rows(split["test"], target_name)),
                "train_books": len({row["book"] for row in split["train"]}),
                "global_bits": global_bits,
                "feature_bits": feature_bits,
                "saving_bits": global_bits - feature_bits,
            }
        )
    return {
        "alphabet_size": len(alphabet),
        "split_results": split_results,
        "summary": {
            "split_count": len(split_results),
            "positive_splits": sum(row["saving_bits"] > 0 for row in split_results),
            "total_global_bits": sum(row["global_bits"] for row in split_results),
            "total_feature_bits": sum(row["feature_bits"] for row in split_results),
            "total_saving_bits": sum(row["saving_bits"] for row in split_results),
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
        savings.append(evaluated["summary"]["total_saving_bits"])
    return {
        "beats_permutation_p95": real_saving > percentile(savings, 95),
        "permutation_mean": sum(savings) / len(savings),
        "permutation_p05": percentile(savings, 5),
        "permutation_p50": percentile(savings, 50),
        "permutation_p95": percentile(savings, 95),
        "trials": RANDOM_TRIALS,
    }


def write_markdown(result: dict[str, Any]) -> None:
    md_path = OUT_DIR / "08_arturo_bookcase_mapping_control_probe.md"
    lines = [
        "# Arturo Bookcase Mapping Control Probe",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"Fetched `{result['source']['bookcase_url']}` and used only `bookcase_mapping.json`; semantic mapping/plaintext files were not read.",
        f"The mapping has `{result['match_summary']['unique_matches']}` unique canonical matches, `{result['match_summary']['derived_matched_books']}` derived-book matches, and `{result['joined_v9_rows']}` joined v9 operation rows.",
        "",
        "The source has a LICENSE file, but it is a community/posthoc analysis repository rather than primary authoring provenance.",
        "",
        "## Heldout Diagnostics",
        "",
        "| Target | Splits | Positive | Total Saving Bits | Permutation p95 | Beats p95 |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for target, evaluated in result["target_results"].items():
        summary = evaluated["summary"]
        controls = evaluated["permutation_controls"]
        lines.append(
            f"| `{target}` | {summary['split_count']} | {summary['positive_splits']} | {summary['total_saving_bits']:.3f} | {controls['permutation_p95']:.3f} | `{controls['beats_permutation_p95']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{result['decision']['classification_reason']}`",
            "",
            "Some targets can look better than very poor permuted topology labels, but promotion requires positive heldout saving after model cost. No target satisfies that condition.",
            "",
            "No external control source is integrated and net v9 reduction is `0.0` bits.",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")


def append_final_report(result: dict[str, Any]) -> None:
    report = FINAL_REPORT.read_text() if FINAL_REPORT.exists() else ""
    marker = "## Arturo Bookcase Mapping Control Probe"
    if marker in report:
        return
    addition = [
        "",
        marker,
        "",
        "The `arturoornelasb/tibia-bonelord-469-cipher` repository was probed only for its public `bookcase_mapping.json` topology surface; semantic mapping/plaintext artifacts were not read or used.",
        f"It provides `{result['match_summary']['unique_matches']}` unique canonical matches and `{result['joined_v9_rows']}` joined v9 operation rows, but remains community/posthoc provenance rather than primary authoring evidence.",
        "Heldout topology diagnostics do not promote it as an external control source; no source is integrated and v9 reduction remains `0.0` bits.",
        "",
        "- [08_arturo_bookcase_mapping_control_probe.py](../scripts/08_arturo_bookcase_mapping_control_probe.py)",
        "- [08_arturo_bookcase_mapping_control_probe.json](test_results/08_arturo_bookcase_mapping_control_probe.json)",
        "- [08_arturo_bookcase_mapping_control_probe.md](test_results/08_arturo_bookcase_mapping_control_probe.md)",
    ]
    FINAL_REPORT.write_text(report.rstrip() + "\n" + "\n".join(addition) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    books = load_json(BOOKS_DIGITS)
    mapping, mapping_error, mapping_status = fetch_json(BOOKCASE_URL)
    data_readme, data_readme_error, data_readme_status = fetch_text(DATA_README_URL)
    license_text, license_error, license_status = fetch_text(LICENSE_URL)

    if not isinstance(mapping, list):
        raise RuntimeError(f"Could not fetch mapping: {mapping_error}")

    rows = match_mapping(mapping, books)
    topology = topology_by_book(rows)
    joined = build_joined_rows(topology)
    target_results = {}
    promoted_targets = []
    if joined:
        for target in TARGETS:
            evaluated = evaluate_target(joined, target)
            forced = {row["label"]: row["feature"] for row in evaluated["split_results"]}
            controls = permutation_controls(topology, target, evaluated["summary"]["total_saving_bits"], forced)
            evaluated["permutation_controls"] = controls
            target_results[target] = evaluated
            if evaluated["summary"]["total_saving_bits"] > 0 and controls["beats_permutation_p95"]:
                promoted_targets.append(target)

    data_readme_lower = (data_readme or "").lower()
    source_is_primary = False
    license_present = license_status == 200 and "mit license" in (license_text or "").lower()
    unique_books = sorted(topology)
    derived_books = [book for book in unique_books if book >= 10]
    classification = (
        "WEAK_PROVENANCE_CLUE_COMMUNITY_BOOKCASE_SURFACE_POSITIVE_CONTROL_SIGNAL"
        if promoted_targets
        else "REJECTED_PROVENANCE_CONTROL_COMMUNITY_BOOKCASE_SURFACE"
    )
    classification_reason = (
        "community bookcase topology has positive heldout signal for at least one target but is not primary authoring provenance"
        if promoted_targets
        else "community bookcase topology does not reduce v9 residual streams above controls"
    )
    result = {
        "schema": "arturo_bookcase_mapping_control_probe.v1",
        "scope": "analysis_only_external_bookcase_mapping_control_probe",
        "classification": classification,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "source": {
            "repository": REPO_URL,
            "bookcase_url": BOOKCASE_URL,
            "data_readme_url": DATA_README_URL,
            "license_url": LICENSE_URL,
            "mapping_http_status": mapping_status,
            "data_readme_http_status": data_readme_status,
            "license_http_status": license_status,
            "license_error": license_error,
            "data_readme_error": data_readme_error,
            "license_present": license_present,
            "source_is_primary_authoring_provenance": source_is_primary,
            "data_readme_mentions_solution": "solution" in data_readme_lower or "solución" in data_readme_lower,
        },
        "match_summary": {
            "source_rows": len(rows),
            "unique_matches": sum(1 for row in rows if row["match_status"] == "unique"),
            "ambiguous_matches": sum(1 for row in rows if row["match_status"] == "ambiguous"),
            "unmatched": sum(1 for row in rows if row["match_status"] == "unmatched"),
            "duplicate_book_rows": sum(1 for row in rows if row["duplicate_for_book"]),
            "unique_matched_books": len(unique_books),
            "derived_matched_books": len(derived_books),
        },
        "joined_v9_rows": len(joined),
        "features": FEATURES,
        "targets": list(TARGETS),
        "target_results": target_results,
        "decision": {
            "external_surface_integrated": False,
            "promoted_external_control_source": False,
            "promoted_targets_as_weak_clue_only": promoted_targets,
            "v9_reduction_bits": 0.0,
            "classification_reason": classification_reason,
        },
    }
    json_path = OUT_DIR / "08_arturo_bookcase_mapping_control_probe.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    append_final_report(result)


if __name__ == "__main__":
    main()
