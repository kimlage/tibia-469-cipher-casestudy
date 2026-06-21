from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

ONLINE_LITERAL = TEST_RESULTS / "06_online_literal_stop_rule_audit.json"
ONLINE_LITERAL_SCRIPT = HERE / "scripts" / "06_online_literal_stop_rule_audit.py"

OUT_STEM = "07_literal_stop_exception_topology_audit"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def classify_failure(row: dict[str, Any]) -> str:
    stable = int(row["literal_length"])
    predicted = int(row["predicted_literal_length"])
    start = int(row["target_start"])
    if start == 0 and predicted < stable:
        return "book_start_understop"
    if start == 0 and predicted > stable:
        return "book_start_overstop"
    if stable <= 1 and predicted == 0:
        return "microgap_zero_offset_understop"
    if stable >= 20 and predicted < stable:
        return "long_internal_understop"
    return "unclassified"


def score_predicate(
    rows: list[dict[str, Any]],
    name: str,
    predicate: Callable[[dict[str, Any]], bool],
    uses_stable_boundary: bool,
) -> dict[str, Any]:
    failures = [row for row in rows if not row["ok"]]
    ok_rows = [row for row in rows if row["ok"]]
    tp = sum(1 for row in failures if predicate(row))
    fp = sum(1 for row in ok_rows if predicate(row))
    return {
        "predicate": name,
        "true_positive_exceptions": tp,
        "false_positive_ok_rows": fp,
        "precision": None if tp + fp == 0 else tp / (tp + fp),
        "recall": tp / len(failures),
        "uses_stable_boundary": uses_stable_boundary,
        "promotes_exception_rule": False,
    }


def make_result() -> dict[str, Any]:
    online = load_json(ONLINE_LITERAL)
    assert_boundary("online_literal_stop_rule_audit", online)
    helper = load_module("online_literal_stop_for_gate07", ONLINE_LITERAL_SCRIPT)
    rows = []
    for row in [
        item
        for item in helper.build_literal_rows()
        if item["next_op_type"] == "copy"
    ]:
        predicted = helper.predict_first_confirmed_peak(
            row, "max_copy_length", 6
        )
        enriched = {
            "book": int(row["book"]),
            "op_index": int(row["op_index"]),
            "target_start": int(row["target_start"]),
            "literal_length": int(row["literal_length"]),
            "next_copy_length": int(row["next_copy_length"]),
            "predicted_literal_length": predicted,
            "prediction_error": None
            if predicted is None
            else predicted - int(row["literal_length"]),
            "predicted_copy_length": None
            if predicted is None
            else row["offset_rows"][predicted]["max_copy_length"],
            "predicted_total_advance": None
            if predicted is None
            else row["offset_rows"][predicted]["total_advance"],
            "ok": predicted == int(row["literal_length"]),
        }
        rows.append(enriched)

    failures = [row for row in rows if not row["ok"]]
    for row in failures:
        row["exception_class"] = classify_failure(row)
    class_counts: dict[str, int] = {}
    for row in failures:
        class_counts[row["exception_class"]] = class_counts.get(row["exception_class"], 0) + 1

    predicate_rows = [
        score_predicate(
            rows,
            "source_free_predicted_offset_zero",
            lambda row: row["predicted_literal_length"] == 0,
            False,
        ),
        score_predicate(
            rows,
            "source_free_predicted_copy_le8",
            lambda row: row["predicted_copy_length"] is not None
            and row["predicted_copy_length"] <= 8,
            False,
        ),
        score_predicate(
            rows,
            "source_free_book_start",
            lambda row: row["target_start"] == 0,
            False,
        ),
        score_predicate(
            rows,
            "diagnostic_predicted_before_stable",
            lambda row: row["prediction_error"] is not None
            and row["prediction_error"] < 0,
            True,
        ),
        score_predicate(
            rows,
            "diagnostic_abs_error_ge6",
            lambda row: row["prediction_error"] is not None
            and abs(row["prediction_error"]) >= 6,
            True,
        ),
        score_predicate(
            rows,
            "diagnostic_short_next_or_long_literal",
            lambda row: row["next_copy_length"] <= 8 or row["literal_length"] >= 20,
            True,
        ),
    ]
    best_source_free = max(
        [row for row in predicate_rows if not row["uses_stable_boundary"]],
        key=lambda row: (row["recall"], row["precision"] or 0),
    )
    promotes_exception_rule = (
        best_source_free["recall"] == 1.0
        and best_source_free["false_positive_ok_rows"] == 0
    )
    return {
        "schema": "literal_stop_exception_topology_audit.v1",
        "classification": "literal_stop_exceptions_heterogeneous_no_rule_promoted",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "online_literal_stop_rule_audit": rel(ONLINE_LITERAL),
        },
        "summary": {
            "followed_by_copy_rows": len(rows),
            "online_rule_hits": sum(1 for row in rows if row["ok"]),
            "exception_count": len(failures),
            "exception_classes": class_counts,
            "best_source_free_exception_flag": best_source_free,
            "promotes_exception_rule": promotes_exception_rule,
            "interpretation": (
                "The four online literal-stop misses are heterogeneous. "
                "Source-free flags such as book-start, predicted offset zero, "
                "or short predicted copy do not isolate them without false "
                "positives. Diagnostic predicates can describe the failures "
                "after seeing the stable stop, but they are not generation rules."
            ),
        },
        "exception_rows": failures,
        "predicate_rows": predicate_rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "literal_stop_residual_exceptions_mapped",
            "literal_window_status": "four_exceptions_retained",
            "source_free_parser_status": "not_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    s = result["summary"]
    lines = [
        "# Literal Stop Exception Topology Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 06 left four followed-by-copy literal-stop exceptions. This audit",
        "maps whether they form a promotable mechanical class or remain retained",
        "exceptions.",
        "",
        "## Exception Classes",
        "",
        f"- Online rule hits: `{s['online_rule_hits']}/{s['followed_by_copy_rows']}`.",
        f"- Exception count: `{s['exception_count']}`.",
        f"- Classes: `{s['exception_classes']}`.",
        "",
        "| Book | Op | Target start | Stable literal | Predicted | Error | Next copy | Class |",
        "|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["exception_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['target_start']}` | "
            f"`{row['literal_length']}` | `{row['predicted_literal_length']}` | "
            f"`{row['prediction_error']}` | `{row['next_copy_length']}` | "
            f"`{row['exception_class']}` |"
        )
    lines.extend(
        [
            "",
            "## Predicate Controls",
            "",
            "| Predicate | TP | FP | Precision | Recall | Uses stable boundary |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in result["predicate_rows"]:
        precision = "None" if row["precision"] is None else f"{row['precision']:.3f}"
        lines.append(
            f"| `{row['predicate']}` | `{row['true_positive_exceptions']}` | "
            f"`{row['false_positive_ok_rows']}` | `{precision}` | "
            f"`{row['recall']:.3f}` | `{row['uses_stable_boundary']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes exception rule: `{s['promotes_exception_rule']}`.",
            f"- {s['interpretation']}",
            "- The four literal-stop exceptions remain retained.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
