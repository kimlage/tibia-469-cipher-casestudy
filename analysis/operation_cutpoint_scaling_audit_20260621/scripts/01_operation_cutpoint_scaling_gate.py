from __future__ import annotations

import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

SKELETON_SCRIPT = (
    ROOT
    / "analysis"
    / "source_free_skeleton_generation_audit_20260621"
    / "scripts"
    / "02_source_free_skeleton_grammar_gate.py"
)
MOTIF_GATE = (
    ROOT
    / "analysis"
    / "operation_length_motif_audit_20260621"
    / "reports"
    / "test_results"
    / "01_operation_length_motif_library_gate.json"
)

OUT_STEM = "01_operation_cutpoint_scaling_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


BookRow = dict[str, Any]
KeyFn = Callable[[BookRow], str]


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


def reconstruct() -> dict[int, list[dict[str, Any]]]:
    module = load_module("source_free_skeleton_for_cutpoint_scaling", SKELETON_SCRIPT)
    return module.reconstruct_canonical_skeleton()


def cumulative(lengths: list[int]) -> list[int]:
    total = 0
    out = []
    for length in lengths:
        total += length
        out.append(total)
    return out


def make_rows(by_book: dict[int, list[dict[str, Any]]]) -> list[BookRow]:
    rows = []
    for book in sorted(by_book):
        lengths = [int(op["length"]) for op in by_book[book]]
        types = [str(op["type"]) for op in by_book[book]]
        book_length = sum(lengths)
        cuts = cumulative(lengths)[:-1]
        ratios = [cut / book_length for cut in cuts]
        type_counts = Counter(types)
        rows.append(
            {
                "book": book,
                "book_length": book_length,
                "op_count": len(lengths),
                "copy_count": type_counts["copy"],
                "literal_count": type_counts["literal"],
                "type_sequence": ",".join(types),
                "lengths": lengths,
                "cutpoints": cuts,
                "ratios": ratios,
            }
        )
    return rows


def key_families() -> dict[str, KeyFn]:
    return {
        "op_count": lambda row: f"ops={row['op_count']}",
        "copy_literal_counts": lambda row: (
            f"copy={row['copy_count']}|lit={row['literal_count']}"
        ),
        "type_sequence": lambda row: f"type_seq={row['type_sequence']}",
        "book_length_bucket_x_op_count": lambda row: (
            f"lenb={bucket(int(row['book_length']))}|ops={row['op_count']}"
        ),
        "book_mod10_x_op_count": lambda row: (
            f"bookmod10={int(row['book']) % 10}|ops={row['op_count']}"
        ),
    }


def bucket(value: int) -> str:
    if value <= 80:
        return "le80"
    if value <= 120:
        return "le120"
    if value <= 160:
        return "le160"
    if value <= 220:
        return "le220"
    return "gt220"


def mean_template(rows: list[BookRow]) -> list[float]:
    if not rows:
        return []
    width = len(rows[0]["ratios"])
    if any(len(row["ratios"]) != width for row in rows):
        raise RuntimeError("template rows with mixed op counts")
    return [sum(row["ratios"][i] for row in rows) / len(rows) for i in range(width)]


def train_templates(rows: list[BookRow], key_name: str, key_fn: KeyFn) -> dict[str, Any]:
    groups: dict[str, list[BookRow]] = defaultdict(list)
    by_op_count: dict[int, list[BookRow]] = defaultdict(list)
    for row in rows:
        groups[key_fn(row)].append(row)
        by_op_count[int(row["op_count"])].append(row)
    templates = {}
    for key, values in groups.items():
        if len({int(row["op_count"]) for row in values}) == 1:
            templates[key] = mean_template(values)
    fallback = {
        str(op_count): mean_template(values) for op_count, values in by_op_count.items()
    }
    global_by_closest = {
        str(op_count): mean_template(values) for op_count, values in by_op_count.items()
    }
    return {
        "key_name": key_name,
        "templates": templates,
        "fallback_by_op_count": fallback,
        "global_by_closest": global_by_closest,
        "template_count": len(templates),
        "template_payload_records": sum(len(value) for value in templates.values()),
    }


def ratios_to_lengths(ratios: list[float], book_length: int, op_count: int) -> list[int]:
    if op_count == 1:
        return [book_length]
    raw_cuts = [round(ratio * book_length) for ratio in ratios]
    cuts = []
    previous = 0
    remaining_cuts = len(raw_cuts)
    for cut in raw_cuts:
        min_cut = previous + 1
        max_cut = book_length - remaining_cuts
        cut = max(min_cut, min(cut, max_cut))
        cuts.append(cut)
        previous = cut
        remaining_cuts -= 1
    lengths = []
    previous = 0
    for cut in cuts + [book_length]:
        lengths.append(cut - previous)
        previous = cut
    if len(lengths) != op_count or sum(lengths) != book_length or min(lengths) <= 0:
        raise RuntimeError("bad scaled lengths")
    return lengths


def closest_op_template(model: dict[str, Any], op_count: int) -> list[float] | None:
    if str(op_count) in model["fallback_by_op_count"]:
        return model["fallback_by_op_count"][str(op_count)]
    if not model["global_by_closest"]:
        return None
    closest = min(model["global_by_closest"], key=lambda key: abs(int(key) - op_count))
    template = list(model["global_by_closest"][closest])
    if len(template) == op_count - 1:
        return template
    return None


def predict_lengths(row: BookRow, model: dict[str, Any], key_fn: KeyFn) -> list[int] | None:
    key = key_fn(row)
    template = model["templates"].get(key)
    if template is None:
        template = closest_op_template(model, int(row["op_count"]))
    if template is None or len(template) != int(row["op_count"]) - 1:
        return None
    return ratios_to_lengths(template, int(row["book_length"]), int(row["op_count"]))


def evaluate(rows: list[BookRow], model: dict[str, Any], key_fn: KeyFn) -> dict[str, Any]:
    out_rows = []
    for row in rows:
        predicted = predict_lengths(row, model, key_fn)
        exact_book = predicted == row["lengths"]
        row_hits = 0
        total_abs_error = None
        if predicted is not None:
            row_hits = sum(1 for left, right in zip(predicted, row["lengths"]) if left == right)
            total_abs_error = sum(abs(left - right) for left, right in zip(predicted, row["lengths"]))
        out_rows.append(
            {
                "book": row["book"],
                "op_count": row["op_count"],
                "predicted": predicted,
                "exact_book": exact_book,
                "row_hits": row_hits,
                "total_abs_error": total_abs_error,
            }
        )
    exact_books = sum(1 for row in out_rows if row["exact_book"])
    row_hits = sum(row["row_hits"] for row in out_rows)
    truth_ops = sum(int(row["op_count"]) for row in rows)
    missing = sum(1 for row in out_rows if row["predicted"] is None)
    correction_records = truth_ops - row_hits
    total_records = model["template_payload_records"] + len(rows) + correction_records
    return {
        "key_name": model["key_name"],
        "template_count": model["template_count"],
        "template_payload_records": model["template_payload_records"],
        "book_count": len(rows),
        "exact_books": exact_books,
        "row_hits": row_hits,
        "truth_ops": truth_ops,
        "missing_predictions": missing,
        "correction_records": correction_records,
        "total_records": total_records,
        "delta_vs_exact_atlas_records": total_records - truth_ops,
        "rows": out_rows,
    }


def prequential(rows: list[BookRow], keys: dict[str, KeyFn]) -> list[dict[str, Any]]:
    result = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        train_scores = []
        trained = []
        for name, fn in keys.items():
            model = train_templates(train, name, fn)
            score = evaluate(train, model, fn)
            train_scores.append(score)
            trained.append((name, fn, model, score))
        selected_name, selected_fn, selected_model, selected_train = min(
            trained,
            key=lambda item: (
                item[3]["delta_vs_exact_atlas_records"],
                -item[3]["exact_books"],
                -item[3]["row_hits"],
                item[0],
            ),
        )
        test_score = evaluate(test, selected_model, selected_fn)
        oracle = min(
            [evaluate(test, model, fn) for _name, fn, model, _score in trained],
            key=lambda score: (
                score["delta_vs_exact_atlas_records"],
                -score["exact_books"],
                -score["row_hits"],
                score["key_name"],
            ),
        )
        result.append(
            {
                "cutoff_book": cutoff,
                "selected_key": selected_name,
                "train_delta_vs_exact_atlas_records": selected_train[
                    "delta_vs_exact_atlas_records"
                ],
                "test_exact_books": test_score["exact_books"],
                "test_book_count": test_score["book_count"],
                "test_row_hits": test_score["row_hits"],
                "test_truth_ops": test_score["truth_ops"],
                "test_delta_vs_exact_atlas_records": test_score[
                    "delta_vs_exact_atlas_records"
                ],
                "oracle_key": oracle["key_name"],
                "oracle_test_delta_vs_exact_atlas_records": oracle[
                    "delta_vs_exact_atlas_records"
                ],
                "selected_matches_oracle": (
                    test_score["delta_vs_exact_atlas_records"]
                    == oracle["delta_vs_exact_atlas_records"]
                    and test_score["exact_books"] == oracle["exact_books"]
                ),
            }
        )
    return result


def make_result() -> dict[str, Any]:
    motif = load_json(MOTIF_GATE)
    assert_boundary("operation_length_motif_gate", motif)
    by_book = reconstruct()
    rows = make_rows(by_book)
    keys = key_families()
    full_scores = []
    for name, fn in keys.items():
        model = train_templates(rows, name, fn)
        full_scores.append(evaluate(rows, model, fn))
    full_scores.sort(
        key=lambda score: (
            score["delta_vs_exact_atlas_records"],
            -score["exact_books"],
            -score["row_hits"],
            score["key_name"],
        )
    )
    preq = prequential(rows, keys)
    best = full_scores[0]
    promotes = (
        best["exact_books"] == best["book_count"]
        and best["delta_vs_exact_atlas_records"] < 0
        and all(row["test_exact_books"] == row["test_book_count"] for row in preq)
    )
    classification = (
        "operation_cutpoint_scaling_generator_promoted"
        if promotes
        else "operation_cutpoint_scaling_generator_rejected"
    )
    return {
        "schema": "operation_cutpoint_scaling_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_free_skeleton_script": rel(SKELETON_SCRIPT),
            "operation_length_motif_gate": rel(MOTIF_GATE),
        },
        "scope": {
            "analysis_only": True,
            "book_lengths_granted": True,
            "op_count_or_type_sequence_granted_by_key": True,
            "tests_normalized_cutpoint_templates": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "book_count": len(rows),
            "operation_count": sum(int(row["op_count"]) for row in rows),
            "key_family_count": len(keys),
            "best_key": best["key_name"],
            "best_template_count": best["template_count"],
            "best_template_payload_records": best["template_payload_records"],
            "best_exact_books": best["exact_books"],
            "best_row_hits": best["row_hits"],
            "best_truth_ops": best["truth_ops"],
            "best_delta_vs_exact_atlas_records": best[
                "delta_vs_exact_atlas_records"
            ],
            "prequential_cells": len(preq),
            "prequential_cover_all_cells": sum(
                1 for row in preq if row["test_exact_books"] == row["test_book_count"]
            ),
            "prequential_positive_delta_cells": sum(
                1 for row in preq if row["test_delta_vs_exact_atlas_records"] > 0
            ),
            "promotes_cutpoint_scaling_generator": promotes,
            "interpretation": (
                "Normalized cutpoint templates do not generate the operation "
                "length atlas. Full-fit templates either memorize too much or "
                "need correction records, and prefix holdout never covers all "
                "future books."
            ),
        },
        "full_fit_scoreboard": [
            {key: value for key, value in row.items() if key != "rows"}
            for row in full_scores
        ],
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "operation_length_status": "atlas_retained_after_cutpoint_scaling_gate",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    lines = [
        "# Operation Cutpoint Scaling Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether operation lengths are generated by normalized cutpoint",
        "templates scaled to the granted book length.",
        "",
        "## Summary",
        "",
        f"- Books/operations: `{s['book_count']}` / `{s['operation_count']}`.",
        f"- Key families: `{s['key_family_count']}`.",
        f"- Best key: `{s['best_key']}`.",
        f"- Best templates/payload records: `{s['best_template_count']}` / `{s['best_template_payload_records']}`.",
        f"- Best exact books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Best row hits: `{s['best_row_hits']}/{s['best_truth_ops']}`.",
        f"- Best delta vs exact atlas records: `{s['best_delta_vs_exact_atlas_records']:+d}`.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_cells']}/{s['prequential_cells']}`.",
        "",
        "## Full-Fit Scoreboard",
        "",
        "| Key | Templates | Payload | Exact books | Row hits | Delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["full_fit_scoreboard"]:
        lines.append(
            f"| `{row['key_name']}` | `{row['template_count']}` | "
            f"`{row['template_payload_records']}` | "
            f"`{row['exact_books']}/{row['book_count']}` | "
            f"`{row['row_hits']}/{row['truth_ops']}` | "
            f"`{row['delta_vs_exact_atlas_records']:+d}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Key | Test exact books | Test row hits | Test delta | Oracle key |",
            "| ---: | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_key']}` | "
            f"`{row['test_exact_books']}/{row['test_book_count']}` | "
            f"`{row['test_row_hits']}/{row['test_truth_ops']}` | "
            f"`{row['test_delta_vs_exact_atlas_records']:+d}` | "
            f"`{row['oracle_key']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes cutpoint-scaling generator: `{s['promotes_cutpoint_scaling_generator']}`.",
            f"- {s['interpretation']}",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
