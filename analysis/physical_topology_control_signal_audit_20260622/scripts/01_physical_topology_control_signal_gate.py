#!/usr/bin/env python3
"""Physical-topology control-signal gate.

Public Hellgate bookcase topology has already failed as a read order and as a
simple row0-similarity signal. This gate tests a narrower mechanical question:
does the partial public bookcase/order metadata predict residual generation
streams in the executable decoder ledger better than topology-label shuffles?

This remains analysis-only. The public manifest is partial, ambiguous, and not
fine tile/slot topology. Only resolved unique public entries are used.
"""

from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "physical_topology_control_signal_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

TOPOLOGY_MANIFEST = (
    ROOT
    / "analysis"
    / "physical_topology_20260620"
    / "tables"
    / "hellgate_public_bookcase_manifest.csv"
)
UNIFIED_TAPE_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
PUBLIC_TOPOLOGY_AUDIT = (
    ROOT
    / "analysis"
    / "physical_topology_20260620"
    / "reports"
    / "test_results"
    / "01_public_topology_manifest_audit.json"
)
TOPOLOGY_SIGNAL_AUDIT = (
    ROOT
    / "analysis"
    / "physical_topology_20260620"
    / "reports"
    / "test_results"
    / "02_topology_mechanical_signal_audit.json"
)

JSON_OUT = TEST_RESULTS / "01_physical_topology_control_signal_gate.json"
MD_OUT = TEST_RESULTS / "01_physical_topology_control_signal_gate.md"
FINAL_OUT = FRONT / "reports" / "final_physical_topology_control_signal_audit.md"

RANDOM_SEED = 46920260622 + 5
RANDOM_TRIALS = 150
ALPHA = 0.5
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]

FEATURES = [
    "topology_bookcase",
    "topology_entry_bucket",
    "topology_bookcase_x_op_pos",
    "topology_entry_bucket_x_op_pos",
    "topology_bookcase_x_length_bucket",
]
TARGETS = {
    "coarse_control": {
        "row_filter": "all",
        "target_field": "coarse_type_length_bucket",
    },
    "copy_hint_rank_bucket": {
        "row_filter": "copy",
        "target_field": "copy_hint_rank_bucket",
    },
    "op_type": {
        "row_filter": "all",
        "target_field": "op_type",
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened the case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    decision = data.get("decision", {})
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")


def load_topology() -> dict[int, dict[str, Any]]:
    mapping: dict[int, dict[str, Any]] = {}
    with TOPOLOGY_MANIFEST.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["local_match_status"] != "resolved_unique":
                continue
            book = int(row["local_bookid"])
            entry = int(row["hg_public_entry"])
            bookcase = int(row["bookcase_public"])
            mapping[book] = {
                "bookcase": bookcase,
                "entry": entry,
                "entry_bucket": f"entry_q{min(3, int((entry - 1) / 71 * 4))}",
            }
    return mapping


def feature_value(row: dict[str, Any], feature: str) -> str:
    if feature == "topology_bookcase":
        return f"bookcase_{row['topology_bookcase']:02d}"
    if feature == "topology_entry_bucket":
        return row["topology_entry_bucket"]
    if feature == "topology_bookcase_x_op_pos":
        return f"bookcase_{row['topology_bookcase']:02d}|{row['op_pos_bucket']}"
    if feature == "topology_entry_bucket_x_op_pos":
        return f"{row['topology_entry_bucket']}|{row['op_pos_bucket']}"
    if feature == "topology_bookcase_x_length_bucket":
        return f"bookcase_{row['topology_bookcase']:02d}|{row['book_length_bucket']}"
    raise KeyError(feature)


def build_rows(
    ledger: dict[str, Any],
    topology: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for raw in ledger["ledger_rows"]:
        book = int(raw["book"])
        if book not in topology:
            continue
        target_copy_hint = raw.get("copy_hint_rank_bucket")
        rows.append(
            {
                "book": book,
                "book_length_bucket": raw["book_length_bucket"],
                "coarse_type_length_bucket": raw["coarse_type_length_bucket"],
                "copy_hint_rank_bucket": target_copy_hint,
                "op_index": int(raw["op_index"]),
                "op_pos_bucket": raw["op_pos_bucket"],
                "op_type": raw["op_type"],
                "topology_bookcase": topology[book]["bookcase"],
                "topology_entry": topology[book]["entry"],
                "topology_entry_bucket": topology[book]["entry_bucket"],
            }
        )
    return rows


def target_rows(rows: list[dict[str, Any]], target_name: str) -> list[dict[str, Any]]:
    spec = TARGETS[target_name]
    if spec["row_filter"] == "copy":
        return [row for row in rows if row["op_type"] == "copy" and row[spec["target_field"]] is not None]
    return rows


def target_alphabet(rows: list[dict[str, Any]], target_name: str) -> list[str]:
    field = TARGETS[target_name]["target_field"]
    return sorted({str(row[field]) for row in target_rows(rows, target_name)})


def train_counts(
    rows: list[dict[str, Any]],
    target_name: str,
    feature: str | None,
) -> tuple[Counter[str], dict[str, Counter[str]]]:
    field = TARGETS[target_name]["target_field"]
    global_counts: Counter[str] = Counter()
    feature_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in target_rows(rows, target_name):
        symbol = str(row[field])
        global_counts[symbol] += 1
        if feature is not None:
            feature_counts[feature_value(row, feature)][symbol] += 1
    return global_counts, feature_counts


def code_bits(
    train: list[dict[str, Any]],
    test: list[dict[str, Any]],
    target_name: str,
    feature: str | None,
    alphabet: list[str],
) -> float:
    global_counts, feature_counts = train_counts(train, target_name, feature)
    field = TARGETS[target_name]["target_field"]
    vocab = len(alphabet)
    bits = 0.0
    for row in target_rows(test, target_name):
        symbol = str(row[field])
        if feature is None:
            counter = global_counts
        else:
            counter = feature_counts.get(feature_value(row, feature), global_counts)
        total = sum(counter.values())
        probability = (counter.get(symbol, 0) + ALPHA) / (total + ALPHA * vocab)
        bits += -math.log2(probability)
    return bits


def loo_train_bits(
    rows: list[dict[str, Any]],
    target_name: str,
    feature: str,
    alphabet: list[str],
) -> float:
    books = sorted({row["book"] for row in rows})
    if len(books) < 2:
        return float("inf")
    total = 0.0
    for heldout in books:
        train = [row for row in rows if row["book"] != heldout]
        test = [row for row in rows if row["book"] == heldout]
        total += code_bits(train, test, target_name, feature, alphabet)
    return total + math.log2(len(FEATURES))


def select_feature(train: list[dict[str, Any]], target_name: str, alphabet: list[str]) -> dict[str, Any]:
    candidates = []
    for feature in FEATURES:
        candidates.append(
            {
                "feature": feature,
                "loo_train_bits": loo_train_bits(train, target_name, feature, alphabet),
            }
        )
    return min(candidates, key=lambda row: (row["loo_train_bits"], row["feature"]))


def split_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    splits = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        if train and test:
            splits.append({"label": f"prefix_{cutoff}", "split_type": "prefix", "train": train, "test": test})
    bookcases = sorted({row["topology_bookcase"] for row in rows})
    for bookcase in bookcases:
        train = [row for row in rows if row["topology_bookcase"] != bookcase]
        test = [row for row in rows if row["topology_bookcase"] == bookcase]
        if train and test and len({row["book"] for row in test}) >= 2:
            splits.append(
                {
                    "label": f"leave_bookcase_{bookcase:02d}",
                    "split_type": "leave_bookcase",
                    "train": train,
                    "test": test,
                }
            )
    return splits


def evaluate_splits(
    rows: list[dict[str, Any]],
    target_name: str,
    forced_features_by_split: dict[str, str] | None = None,
) -> dict[str, Any]:
    alphabet = target_alphabet(rows, target_name)
    split_results = []
    for split in split_rows(rows):
        if forced_features_by_split and split["label"] in forced_features_by_split:
            selected = {
                "feature": forced_features_by_split[split["label"]],
                "loo_train_bits": None,
            }
        else:
            selected = select_feature(split["train"], target_name, alphabet)
        global_bits = code_bits(split["train"], split["test"], target_name, None, alphabet)
        topology_bits = code_bits(
            split["train"],
            split["test"],
            target_name,
            selected["feature"],
            alphabet,
        ) + math.log2(len(FEATURES))
        test_rows = target_rows(split["test"], target_name)
        split_results.append(
            {
                "feature": selected["feature"],
                "global_bits": global_bits,
                "label": split["label"],
                "saving_bits": global_bits - topology_bits,
                "split_type": split["split_type"],
                "target_rows": len(test_rows),
                "topology_bits": topology_bits,
                "train_books": len({row["book"] for row in split["train"]}),
            }
        )
    total_global = sum(row["global_bits"] for row in split_results)
    total_topology = sum(row["topology_bits"] for row in split_results)
    return {
        "alphabet_size": len(alphabet),
        "split_results": split_results,
        "summary": {
            "positive_splits": sum(row["saving_bits"] > 0 for row in split_results),
            "split_count": len(split_results),
            "total_global_bits": total_global,
            "total_saving_bits": total_global - total_topology,
            "total_target_rows": sum(row["target_rows"] for row in split_results),
            "total_topology_bits": total_topology,
        },
    }


def permute_topology(topology: dict[int, dict[str, Any]], rng: random.Random) -> dict[int, dict[str, Any]]:
    books = sorted(topology)
    values = [dict(topology[book]) for book in books]
    rng.shuffle(values)
    return {book: value for book, value in zip(books, values)}


def permutation_controls(
    ledger: dict[str, Any],
    topology: dict[int, dict[str, Any]],
    target_name: str,
    real_saving: float,
    forced_features_by_split: dict[str, str],
) -> dict[str, Any]:
    stable_offset = sum(ord(ch) for ch in target_name)
    rng = random.Random(RANDOM_SEED + stable_offset)
    savings = []
    for _ in range(RANDOM_TRIALS):
        rows = build_rows(ledger, permute_topology(topology, rng))
        savings.append(
            evaluate_splits(
                rows,
                target_name,
                forced_features_by_split=forced_features_by_split,
            )["summary"]["total_saving_bits"]
        )
    return {
        "beats_permutation_p95": real_saving > percentile(savings, 95),
        "permutation_mean": sum(savings) / len(savings),
        "permutation_p05": percentile(savings, 5),
        "permutation_p50": percentile(savings, 50),
        "permutation_p95": percentile(savings, 95),
        "trials": RANDOM_TRIALS,
    }


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(p / 100 * len(ordered)) - 1))
    return ordered[index]


def make_result() -> dict[str, Any]:
    ledger = load_json(UNIFIED_TAPE_LEDGER)
    manifest_audit = load_json(PUBLIC_TOPOLOGY_AUDIT)
    signal_audit = load_json(TOPOLOGY_SIGNAL_AUDIT)
    assert_boundary("unified_external_tape_ledger", ledger)
    assert_boundary("public_topology_manifest_audit", manifest_audit)
    assert_boundary("topology_mechanical_signal_audit", signal_audit)
    topology = load_topology()
    rows = build_rows(ledger, topology)
    target_results = {}
    promoted = []
    weak = []
    for target_name in TARGETS:
        evaluated = evaluate_splits(rows, target_name)
        forced_features_by_split = {
            row["label"]: row["feature"]
            for row in evaluated["split_results"]
        }
        controls = permutation_controls(
            ledger,
            topology,
            target_name,
            evaluated["summary"]["total_saving_bits"],
            forced_features_by_split,
        )
        evaluated["permutation_controls"] = controls
        target_results[target_name] = evaluated
        if evaluated["summary"]["total_saving_bits"] > 0 and controls["beats_permutation_p95"]:
            promoted.append(target_name)
        elif evaluated["summary"]["total_saving_bits"] > 0:
            weak.append(target_name)
    classification = (
        "PROMOTED_PARTIAL_TOPOLOGY_CONTROL_SIGNAL"
        if promoted
        else "WEAK_PARTIAL_TOPOLOGY_CONTROL_SIGNAL"
        if weak
        else "PARTIAL_TOPOLOGY_CONTROL_SIGNAL_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "fine_topology_available": False,
            "generator_promoted": False,
            "promoted_targets": promoted,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
            "weak_targets": weak,
        },
        "inputs": {
            "public_topology_manifest": rel(TOPOLOGY_MANIFEST),
            "public_topology_manifest_audit": rel(PUBLIC_TOPOLOGY_AUDIT),
            "topology_mechanical_signal_audit": rel(TOPOLOGY_SIGNAL_AUDIT),
            "unified_external_tape_ledger": rel(UNIFIED_TAPE_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "physical_topology_control_signal_gate.v1",
        "scope": "analysis_only_partial_public_topology_vs_residual_control_streams",
        "summary": {
            "covered_books": len({row["book"] for row in rows}),
            "covered_operations": len(rows),
            "random_trials": RANDOM_TRIALS,
            "resolved_unique_topology_books": len(topology),
            "target_summaries": {
                target: {
                    **data["summary"],
                    "beats_permutation_p95": data["permutation_controls"]["beats_permutation_p95"],
                    "permutation_p95": data["permutation_controls"]["permutation_p95"],
                }
                for target, data in target_results.items()
            },
        },
        "target_results": target_results,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# Physical Topology Control Signal Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether partial public Hellgate bookcase/order metadata predicts "
        "residual executable-decoder control streams better than topology-label "
        "permutations.",
        "",
        "## Summary",
        "",
        f"- Resolved unique topology books: `{result['summary']['resolved_unique_topology_books']}`.",
        f"- Covered derived books: `{result['summary']['covered_books']}`.",
        f"- Covered operations: `{result['summary']['covered_operations']}`.",
        "",
        "| Target | Saving | Global bits | Topology bits | Positive splits | Permutation p95 | Beats p95 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for target, data in result["target_results"].items():
        summary = data["summary"]
        controls = data["permutation_controls"]
        lines.append(
            f"| `{target}` | `{summary['total_saving_bits']:.3f}` | "
            f"`{summary['total_global_bits']:.3f}` | `{summary['total_topology_bits']:.3f}` | "
            f"`{summary['positive_splits']}/{summary['split_count']}` | "
            f"`{controls['permutation_p95']:.3f}` | `{controls['beats_permutation_p95']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Promotion requires positive heldout savings that beat topology-label "
            "permutation p95. Partial public topology is not fine tile/slot topology "
            "and cannot by itself promote an authorial order or plaintext.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    promoted = result["decision"]["promoted_targets"]
    weak = result["decision"]["weak_targets"]
    lines = [
        "# Final Physical Topology Control Signal Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can partial public Hellgate bookcase/order metadata predict residual "
        "generation-control streams in the executable decoder ledger?",
        "",
        "## Result",
        "",
        f"Promoted targets: `{promoted}`. Weak positive targets: `{weak}`.",
        "",
        "| Target | Saving | Permutation p95 | Beats p95 |",
        "| --- | ---: | ---: | --- |",
    ]
    for target, data in result["target_results"].items():
        summary = data["summary"]
        controls = data["permutation_controls"]
        lines.append(
            f"| `{target}` | `{summary['total_saving_bits']:.3f}` | "
            f"`{controls['permutation_p95']:.3f}` | `{controls['beats_permutation_p95']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Partial public topology does not become a generator unless it predicts "
            "residual streams above permutation controls. Row0, plaintext, translation, "
            "and compression_bound remain unchanged.",
            "",
            "## Reproducible Artifacts",
            "",
            "- [01_physical_topology_control_signal_gate.py](../scripts/01_physical_topology_control_signal_gate.py)",
            "- [01_physical_topology_control_signal_gate.json](test_results/01_physical_topology_control_signal_gate.json)",
            "- [01_physical_topology_control_signal_gate.md](test_results/01_physical_topology_control_signal_gate.md)",
        ]
    )
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
